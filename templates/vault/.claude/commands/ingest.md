---
description: Fetch a URL, save raw content to Ingested/raw/, write a curated distilled note to Ingested/curated/.
---

Ingest the URL provided as `$ARGUMENTS`:

1. Delegate to the `content-ingestor` subagent with the URL.
2. The subagent:
   - Fetches the page via WebFetch.
   - Writes the raw content to `Ingested/raw/YYYYMMDDHHMM-<slug>.md` with frontmatter: `type: ingested`, `source_url`, `source_title`, `source_author` (if discoverable), `fetched_at`, `distilled: false`.
   - Uses the `content-distiller` skill to produce a curated summary at `Ingested/curated/<slug>.md` with frontmatter: `type: ingested`, `distilled: true`, `raw_ref: Ingested/raw/...`, `source_url`, `tags`.
   - Suggests 2-5 links to existing notes (via `zettel-linker` skill) and adds them to `links:` in the curated note's frontmatter.
3. Append a one-line entry under `## Ingested` in `_meta/_master-index.md`.
4. Show the user the curated summary and ask if they want to promote any claims into atomic zettels in `Notes/`.
