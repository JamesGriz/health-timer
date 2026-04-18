"""Tests for ritual definitions + config-driven overrides."""

from __future__ import annotations

from life_os.rituals import DEFAULT_RITUALS, build_rituals_from_config


def test_default_ritual_ids_are_unique() -> None:
    ids = [r.id for r in DEFAULT_RITUALS]
    assert len(ids) == len(set(ids))


def test_default_rituals_cover_four_moments() -> None:
    ids = {r.id for r in DEFAULT_RITUALS}
    assert ids == {"morning_journal", "midday_inbox", "evening_shutdown", "weekly_review"}


def test_build_rituals_applies_overrides() -> None:
    rituals = build_rituals_from_config(
        morning_at="07:30",
        midday_at="13:00",
        evening_at="18:15",
        weekly_at="Sat 09:00",
    )
    crons = {r.id: r.cron for r in rituals}
    assert crons["morning_journal"] == "07:30"
    assert crons["midday_inbox"] == "13:00"
    assert crons["evening_shutdown"] == "18:15"
    assert crons["weekly_review"] == "Sat 09:00"


def test_build_preserves_slash_commands() -> None:
    rituals = build_rituals_from_config("08:00", "12:00", "17:00", "Sun 10:00")
    commands = {r.id: r.slash_command for r in rituals}
    assert commands["morning_journal"] == "/daily"
    assert commands["weekly_review"] == "/weekly-review"
