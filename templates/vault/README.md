# life-os vault

A Claude-Code-managed second brain. Structured as PARA + Zettelkasten.

## Using it

```bash
cd <this-vault>
claude                                # start a Claude Code session
/capture "something on my mind"       # drop in Inbox/
/daily                                # open/create today's daily note
/process-inbox                        # iterate Inbox/, classify, file
/weekly-review                        # Sunday review ritual
/tasks                                # roll-up of open tasks
/lint-vault                           # health check
```

See `.claude/commands/` for the full list.

## Philosophy

- **Inbox is the only capture surface.** Dump everything there; process on a schedule.
- **PARA for action.** Projects have deadlines, Areas don't, Resources are reference, Archive is the past.
- **Zettels for ideas.** One atomic thought per note in `Notes/`, linked by ID.
- **Daily for rhythm.** Morning intent, evening reflection, tomorrow's top three.

## Sync

Git works well. `git init` here and push to a private remote. Avoid iCloud/Dropbox — file watchers and sync clients fight each other.

## How the daemon fits

The `health-timer` CLI (installed via `life-os`) fires scheduled prompts throughout the day (morning journal, midday inbox, evening shutdown, weekly review) and alerts you when tasks go overdue. Config lives at `~/.config/health-timer/config.json`.
