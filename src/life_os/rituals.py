"""Definitions of the scheduled second-brain rituals.

A `Ritual` is a scheduled, self-contained nudge that fires once per window and
asks the user to run a Claude Code slash command. The scheduler is pure — it
decides what's due; the daemon calls `ui.notify` / `ui.open_claude` to deliver.

Times are parsed from config (strings like ``"08:00"`` or ``"Sun 10:00"``) at
daemon start so we don't repeatedly parse inside the loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

InvokeMode = Literal["notify_only", "dialog", "terminal", "headless"]


@dataclass(frozen=True)
class Ritual:
    """A scheduled second-brain nudge."""

    id: str
    display_name: str
    cron: str  # "HH:MM" or "<Dow> HH:MM" (Dow ∈ Mon/Tue/Wed/Thu/Fri/Sat/Sun)
    slash_command: str  # e.g. "/daily"
    notification_title: str
    notification_body: str
    invoke: InvokeMode = "dialog"
    grace_min: int = 30  # fire if we missed the exact minute within this window


# The default ritual set. Users don't edit this file — they override `cron` via
# Config.<ritual>_at fields; the daemon rebuilds this list at startup.
DEFAULT_RITUALS: list[Ritual] = [
    Ritual(
        id="morning_journal",
        display_name="Morning journal",
        cron="08:00",
        slash_command="/daily",
        notification_title="Morning journal 🌅",
        notification_body="A few minutes to set the day. Open today's daily?",
    ),
    Ritual(
        id="midday_inbox",
        display_name="Process inbox",
        cron="12:00",
        slash_command="/process-inbox",
        notification_title="Inbox check 📥",
        notification_body="Clear the inbox before lunch?",
        invoke="notify_only",
    ),
    Ritual(
        id="evening_shutdown",
        display_name="Evening shutdown",
        cron="17:00",
        slash_command="/shutdown",
        notification_title="Shutdown 🌙",
        notification_body="Close out the day — reflection + tomorrow's top three.",
    ),
    Ritual(
        id="weekly_review",
        display_name="Weekly review",
        cron="Sun 10:00",
        slash_command="/weekly-review",
        notification_title="Weekly review 📓",
        notification_body="Sunday review — 20 minutes.",
    ),
]


def build_rituals_from_config(
    morning_at: str,
    midday_at: str,
    evening_at: str,
    weekly_at: str,
) -> list[Ritual]:
    """Apply user-configured times to the default ritual definitions."""
    overrides = {
        "morning_journal": morning_at,
        "midday_inbox": midday_at,
        "evening_shutdown": evening_at,
        "weekly_review": weekly_at,
    }
    return [
        Ritual(
            id=r.id,
            display_name=r.display_name,
            cron=overrides.get(r.id, r.cron),
            slash_command=r.slash_command,
            notification_title=r.notification_title,
            notification_body=r.notification_body,
            invoke=r.invoke,
            grace_min=r.grace_min,
        )
        for r in DEFAULT_RITUALS
    ]
