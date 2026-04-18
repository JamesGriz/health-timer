---
name: para-classifier
description: Classify a raw note into Zettel / Project / Area / Resource / Task / Trash. Used by /process-inbox and inbox-triager.
---

# PARA classifier

Decision tree, in order:

1. **Trash** — the note is a duplicate of an existing one, superseded, or obvious ephemera ("reminder to check X tomorrow" that's already past).
2. **Task for existing project** — the note's content is an actionable next step and maps clearly to one of the `Projects/*/_project.md` files. Append as a checkbox in that project's `tasks.md`.
3. **Project** — outcome-bound with a natural deadline: "ship X", "plan Y trip", "write Z". Has more than one step. Scaffold `Projects/<slug>/`.
4. **Area** — an ongoing responsibility that doesn't have a completion state: "health", "finances", "relationship". File under `Areas/<slug>/_area.md`.
5. **Resource** — reference material, not actionable: "rust ownership notes", "best cafes in Berlin". File under `Resources/<slug>.md`.
6. **Zettel** — an atomic idea or insight worth keeping for future connection: "compounding attention works like interest", "bias for action is cheaper than planning". File under `Notes/YYYYMMDDHHMM-<slug>.md`.

Heuristics:

- If the note is a question, it's often a zettel seed (once answered) or a task (if answerable now).
- If the note mentions a specific person, project, or time frame, lean **project** or **task**.
- If the note is abstract and general, lean **zettel** or **resource**.
- When uncertain between zettel and resource: zettel if there's a novel take or connection; resource if it's compiled external knowledge.

Always return both the classification and a one-sentence rationale so the user can correct you.
