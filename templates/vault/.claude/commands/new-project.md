---
description: Scaffold a new project under Projects/<slug>/ with _project.md and tasks.md.
---

Create a new project from `$ARGUMENTS` (the project name):

1. Slugify the name into `<kebab-slug>`.
2. Confirm the user's intended outcome (the one-sentence description of "done"), deadline (or "none"), and parent area.
3. Create `Projects/<slug>/_project.md` from `Templates/project.md`, substituting the answers.
4. Create `Projects/<slug>/tasks.md` with a single seed task: the `next_action` the user names.
5. Append `[[<slug>]]` under `## Projects` in `_meta/_master-index.md`.
6. If a parent area was named, add the project link to that `_area.md`'s `projects:` list.
