---
description: Grep + frontmatter-aware search over the vault. Returns ranked matches.
---

Search the vault for `$ARGUMENTS`:

1. Run ripgrep/grep over `**/*.md` (exclude `_meta/query-cache/**`).
2. For each hit, read the file's frontmatter and weight the match:
   - Title match: +3
   - Tag match: +2
   - Body match: +1
   - Recency boost: newer `updated:` ranks higher on ties.
3. Return the top 20 hits as a markdown list: `- [[ID-slug]] — <title> (<one-line snippet>)`.
4. Offer to open any of them for deeper inspection.

If the user's query looks like an ID (`YYYYMMDDHHMM...`), jump straight to that file.
