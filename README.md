# Health Timer

Smart break reminders for long computer sessions on macOS. Detects 45 minutes of *real* active use (not idle), then suggests a context-appropriate healthy activity — walk, snack, water, stretch, core, or yoga — and prompts you back to work when the break is up. Picks feel fresh: time-of-day weighting, anti-repetition, hydration override, and a randomised top-N sample so it never feels predictable.

[![CI](https://github.com/JamesGriz/health-timer/actions/workflows/ci.yml/badge.svg)](https://github.com/JamesGriz/health-timer/actions/workflows/ci.yml)

## How it works

A small Python daemon polls macOS HID idle time every 30 seconds. It accumulates *active* seconds (idle < 3 min). When you've been actively working for 45 minutes, it:

1. Picks a smart activity based on time of day, recent history, and hydration status.
2. Shows a notification + dialog with **Start now / Snooze 5 min / Skip**.
3. On Start, waits for the activity duration, then nudges you back to work.

If you go idle for 2+ minutes during a working stretch (an unscheduled walk-away — bathroom, knock at the door, drifted into a tab), it sends a single "Still there?" nudge to pull you back. The nudge re-arms once you're active again.

State persists across reboots. Auto-starts at login via `launchd`.

## Quick start

```bash
git clone https://github.com/JamesGriz/health-timer.git
cd health-timer

# 1. One-shot dev env setup (creates .venv, installs deps, runs checks)
./scripts/bootstrap-dev.sh

# 2. Try it foreground with a short threshold (90s instead of 45min)
source .venv/bin/activate
python -m life_os --debug --threshold-sec 90 --poll-sec 5

# 3. Install as a LaunchAgent (auto-starts at login)
./scripts/install.sh
```

## Configuration

Optional config file at `~/.config/health-timer/config.json`:

```json
{
    "work_threshold_min": 45,
    "idle_threshold_min": 3,
    "poll_sec": 30,
    "snooze_min": 5,
    "inactive_nudge_min": 2
}
```

| field                | default | meaning                                                                  |
| -------------------- | ------- | ------------------------------------------------------------------------ |
| `work_threshold_min` | 45      | Active minutes before suggesting a break.                                |
| `idle_threshold_min` | 3       | Idle stretch that pauses active-time accumulation.                       |
| `poll_sec`           | 30      | How often to check HID idle.                                             |
| `snooze_min`         | 5       | How long the **Snooze** button defers the next break.                    |
| `inactive_nudge_min` | 2       | Idle minutes during a working stretch before a "Still there?" nudge.     |

State persists at `~/.local/state/health-timer/state.json`. Logs at `~/Library/Logs/healthtimer.log`.

## Activity catalog

Around 30 specific activities across 6 categories. Each has time-of-day fit weights so morning suggestions favour energising activities (yoga, core, walk) and evenings lean toward winding down (legs-up-the-wall, hip openers, herbal tea). Add your own in [`src/life_os/activities.py`](src/life_os/activities.py).

## Development

Modern Python tooling: ruff (lint + format), mypy (strict), pytest (with coverage), pre-commit, GitHub Actions CI on macOS for Python 3.11 and 3.12.

```bash
ruff check . && ruff format .   # lint + format
mypy src                         # type-check
pytest -v --cov                  # tests + coverage
```

## Uninstall

```bash
./scripts/uninstall.sh
```

## License

MIT — see [LICENSE](LICENSE).
