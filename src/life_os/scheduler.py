"""Pure scheduler for life-os rituals.

No I/O, no subprocess. The daemon polls `due_now()` each iteration; any ritual
returned gets fired and recorded in `DaemonState.ritual_last_fired`.

Cron subset:
- ``"HH:MM"`` — every day at HH:MM
- ``"<Dow> HH:MM"`` — only on Dow (Mon/Tue/Wed/Thu/Fri/Sat/Sun) at HH:MM

Fires within ``grace_min`` minutes after the target time, once per day. This
survives daemon sleep/wake and poll intervals up to 30 minutes.
"""

from __future__ import annotations

import datetime as dt
import logging

from .rituals import Ritual

logger = logging.getLogger(__name__)

_DOW_MAP = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6,
}


def parse_cron(expr: str) -> tuple[int | None, int, int]:
    """Return (dow_or_none, hour, minute). Raises ValueError on malformed input.

    - ``"08:00"`` → (None, 8, 0)
    - ``"Sun 10:00"`` → (6, 10, 0)
    """
    parts = expr.strip().split()
    if len(parts) == 1:
        hh, mm = parts[0].split(":")
        return None, int(hh), int(mm)
    if len(parts) == 2:
        dow_raw, time_raw = parts
        if dow_raw not in _DOW_MAP:
            raise ValueError(f"unknown weekday {dow_raw!r}")
        hh, mm = time_raw.split(":")
        return _DOW_MAP[dow_raw], int(hh), int(mm)
    raise ValueError(f"malformed cron expression {expr!r}")


def _target_today(
    now: dt.datetime, hour: int, minute: int, dow: int | None
) -> dt.datetime | None:
    """Return today's scheduled datetime, or None if today isn't a match day."""
    if dow is not None and now.weekday() != dow:
        return None
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def due_now(
    rituals: list[Ritual],
    last_fired: dict[str, float],
    now: dt.datetime,
) -> list[Ritual]:
    """Return rituals that should fire right now.

    A ritual fires if:
    1. Today is a scheduling match (every day or matches the Dow).
    2. ``now`` is at or past the scheduled time.
    3. ``now`` is within ``grace_min`` minutes after the scheduled time.
    4. It hasn't already fired today (tracked by the unix ts of last fire).
    """
    due: list[Ritual] = []
    now_ts = now.timestamp()
    for ritual in rituals:
        try:
            dow, hour, minute = parse_cron(ritual.cron)
        except ValueError as exc:
            logger.warning("skipping ritual %s: %s", ritual.id, exc)
            continue

        target = _target_today(now, hour, minute, dow)
        if target is None:
            continue
        if now < target:
            continue
        if (now - target).total_seconds() > ritual.grace_min * 60:
            continue

        last = last_fired.get(ritual.id)
        if last is not None:
            last_dt = dt.datetime.fromtimestamp(last)
            if last_dt.date() == now.date():
                continue

        logger.debug("ritual %s due (target=%s now=%s)", ritual.id, target, now)
        due.append(ritual)
        # Optimistically mark so repeated calls within the same poll don't double-fire.
        last_fired[ritual.id] = now_ts
    return due
