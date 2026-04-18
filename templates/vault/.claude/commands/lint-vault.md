---
description: Health check — broken links, orphan notes, malformed frontmatter, missing updated timestamps.
---

Delegate to the `vault-linter` subagent with this scope:

1. **Broken links** — for every `[[ID-slug]]` reference in any `.md`, verify the target file exists.
2. **Orphans** — zettels in `Notes/` with zero inbound links.
3. **Frontmatter** — every note has `type:` and `created:`; `updated:` present on notes older than 1 day.
4. **Duplicates** — zettel IDs are unique; filename slugs should not collide within a folder.
5. **Stale indices** — `_meta/_master-index.md` references files that still exist.

Write the report to `_meta/query-cache/lint-<YYYY-MM-DD>.md` with sections for each issue type, sorted by severity. Show the user a one-paragraph summary and the path to the full report.

Don't auto-fix — flag. Offer a follow-up `/rebuild-index` if many stale entries.
