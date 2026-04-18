---
name: vault-writer
description: Safe write primitives — atomic edits, frontmatter preservation, updated-timestamp bump.
---

# Vault writer

Rules for every file write inside the vault:

1. **Preserve frontmatter** — read the existing YAML block first. Merge your changes in; never drop existing keys even if unfamiliar.
2. **Bump `updated:`** to the current local ISO timestamp on every modification.
3. **Atomic writes** — write to a `.tmp` sibling, then rename over the target. Prevents corruption on crash.
4. **No body rewrites without diff** — show the user a unified diff before destructive replacements.
5. **Never edit `Archive/**` or `Daily/**` notes older than 30 days** without explicit instruction; those are historical.
6. **Respect gitignore** — if the vault has `.gitignore`, don't create files at paths it excludes without warning.

When creating a new note, always:

- Fill `type:`, `created:`, `updated:`, `title:` at minimum.
- Place the file at the canonical path for its type (see vault root CLAUDE.md naming table).
- Append a one-line entry to `_meta/_master-index.md` under the correct section.
