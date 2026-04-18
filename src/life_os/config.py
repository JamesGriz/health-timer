"""Config + persisted state loading.

Config lives at ``~/.config/health-timer/config.json`` (user-editable).
State lives at ``~/.local/state/health-timer/state.json`` (written by the daemon).
Both follow XDG-style paths so they don't clutter ``$HOME``.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .suggester import SuggesterState

logger = logging.getLogger(__name__)


def _xdg(var: str, fallback: str) -> Path:
    raw = os.environ.get(var)
    base = Path(raw) if raw else Path.home() / fallback
    return base / "health-timer"


CONFIG_DIR = _xdg("XDG_CONFIG_HOME", ".config")
STATE_DIR = _xdg("XDG_STATE_HOME", ".local/state")
CONFIG_PATH = CONFIG_DIR / "config.json"
STATE_PATH = STATE_DIR / "state.json"


@dataclass
class Config:
    """User-tweakable behaviour knobs."""

    work_threshold_min: int = 45
    idle_threshold_min: int = 3
    poll_sec: int = 30
    snooze_min: int = 5
    inactive_nudge_min: int = 2  # idle this long while WORKING → "back to work" notification

    # ─── life-os: vault ────────────────────────────────────────────────────
    vault_path: str | None = None  # None → default_vault_path()
    vault_enabled: bool = False  # master opt-in; existing installs upgrade unchanged

    # ─── life-os: rituals ──────────────────────────────────────────────────
    rituals_enabled: bool = False  # off by default; flip to True once vault is ready
    morning_journal_at: str = "08:00"
    midday_inbox_at: str = "12:00"
    evening_shutdown_at: str = "17:00"
    weekly_review_at: str = "Sun 10:00"

    # ─── life-os: overdue scan ─────────────────────────────────────────────
    overdue_scan_enabled: bool = False
    overdue_scan_interval_min: int = 60
    overdue_notify_threshold: int = 1  # notify when >= N tasks are overdue

    # ─── life-os: Claude CLI ───────────────────────────────────────────────
    claude_invoke_mode: str = "dialog"  # notify_only | dialog | terminal | headless
    claude_cli_path: str = "claude"

    # ─── life-os: break-time capture ──────────────────────────────────────
    capture_activities_enabled: bool = False
    capture_activity_bias: float = 0.3  # multiplier on capture-category scores


DEFAULT_CONFIG = Config()


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Read ``config.json`` if present, otherwise return defaults.

    Missing or malformed files silently fall back to defaults so the daemon
    keeps running — a nudged break is better than a crashed daemon.
    """
    if not path.exists():
        return DEFAULT_CONFIG
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("config load failed (%s) — using defaults", exc)
        return DEFAULT_CONFIG
    return Config(**{k: v for k, v in data.items() if k in DEFAULT_CONFIG.__dataclass_fields__})


@dataclass
class DaemonState:
    """Everything persisted across restarts."""

    active_seconds: float = 0.0
    last_break_at: float | None = None
    suggester: SuggesterState = field(default_factory=SuggesterState)
    # life-os additions — default to empty so existing state files load cleanly.
    ritual_last_fired: dict[str, float] = field(default_factory=dict)
    last_overdue_scan_at: float | None = None
    schema_version: int = 1  # migrate.run_migration() bumps this to CURRENT_SCHEMA


def load_state(path: Path = STATE_PATH) -> DaemonState:
    """Load persisted daemon state, or return a fresh one."""
    if not path.exists():
        return DaemonState()
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("state load failed (%s) — starting fresh", exc)
        return DaemonState()

    suggester_data = data.get("suggester", {})
    return DaemonState(
        active_seconds=float(data.get("active_seconds", 0.0)),
        last_break_at=data.get("last_break_at"),
        suggester=SuggesterState(
            recent_activity_ids=list(suggester_data.get("recent_activity_ids", [])),
            last_water_at=suggester_data.get("last_water_at"),
            last_category=suggester_data.get("last_category"),
            last_seen_per_id=dict(suggester_data.get("last_seen_per_id", {})),
        ),
        ritual_last_fired=dict(data.get("ritual_last_fired", {})),
        last_overdue_scan_at=data.get("last_overdue_scan_at"),
        schema_version=int(data.get("schema_version", 1)),
    )


def save_state(state: DaemonState, path: Path = STATE_PATH) -> None:
    """Write state atomically (write + rename) to avoid corruption on crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(state), indent=2))
    tmp.replace(path)
