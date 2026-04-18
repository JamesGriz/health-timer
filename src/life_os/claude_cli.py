"""Wrappers for invoking Claude Code from the daemon.

Three invocation modes per ritual:

- ``notify_only`` — no Claude spawn; the daemon already posted the notification.
- ``dialog`` — a macOS dialog with Open/Later/Skip buttons; Open → terminal spawn.
- ``terminal`` — unconditionally spawn a Terminal window with ``claude <command>``.
- ``headless`` — run ``claude -p <command>`` in the background, logs only.

All modes degrade gracefully when the ``claude`` binary is missing — they log
and return without raising. The daemon must keep running even if Claude Code
isn't installed.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def claude_available(binary: str = "claude") -> bool:
    """True iff the ``claude`` CLI is on PATH (or an absolute path exists)."""
    if "/" in binary:
        return Path(binary).exists()
    return shutil.which(binary) is not None


def spawn_terminal(vault: Path, command: str, binary: str = "claude") -> None:
    """Open Terminal.app at ``vault`` and run ``claude <command>``.

    Fire-and-forget — we don't wait for the user's session. Errors are logged,
    not raised, so a scheduler miss never crashes the daemon.
    """
    if not claude_available(binary):
        logger.warning("claude CLI not found — skipping terminal spawn")
        return

    cd_cmd = f"cd {_quote(str(vault))} && {_quote(binary)} {_quote(command)}"
    script = (
        f'tell application "Terminal"\n  do script "{_escape_osa(cd_cmd)}"\n  activate\nend tell'
    )
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.warning("terminal spawn failed: %s", exc)


def run_headless(
    vault: Path,
    command: str,
    binary: str = "claude",
    timeout_sec: int = 600,
) -> int:
    """Run ``claude -p <command>`` in ``vault`` and return the exit code.

    Non-interactive. stdout/stderr land in the caller's log stream. Good for
    maintenance rituals (e.g. nightly ``/lint-vault``).
    """
    if not claude_available(binary):
        logger.warning("claude CLI not found — skipping headless run")
        return 127
    try:
        proc = subprocess.run(
            [binary, "-p", command],
            cwd=vault,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("headless claude timed out after %ds", timeout_sec)
        return 124
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.warning("headless claude failed: %s", exc)
        return 1

    if proc.stdout:
        logger.info("claude stdout (%s): %s", command, proc.stdout[:500])
    if proc.returncode != 0 and proc.stderr:
        logger.warning("claude stderr (%s): %s", command, proc.stderr[:500])
    return proc.returncode


def _quote(text: str) -> str:
    """Single-quote a shell token for use inside an AppleScript `do script`."""
    return "'" + text.replace("'", "'\\''") + "'"


def _escape_osa(text: str) -> str:
    """Escape a string for embedding inside an AppleScript string literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')
