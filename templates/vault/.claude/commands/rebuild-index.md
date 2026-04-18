---
description: Full rescan of the vault — rewrite _meta/_master-index.md from scratch.
---

Rebuild the master index:

1. Delegate to the `vault-linter` subagent.
2. Walk the vault and produce a fresh `_meta/_master-index.md` with sections:
   - `## Projects` — list each `Projects/*/_project.md` with title, status, deadline.
   - `## Areas` — list each `Areas/*/_area.md` with title, last_reviewed.
   - `## Resources` — one line per resource.
   - `## Notes` — one line per zettel, newest first (cap at 100; link to a full listing for the rest).
   - `## Ingested` — curated notes, newest first.
   - `## Daily` — last 14 days, with a "..." link to the full archive.
3. Set `updated:` to now.

This is a destructive rewrite — use sparingly. Prefer `/lint-vault` for normal health checks.
