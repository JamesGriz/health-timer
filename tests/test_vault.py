"""Tests for vault discovery + skeleton init."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from life_os.vault import (
    REQUIRED_DIRS,
    default_vault_path,
    init_skeleton,
    is_initialized,
    scan_overdue,
)


def test_default_vault_path_honors_xdg_data_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert default_vault_path() == tmp_path / "health-timer" / "vault"


def test_default_vault_path_falls_back_to_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    path = default_vault_path()
    assert path == tmp_path / ".local" / "share" / "health-timer" / "vault"


def test_init_skeleton_creates_required_dirs(tmp_path: Path) -> None:
    dest = tmp_path / "vault"
    init_skeleton(dest)
    for d in REQUIRED_DIRS:
        assert (dest / d).is_dir(), f"{d} not created"


def test_init_skeleton_is_idempotent(tmp_path: Path) -> None:
    dest = tmp_path / "vault"
    init_skeleton(dest)
    (dest / "CLAUDE.md").write_text("USER OVERRIDE")
    init_skeleton(dest)  # re-run — must not clobber
    assert (dest / "CLAUDE.md").read_text() == "USER OVERRIDE"


def test_is_initialized_false_for_fresh_dir(tmp_path: Path) -> None:
    assert is_initialized(tmp_path) is False


def test_is_initialized_true_after_skeleton(tmp_path: Path) -> None:
    dest = tmp_path / "vault"
    init_skeleton(dest)
    assert is_initialized(dest) is True


def test_init_skeleton_seeds_claude_md_and_templates(tmp_path: Path) -> None:
    """The packaged templates/vault/ tree should land under dest."""
    dest = tmp_path / "vault"
    init_skeleton(dest)
    assert (dest / "CLAUDE.md").exists()
    assert (dest / ".claude" / "CLAUDE.md").exists()
    assert (dest / ".claude" / "commands" / "daily.md").exists()
    assert (dest / "Templates" / "daily.md").exists()
    assert (dest / "_meta" / "_master-index.md").exists()


# ─── scan_overdue ───────────────────────────────────────────────────────────


def _build_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    init_skeleton(vault)
    return vault


def test_scan_overdue_finds_checkbox_task_past_due(tmp_path: Path) -> None:
    vault = _build_vault(tmp_path)
    project_dir = vault / "Projects" / "demo"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "tasks.md").write_text(
        "# tasks\n\n"
        "- [ ] write the thing <!-- due:2025-01-01 priority:p1 -->\n"
        "- [ ] future work <!-- due:2099-01-01 -->\n"
        "- [x] already done <!-- due:2020-01-01 -->\n"
    )
    overdue = scan_overdue(vault, dt.date(2026, 4, 20))
    assert len(overdue) == 1
    assert overdue[0].text == "write the thing"
    assert overdue[0].due == dt.date(2025, 1, 1)
    assert overdue[0].priority == "p1"


def test_scan_overdue_finds_frontmatter_task(tmp_path: Path) -> None:
    vault = _build_vault(tmp_path)
    (vault / "Projects" / "overdue-task.md").write_text(
        "---\ntype: task\ndue: 2025-01-01\nstatus: open\n---\n\nbody\n"
    )
    overdue = scan_overdue(vault, dt.date(2026, 4, 20))
    assert len(overdue) == 1


def test_scan_overdue_skips_done_frontmatter_tasks(tmp_path: Path) -> None:
    vault = _build_vault(tmp_path)
    (vault / "Projects" / "closed-task.md").write_text(
        "---\ntype: task\ndue: 2025-01-01\nstatus: done\n---\n"
    )
    assert scan_overdue(vault, dt.date(2026, 4, 20)) == []


def test_scan_overdue_ignores_archive_tree(tmp_path: Path) -> None:
    vault = _build_vault(tmp_path)
    archived = vault / "Archive" / "2025-Q4" / "old"
    archived.mkdir(parents=True)
    (archived / "tasks.md").write_text("- [ ] historical <!-- due:2025-01-01 -->\n")
    assert scan_overdue(vault, dt.date(2026, 4, 20)) == []


def test_scan_overdue_handles_missing_vault(tmp_path: Path) -> None:
    assert scan_overdue(tmp_path / "missing", dt.date(2026, 4, 20)) == []
