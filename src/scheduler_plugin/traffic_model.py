from __future__ import annotations


def calculate_score(post):
    return post["reach"] * 0.5 + post["engagement"] * 0.3 + post["clicks"] * 0.2


def build_traffic_stats(history_posts):
    stats: dict[str, list[float]] = {}
    for post in history_posts:
        time = post["post_time"]
        score = calculate_score(post)
        stats.setdefault(time, []).append(score)
    return {time: sum(scores) / len(scores) for time, scores in stats.items()}
