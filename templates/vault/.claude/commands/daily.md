---
description: Open or create today's daily note and prompt for journal fields.
---

Open today's daily note using this recipe:

1. Compute today's local date as `YYYY-MM-DD`. Target path: `Daily/YYYY/MM/YYYY-MM-DD.md`.
2. If the file exists, read it and show the user the current contents. Skip to step 5.
3. Otherwise, create parent directories and write the file using `Templates/daily.md` as the template, substituting `{{date}}`, `{{created}}`, `{{updated}}` with today's values.
4. Pre-populate `morning_intent` if the user's message after `/daily` contains an intent; otherwise leave blank for them to fill.
5. Ask the user, one at a time (unless they batch-answer):
   - Mood (1-10)?
   - Energy (1-10)?
   - Morning intent — what's the one thing that matters today?
6. Update the frontmatter with their answers, set `updated:` to now, and save.
7. Append a link to today's daily from `_meta/_master-index.md` under the `## Daily` section if not already present.

If the user runs `/daily` in the afternoon or evening, they may be adding reflection instead — in that case append a `## Reflection` section at the end of the existing note rather than re-prompting for morning fields.
