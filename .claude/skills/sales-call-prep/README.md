# sales-call-prep (skill)

A workflow Claude follows when an Account Executive wants prep for a sales discovery call. Produces three artifacts in one response: a company brief, five tailored discovery questions, and a draft follow-up email in the Account Executive's voice.

This README is for human readers. The file Claude actually reads at runtime is `SKILL.md` next to it.

## What this directory contains

| File | Purpose |
| --- | --- |
| `SKILL.md` | The runbook Claude reads at runtime. Frontmatter describes *when* the skill should fire; the body describes *what* Claude should do once it does. |
| `README.md` | This file. Documentation for humans. Not read by Claude at runtime. |

The skill itself contains no Python code. The deterministic data work lives in `../../../src/gtm_sales/enrichment.py`, and the fixtures live in `../../../fixtures/`.

## Two ways the skill is reached

Unlike the sibling `cs-account-health` skill which has a single natural-language entry point, this skill has **two** entry points that converge on the same workflow:

### Entry point 1 — the `/prep-call` slash command

The most common path. An Account Executive runs the same prep workflow many times a week with a single argument (the company name), so a memorized shortcut beats re-typing. The slash command definition lives at `../../../commands/prep-call.md`. When the user types `/prep-call Foundry Contractors`, Claude Code substitutes `$1 → Foundry Contractors` in the command's prompt body, then sends that prompt to Claude — which then matches it against this skill's description and follows the runbook.

### Entry point 2 — plain English

If someone asks *"help me prep for the Foundry call"* or *"give me discovery questions for Cornerstone Design-Build"*, Claude auto-routes to this skill via the same description-matching mechanism as the `cs-account-health` skill. Trigger phrases in the description include "prep for", "prepare for", "discovery questions for", and "context on", among others.

Both entry points end up running the same runbook in `SKILL.md`.

## End-to-end flow when the skill fires

1. **Claude reads the runbook in `SKILL.md`.**
2. **Claude confirms the input** (echoes the company name for sanity-check).
3. **Claude runs the enrichment program via the Bash tool**:
   ```
   uv run --package gtm-sales-ai-automations gtm-sales-enrich "<company>"
   ```
4. **The Python program** (`../../../src/gtm_sales/enrichment.py`):
   - Loads `../../../fixtures/companies.json`.
   - Tries an exact case-insensitive name match.
   - Falls back to a fuzzy match (substring + similarity score).
   - Returns either a match (with `match_type: "exact"` or `"fuzzy"`) or an unknown response with up to 3 candidate names.
5. **Claude handles the lookup result**:
   - Exact match → proceed.
   - Fuzzy match → prepend a one-line note to the response so the user knows we used the closest name.
   - No match → surface the candidate list and ask the user to clarify. Do not fabricate.
6. **Claude reads the persona file** at `../../../fixtures/persona.md` to learn the Account Executive's voice for the email draft.
7. **Claude generates 5 discovery questions** grounded in `industry`, `pain_points_inferred`, and `recent_events`. Each question is open-ended, specific to this company, forward-looking, and free of Bridgit product mentions.
8. **Claude drafts the follow-up email** in the persona's voice, following the structure spelled out in the persona file (greeting → specific acknowledgment → one observation → one clear next step → sign-off).
9. **Claude assembles the three artifacts** in the exact `### Company brief / ### Discovery questions / ### Draft follow-up email` shape specified in the SKILL.md.

As with Plugin 1, the principle is: **Python does the lookup and structured-data work; Claude does the writing.** The discovery questions and the email are the parts that need judgment — those are where Claude earns its keep.

## The contract between SKILL.md and the Python program

The skill expects the Python program to print this JSON shape to standard output (see `../../../src/gtm_sales/enrichment.py::EnrichmentResult.to_dict`):

```json
{
  "name": "Foundry Contractors",
  "found": true,
  "match_type": "exact",
  "candidates": [],
  "company": {
    "name": "Foundry Contractors",
    "type": "private",
    "industry": "general_contractor",
    "headcount_band": "1000-5000",
    "revenue_band": "$500M-$1B",
    "headquarters": "Denver, CO",
    "founded_year": 1962,
    "regions_active": ["Mountain West", "Pacific Northwest"],
    "recent_events": [...],
    "notable_projects": [...],
    "pain_points_inferred": [...],
    "source": "fixture"
  },
  "source": "fixture"
}
```

If the company name doesn't match, the response shape is:

```json
{
  "name": "<user's input>",
  "found": false,
  "match_type": "none",
  "candidates": ["closest name 1", "closest name 2", "closest name 3"],
  "company": null,
  "source": "fixture"
}
```

If you change the keys here (in the Python program), you must also update the corresponding `<placeholder>` references in `SKILL.md`'s `## Output shape` section.

## The persona file — controlling email tone

`../../../fixtures/persona.md` is a markdown file written in first-person describing the Account Executive's voice, common phrases, words she avoids, and the structural template for her emails. The skill reads it as context when drafting step 6.

To customize for a real Account Executive: edit `persona.md` to capture their actual voice. Tone-of-voice configuration lives entirely in that file; no code change needed.

## Where to make common changes

| You want to... | Edit this file |
| --- | --- |
| Add a new trigger phrase so a different phrasing routes here | `description:` in `SKILL.md` frontmatter |
| Change the structure or sections of the final 3-artifact response | `## Output shape` section of `SKILL.md` |
| Change the question-generation guidance (number of questions, style) | `## Steps` step 5 of `SKILL.md` |
| Change the email tone or structure | `../../../fixtures/persona.md` |
| Add a company to the database | `../../../fixtures/companies.json` |
| Change the company-name matching logic (fuzzy threshold, etc.) | `../../../src/gtm_sales/enrichment.py` |
| Swap the fixture for a real enrichment API | Replace the body of `lookup()` in `enrichment.py` with an HTTP client; the return shape stays the same. |

## Verifying changes after editing

From the plugin root (`gtm-cs-ai-automations/gtm-sales-ai-automations/`):

```bash
# Run the unit tests
uv run pytest -v

# Spot-check the enrichment program directly
uv run gtm-sales-enrich "Foundry Contractors"   # exact match
uv run gtm-sales-enrich "foundry"               # fuzzy match
uv run gtm-sales-enrich "Acme Holdings"         # no match → candidates
```

From the monorepo root (`gtm-cs-ai-automations/`):

```bash
# Validate that the SKILL.md frontmatter is still well-formed
uv run --no-project python scripts/validate_manifests.py
```

Then in a fresh Claude Code session with `claude --strict-mcp-config`, test both entry points:

```
/prep-call Foundry Contractors
```

and

```
help me prep for the call with Cascade Construction
```

Both should produce the same 3-artifact response shape.

## Design choice — why slash command + skill, not one or the other

A deliberate design choice. The slash command gives Account Executives the keystroke-efficient shortcut they want for repeat use. The skill gives anyone (including the same Account Executive in a different mood) a plain-English entry point. Both reach the same workflow, so we don't pay maintenance cost for two parallel implementations — the slash command is a thin pass-through that delegates to the skill.

## Why no Model Context Protocol server for this plugin

The data is on disk (a fixture JSON file). Model Context Protocol servers exist to give Claude access to live external systems — databases, internal APIs, third-party services. Here there's no external system to reach. If we wanted to swap the fixture for a live enrichment provider (SEC EDGAR, Apollo, Clearbit), we'd replace the body of `lookup()` in `enrichment.py` with an HTTP client and nothing else would change. The next plugin in this monorepo (`gtm-revops-ai-automations`) introduces the Model Context Protocol server primitive where it's genuinely the right choice.
