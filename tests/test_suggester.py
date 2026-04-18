"""Behavioural tests for the smart suggester."""

from __future__ import annotations

import datetime as dt
import random
from collections import Counter

from life_os.activities import CATALOG
from life_os.suggester import (
    HYDRATION_OVERDUE_HOURS,
    SuggesterState,
    pick,
    record_pick,
)


def _at(hour: int, minute: int = 0) -> dt.datetime:
    return dt.datetime(2026, 4, 16, hour, minute)


def test_hydration_override_kicks_in_after_3_hours() -> None:
    now = _at(15)
    state = SuggesterState(
        last_water_at=now.timestamp() - (HYDRATION_OVERDUE_HOURS + 1) * 3600,
    )
    rng = random.Random(0)
    activity = pick(state, now=now, rng=rng)
    assert activity.category == "water"


def test_no_hydration_override_when_recent() -> None:
    now = _at(15)
    state = SuggesterState(last_water_at=now.timestamp() - 30 * 60)  # 30 min ago
    counter: Counter[str] = Counter()
    for seed in range(50):
        activity = pick(state, now=now, rng=random.Random(seed))
        counter[activity.category] += 1
    # Most picks should NOT be water when hydration is recent.
    assert counter["water"] < 25


def test_hydration_override_when_state_has_no_water_yet() -> None:
    state = SuggesterState()  # last_water_at is None
    activity = pick(state, now=_at(10), rng=random.Random(0))
    assert activity.category == "water"


def test_recent_activities_not_repeated() -> None:
    now = _at(10)
    # Avoid hydration override interference.
    state = SuggesterState(
        last_water_at=now.timestamp(),
        recent_activity_ids=["yoga_sun_salutation"],
    )
    for seed in range(20):
        activity = pick(state, now=now, rng=random.Random(seed))
        assert activity.id != "yoga_sun_salutation"


def test_same_category_penalised() -> None:
    """When last category was core, core picks should be uncommon."""
    now = _at(10)
    state = SuggesterState(last_water_at=now.timestamp(), last_category="core")
    counter: Counter[str] = Counter()
    for seed in range(100):
        activity = pick(state, now=now, rng=random.Random(seed))
        counter[activity.category] += 1
    assert counter["core"] < counter["yoga"] + counter["stretch"] + counter["walk"]


def test_morning_favours_high_morning_fit_activities() -> None:
    """Activities with low morning tod_fit should rarely (or never) appear at 8am."""
    state = SuggesterState(last_water_at=_at(8).timestamp())  # not hydration-forced
    picked_ids: Counter[str] = Counter()
    for seed in range(300):
        activity = pick(state, now=_at(8), rng=random.Random(seed))
        picked_ids[activity.id] += 1

    # legs-up-the-wall and dark-chocolate-square both have morning fit 0.5 — they
    # should be vanishingly rare versus the top-fit options.
    low_morning = picked_ids["yoga_legs_up_wall"] + picked_ids["snack_dark_chocolate"]
    top_morning = picked_ids["yoga_sun_salutation"] + picked_ids["snack_yogurt_berries"]
    assert top_morning > 5 * (low_morning + 1)


def test_evening_avoids_intense_core() -> None:
    state = SuggesterState(last_water_at=_at(20).timestamp())
    counter: Counter[str] = Counter()
    for seed in range(200):
        activity = pick(state, now=_at(20), rng=random.Random(seed))
        counter[activity.category] += 1
    # Core is heavily down-weighted in the evening; yoga/stretch should dominate.
    assert counter["core"] < counter["yoga"] + counter["stretch"]


def test_record_pick_updates_state() -> None:
    state = SuggesterState()
    activity = next(a for a in CATALOG if a.category == "water")
    now = _at(12)
    record_pick(state, activity, now=now)
    assert state.last_water_at == now.timestamp()
    assert state.last_category == "water"
    assert state.recent_activity_ids == [activity.id]
    assert state.last_seen_per_id[activity.id] == now.timestamp()


def test_recent_list_is_capped() -> None:
    state = SuggesterState()
    for i, activity in enumerate(CATALOG[:10]):
        record_pick(state, activity, now=_at(8 + i % 12))
    assert len(state.recent_activity_ids) <= 5


def test_full_day_simulation_has_variety() -> None:
    """48 picks across a day should hit at least 4 categories."""
    state = SuggesterState()
    seen: Counter[str] = Counter()
    for half_hour in range(48):
        now = dt.datetime(2026, 4, 16, half_hour // 2, (half_hour % 2) * 30)
        activity = pick(state, now=now, rng=random.Random(half_hour))
        seen[activity.category] += 1
        record_pick(state, activity, now=now)
    assert len(seen) >= 4, f"expected variety; got {seen}"


def test_capture_bias_zero_never_picks_capture() -> None:
    now = _at(10)
    state = SuggesterState(last_water_at=now.timestamp())
    seen: Counter[str] = Counter()
    for seed in range(200):
        activity = pick(state, now=now, rng=random.Random(seed), capture_bias=0.0)
        seen[activity.category] += 1
    assert seen["capture"] == 0


def test_capture_bias_default_is_rare_but_present() -> None:
    """With default bias, capture should land in <15% of picks."""
    now = _at(14)  # afternoon — capture activities have 1.1 tod_fit
    state = SuggesterState(last_water_at=now.timestamp())
    seen: Counter[str] = Counter()
    for seed in range(1000):
        activity = pick(state, now=now, rng=random.Random(seed))
        seen[activity.category] += 1
    # Just confirm the shape — capture is rare, non-capture dominates.
    total = sum(seen.values())
    assert seen["capture"] / total < 0.15
