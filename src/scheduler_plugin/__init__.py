"""Ported FB auto-scheduler engine + CMS board adapters (see SCHEDULER_PLUGIN.md)."""

from src.scheduler_plugin.pipeline import generate_schedule_suggestions

__all__ = ["generate_schedule_suggestions"]
