---
description: Regenerate _meta/tasks.md with all open tasks, sorted by priority and due date.
---

Rebuild the tasks roll-up:

1. Glob every `**/*.md` except `Archive/**` and `_meta/query-cache/**`.
2. For each file, find:
   - Markdown checkboxes `- [ ] ...` — unchecked only. Parse any `<!-- due:YYYY-MM-DD priority:pN project:slug -->` hint after the text.
   - Standalone task notes (frontmatter `type: task`, status != done).
3. Sort: overdue first, then by priority (p0 > p1 > p2 > p3), then by due date ascending, then by creation time.
4. Write `_meta/tasks.md`:

   ```markdown
   ---
   type: index
   updated: <now>
   ---

   # Open tasks

   ## Overdue (N)
   - [ ] ...    [project] (due YYYY-MM-DD · p1) — path/to/file.md:LINE

   ## Due this week (N)
   ...

   ## All open (N)
   ...
   ```

5. Show the user the top 10 and ask what they want to do first.
