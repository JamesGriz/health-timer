"""Tests for the schema-migration routine."""

from __future__ import annotations

import json
from pathlib import Path

from life_os.config import DEFAULT_CONFIG, DaemonState, load_state, save_state
from life_os.migrate import CURRENT_SCHEMA, needs_migration, run_migration


def test_needs_migration_true_for_fresh_state() -> None:
    assert needs_migration(DaemonState()) is True


def test_needs_migration_false_when_current() -> None:
    state = DaemonState(schema_version=CURRENT_SCHEMA)
    assert needs_migration(state) is False


def test_run_migration_bumps_schema_version(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    config_path = tmp_path / "config.json"
    save_state(DaemonState(active_seconds=42.0), state_path)

    migrated = run_migration(config_path=config_path, state_path=state_path)

    assert migrated.schema_version == CURRENT_SCHEMA
    assert migrated.active_seconds == 42.0  # untouched
    # Persisted too
    assert load_state(state_path).schema_version == CURRENT_SCHEMA


def test_run_migration_fills_missing_config_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    state_path = tmp_path / "state.json"
    config_path.write_text(json.dumps({"work_threshold_min": 25}))

    run_migration(config_path=config_path, state_path=state_path)

    written = json.loads(config_path.read_text())
    assert written["work_threshold_min"] == 25  # preserved user override
    assert written["idle_threshold_min"] == DEFAULT_CONFIG.idle_threshold_min  # filled default


def test_run_migration_is_idempotent(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    state_path = tmp_path / "state.json"
    run_migration(config_path=config_path, state_path=state_path)
    snapshot = config_path.read_text()

    run_migration(config_path=config_path, state_path=state_path)

    assert config_path.read_text() == snapshot


def test_run_migration_creates_config_when_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    state_path = tmp_path / "state.json"
    assert not config_path.exists()

    run_migration(config_path=config_path, state_path=state_path)

    assert config_path.exists()
    data = json.loads(config_path.read_text())
    assert data["work_threshold_min"] == DEFAULT_CONFIG.work_threshold_min
