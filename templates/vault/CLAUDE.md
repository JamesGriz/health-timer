# life-os Vault — Claude Code Instructions

You are the steward of this vault. Every read, write, move, and link flows through you.

## What this is

A **PARA + Zettelkasten** hybrid second brain:

- **PARA** is the execution engine. Projects (outcome-bound, deadline), Areas (ongoing responsibilities), Resources (reference), Archive (done/dormant).
- **Zettelkasten** is the insight engine. Atomic notes in `Notes/`, linked by ID, accumulated over years.
- **Inbox** is the single capture surface. Everything starts there; the weekly review empties it.
- **Daily** holds one note per day — journal, reflection, intent, tomorrow's top-three.
- **Ingested** holds raw external content (URLs, articles) and its distilled curated form.

## Vault layout

```
Inbox/                            Raw capture — unprocessed.
Projects/<slug>/_project.md       Active outcome-bound work + tasks.md.
Areas/<slug>/_area.md             Ongoing responsibilities, reviewed periodically.
Resources/<slug>.md               Reference material by topic.
Archive/<YYYY-Qn>/…               Completed projects, dormant areas.
Notes/YYYYMMDDHHMM-slug.md        Atomic zettels — one idea, linked.
Daily/YYYY/MM/YYYY-MM-DD.md       Daily journal.
Ingested/raw/                     Unmodified fetched content.
Ingested/curated/                 Distilled wiki pages with source links.
Templates/                        Seed content for new notes.
_meta/_master-index.md            Auto-maintained orientation map.
_meta/tasks.md                    Auto-generated open-task roll-up.
```

## Naming conventions

| Type     | Pattern                                      |
|----------|----------------------------------------------|
| Daily    | `Daily/YYYY/MM/YYYY-MM-DD.md`                |
| Zettel   | `Notes/YYYYMMDDHHMM-kebab-slug.md`           |
| Inbox    | `Inbox/YYYY-MM-DDTHHMM-kebab-slug.md`        |
| Project  | `Projects/<kebab-slug>/_project.md`          |
| Area     | `Areas/<kebab-slug>/_area.md`                |
| Resource | `Resources/<kebab-slug>.md`                  |
| Ingested | `Ingested/(raw\|curated)/YYYYMMDDHHMM-slug.md` |

Timestamps are local time, zero-padded, no separators in zettel IDs (so they sort and embed in links).

## Frontmatter schema

Every note starts with a YAML block. `type` and `created` are required; the rest is opt-in.

```yaml
---
type: daily|zettel|inbox|project|area|resource|ingested|task
id: 202604181423
title: "Human-readable title"
created: 2026-04-18T14:23
updated: 2026-04-18T14:23
tags: [focus, pkm]
links: [202604101030-deep-work, areas/health]
---
```

Per-type extras are documented in `Templates/`.

## Wiki links

Use Obsidian-style `[[202604181423-compounding-attention]]` with optional display text `[[202604181423|compounding attention]]`. Prefer zettel IDs over slug-only links — slugs can collide; IDs cannot.

## Tasks

Tasks live two ways:

1. **Markdown checkboxes inside `Projects/*/tasks.md`** with inline hints:
   ```md
   - [ ] Write scheduler tests <!-- due:2026-04-22 priority:p1 -->
   ```
2. **Standalone notes** with `type: task` frontmatter (for non-project tasks).

The daemon's overdue scan reads both. Don't reinvent task tracking with tags.

## Rules you follow

1. **Always read `_meta/_master-index.md` first** when a session starts — it's your orientation map.
2. **Preserve frontmatter** on any edit. Update `updated:` to `now`. Never drop existing keys.
3. **When you create a note**, append a one-line summary under the right section of `_meta/_master-index.md`.
4. **When you move a note** across PARA folders, update every `[[link]]` that points to it. Run `/lint-vault` after bulk moves.
5. **Never delete `Daily/**` or `Archive/**`** without the user explicitly naming the file.
6. **Prefer small edits** over full rewrites. Markdown is for humans too.
7. **One idea per zettel** — atomicity is the point. If a note has two ideas, split it.
8. **Source traceability** — every curated ingested note must link back to its raw source.

## Slash commands

See `.claude/commands/`. Composition encouraged: `/weekly-review` calls `/lint-vault` and `/tasks`; `/process-inbox` calls `/zettel` or `/new-project` per item.

## Safety

Don't invoke Bash for destructive ops (`rm -rf`, `git reset --hard`) without explicit user approval. `git add` / `git commit` inside the vault are fine when the user asks.
