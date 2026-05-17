---
name: sales-call-prep
description: Prep an Account Executive for a sales discovery call with a target company. Trigger when the user asks to "prep for / prepare for / help me prep for / get me ready for" a sales / discovery / intro / first call with a named company, or asks for "discovery questions for / context on / a brief on" a company, or when the /prep-call slash command delegates to this skill. Produces three artifacts: a company brief, five tailored discovery questions, and a draft follow-up email in the AE's voice.
---

# sales-call-prep skill

This skill orchestrates the end-to-end prep for an Account Executive's discovery call with a target company. It wraps the deterministic `gtm-sales-enrich` Python program (for company lookup) and then asks Claude to do three pieces of original writing: tailor discovery questions, draft a follow-up email in a specific voice, and assemble the final output.

## When to use

Invoke this skill when the user:

- Asks to "prep for / prepare for" a sales or discovery call with a named company.
- Asks for "discovery questions for <company>" or "context on <company>" or "a brief on <company>".
- Uses the `/prep-call <company>` slash command (which delegates here).
- Asks for help drafting a follow-up email for a sales meeting.

Do NOT invoke for:

- Meetings with existing customers (use the `cs-account-health` skill in the sibling `gtm-cs-ai-automations` plugin).
- Cold-outreach emails to prospects we haven't yet met (that's a different workflow).
- Generic email drafting that doesn't involve a target company name.

## Prerequisites (verify before running)

1. The working directory is somewhere inside the monorepo. The `gtm-sales-enrich` program is invoked as `uv run --package gtm-sales-ai-automations gtm-sales-enrich "<company>"` from any directory in the monorepo.
2. The companies fixture exists at `gtm-sales-ai-automations/fixtures/companies.json`. It's committed to the repo and should always be present.
3. The persona file exists at `gtm-sales-ai-automations/fixtures/persona.md`. Read it before drafting the email — it controls tone.
4. Dependencies are synced (`uv sync` from the monorepo root) if you haven't run anything else from this workspace yet.

## Steps

1. **Confirm the input.** Echo back `Prepping for a discovery call with <company>` so the user can verify the company name before we spend compute.

2. **Run the enrichment program**:
   ```bash
   uv run --package gtm-sales-ai-automations gtm-sales-enrich "<company>"
   ```
   The program prints a structured JSON result to standard output. Capture it.

3. **Handle the lookup result**:
   - If `found` is `true` and `match_type` is `"exact"`: proceed with the matched company data.
   - If `found` is `true` and `match_type` is `"fuzzy"`: mention to the user that the exact name wasn't found and you're proceeding with the closest match (give its name). Then continue.
   - If `found` is `false`: surface the `candidates` list to the user and ask which one they meant, OR offer to proceed with generic discovery questions if no candidate fits. Do not fabricate a company.

4. **Read the persona file** at `gtm-sales-ai-automations/fixtures/persona.md`. This controls the voice of the follow-up email you'll draft in step 6.

5. **Generate five discovery questions**, grounded in the company's `industry`, `pain_points_inferred`, and `recent_events`. Each question should be:
   - Open-ended (not a yes/no).
   - Specific to *this* company (referencing a recent event, a project, or a pain point).
   - Forward-looking (about how they handle X, not whether they have a problem).
   - Free of Bridgit product mentions (these are discovery, not pitch).

6. **Draft a follow-up email** in the persona's voice. Follow the structure spelled out in the persona file: greeting → acknowledgment with one specific reference → one observation or hypothesis → one clear next step → sign-off. The email should reference at least one specific item from `recent_events` or `notable_projects`.

