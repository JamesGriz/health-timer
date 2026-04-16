"""Health Timer daemon — the polling loop and state machine.

Run with ``python -m health_timer``. Use ``--debug`` for verbose logging and
``--threshold-sec N`` to override the work threshold for testing.
"""

from __future__ import annotations

import argparse
import logging
import re
import signal
import subprocess
import sys
import time
from enum import Enum, auto
from typing import NoReturn

from . import __version__
from .activities import Activity
from .config import Config, DaemonState, load_config, load_state, save_state
from .suggester import pick, record_pick
from .ui import BreakChoice, ask_break, break_complete, notify

logger = logging.getLogger("health_timer")

_HID_IDLE_RE = re.compile(r'"HIDIdleTime"\s*=\s*(\d+)')


class Phase(Enum):
    WORKING = auto()
    BREAK_SUGGESTED = auto()
    ON_BREAK = auto()


def get_idle_seconds() -> float:
    """Return seconds since last HID input event (mouse/keyboard).

    Reads ``ioreg -c IOHIDSystem`` and parses the ``HIDIdleTime`` value, which
    is reported in nanoseconds. Returns 0.0 if the read fails so the daemon
    behaves as if the user is active (safer than skipping breaks).
    """
    try:
        proc = subprocess.run(
            ["/usr/sbin/ioreg", "-c", "IOHIDSystem"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.warning("ioreg failed: %s", exc)
        return 0.0

    match = _HID_IDLE_RE.search(proc.stdout)
    if not match:
        logger.warning("HIDIdleTime not found in ioreg output")
        return 0.0
    return int(match.group(1)) / 1_000_000_000


def _suggest_and_handle(config: Config, state: DaemonState) -> tuple[Phase, Activity | None, float]:
    """Show the break dialog. Returns (next_phase, chosen_activity, break_until_ts)."""
    activity = pick(state.suggester)
    notify("Break time 🌿", f"{activity.display_name} — {activity.duration_min} min")
    choice = ask_break(activity.display_name, activity.description, activity.duration_min)

    if choice == BreakChoice.START:
        logger.info("user started break: %s", activity.id)
        break_until = time.time() + activity.duration_min * 60
        return Phase.ON_BREAK, activity, break_until

    if choice == BreakChoice.SNOOZE:
        logger.info("user snoozed break")
        # Re-fire in `snooze_min` minutes by rewinding active_seconds.
        state.active_seconds = max(0.0, config.work_threshold_min * 60 - config.snooze_min * 60)
        return Phase.WORKING, None, 0.0

    logger.info("user skipped break")
    state.active_seconds = 0.0
    return Phase.WORKING, None, 0.0


def run(config: Config, state: DaemonState) -> NoReturn:
    """Main loop. Runs forever; SIGINT/SIGTERM handled by ``main()``."""
    threshold_sec = config.work_threshold_min * 60
    idle_threshold_sec = config.idle_threshold_min * 60

    phase = Phase.WORKING
    current_activity: Activity | None = None
    break_until = 0.0

    logger.info(
        "starting health-timer v%s — threshold=%ds idle=%ds poll=%ds",
        __version__,
        threshold_sec,
        idle_threshold_sec,
        config.poll_sec,
    )

    while True:
        now = time.time()
        idle = get_idle_seconds()
        logger.debug("phase=%s active=%.0fs idle=%.0fs", phase.name, state.active_seconds, idle)

        if phase == Phase.WORKING:
            if idle < idle_threshold_sec:
                state.active_seconds += config.poll_sec
            if state.active_seconds >= threshold_sec and idle < idle_threshold_sec:
                phase = Phase.BREAK_SUGGESTED

        if phase == Phase.BREAK_SUGGESTED:
            phase, current_activity, break_until = _suggest_and_handle(config, state)
            save_state(state)

        elif phase == Phase.ON_BREAK:
            if now >= break_until and current_activity is not None:
                logger.info("break complete: %s", current_activity.id)
                break_complete(current_activity.display_name)
                record_pick(state.suggester, current_activity)
                state.active_seconds = 0.0
                state.last_break_at = now
                current_activity = None
                phase = Phase.WORKING
                save_state(state)

        time.sleep(config.poll_sec)


def _install_signal_handlers() -> None:
    def _bye(signum: int, _frame: object) -> None:
        logger.info("received signal %d — exiting", signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, _bye)
    signal.signal(signal.SIGTERM, _bye)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="health-timer", description=__doc__)
    parser.add_argument("--debug", action="store_true", help="verbose logging")
    parser.add_argument(
        "--threshold-sec",
        type=int,
        help="override work threshold (in seconds) for testing",
    )
    parser.add_argument(
        "--poll-sec",
        type=int,
        help="override poll interval (in seconds) for testing",
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config()
    if args.threshold_sec is not None:
        config = Config(
            work_threshold_min=max(1, args.threshold_sec // 60) if args.threshold_sec >= 60 else 1,
            idle_threshold_min=config.idle_threshold_min,
            poll_sec=config.poll_sec,
            snooze_min=config.snooze_min,
        )
        # Allow sub-minute thresholds via direct field override:
        object.__setattr__(config, "work_threshold_min", args.threshold_sec / 60)
    if args.poll_sec is not None:
        object.__setattr__(config, "poll_sec", args.poll_sec)

    state = load_state()
    _install_signal_handlers()

    try:
        run(config, state)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
