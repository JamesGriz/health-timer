"""Integration tests for the daemon's polling loop.

Rather than test the literal ``while True`` loop, we drive a small number of
iterations by patching ``time.sleep`` to raise after N polls and patching
``get_idle_seconds`` to return a scripted sequence. This proves the
state-machine transitions and notification timing without real waiting.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import patch

import pytest

from health_timer import daemon
from health_timer.config import Config, DaemonState


class _StopLoopError(Exception):
    """Raised inside the patched sleep to break out of the daemon's loop."""


def _drive_loop(
    config: Config,
    state: DaemonState,
    idle_sequence: list[float],
) -> dict[str, list[Any]]:
    """Run the daemon's loop for ``len(idle_sequence)`` iterations.

    Returns a record of the calls made to UI side-effects so tests can assert
    on what the user would have seen.
    """
    calls: dict[str, list[Any]] = {
        "notify": [],
        "nudge": [],
        "ask_break": [],
        "break_complete": [],
    }
    idle_iter: Iterator[float] = iter(idle_sequence)

    def _next_idle() -> float:
        try:
            return next(idle_iter)
        except StopIteration as exc:
            raise _StopLoopError from exc

    def _sleep(_seconds: float) -> None:
        # Each loop iteration ends with sleep — we use that as our pacing signal.
        return None

    with (
        patch.object(daemon, "get_idle_seconds", side_effect=_next_idle),
        patch.object(daemon.time, "sleep", side_effect=_sleep),
        patch.object(
            daemon, "nudge_back_to_work", side_effect=lambda mins: calls["nudge"].append(mins)
        ),
        patch.object(daemon, "notify", side_effect=lambda *a, **kw: calls["notify"].append(a)),
        patch.object(
            daemon, "ask_break", side_effect=lambda *a, **kw: calls["ask_break"].append(a)
        ),
        patch.object(
            daemon,
            "break_complete",
            side_effect=lambda name: calls["break_complete"].append(name),
        ),
        patch.object(daemon, "save_state"),  # don't touch disk in tests
        pytest.raises(_StopLoopError),
    ):
        daemon.run(config, state)
    return calls


def _short_config(**overrides: Any) -> Config:
    """Config tuned for fast loop iteration in tests."""
    base = Config(
        work_threshold_min=45,
        idle_threshold_min=3,
        poll_sec=30,
        snooze_min=5,
        inactive_nudge_min=2,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_nudge_fires_once_when_user_goes_idle() -> None:
    """One idle stretch above the threshold = one nudge, not many."""
    config = _short_config()
    state = DaemonState()
    # 5 polls all above 2-min idle (120s).
    calls = _drive_loop(config, state, idle_sequence=[150, 160, 170, 180, 190])
    assert len(calls["nudge"]) == 1
    assert calls["nudge"][0] == pytest.approx(150 / 60)


def test_nudge_does_not_fire_below_threshold() -> None:
    config = _short_config()
    state = DaemonState()
    calls = _drive_loop(config, state, idle_sequence=[10, 30, 60, 90, 100])
    assert calls["nudge"] == []


def test_nudge_rearms_after_user_returns() -> None:
    """Idle → active → idle again should fire the nudge a second time."""
    config = _short_config()
    state = DaemonState()
    calls = _drive_loop(
        config,
        state,
        idle_sequence=[150, 160, 5, 5, 130, 140],  # idle, idle, active, active, idle, idle
    )
    assert len(calls["nudge"]) == 2


def test_nudge_uses_configured_threshold() -> None:
    """Setting inactive_nudge_min=5 should suppress nudges at 3-min idle."""
    config = _short_config(inactive_nudge_min=5)
    state = DaemonState()
    calls = _drive_loop(config, state, idle_sequence=[200, 220, 240, 260])  # all < 5 min
    assert calls["nudge"] == []


def test_active_seconds_accumulates_only_when_active() -> None:
    config = _short_config()
    state = DaemonState()
    # Three active polls (idle < 180s), two idle ones (idle ≥ 180s).
    _drive_loop(config, state, idle_sequence=[10, 10, 10, 200, 200])
    # 3 active polls × 30s/poll = 90s accumulated.
    assert state.active_seconds == 90.0


def test_break_suggestion_fires_at_threshold() -> None:
    """When active_seconds crosses the work threshold, the dialog is shown."""
    config = _short_config(work_threshold_min=1)  # 60s threshold
    state = DaemonState(active_seconds=30.0)  # one poll away from firing
    # First poll pushes us to 60s → dialog opens. ask_break (patched) returns
    # None → falls through to the SKIP branch → active_seconds = 0 → WORKING.
    calls = _drive_loop(config, state, idle_sequence=[5, 5])
    assert len(calls["ask_break"]) == 1, "the break dialog should have been shown exactly once"
    assert len(calls["notify"]) >= 1, "the break notification should have been posted"
