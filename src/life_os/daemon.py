"""life-os daemon — the polling loop, state machine, and ritual scheduler.

Run with ``python -m life_os``. Use ``--debug`` for verbose logging and
``--threshold-sec N`` to override the work threshold for testing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import signal
import subprocess
import sys
import time
from enum import Enum, auto
from pathlib import Path
from typing import NoReturn

from . import __version__
from .activities import Activity
from .claude_cli import run_headless, spawn_terminal
from .config import Config, DaemonState, load_config, load_state, save_state
from .migrate import needs_migration, run_migration
from .rituals import Ritual, build_rituals_from_config
from .scheduler import due_now
from .suggester import pick, record_pick
from .ui import (
    BreakChoice,
    RitualChoice,
    ask_break,
    break_complete,
    notify,
    nudge_back_to_work,
    ritual_dialog,
)
from .vault import default_vault_path, init_skeleton, scan_overdue

logger = logging.getLogger("life_os")

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


_CAPTURE_COMMANDS: dict[str, str] = {
    "capture_inbox": "/process-inbox",
    "capture_zettel": "/zettel",
    "capture_links": "/lint-vault",
}


def _suggest_and_handle(config: Config, state: DaemonState) -> tuple[Phase, Activity | None, float]:
    """Show the break dialog. Returns (next_phase, chosen_activity, break_until_ts)."""
    capture_bias = config.capture_activity_bias if config.capture_activities_enabled else 0.0
    activity = pick(state.suggester, capture_bias=capture_bias)
    notify("Break time 🌿", f"{activity.display_name} — {activity.duration_min} min")
    choice = ask_break(activity.display_name, activity.description, activity.duration_min)

    if choice == BreakChoice.START:
        logger.info("user started break: %s", activity.id)
        if activity.category == "capture":
            _launch_capture_activity(activity, config)
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


def _launch_capture_activity(activity: Activity, config: Config) -> None:
    """Spawn a Claude session for a capture-category break activity."""
    command = _CAPTURE_COMMANDS.get(activity.id)
    if command is None:
        logger.warning("no Claude command mapped for capture activity %s", activity.id)
        return
    spawn_terminal(_resolve_vault_path(config), command, binary=config.claude_cli_path)


def _resolve_vault_path(config: Config) -> Path:
    return Path(config.vault_path) if config.vault_path else default_vault_path()


def _fire_ritual(ritual: Ritual, config: Config) -> None:
    """Deliver a ritual via the mode configured.

    ``notify_only`` — quiet notification. User opens Claude on their own.
    ``dialog``      — blocking dialog with Open now / Later / Skip. Open → terminal.
    ``terminal``    — unconditional terminal spawn (no dialog).
    ``headless``    — background ``claude -p <command>`` run, logs only.

    The ritual's own ``invoke`` field takes precedence; config provides the
    global default for rituals that haven't opted in.
    """
    mode = ritual.invoke if ritual.invoke != "dialog" else config.claude_invoke_mode
    vault = _resolve_vault_path(config)

    if mode == "notify_only":
        notify(ritual.notification_title, ritual.notification_body)
        return

    if mode == "headless":
        notify(ritual.notification_title, ritual.notification_body)
        run_headless(vault, ritual.slash_command, binary=config.claude_cli_path)
        return

    if mode == "terminal":
        notify(ritual.notification_title, ritual.notification_body)
        spawn_terminal(vault, ritual.slash_command, binary=config.claude_cli_path)
        return

    # Default: dialog
    choice = ritual_dialog(ritual.notification_title, ritual.notification_body)
    if choice == RitualChoice.OPEN:
        spawn_terminal(vault, ritual.slash_command, binary=config.claude_cli_path)
    elif choice == RitualChoice.LATER:
        logger.info("ritual %s deferred (Later)", ritual.id)
    else:
        logger.info("ritual %s skipped", ritual.id)


def _maybe_scan_overdue(config: Config, state: DaemonState, now_ts: float) -> None:
    """Hourly (by default) scan the vault for overdue tasks and notify if any."""
    if not config.overdue_scan_enabled:
        return
    last = state.last_overdue_scan_at
    interval = config.overdue_scan_interval_min * 60
    if last is not None and (now_ts - last) < interval:
        return

    vault = _resolve_vault_path(config)
    tasks = scan_overdue(vault, dt.date.today())
    state.last_overdue_scan_at = now_ts
    save_state(state)

    if len(tasks) >= config.overdue_notify_threshold:
        notify(
            f"{len(tasks)} overdue task{'s' if len(tasks) != 1 else ''}",
            "Run /tasks in the vault to review.",
        )
        logger.info("overdue scan: %d tasks over deadline", len(tasks))


def run(config: Config, state: DaemonState) -> NoReturn:
    """Main loop. Runs forever; SIGINT/SIGTERM handled by ``main()``."""
    threshold_sec = config.work_threshold_min * 60
    idle_threshold_sec = config.idle_threshold_min * 60
    inactive_nudge_sec = config.inactive_nudge_min * 60

    rituals = (
        build_rituals_from_config(
            config.morning_journal_at,
            config.midday_inbox_at,
            config.evening_shutdown_at,
            config.weekly_review_at,
        )
        if config.rituals_enabled
        else []
    )

    phase = Phase.WORKING
    current_activity: Activity | None = None
    break_until = 0.0
    # In-memory only: tracks whether we've already nudged for the current idle stretch.
    # Reset whenever the user becomes active again.
    inactive_nudge_sent = False

    logger.info(
        "starting life-os v%s — threshold=%ds idle=%ds nudge=%ds poll=%ds rituals=%d",
        __version__,
        threshold_sec,
        idle_threshold_sec,
        inactive_nudge_sec,
        config.poll_sec,
        len(rituals),
    )

    while True:
        now = time.time()
        idle = get_idle_seconds()
        logger.debug(
            "phase=%s active=%.0fs idle=%.0fs nudge_sent=%s",
            phase.name,
            state.active_seconds,
            idle,
            inactive_nudge_sent,
        )

        if rituals:
            for ritual in due_now(rituals, state.ritual_last_fired, dt.datetime.now()):
                logger.info("firing ritual %s", ritual.id)
                _fire_ritual(ritual, config)
                save_state(state)

        _maybe_scan_overdue(config, state, now)

        if phase == Phase.WORKING:
            if idle < idle_threshold_sec:
                state.active_seconds += config.poll_sec
            if state.active_seconds >= threshold_sec and idle < idle_threshold_sec:
                phase = Phase.BREAK_SUGGESTED

            # Inactivity nudge: fire once per idle stretch while WORKING.
            if idle >= inactive_nudge_sec and not inactive_nudge_sent:
                logger.info("inactivity nudge fired (idle=%.0fs)", idle)
                nudge_back_to_work(idle / 60)
                inactive_nudge_sent = True
            elif idle < inactive_nudge_sec and inactive_nudge_sent:
                # User is back at the desk — arm the nudge for the next idle stretch.
                inactive_nudge_sent = False

        if phase == Phase.BREAK_SUGGESTED:
            phase, current_activity, break_until = _suggest_and_handle(config, state)
            # Don't immediately re-nudge once we return to WORKING from a snooze/skip.
            inactive_nudge_sent = False
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
                inactive_nudge_sent = False
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
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("migrate", help="run the one-shot schema migration and exit")
    init_parser = subparsers.add_parser(
        "init-vault", help="create the second-brain vault skeleton and exit"
    )
    init_parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="override the vault path (defaults to config.vault_path or XDG default)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if args.command == "migrate":
        run_migration()
        return 0

    if args.command == "init-vault":
        cfg = load_config()
        target = args.path or (
            Path(cfg.vault_path) if cfg.vault_path is not None else default_vault_path()
        )
        init_skeleton(target)
        logger.info("vault initialized at %s", target)
        print(f"Vault initialized at {target}")
        return 0

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
    if needs_migration(state):
        state = run_migration()
    _install_signal_handlers()

    try:
        run(config, state)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
