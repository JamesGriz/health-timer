"""Tests for the Claude CLI wrapper. Subprocess calls are mocked."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from life_os import claude_cli


def test_claude_available_returns_false_when_missing() -> None:
    with patch("life_os.claude_cli.shutil.which", return_value=None):
        assert claude_cli.claude_available("claude") is False


def test_claude_available_returns_true_when_on_path() -> None:
    with patch("life_os.claude_cli.shutil.which", return_value="/usr/bin/claude"):
        assert claude_cli.claude_available("claude") is True


def test_spawn_terminal_skips_when_binary_missing(tmp_path: Path) -> None:
    with (
        patch("life_os.claude_cli.claude_available", return_value=False),
        patch("life_os.claude_cli.subprocess.run") as run_mock,
    ):
        claude_cli.spawn_terminal(tmp_path, "/daily")
    run_mock.assert_not_called()


def test_spawn_terminal_builds_osascript_with_vault_and_command(tmp_path: Path) -> None:
    with (
        patch("life_os.claude_cli.claude_available", return_value=True),
        patch("life_os.claude_cli.subprocess.run") as run_mock,
    ):
        claude_cli.spawn_terminal(tmp_path, "/daily")
    run_mock.assert_called_once()
    argv = run_mock.call_args.args[0]
    assert argv[0] == "/usr/bin/osascript"
    assert argv[1] == "-e"
    script = argv[2]
    assert str(tmp_path) in script
    assert "/daily" in script
    assert "Terminal" in script


def test_run_headless_invokes_claude_p(tmp_path: Path) -> None:
    with (
        patch("life_os.claude_cli.claude_available", return_value=True),
        patch("life_os.claude_cli.subprocess.run") as run_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        rc = claude_cli.run_headless(tmp_path, "/lint-vault")

    assert rc == 0
    args, kwargs = run_mock.call_args.args, run_mock.call_args.kwargs
    assert args[0] == ["claude", "-p", "/lint-vault"]
    assert kwargs["cwd"] == tmp_path


def test_run_headless_returns_127_when_binary_missing(tmp_path: Path) -> None:
    with patch("life_os.claude_cli.claude_available", return_value=False):
        rc = claude_cli.run_headless(tmp_path, "/daily")
    assert rc == 127


def test_run_headless_returns_124_on_timeout(tmp_path: Path) -> None:
    with (
        patch("life_os.claude_cli.claude_available", return_value=True),
        patch(
            "life_os.claude_cli.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=1),
        ),
    ):
        rc = claude_cli.run_headless(tmp_path, "/daily", timeout_sec=1)
    assert rc == 124
