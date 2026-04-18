"""Catalog of healthy break activities.

Each activity has time-of-day fit weights so the suggester can pick something
appropriate for the moment. Categories rotate so consecutive breaks feel varied.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Category = Literal["walk", "snack", "water", "stretch", "core", "yoga", "capture"]
TimeWindow = Literal["morning", "midday", "afternoon", "evening"]


@dataclass(frozen=True)
class Activity:
    """A single break activity."""

    id: str
    display_name: str
    description: str
    category: Category
    duration_min: int
    tod_fit: dict[TimeWindow, float] = field(
        default_factory=lambda: {"morning": 1.0, "midday": 1.0, "afternoon": 1.0, "evening": 1.0}
    )


# Time-of-day weights cheat sheet:
#   morning  06:00–11:00  energising activities
#   midday   11:00–14:00  food + longer movement
#   afternoon 14:00–17:00 hydration + posture resets
#   evening  17:00–22:00  wind-down, gentler movement


CATALOG: list[Activity] = [
    # ─── Walks ────────────────────────────────────────────────────────────
    Activity(
        id="walk_outside_loop",
        display_name="Outside loop",
        description="Step outside and walk a 10-minute loop. Bonus: leave your phone.",
        category="walk",
        duration_min=10,
        tod_fit={"morning": 1.3, "midday": 1.5, "afternoon": 1.2, "evening": 0.8},
    ),
    Activity(
        id="walk_stairs",
        display_name="Stair climb",
        description="Climb 5 floors of stairs, twice. Steady pace, breathe through the nose.",
        category="walk",
        duration_min=7,
        tod_fit={"morning": 1.3, "midday": 1.0, "afternoon": 1.2, "evening": 0.6},
    ),
    Activity(
        id="walk_mindful",
        display_name="Mindful walk",
        description="5-minute walk. Notice 5 sounds, 5 sights, 5 sensations. Reset.",
        category="walk",
        duration_min=5,
        tod_fit={"morning": 1.0, "midday": 1.0, "afternoon": 1.2, "evening": 1.3},
    ),
    Activity(
        id="walk_water_run",
        display_name="Water-fill walk",
        description="Walk to refill your bottle. Take the long way. Reset posture on the way back.",
        category="walk",
        duration_min=5,
        tod_fit={"morning": 1.0, "midday": 1.0, "afternoon": 1.3, "evening": 1.0},
    ),
    Activity(
        id="walk_long",
        display_name="15-min explore walk",
        description="Pick a direction you don't usually go and walk for 15 minutes.",
        category="walk",
        duration_min=15,
        tod_fit={"morning": 1.0, "midday": 1.5, "afternoon": 1.0, "evening": 0.8},
    ),
    # ─── Snacks ───────────────────────────────────────────────────────────
    Activity(
        id="snack_apple_almonds",
        display_name="Apple + almonds",
        description="Apple with a small handful of almonds. Slow protein + crunch.",
        category="snack",
        duration_min=5,
        tod_fit={"morning": 1.4, "midday": 0.6, "afternoon": 1.4, "evening": 0.6},
    ),
    Activity(
        id="snack_yogurt_berries",
        display_name="Yogurt + berries",
        description="Greek yogurt with berries. Protein + antioxidants.",
        category="snack",
        duration_min=5,
        tod_fit={"morning": 1.5, "midday": 0.8, "afternoon": 1.0, "evening": 0.5},
    ),
    Activity(
        id="snack_carrots_hummus",
        display_name="Carrots + hummus",
        description="Carrot sticks with hummus. Crunch + savoury fix.",
        category="snack",
        duration_min=5,
        tod_fit={"morning": 0.6, "midday": 1.2, "afternoon": 1.4, "evening": 0.8},
    ),
    Activity(
        id="snack_banana_pb",
        display_name="Banana + peanut butter",
        description="Banana with a spoon of peanut butter. Quick fuel, stable energy.",
        category="snack",
        duration_min=5,
        tod_fit={"morning": 1.4, "midday": 1.0, "afternoon": 1.2, "evening": 0.5},
    ),
    Activity(
        id="snack_dark_chocolate",
        display_name="Dark chocolate square",
        description="One square of dark chocolate (70%+) and a glass of water. Mindful.",
        category="snack",
        duration_min=5,
        tod_fit={"morning": 0.5, "midday": 0.8, "afternoon": 1.4, "evening": 1.2},
    ),
    # ─── Water ────────────────────────────────────────────────────────────
    Activity(
        id="water_cold_glass",
        display_name="Cold water reset",
        description="Drink a full 16oz / 500ml glass of cold water. Slowly.",
        category="water",
        duration_min=5,
        tod_fit={"morning": 1.5, "midday": 1.2, "afternoon": 1.3, "evening": 0.8},
    ),
    Activity(
        id="water_herbal_tea",
        display_name="Herbal tea brew",
        description="Brew a cup of herbal tea. Wait. Smell it. Sip slowly.",
        category="water",
        duration_min=8,
        tod_fit={"morning": 1.2, "midday": 1.0, "afternoon": 1.3, "evening": 1.5},
    ),
    Activity(
        id="water_sparkling_lemon",
        display_name="Sparkling water + lemon",
        description="Glass of sparkling water with a squeeze of lemon. Refreshing reset.",
        category="water",
        duration_min=5,
        tod_fit={"morning": 1.0, "midday": 1.3, "afternoon": 1.4, "evening": 0.8},
    ),
    Activity(
        id="water_electrolytes",
        display_name="Electrolyte top-up",
        description="Glass of water with a pinch of salt + lemon, or an electrolyte tab.",
        category="water",
        duration_min=5,
        tod_fit={"morning": 1.3, "midday": 1.0, "afternoon": 1.2, "evening": 0.6},
    ),
    # ─── Stretches ────────────────────────────────────────────────────────
    Activity(
        id="stretch_neck_shoulders",
        display_name="Neck + shoulders",
        description="Neck rolls (5 each way) + shoulder shrugs (10) + ear-to-shoulder hold (30s/side).",
        category="stretch",
        duration_min=5,
        tod_fit={"morning": 1.0, "midday": 1.0, "afternoon": 1.4, "evening": 1.2},
    ),
    Activity(
        id="stretch_wrist_forearm",
        display_name="Wrist + forearm reset",
        description="Prayer stretch (30s) + reverse prayer (30s) + wrist circles (10 each way).",
        category="stretch",
        duration_min=5,
        tod_fit={"morning": 0.8, "midday": 1.0, "afternoon": 1.4, "evening": 1.3},
    ),
    Activity(
        id="stretch_doorway_chest",
        display_name="Doorway chest opener",
        description="Doorway chest stretch — 30s × 3, alternating high/mid/low arm position.",
        category="stretch",
        duration_min=5,
        tod_fit={"morning": 1.2, "midday": 1.0, "afternoon": 1.4, "evening": 1.2},
    ),
    Activity(
        id="stretch_hamstring_hipflexor",
        display_name="Hamstring + hip flexor",
        description="Standing forward fold (30s) + half-kneeling hip flexor stretch (30s/side × 2).",
        category="stretch",
        duration_min=7,
        tod_fit={"morning": 1.2, "midday": 1.0, "afternoon": 1.3, "evening": 1.3},
    ),
    Activity(
        id="stretch_full_body",
        display_name="Full-body flow",
        description="Reach overhead → side bends → forward fold → squat → roll up. 3 rounds, slow.",
        category="stretch",
        duration_min=7,
        tod_fit={"morning": 1.4, "midday": 1.1, "afternoon": 1.2, "evening": 1.2},
    ),
    # ─── Core ─────────────────────────────────────────────────────────────
    Activity(
        id="core_plank_rotations",
        display_name="Plank rotations",
        description="30s plank → 30s right side plank → 30s left side plank. Repeat ×2 with 15s rest.",
        category="core",
        duration_min=7,
        tod_fit={"morning": 1.4, "midday": 1.2, "afternoon": 1.0, "evening": 0.5},
    ),
    Activity(
        id="core_dead_bug",
        display_name="Dead bug",
        description="Dead bug — 10/side, controlled, lower back glued to floor. 3 rounds.",
        category="core",
        duration_min=5,
        tod_fit={"morning": 1.3, "midday": 1.2, "afternoon": 1.0, "evening": 0.6},
    ),
    Activity(
        id="core_bicycle_legraise",
        display_name="Bicycle + leg raises",
        description="20 bicycle crunches + 10 slow leg raises. 2 rounds.",
        category="core",
        duration_min=6,
        tod_fit={"morning": 1.3, "midday": 1.1, "afternoon": 1.0, "evening": 0.5},
    ),
    Activity(
        id="core_mountain_climbers",
        display_name="Mountain climbers",
        description="30s mountain climbers, 30s rest — 4 rounds. Steady, not sprinting.",
        category="core",
        duration_min=5,
        tod_fit={"morning": 1.4, "midday": 1.2, "afternoon": 0.9, "evening": 0.4},
    ),
    Activity(
        id="core_birddog_glutebridge",
        display_name="Bird-dog + glute bridge",
        description="10 bird-dogs/side + 15 glute bridges. 2 rounds. Focus on the squeeze.",
        category="core",
        duration_min=7,
        tod_fit={"morning": 1.2, "midday": 1.1, "afternoon": 1.1, "evening": 0.7},
    ),
    # ─── Yoga ─────────────────────────────────────────────────────────────
    Activity(
        id="yoga_sun_salutation",
        display_name="Sun salutation A × 5",
        description="5 rounds of Sun Salutation A. Match breath to movement.",
        category="yoga",
        duration_min=8,
        tod_fit={"morning": 1.6, "midday": 1.0, "afternoon": 0.8, "evening": 0.8},
    ),
    Activity(
        id="yoga_cat_cow_child",
        display_name="Cat-cow + child's pose",
        description="2 min cat-cow, 2 min child's pose, 2 min thread-the-needle.",
        category="yoga",
        duration_min=8,
        tod_fit={"morning": 1.0, "midday": 1.0, "afternoon": 1.2, "evening": 1.4},
    ),
    Activity(
        id="yoga_hip_openers",
        display_name="Hip openers",
        description="Pigeon (1 min/side) + lizard (1 min/side) + figure-4 (1 min/side).",
        category="yoga",
        duration_min=10,
        tod_fit={"morning": 0.8, "midday": 1.0, "afternoon": 1.2, "evening": 1.5},
    ),
    Activity(
        id="yoga_standing_balance",
        display_name="Standing balance flow",
        description="Tree pose (30s/side) + warrior 3 (30s/side) + half-moon (30s/side). Repeat ×2.",
        category="yoga",
        duration_min=8,
        tod_fit={"morning": 1.3, "midday": 1.1, "afternoon": 1.0, "evening": 1.0},
    ),
    Activity(
        id="yoga_legs_up_wall",
        display_name="Legs up the wall",
        description="Lie on your back, legs up the wall. 8 minutes. Slow breath. Eyes closed.",
        category="yoga",
        duration_min=10,
        tod_fit={"morning": 0.5, "midday": 0.8, "afternoon": 1.2, "evening": 1.6},
    ),
    # ─── Capture (vault-integrated breaks) ────────────────────────────────
    Activity(
        id="capture_inbox",
        display_name="Inbox clear",
        description="Open one Inbox note. File it, zettel it, or bin it. One item only.",
        category="capture",
        duration_min=3,
        tod_fit={"morning": 1.0, "midday": 1.1, "afternoon": 1.1, "evening": 0.9},
    ),
    Activity(
        id="capture_zettel",
        display_name="One atomic thought",
        description="Capture a single idea as a zettel. Link it to one existing note.",
        category="capture",
        duration_min=3,
        tod_fit={"morning": 1.1, "midday": 1.0, "afternoon": 1.1, "evening": 1.0},
    ),
    Activity(
        id="capture_links",
        display_name="Link two notes",
        description="Open a random zettel. Find one existing note it connects to. Link them.",
        category="capture",
        duration_min=3,
        tod_fit={"morning": 1.0, "midday": 1.0, "afternoon": 1.1, "evening": 1.0},
    ),
]


def time_window(hour: int) -> TimeWindow:
    """Map an hour-of-day (0–23) to a coarse time window."""
    if 6 <= hour < 11:
        return "morning"
    if 11 <= hour < 14:
        return "midday"
    if 14 <= hour < 17:
        return "afternoon"
    return "evening"
