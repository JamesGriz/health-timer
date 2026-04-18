"""Tests for the pure ritual scheduler."""

from __future__ import annotations

import datetime as dt

import pytest

from life_os.rituals import Ritual
from life_os.scheduler import due_now, parse_cron


def _r(cron: str, rid: str = "test", grace: int = 30) -> Ritual:
    return Ritual(
        id=rid,
        display_name="Test",
        cron=cron,
        slash_command="/noop",
        notification_title="T",
        notification_body="B",
        grace_min=grace,
    )


# ─── parse_cron ──────────────────────────────────────────────────────────────


def test_parse_cron_daily() -> None:
    assert parse_cron("08:00") == (None, 8, 0)


def test_parse_cron_weekly() -> None:
    assert parse_cron("Sun 10:00") == (6, 10, 0)


def test_parse_cron_rejects_bad_weekday() -> None:
    with pytest.raises(ValueError):
        parse_cron("Xyz 10:00")


def test_parse_cron_rejects_malformed() -> None:
    with pytest.raises(ValueError):
        parse_cron("just some words that don't parse")


# ─── due_now ────────────────────────────────────────────────────────────────


def test_fires_at_exact_minute() -> None:
    now = dt.datetime(2026, 4, 20, 8, 0)  # Monday 08:00
    due = due_now([_r("08:00")], last_fired={}, now=now)
    assert [r.id for r in due] == ["test"]


def test_fires_within_grace_window() -> None:
    now = dt.datetime(2026, 4, 20, 8, 25)
    due = due_now([_r("08:00", grace=30)], last_fired={}, now=now)
    assert len(due) == 1


def test_does_not_fire_before_target() -> None:
    now = dt.datetime(2026, 4, 20, 7, 59)
    due = due_now([_r("08:00")], last_fired={}, now=now)
    assert due == []


def test_does_not_fire_past_grace_window() -> None:
    now = dt.datetime(2026, 4, 20, 8, 45)
    due = due_now([_r("08:00", grace=30)], last_fired={}, now=now)
    assert due == []


def test_fires_weekly_ritual_on_matching_dow_only() -> None:
    # April 20 2026 is a Monday; April 19 is a Sunday.
    sunday = dt.datetime(2026, 4, 19, 10, 0)
    monday = dt.datetime(2026, 4, 20, 10, 0)
    assert len(due_now([_r("Sun 10:00")], last_fired={}, now=sunday)) == 1
    assert due_now([_r("Sun 10:00")], last_fired={}, now=monday) == []


def test_does_not_fire_twice_same_day() -> None:
    first = dt.datetime(2026, 4, 20, 8, 0)
    second = dt.datetime(2026, 4, 20, 8, 5)
    last_fired: dict[str, float] = {}
    due_now([_r("08:00")], last_fired=last_fired, now=first)
    # Same day, same ritual → suppressed.
    again = due_now([_r("08:00")], last_fired=last_fired, now=second)
    assert again == []


def test_fires_again_next_day() -> None:
    first = dt.datetime(2026, 4, 20, 8, 0)
    last_fired: dict[str, float] = {}
    due_now([_r("08:00")], last_fired=last_fired, now=first)

    next_day = dt.datetime(2026, 4, 21, 8, 0)
    again = due_now([_r("08:00")], last_fired=last_fired, now=next_day)
    assert len(again) == 1


def test_multiple_rituals_due_in_same_poll() -> None:
    now = dt.datetime(2026, 4, 20, 8, 0)
    due = due_now(
        [_r("08:00", "a"), _r("08:00", "b"), _r("17:00", "c")],
        last_fired={},
        now=now,
    )
    assert sorted(r.id for r in due) == ["a", "b"]


def test_malformed_ritual_is_skipped_not_crashing() -> None:
    now = dt.datetime(2026, 4, 20, 8, 0)
    due = due_now([_r("not-a-time", "bad"), _r("08:00", "good")], last_fired={}, now=now)
    assert [r.id for r in due] == ["good"]
