"""Smart activity selection.

The aim is for the next break to feel fresh, surprising, and well-timed —
never the same thing twice in a row, but also nudging hydration when overdue.
"""

from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass, field

from .activities import CATALOG, Activity, time_window

HYDRATION_OVERDUE_HOURS = 3
NOVELTY_LOOKBACK_DAYS = 14
RECENT_CAP = 5
TOP_N_SAMPLE = 5

# Capture activities are deliberately rare — they pull the user into a Claude
# Code session during their break, which we want to feel like a treat, not a
# chore. The multiplier lands capture at ~1-in-10 picks with the default bias.
DEFAULT_CAPTURE_BIAS = 0.3


@dataclass
class SuggesterState:
    """The minimum state the suggester needs to make a good pick."""

    recent_activity_ids: list[str] = field(default_factory=list)
    last_water_at: float | None = None  # unix timestamp
    last_category: str | None = None
    last_seen_per_id: dict[str, float] = field(default_factory=dict)


def _recency_penalty(activity: Activity, state: SuggesterState) -> float:
    if activity.id in state.recent_activity_ids:
        return 0.0
    if state.last_category and activity.category == state.last_category:
        return 0.3
    return 1.0


def _novelty_boost(activity: Activity, state: SuggesterState, now_ts: float) -> float:
    last_seen = state.last_seen_per_id.get(activity.id)
    if last_seen is None:
        return 1.2
    days_since = (now_ts - last_seen) / 86400
    return 1.2 if days_since >= NOVELTY_LOOKBACK_DAYS else 1.0


def _hydration_overdue(state: SuggesterState, now_ts: float) -> bool:
    if state.last_water_at is None:
        return True
    return (now_ts - state.last_water_at) >= HYDRATION_OVERDUE_HOURS * 3600


def pick(
    state: SuggesterState,
    now: dt.datetime | None = None,
    rng: random.Random | None = None,
    capture_bias: float = DEFAULT_CAPTURE_BIAS,
) -> Activity:
    """Pick a single activity tailored to the current moment.

    Args:
        state: persisted history used to avoid repeats and track hydration.
        now: defaults to ``datetime.now()`` (injectable for tests).
        rng: defaults to a fresh ``Random()`` (injectable for tests).
        capture_bias: multiplier on ``category == "capture"`` scores. Default
            ``0.3`` makes capture rare (~1 in 10). Set ``0.0`` to disable.

    Returns:
        The chosen :class:`Activity`. Always returns something — the catalog
        is large enough that scores never collectively reach zero.
    """
    now = now or dt.datetime.now()
    rng = rng or random.Random()
    now_ts = now.timestamp()
    window = time_window(now.hour)

    # Hydration override: if it's been too long, pick water from the start.
    candidates = CATALOG
    if _hydration_overdue(state, now_ts):
        water_pool = [a for a in CATALOG if a.category == "water"]
        # Still apply recency so we vary the water option chosen.
        candidates = water_pool

    scored: list[tuple[float, Activity]] = []
    for activity in candidates:
        tod = activity.tod_fit.get(window, 1.0)
        score = tod * _recency_penalty(activity, state) * _novelty_boost(activity, state, now_ts)
        if activity.category == "capture":
            score *= capture_bias
        if score > 0:
            scored.append((score, activity))

    # If recency penalties zeroed everything (rare), fall back to full catalog.
    if not scored:
        scored = [(activity.tod_fit.get(window, 1.0), activity) for activity in candidates]

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = scored[:TOP_N_SAMPLE]
    weights = [score for score, _ in top]
    activities = [a for _, a in top]
    return rng.choices(activities, weights=weights, k=1)[0]


def record_pick(state: SuggesterState, activity: Activity, now: dt.datetime | None = None) -> None:
    """Update ``state`` after a break completes so future picks stay varied."""
    now = now or dt.datetime.now()
    now_ts = now.timestamp()

    state.recent_activity_ids.append(activity.id)
    if len(state.recent_activity_ids) > RECENT_CAP:
        state.recent_activity_ids = state.recent_activity_ids[-RECENT_CAP:]

    state.last_category = activity.category
    state.last_seen_per_id[activity.id] = now_ts
    if activity.category == "water":
        state.last_water_at = now_ts
