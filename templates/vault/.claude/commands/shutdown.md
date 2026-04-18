---
description: Evening shutdown ritual — reflection + tomorrow's top 3.
---

Close the day:

1. Open today's `Daily/YYYY/MM/YYYY-MM-DD.md`. If it doesn't exist, create it from `Templates/daily.md`.
2. Append (or update) a `## Reflection` section. Ask, one at a time:
   - What shipped today?
   - What got in the way?
   - What are you grateful for?
3. Append (or update) a `## Tomorrow` section with exactly **three** items. Ask the user to name them; keep the list to 3 — constraint is the point.
4. Scan `Projects/*/tasks.md` for tasks completed today (`- [x]`) — mention them in reflection if the user forgot.
5. Update the daily's `updated:` timestamp and save.
6. If `Inbox/` has unprocessed items, remind the user (don't force a `/process-inbox`).
