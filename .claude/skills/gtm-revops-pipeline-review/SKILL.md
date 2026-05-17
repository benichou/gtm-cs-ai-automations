---
name: gtm-revops-pipeline-review
description: Run a Revenue Operations pipeline review for a sales leader or RevOps analyst. Trigger when the user asks to "review / roll up / summarize / brief me on / check" the pipeline, asks "how's the pipeline looking", asks for "pipeline by stage / by owner / by rep", asks to "find / flag / show stale deals / stuck deals / inactive opps", or asks for "data quality / hygiene / cleanup" issues in the pipeline. Calls the gtm-revops Model Context Protocol tools to assemble a Monday-morning pipeline summary.
---

# gtm-revops-pipeline-review skill

This skill produces a Monday-morning pipeline review for a Revenue Operations analyst or sales leader. It orchestrates the four tools exposed by the `gtm-revops` Model Context Protocol server: pipeline roll-up, data quality scan, stale-deal detection, and (when needed) deep-dive listing of open deals.

The skill assumes the `gtm-revops` Model Context Protocol server is registered in the user's Claude Code session. If it isn't, step 1 catches that and tells the user how to register it.

## When to use

Invoke this skill when the user:

- Asks for a pipeline review, pipeline roll-up, or pipeline summary.
- Asks to brief them on the pipeline or asks how the pipeline is looking.
- Asks for a breakdown by stage, by owner, or by sales rep.
- Asks to find stale, stuck, or inactive open opportunities.
- Asks about pipeline data quality, hygiene, or cleanup.
- Asks "what should I clean up before the forecast call?" or similar.

Do NOT invoke for:

- Single-account questions (use the `cs-account-health` skill in the sibling `gtm-cs-ai-automations` plugin).
- Discovery-call prep for a single prospect (use the `sales-call-prep` skill in `gtm-sales-ai-automations`).
- Closed-deal analysis or forecasting modeling (out of scope — this is current-pipeline hygiene + roll-up).

## Prerequisites (verify before running)

1. The `gtm-revops` Model Context Protocol server is registered. You should see tools whose names start with `mcp__gtm-revops__` (or similar, depending on Claude Code's naming convention) available. If not, tell the user to add this entry to their `.claude/settings.json` or `.claude/settings.local.json`:
   ```json
   {
     "mcpServers": {
       "gtm-revops": {
         "command": "uv",
         "args": [
           "run",
           "--package",
           "gtm-revops-ai-automations",
           "gtm-revops-mcp",
           "--stdio"
         ]
       }
     }
   }
   ```
   …then restart Claude Code.

2. The opportunities fixture exists. If any tool call returns a `FileNotFoundError` about `fixtures/opps.json`, tell the user to run:
   ```bash
   uv run --package gtm-revops-ai-automations gtm-revops-seed
   ```

## Steps

1. **Confirm the user's intent.** If the question was generic ("how's the pipeline looking?"), proceed with the default flow below. If they asked for a specific cut (by owner, by stage, stale-only, etc.), skip directly to that step.

2. **Run the pipeline roll-up by stage.** Call `roll_up_pipeline(group_by="stage")`. This is the headline number — total open pipeline value and count, broken down by stage.

3. **Run the data quality check.** Call `check_data_quality()`. Note the total number of issues and the breakdown by category. If there are issues that would distort the roll-up (e.g., negative amounts), call them out explicitly.

4. **Run the stale-deal check.** Call `flag_stale_opps(days=30)`. The result is sorted oldest-first — the top 5 are the priority follow-ups.

5. **Assemble the response** in this exact shape:

   ```
   ## Pipeline Review — <as_of>

   ### Open pipeline by stage
   **Total open**: $<total_open_amount, formatted with commas> across <total_open_count> deals
   <For each item in breakdown:>
   - **<stage>**: <count> deals · $<amount, formatted>

   ### Data quality
   <If total_issues == 0:>
   No data quality issues found.
   <Otherwise:>
   <total_issues> issues found across <number of non-empty categories> categories:
   - **Missing close date**: <count> deals
   - **Negative amount**: <count> deals (data-entry errors; excluded from roll-up totals)
   - **Orphan account**: <count> deals (account record was deleted)
   <If any individual issues stand out (e.g. very large amounts), list the top 3 by opp_id.>

   ### Stale open deals (no activity >30 days)
   <If empty:>
   No stale deals — pipeline activity looks healthy.
   <Otherwise list the top 5 by days_since_activity:>
   1. **<opp_id>** — <account_name>, <stage>, $<amount>, last touched <days_since_activity> days ago (<owner>)
   2. ...

   ### Recommended actions
   <Generate 3 specific actions grounded in what the data showed:
    - data quality issues to clean up (which ones, by whom),
    - stale deals to follow up on (highest-amount or oldest first),
    - any stage where pipeline coverage looks light or heavy.>
   ```

6. **If the user asked for a non-default cut** (e.g., "by owner", "just the data quality issues", "just the stale deals"), produce only the relevant section instead of the full review.

7. **Offer one follow-up.** End the response with a one-line nudge like:
   > Want me to drill into the top stale deal, or run the roll-up by owner instead?

## Failure handling

- **`gtm-revops` server not registered**: surface the settings snippet from Prerequisites step 1. Do not attempt to fall back to running the program manually via Bash — the user should register the server properly for the rest of the session to work cleanly.
- **`FileNotFoundError` on `fixtures/opps.json`**: tell the user to run `gtm-revops-seed` (see Prerequisites step 2).
- **A tool raises an unexpected exception**: surface the error to the user. Do not invent data.
- **The fixture is empty**: rare; tell the user the fixture has 0 rows and suggest regenerating it.

## Output shape (verbatim example)

```
## Pipeline Review — 2026-05-17

### Open pipeline by stage
**Total open**: $24,180,500 across 187 deals
- **Discovery**: 56 deals · $5,620,000
- **Qualification**: 62 deals · $7,830,500
- **Proposal**: 41 deals · $6,940,000
- **Negotiation**: 28 deals · $3,790,000

### Data quality
12 issues found across 3 categories:
- **Missing close date**: 5 deals
- **Negative amount**: 3 deals (data-entry errors; excluded from roll-up totals)
- **Orphan account**: 4 deals (account record was deleted)

Worth a quick triage — the orphan-account deals are likely blocking forecast accuracy.

### Stale open deals (no activity >30 days)
1. **O0042** — Foundry Contractors, Negotiation, $185,000, last touched 78 days ago (Sarah Chen)
2. **O0118** — Westbound Infrastructure, Proposal, $240,000, last touched 65 days ago (Marcus Rivera)
3. **O0227** — Anchor Construction Holdings, Discovery, $95,000, last touched 54 days ago (Priya Patel)
4. **O0091** — Cascade Construction Group, Qualification, $42,000, last touched 47 days ago (Diego Moreno)
5. **O0156** — Heartland Build Partners, Proposal, $310,000, last touched 41 days ago (Hannah Lindqvist)

### Recommended actions
1. Clean up the 3 orphan-account deals before the forecast call — they're distorting account-level reporting.
2. Sarah Chen has the top stale deal (O0042 at $185k, 78 days idle). Worth a Monday standup mention.
3. Negotiation has the smallest count (28 deals) — coverage looks thin vs. Proposal (41). Check whether late-stage deals are stalling out before close.

Want me to drill into the top stale deal, or run the roll-up by owner instead?
```

## Helpful files in this skill directory

- `README.md` — human-readable docs for this skill, explaining how the Model Context Protocol server primitive works at runtime.
