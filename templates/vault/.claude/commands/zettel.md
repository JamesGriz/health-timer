---
description: Create a new atomic zettel in Notes/ from Templates/zettel.md.
---

Create a new zettel for the idea in `$ARGUMENTS` (or ask the user if no argument):

1. Generate ID `YYYYMMDDHHMM` (local time, zero-padded).
2. Distil a 3-6 word slug from the idea.
3. Write `Notes/<ID>-<slug>.md` from `Templates/zettel.md`.
4. Invoke the `zettel-linker` skill to suggest 2-5 candidate links to existing `Notes/*`. Add them to `links:` if the user approves.
5. Append a one-line entry under `## Notes` in `_meta/_master-index.md`.
6. Print the new file path.

Remind the user: one idea per note. If they want to capture multiple, split now.
