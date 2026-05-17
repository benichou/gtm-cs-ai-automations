---
description: Prep for a sales discovery call with a target company — produces a company brief, 5 discovery questions, and a draft follow-up email
argument-hint: <company-name>
---

I'm prepping for a sales discovery call with **$1**.

Please use the `sales-call-prep` skill to generate the full prep package:

1. A short company brief (industry, headquarters, recent business events, notable projects).
2. Five tailored discovery questions, grounded in the company's inferred pain points and recent events.
3. A draft follow-up email written in my voice — see `gtm-sales-ai-automations/fixtures/persona.md` for tone and structure.

If the `sales-call-prep` skill isn't available, follow this fallback procedure manually:

- Run `uv run --package gtm-sales-ai-automations gtm-sales-enrich "$1"` to enrich the company.
- If the lookup returns `found: false`, surface the listed candidate names and ask which one I meant.
- Otherwise, generate the three artifacts described above, clearly delimited with `### Company brief`, `### Discovery questions`, and `### Draft follow-up email` section headers.
