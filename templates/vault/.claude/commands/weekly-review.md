---
description: Sunday weekly-review ritual. Walks projects, areas, inbox, and tasks; writes a review note.
---

Run the weekly review:

1. **Inbox check** — if `Inbox/` is non-empty, invoke `/process-inbox` inline. Don't block the review on it; note the count if skipped.
2. **Projects** — for each `Projects/*/_project.md`:
   - Is `status: active` but `next_action` empty or unchanged in 7+ days? Flag as stale.
   - Is `deadline` past? Flag as overdue.
   - Is it actually done? Offer to move to `Archive/<YYYY-Qn>/`.
3. **Areas** — for each `Areas/*/_area.md`:
   - Is `last_reviewed` > the `review_cadence` (weekly/monthly)? Flag for attention.
4. **Tasks** — invoke `/tasks` inline to regenerate `_meta/tasks.md`. Highlight overdue and p0 items.
5. **Lint** — invoke `/lint-vault` and summarize findings (broken links, orphans, missing frontmatter).
6. **Write the review note** at `Daily/YYYY/MM/YYYY-MM-DD.md` under a `## Weekly review` section (or a dedicated note if the user prefers). Include:
   - What shipped this week (projects moved to archive, tasks closed).
   - What's stuck (stale projects, overdue items).
   - Top 3 for next week.
   - Open questions / thoughts.

Keep it conversational — this is a ritual, not a status report. Ask the user before making big moves (archive a project, delete a resource).
