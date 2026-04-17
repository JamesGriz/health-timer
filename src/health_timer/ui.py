"""macOS UI wrappers built on ``osascript``.

Notifications are non-blocking. Dialogs block until the user clicks a button,
or until ``DIALOG_TIMEOUT_SEC`` passes (in which case we treat it as a skip).
"""

from __future__ import annotations

import logging
import subprocess
from enum import Enum

logger = logging.getLogger(__name__)

DIALOG_TIMEOUT_SEC = 120


class BreakChoice(Enum):
    START = "start"
    SNOOZE = "snooze"
    SKIP = "skip"


def _osascript(script: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("osascript timed out after %ds", timeout)
        return 124, "", "timeout"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _escape(text: str) -> str:
    """Escape text for embedding in an AppleScript string literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str) -> None:
    """Post a non-blocking macOS notification."""
    script = f'display notification "{_escape(message)}" with title "{_escape(title)}"'
    code, _, err = _osascript(script, timeout=10)
    if code != 0:
        logger.warning("notify failed: %s", err)


def ask_break(activity_name: str, description: str, duration_min: int) -> BreakChoice:
    """Show the break-suggestion dialog and return the user's choice.

    Times out (treated as :attr:`BreakChoice.SKIP`) after ``DIALOG_TIMEOUT_SEC``
    so the daemon never deadlocks if the user is away from the keyboard.
    """
    body = f"{activity_name}  ({duration_min} min)\n\n{description}"
    script = (
        f'display dialog "{_escape(body)}" '
        f'with title "Break time 🌿" '
        'buttons {"Skip", "Snooze 5 min", "Start now"} '
        'default button "Start now" '
        "with icon note "
        f"giving up after {DIALOG_TIMEOUT_SEC}"
    )
    code, out, err = _osascript(script, timeout=DIALOG_TIMEOUT_SEC + 10)
    if code != 0:
        # User dismissed via Esc → osascript exits 1 with "User canceled".
        if "User canceled" in err:
            return BreakChoice.SKIP
        logger.warning("ask_break failed: %s", err)
        return BreakChoice.SKIP

    if "Start now" in out:
        return BreakChoice.START
    if "Snooze" in out:
        return BreakChoice.SNOOZE
    if "gave up" in out:
        return BreakChoice.SKIP
    return BreakChoice.SKIP


def break_complete(activity_name: str) -> None:
    """Notify that the break period has elapsed."""
    notify(
        "Back to it 💪",
        f"Hope that {activity_name.lower()} felt good — back at it for the next stint.",
    )


def nudge_back_to_work(idle_min: float) -> None:
    """Nudge the user back to the desk after an unscheduled idle stretch."""
    notify(
        "Still there? 👀",
        f"You've been idle {idle_min:.0f} min — head back when you're ready.",
    )
