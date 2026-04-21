from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from zoneinfo import ZoneInfo

from src.scheduler_plugin.calendar_engine import get_schedule_for_date, is_weekend_or_holiday
from src.scheduler_plugin.data_source import load_recent_post_performance
from src.scheduler_plugin.models.article import Article
from src.scheduler_plugin.schedule_config import REPOST_LANE, SPECIAL_LANE
from src.scheduler_plugin.time_provider import TimeProvider
from src.scheduler_plugin.traffic_model import build_traffic_stats

BREAKING_PRIORITY_MAP = {3: 0, 2: 1, 1: 2}

HK_TZ = ZoneInfo("Asia/Hong_Kong")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SchedulerEngine:
    EXCLUDED_BREAKING_TYPES = {"death", "marriage", "baby"}
    PRIMARY_CANDIDATE_COUNT = 3

    def __init__(self) -> None:
        self.primary_candidates: Dict[datetime, List[Article]] = {}

    def run(self, now: datetime, articles: List[Article]) -> Dict[datetime, Article]:
        if now.tzinfo is None:
            now = now.replace(tzinfo=HK_TZ)

        for a in articles:
            a.is_scheduled = False

        self.primary_candidates.clear()

        history = load_recent_post_performance()
        traffic_stats = build_traffic_stats(history)

        draft: Dict[datetime, Article] = {}

        today = now.date()
        tomorrow = today + timedelta(days=1)

        for target_date in [today, tomorrow]:
            draft = self._generate_schedule_for_date(now, target_date, articles, traffic_stats, draft)

        self._force_insert_breaking_news(now, articles, draft)
        self._rebalance_soft_locked_slots(draft, articles)
        self._validate_no_duplicate(draft)

        logging.info("Scheduling completed successfully")
        return draft

    def run_2350_repost_job(self) -> None:
        try:
            from src.scheduler_plugin import repost_nightly

            result = repost_nightly.run_nightly_repost_job()
            logging.info("[23:50 REPOST JOB] result=%s", result)
        except Exception as e:
            logging.error("[23:50 REPOST JOB FAILED] %s", e)

    def _is_primary_slot(self, slot_time: str, target_date):
        if is_weekend_or_holiday(target_date):
            return slot_time == "10:30"
        return slot_time == "08:30"

    def _generate_schedule_for_date(self, now, target_date, articles, traffic_stats, draft_schedule):
        schedule = get_schedule_for_date(target_date)
        prime_slots = self._build_prime_slots(traffic_stats)

        for slot in schedule:
            slot_datetime = datetime.combine(
                target_date,
                datetime.strptime(slot["time"], "%H:%M").time(),
                tzinfo=HK_TZ,
            )

            if slot_datetime < now:
                continue

            if slot_datetime in draft_schedule:
                continue

            article = None
            mode = slot.get("mode", "auto")
            lane = slot.get("lane")

            if lane == REPOST_LANE:
                article = self._select_link_repost(slot, articles)
            elif lane == SPECIAL_LANE:
                article = self._select_fixed_link(slot, articles)
            elif mode == "manual":
                logging.info("Manual slot at %s, waiting for user selection", slot_datetime)
                continue
            else:
                article = self._select_auto(slot, articles, prime_slots, target_date, slot_datetime)

            if article:
                article.is_scheduled = True
                draft_schedule[slot_datetime] = article
                logging.info("Scheduled article %s at %s", article.id, slot_datetime)

        return draft_schedule

    def _select_auto(self, slot, articles, prime_slots, target_date, slot_datetime):
        candidates = [
            a
            for a in articles
            if a.category in slot.get("categories", []) and not a.is_scheduled and not a.is_published_to_fb
        ]

        if not candidates:
            return None

        if self._is_primary_slot(slot["time"], target_date):
            filtered = [a for a in candidates if getattr(a, "breaking_type", None) not in self.EXCLUDED_BREAKING_TYPES]
            if not filtered:
                filtered = candidates
            filtered.sort(key=lambda x: self._calculate_score(x), reverse=True)
            self.primary_candidates[slot_datetime] = filtered[: self.PRIMARY_CANDIDATE_COUNT]
            return filtered[0]

        candidates.sort(key=lambda x: self._calculate_score(x), reverse=True)
        return candidates[0]

    def _select_fixed_link(self, slot, articles):
        return next(
            (a for a in articles if getattr(a, "source_type", None) == slot.get("source") and not a.is_scheduled),
            None,
        )

    def _select_link_repost(self, slot, articles):
        candidates = [
            a
            for a in articles
            if a.category in slot.get("categories", [])
            and a.is_published_to_fb
            and getattr(a, "is_high_engagement", False)
        ]

        if not candidates:
            return None

        candidates.sort(key=lambda x: x.heat_score, reverse=True)
        return candidates[0]

    def _build_prime_slots(self, traffic_stats):
        if not traffic_stats:
            return []
        sorted_slots = sorted(traffic_stats.items(), key=lambda x: x[1], reverse=True)
        top_n = max(1, int(len(sorted_slots) * 0.25))
        return [slot for slot, _ in sorted_slots[:top_n]]

    def _calculate_score(self, article):
        score = article.heat_score
        if getattr(article, "social_share", False):
            score += 1000
        return score

    def _force_insert_breaking_news(self, now, articles, draft_schedule):
        breaking_articles = [
            a
            for a in articles
            if getattr(a, "urgency_level", 0) > 0 and not a.is_scheduled and not a.is_published_to_fb
        ]

        if not breaking_articles:
            return

        breaking_articles.sort(key=lambda x: (BREAKING_PRIORITY_MAP.get(x.urgency_level, 99), -x.heat_score))

        for article in breaking_articles:
            priority = BREAKING_PRIORITY_MAP.get(article.urgency_level, 99)

            if priority == 0:
                target_time = now + timedelta(minutes=2)
            else:
                future_slots = sorted([t for t in draft_schedule.keys() if t > now and draft_schedule[t] != article])
                if not future_slots:
                    continue
                target_time = future_slots[0]

            if target_time in draft_schedule:
                replaced = draft_schedule[target_time]
                replaced.is_scheduled = False
                draft_schedule[target_time] = article
                article.is_scheduled = True
                logging.warning("[BREAKING] priority=%s inserted at %s, replaced %s", priority, target_time, replaced.id)
            else:
                draft_schedule[target_time] = article
                article.is_scheduled = True
                logging.warning("[BREAKING] priority=%s inserted new slot at %s", priority, target_time)

    def _rebalance_soft_locked_slots(self, draft_schedule, articles):
        unscheduled = [a for a in articles if not a.is_scheduled and not a.is_published_to_fb]
        unscheduled.sort(key=lambda x: x.heat_score, reverse=True)

        for slot_time, article in draft_schedule.items():
            if not getattr(article, "soft_locked", False):
                continue
            if not unscheduled:
                break
            best_candidate = unscheduled[0]
            if best_candidate.heat_score > article.heat_score:
                article.is_scheduled = False
                best_candidate.is_scheduled = True
                draft_schedule[slot_time] = best_candidate
                logging.info("Rebalanced slot %s with article %s", slot_time, best_candidate.id)

    def _validate_no_duplicate(self, draft_schedule):
        seen = set()
        for article in draft_schedule.values():
            if article.id in seen:
                raise RuntimeError(f"Duplicate scheduling detected: {article.id}")
            seen.add(article.id)
