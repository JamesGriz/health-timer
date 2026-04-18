---
description: Drop a raw thought into Inbox/ with a timestamp. No processing.
---

Capture the user's thought as a new file in `Inbox/` with this recipe:

1. Read `$ARGUMENTS` as the free-form thought.
2. Generate a filename: `Inbox/YYYY-MM-DDTHHMM-<kebab-slug>.md` using local time. The slug is ~3-6 words distilled from the content.
3. Write the file with this frontmatter + body:

   ```markdown
   ---
   type: inbox
   created: <ISO timestamp>
   updated: <ISO timestamp>
   tags: []
   ---

   <the user's thought verbatim>
   ```

4. Print the path you wrote.

Do not classify, link, or modify the content. The Inbox is intentionally raw. Processing happens in `/process-inbox`.
