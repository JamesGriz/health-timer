---
name: content-distiller
description: Reduce a long ingested article to a curated wiki page with source-traceable claims.
---

# Content distiller

Given raw fetched content at `Ingested/raw/<file>.md`, produce a curated summary at `Ingested/curated/<slug>.md`.

Structure of the curated note:

```markdown
---
<frontmatter>
---

# <title>

> Source: [source_title](source_url) — fetched <fetched_at>

## TL;DR
Three sentences. What the piece is about and why it matters.

## Key claims
- Claim 1. [[Ingested/raw/...-file#Section-anchor]]
- Claim 2. [[Ingested/raw/...-file#Section-anchor]]

## Methods / evidence
What the author actually did or cited to support the claims. Keep it tight.

## Open questions
Things the piece raised but didn't answer. Seeds for future zettels.

## My take
Your reaction. Where it connects to existing notes. Where it's wrong.
```

Rules:

- **Every claim links back to the raw source** — source-traceable or it doesn't belong.
- **Compress ruthlessly** — if the raw is 5000 words, curated should be 300-500.
- **Preserve the author's voice for direct quotes** — quote, don't paraphrase contested claims.
- **"My take" is optional but encouraged** — the vault is yours; colour it.
