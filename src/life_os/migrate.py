"""Idempotent schema migration for upgrading existing installs to life-os.

Runs automatically on daemon startup if the persisted ``DaemonState.schema_version``
is below the current schema. Safe to re-run — every step is a no-op once already
applied. Also exposed as ``health-timer migrate`` for manual use.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from .config import CONFIG_PATH, DEFAULT_CONFIG, STATE_PATH, DaemonState, load_state, save_state

logger = logging.getLogger(__name__)

CURRENT_SCHEMA = 2


def needs_migration(state: DaemonState) -> bool:
    return state.schema_version < CURRENT_SCHEMA


def run_migration(
    config_path: Path = CONFIG_PATH,
    state_path: Path = STATE_PATH,
) -> DaemonState:
    """Bring an existing install up to the current schema. Returns the migrated state.

    Steps (all idempotent):
    1. Ensure every :class:`Config` field has a value in ``config.json`` — missing
       keys are filled from defaults and the file is rewritten. Safe to re-run.
    2. Ensure :class:`DaemonState` carries the new fields (``ritual_last_fired``,
       ``last_overdue_scan_at``, ``schema_version``) and persist.
    """
    _migrate_config_file(config_path)
    state = load_state(state_path)
    state.schema_version = CURRENT_SCHEMA
    save_state(state, state_path)
    logger.info("migration complete — schema_version=%d", state.schema_version)
    return state


def _migrate_config_file(path: Path) -> None:
    default_dict = asdict(DEFAULT_CONFIG)
    existing: dict[str, object] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            logger.warning("config at %s unreadable — rewriting with defaults", path)
            existing = {}

    merged = {**default_dict, **{k: v for k, v in existing.items() if k in default_dict}}
    if merged == existing and path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(merged, indent=2))
    tmp.replace(path)
    logger.info("config migrated at %s", path)
