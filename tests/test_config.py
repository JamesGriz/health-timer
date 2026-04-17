"""Round-trip tests for config + state persistence."""

from __future__ import annotations

import json
from pathlib import Path

from health_timer.config import (
    DEFAULT_CONFIG,
    DaemonState,
    load_config,
    load_state,
    save_state,
)
from health_timer.suggester import SuggesterState


def test_load_config_returns_defaults_when_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.json")
    assert config == DEFAULT_CONFIG


def test_load_config_returns_defaults_on_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not valid json")
    config = load_config(path)
    assert config == DEFAULT_CONFIG


def test_load_config_picks_up_overrides(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"work_threshold_min": 30, "snooze_min": 10}))
    config = load_config(path)
    assert config.work_threshold_min == 30
    assert config.snooze_min == 10
    assert config.idle_threshold_min == DEFAULT_CONFIG.idle_threshold_min


def test_default_config_values() -> None:
    """Lock in the production defaults so a refactor can't quietly change them."""
    assert DEFAULT_CONFIG.work_threshold_min == 45
    assert DEFAULT_CONFIG.idle_threshold_min == 3
    assert DEFAULT_CONFIG.poll_sec == 30
    assert DEFAULT_CONFIG.snooze_min == 5
    assert DEFAULT_CONFIG.inactive_nudge_min == 2


def test_load_config_picks_up_inactive_nudge(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"inactive_nudge_min": 5}))
    config = load_config(path)
    assert config.inactive_nudge_min == 5


def test_load_config_ignores_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"work_threshold_min": 25, "garbage": "ignored"}))
    config = load_config(path)
    assert config.work_threshold_min == 25


def test_state_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    state = DaemonState(
        active_seconds=123.4,
        last_break_at=1700000000.0,
        suggester=SuggesterState(
            recent_activity_ids=["a", "b"],
            last_water_at=1700000100.0,
            last_category="water",
            last_seen_per_id={"a": 1700000000.0},
        ),
    )
    save_state(state, path)
    loaded = load_state(path)
    assert loaded.active_seconds == 123.4
    assert loaded.last_break_at == 1700000000.0
    assert loaded.suggester.recent_activity_ids == ["a", "b"]
    assert loaded.suggester.last_water_at == 1700000100.0
    assert loaded.suggester.last_category == "water"
    assert loaded.suggester.last_seen_per_id == {"a": 1700000000.0}


def test_load_state_returns_default_when_missing(tmp_path: Path) -> None:
    state = load_state(tmp_path / "missing.json")
    assert state == DaemonState()


def test_load_state_returns_default_on_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("garbage")
    state = load_state(path)
    assert state == DaemonState()


def test_save_state_is_atomic(tmp_path: Path) -> None:
    """Writes go through a temp file and rename — leftover should not exist."""
    path = tmp_path / "state.json"
    save_state(DaemonState(active_seconds=1.0), path)
    assert path.exists()
    assert not (tmp_path / "state.json.tmp").exists()
