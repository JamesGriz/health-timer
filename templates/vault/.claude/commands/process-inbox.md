---
description: Iterate Inbox/, classify each note, move it to the right PARA location, clear inbox.
---

Process the inbox one note at a time:

1. List every `.md` file under `Inbox/`, oldest first.
2. For each file, read it and **propose** a classification to the user:
   - **Zettel** (atomic idea worth keeping) → move to `Notes/YYYYMMDDHHMM-<slug>.md`, rewrite frontmatter as `type: zettel`, suggest 1-3 links to existing notes.
   - **Project** (outcome-bound) → scaffold `Projects/<slug>/_project.md` with a `next_action`; move the raw capture into `Projects/<slug>/_project.md` as context.
   - **Area** (ongoing responsibility) → file into an existing `Areas/<slug>/_area.md` or create a new one.
   - **Resource** (reference, not actionable) → move to `Resources/<slug>.md`.
   - **Task for existing project** → append as a checkbox line in that project's `tasks.md`.
   - **Trash** (stale or superseded) → delete the file after the user confirms.
3. Show the user the proposed action and wait for `y`/`n`/`edit`. Apply on confirm.
4. After each move, update `_meta/_master-index.md` with a one-line entry.
5. At the end, report: N inbox items processed, M zettels, P projects, Q resources, R trashed.

Use the `para-classifier` skill for the classification heuristic and the `zettel-linker` skill when proposing links.

Inbox should end empty. If the user gets tired, stop where they are — partial processing is fine.
