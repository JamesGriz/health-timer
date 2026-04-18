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

from life_os import daemon
from life_os.config import Config, DaemonState


class _StopLoopError(Exception):
    """Raised inside the patched sleep to break out of the daemon's loop."""


def _drive_loop(
    config: Config,
    state: DaemonState,
    idle_sequence: list[float],
    now_sequence: list[Any] | None = None,
    ask_break_return: Any = None,
) -> dict[str, list[Any]]:
    """Run the daemon's loop for ``len(idle_sequence)`` iterations.

    Returns a record of the calls made to UI side-effects so tests can assert
    on what the user would have seen. ``now_sequence`` lets tests control the
    perceived clock for ritual-scheduler tests.
    """
    calls: dict[str, list[Any]] = {
        "notify": [],
        "nudge": [],
        "ask_break": [],
        "break_complete": [],
        "spawn_terminal": [],
    }
    idle_iter: Iterator[float] = iter(idle_sequence)
    now_iter: Iterator[Any] | None = iter(now_sequence) if now_sequence else None

    def _next_idle() -> float:
        try:
            return next(idle_iter)
        except StopIteration as exc:
            raise _StopLoopError from exc

    def _sleep(_seconds: float) -> None:
        # Each loop iteration ends with sleep — we use that as our pacing signal.
        return None

    from life_os.ui import RitualChoice

    patches: list[Any] = [
        patch.object(daemon, "get_idle_seconds", side_effect=_next_idle),
        patch.object(daemon.time, "sleep", side_effect=_sleep),
        patch.object(
            daemon, "nudge_back_to_work", side_effect=lambda mins: calls["nudge"].append(mins)
        ),
        patch.object(daemon, "notify", side_effect=lambda *a, **kw: calls["notify"].append(a)),
        patch.object(
            daemon,
            "ask_break",
            side_effect=lambda *a, **kw: (calls["ask_break"].append(a), ask_break_return)[1],
        ),
        patch.object(
            daemon,
            "break_complete",
            side_effect=lambda name: calls["break_complete"].append(name),
        ),
        patch.object(daemon, "ritual_dialog", return_value=RitualChoice.SKIP),
        patch.object(
            daemon,
            "spawn_terminal",
            side_effect=lambda *a, **kw: calls["spawn_terminal"].append(a),
        ),
        patch.object(daemon, "run_headless", return_value=0),
        patch.object(daemon, "save_state"),  # don't touch disk in tests
    ]
    if now_iter is not None:
        # Subclass so `fromtimestamp` etc. still work inside the scheduler module.
        real_datetime = daemon.dt.datetime

        class _DatetimeStub(real_datetime):  # type: ignore[misc,valid-type]
            @classmethod
            def now(cls, tz: Any | None = None) -> Any:
                return next(now_iter)  # type: ignore[arg-type]

        patches.append(patch.object(daemon.dt, "datetime", _DatetimeStub))

    with _enter_all(patches), pytest.raises(_StopLoopError):
        daemon.run(config, state)
    return calls


def _enter_all(patches: list[Any]) -> Any:
    """Tiny context manager that enters a dynamic list of patches."""
    from contextlib import ExitStack

    stack = ExitStack()
    for p in patches:
        stack.enter_context(p)
    return stack


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


# ─── rituals ────────────────────────────────────────────────────────────────
import datetime as _dt  # noqa: E402  (below the main test block intentionally)


def _ritual_config() -> Config:
    cfg = _short_config()
    cfg.rituals_enabled = True
    cfg.morning_journal_at = "08:00"
    # Use notify_only so the test doesn't care about the dialog pathway.
    cfg.claude_invoke_mode = "notify_only"
    return cfg


def test_morning_ritual_fires_on_schedule() -> None:
    cfg = _ritual_config()
    state = DaemonState()
    now_seq = [
        _dt.datetime(2026, 4, 20, 7, 59),  # before
        _dt.datetime(2026, 4, 20, 8, 0),  # at target → fires
        _dt.datetime(2026, 4, 20, 8, 1),  # already fired today
    ]
    calls = _drive_loop(cfg, state, idle_sequence=[5, 5, 5], now_sequence=now_seq)
    titles = [c[0] for c in calls["notify"]]
    assert titles.count("Morning journal 🌅") == 1


def test_rituals_do_not_fire_when_disabled() -> None:
    cfg = _short_config()
    cfg.rituals_enabled = False
    state = DaemonState()
    now_seq = [_dt.datetime(2026, 4, 20, 8, 0), _dt.datetime(2026, 4, 20, 8, 0)]
    calls = _drive_loop(cfg, state, idle_sequence=[5, 5], now_sequence=now_seq)
    assert all(c[0] != "Morning journal 🌅" for c in calls["notify"])


# ─── overdue scan ────────────────────────────────────────────────────────────


def test_overdue_scan_notifies_when_tasks_overdue(tmp_path: Any) -> None:
    from life_os.vault import init_skeleton

    vault = tmp_path / "vault"
    init_skeleton(vault)
    (vault / "Projects" / "demo").mkdir(parents=True)
    (vault / "Projects" / "demo" / "tasks.md").write_text(
        "- [ ] do the thing <!-- due:2020-01-01 -->\n"
    )

    cfg = _short_config()
    cfg.overdue_scan_enabled = True
    cfg.vault_path = str(vault)
    cfg.overdue_scan_interval_min = 60
    state = DaemonState()

    calls = _drive_loop(cfg, state, idle_sequence=[5])
    titles = [c[0] for c in calls["notify"]]
    assert any("overdue" in t for t in titles)


def test_capture_activity_spawns_claude(tmp_path: Any) -> None:
    """When a capture activity is picked and started, Claude should be spawned."""
    from life_os.activities import Activity
    from life_os.ui import BreakChoice

    cfg = _short_config(work_threshold_min=1)
    cfg.capture_activities_enabled = True
    cfg.vault_path = str(tmp_path / "vault")
    state = DaemonState(active_seconds=30.0)

    capture_activity = Activity(
        id="capture_zettel",
        display_name="One atomic thought",
        description="Capture.",
        category="capture",
        duration_min=3,
    )

    with patch.object(daemon, "pick", return_value=capture_activity):
        calls = _drive_loop(cfg, state, idle_sequence=[5, 5], ask_break_return=BreakChoice.START)

    assert len(calls["spawn_terminal"]) == 1
    # args are (vault_path, command) positional
    assert calls["spawn_terminal"][0][1] == "/zettel"


def test_overdue_scan_is_throttled(tmp_path: Any) -> None:
    """Two polls within the interval should only produce one scan notification."""
    from life_os.vault import init_skeleton

    vault = tmp_path / "vault"
    init_skeleton(vault)
    (vault / "Projects" / "demo").mkdir(parents=True)
    (vault / "Projects" / "demo" / "tasks.md").write_text("- [ ] stale <!-- due:2020-01-01 -->\n")

    cfg = _short_config()
    cfg.overdue_scan_enabled = True
    cfg.vault_path = str(vault)
    cfg.overdue_scan_interval_min = 60
    state = DaemonState()

    calls = _drive_loop(cfg, state, idle_sequence=[5, 5])
    overdue_notifications = [c for c in calls["notify"] if "overdue" in c[0]]
    assert len(overdue_notifications) == 1