7. **Assemble the final response** in this exact shape:

   ```
   ### Company brief

   **<company.name>** — <company.industry, prettified> · <company.headcount_band> employees · <company.revenue_band>
   <company.headquarters> · Founded <company.founded_year> · Active in: <company.regions_active, comma-separated>

   **Recent events:**
   <bullet-list of company.recent_events>

   **Notable projects:**
   <bullet-list of company.notable_projects>

   **Inferred pain points relevant to workforce planning:**
   <bullet-list of company.pain_points_inferred>

   ### Discovery questions

   1. <question 1>
   2. <question 2>
   3. <question 3>
   4. <question 4>
   5. <question 5>

   ### Draft follow-up email

   Subject: <one-line subject>

   <email body following the persona structure>

   Thanks,
   Sarah
   ```

8. **If `match_type` was `"fuzzy"`**, prepend the entire response with a single one-line note:

   > _Note: exact company name not found in the database; proceeding with closest match `<company.name>`. Let me know if this is wrong._

## Failure handling

- **Lookup returns `found: false`**: do NOT proceed silently. Show the user the `candidates` list and ask which one they meant. If they confirm "none of these," offer to proceed with generic discovery questions for the industry (but flag that the email draft will be weaker without specifics).
- **Enrichment program fails to run**: surface the stderr to the user. Most common cause is a missing fixture file — suggest `git status` to verify nothing's been deleted.
- **Persona file missing**: the email will sound generic. Tell the user explicitly: "I'm drafting without the persona file at `fixtures/persona.md` — the email may sound less like you. Restore the file and re-run for a better draft."
- **Company name in the user's question contains potentially-real customer data** (e.g., looks like a real company they shouldn't be paste-leaking): proceed normally — the fixture is synthetic and the lookup will return `found: false` for any real name, which is the right outcome.

## Output shape (verbatim example)

```
### Company brief

**Foundry Contractors** — General contractor · 1000-5000 employees · $500M-$1B
Denver, CO · Founded 1962 · Active in: Mountain West, Pacific Northwest

**Recent events:**
- Announced expansion into Idaho data-center construction (Q1 2026)
- Hired new VP of Field Operations from a Top-50 ENR competitor (Mar 2026)
- Reported 18% YoY revenue growth in their 2025 annual review

**Notable projects:**
- Phoenix Light Rail Extension ($420M, 2024-2026)
- Boise Federal Courthouse retrofit ($110M, 2023-2025)
- Denver International Airport concourse expansion ($380M, ongoing)

**Inferred pain points relevant to workforce planning:**
- Rapid hiring in skilled trades during a national shortage
- Multi-region scheduling across 8+ active megaprojects
- Subcontractor coordination on federal contracts with strict prevailing-wage compliance

### Discovery questions

1. With the move into data-center construction, what's changing about how you forecast skilled-trade demand 6-12 months out?
2. How are you currently coordinating crew schedules across Phoenix Light Rail, the Denver airport concourse, and the new Idaho work — same tooling or different per region?
3. Your new VP of Field Operations came from a Top-50 ENR competitor — what's she pushing to change about how the field-ops team plans headcount?
4. On the federal courthouse work, how are you currently tracking prevailing-wage compliance against your scheduled crew hours?
5. When you grew 18% last year, what was the first system that started to creak under the load — and what did you patch?

### Draft follow-up email

Subject: Quick follow-up on Foundry's multi-region scheduling

Hi <prospect>,

Thanks for the time today — the piece on coordinating crews across the Phoenix
Light Rail extension, the Denver airport concourse, and now the Idaho data-center
work really stood out to me. The 8+ megaproject pattern usually starts to break
the tools that worked at 3-4.

A couple of our customers running similar multi-region books — Northstar Civil
in Minneapolis is the closest analog — found their existing scheduling stack
held up fine on individual projects but lost the cross-region view your VP of
Field Ops probably wants in her first 90 days.

Worth a 30-minute walk-through of how Northstar handled the same transition?
Open Tuesday or Wednesday next week.

Thanks,
Sarah
```

## Helpful files in this skill directory

- `README.md` — human-readable docs for this skill (the file you'd land on first as a developer reading this directory cold).
