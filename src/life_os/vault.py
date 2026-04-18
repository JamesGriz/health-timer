"""Vault discovery + skeleton initialization.

The vault is a directory of Markdown + YAML-frontmatter files that Claude Code
manages. Python only touches frontmatter (for overdue scans and index updates);
it never parses Markdown bodies.

Default location follows XDG data-home conventions: ``~/.local/share/health-timer/vault``.
Override via ``Config.vault_path``.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_TEMPLATES_ROOT = Path(__file__).resolve().parent.parent.parent / "templates" / "vault"

# These dirs must exist in an initialized vault. The init routine creates them
# and copies the seed content from templates/vault/.
REQUIRED_DIRS: tuple[str, ...] = (
    "Inbox",
    "Projects",
    "Areas",
    "Resources",
    "Archive",
    "Notes",
    "Daily",
    "Ingested/raw",
    "Ingested/curated",
    "Templates",
    ".claude/commands",
    ".claude/agents",
    ".claude/skills",
    "_meta",
)


def default_vault_path() -> Path:
    """Return the XDG-style default vault path."""
    raw = os.environ.get("XDG_DATA_HOME")
    base = Path(raw) if raw else Path.home() / ".local" / "share"
    return base / "health-timer" / "vault"


def is_initialized(path: Path) -> bool:
    """Return True iff ``path`` already looks like a life-os vault."""
    return (path / "CLAUDE.md").exists() and (path / ".claude").is_dir()


def init_skeleton(dest: Path, templates_root: Path = _TEMPLATES_ROOT) -> None:
    """Create the vault skeleton at ``dest``. Idempotent — safe to re-run.

    Copies every file from ``templates_root`` that does not already exist at the
    destination. Existing user content is never overwritten.
    """
    dest.mkdir(parents=True, exist_ok=True)
    for d in REQUIRED_DIRS:
        (dest / d).mkdir(parents=True, exist_ok=True)

    if not templates_root.exists():
        logger.warning("template root %s missing — skeleton dirs only", templates_root)
        return

    for src in templates_root.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(templates_root)
        target = dest / rel
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        logger.debug("seeded %s", rel)


# ─── overdue task scanning ──────────────────────────────────────────────────

_FRONTMATTER_DELIM = "---"
_FRONTMATTER_DUE = re.compile(r"^due:\s*(\S+)\s*$", re.MULTILINE)
_FRONTMATTER_STATUS = re.compile(r"^status:\s*(\S+)\s*$", re.MULTILINE)
_FRONTMATTER_TYPE = re.compile(r"^type:\s*(\S+)\s*$", re.MULTILINE)
_CHECKBOX_DUE = re.compile(
    r"^\s*-\s*\[\s\]\s*(?P<text>.+?)\s*(?:<!--\s*(?P<meta>.+?)\s*-->)?\s*$",
    re.MULTILINE,
)
_DUE_HINT = re.compile(r"due:(\d{4}-\d{2}-\d{2})")
_PRIORITY_HINT = re.compile(r"priority:(p[0-3])")

# Dirs we never scan — historical content, transient caches.
_SKIP_DIRS = {"Archive", "_meta"}


@dataclass(frozen=True)
class OverdueTask:
    """A single overdue task surfaced to the user."""

    file: Path
    text: str
    due: dt.date
    priority: str | None  # "p0".."p3" or None


def _read_frontmatter(path: Path) -> str | None:
    """Return the raw YAML block (text between the first two ``---`` lines), or None."""
    try:
        with path.open(encoding="utf-8") as fh:
            lines: list[str] = []
            first = fh.readline()
            if first.rstrip() != _FRONTMATTER_DELIM:
                return None
            for line in fh:
                if line.rstrip() == _FRONTMATTER_DELIM:
                    return "".join(lines)
                lines.append(line)
    except OSError:
        return None
    return None


def scan_overdue(vault: Path, today: dt.date) -> list[OverdueTask]:
    """Walk the vault and return every open task whose due date is before today.

    Reads frontmatter of every ``.md`` (to catch ``type: task`` notes) and every
    Markdown checkbox line with a ``<!-- due:YYYY-MM-DD --!>`` hint. Silently
    skips files it can't read.
    """
    if not vault.exists():
        return []

    overdue: list[OverdueTask] = []
    for path in vault.rglob("*.md"):
        # Skip historical / transient trees.
        if any(part in _SKIP_DIRS for part in path.relative_to(vault).parts):
            continue

        overdue.extend(_scan_frontmatter_task(path, today))
        overdue.extend(_scan_checkbox_tasks(path, today))
    return overdue


def _scan_frontmatter_task(path: Path, today: dt.date) -> list[OverdueTask]:
    fm = _read_frontmatter(path)
    if fm is None:
        return []
    type_match = _FRONTMATTER_TYPE.search(fm)
    if type_match is None or type_match.group(1) != "task":
        return []
    due_match = _FRONTMATTER_DUE.search(fm)
    if due_match is None:
        return []
    status_match = _FRONTMATTER_STATUS.search(fm)
    if status_match and status_match.group(1) in ("done", "dropped"):
        return []
    try:
        due = dt.date.fromisoformat(due_match.group(1))
    except ValueError:
        return []
    if due >= today:
        return []
    return [OverdueTask(file=path, text=path.stem, due=due, priority=None)]


def _scan_checkbox_tasks(path: Path, today: dt.date) -> list[OverdueTask]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    out: list[OverdueTask] = []
    for match in _CHECKBOX_DUE.finditer(text):
        meta = match.group("meta") or ""
        due_hint = _DUE_HINT.search(meta)
        if due_hint is None:
            continue
        try:
            due = dt.date.fromisoformat(due_hint.group(1))
        except ValueError:
            continue
        if due >= today:
            continue
        priority_hint = _PRIORITY_HINT.search(meta)
        out.append(
            OverdueTask(
                file=path,
                text=match.group("text").strip(),
                due=due,
                priority=priority_hint.group(1) if priority_hint else None,
            )
        )
    return out
