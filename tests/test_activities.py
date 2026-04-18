"""Sanity checks on the activity catalog itself."""

from __future__ import annotations

from collections import Counter

import pytest

from life_os.activities import CATALOG, time_window


def test_catalog_is_not_empty() -> None:
    assert len(CATALOG) >= 20, "catalog should offer plenty of variety"


def test_ids_are_unique() -> None:
    ids = [a.id for a in CATALOG]
    dupes = [i for i, count in Counter(ids).items() if count > 1]
    assert not dupes, f"duplicate activity ids: {dupes}"


def test_every_category_has_multiple_options() -> None:
    by_cat = Counter(a.category for a in CATALOG)
    for category, count in by_cat.items():
        assert count >= 3, f"category {category} only has {count} options — needs variety"


def test_durations_are_reasonable() -> None:
    for activity in CATALOG:
        assert 3 <= activity.duration_min <= 15, (
            f"{activity.id} duration {activity.duration_min} out of 3–15 range"
        )


def test_tod_fit_has_all_windows() -> None:
    for activity in CATALOG:
        for window in ("morning", "midday", "afternoon", "evening"):
            assert window in activity.tod_fit, f"{activity.id} missing window {window}"
            assert 0 < activity.tod_fit[window] <= 2.0


@pytest.mark.parametrize(
    ("hour", "expected"),
    [
        (6, "morning"),
        (10, "morning"),
        (11, "midday"),
        (13, "midday"),
        (14, "afternoon"),
        (16, "afternoon"),
        (17, "evening"),
        (21, "evening"),
        (2, "evening"),
    ],
)
def test_time_window(hour: int, expected: str) -> None:
    assert time_window(hour) == expected
