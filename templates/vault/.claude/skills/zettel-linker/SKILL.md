---
name: zettel-linker
description: Given a note, find 2-5 candidate links in existing Notes/ via title/tag/body match.
---

# Zettel linker

When asked to suggest links for a note:

1. Extract the note's key concepts (the 3-7 most distinctive nouns/phrases from title + body).
2. Grep `Notes/**/*.md` for each concept. Collect candidate files.
3. Score candidates:
   - Tag overlap with the source note: +3 per shared tag
   - Title keyword match: +2
   - Body keyword match: +1
   - Same explicit `tags:` section: +1
4. Return the top 2-5 with score above a minimum threshold (default 3). Format each as:

   ```
   - [[YYYYMMDDHHMM-slug]] — <title> — <one-line why>
   ```

5. If fewer than 2 strong candidates exist, return what you have rather than padding. Bad links are worse than no links.

Never auto-add links — always propose for user confirmation.
