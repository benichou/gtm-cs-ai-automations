---
name: cs-account-health
description: Generate a QBR-ready 1-page account health summary for a Customer Success Manager. Trigger when the user asks to "summarize / review / prep QBR for / generate health brief for / give me context on" a Bridgit account, or provides an account_id (e.g. A007) and asks for context, status, or talking points.
---

# cs-account-health skill

This skill produces a CSM-ready brief for a single account, suitable for QBR prep or as the cold-open context before a customer call. It wraps the deterministic `gtm-cs` Python CLI in this repo and reshapes its JSON output into a 1-page markdown brief.

## When to use

Invoke this skill when the user:

- Provides an `account_id` (e.g. `A007`, `A042`) and asks for a brief, summary, status, or talking points.
- Asks to "prep me for the QBR with <account name>" or "give me context on <account>".
- Asks "what's going on with <account>?" or "is <account> at risk?".

Do NOT invoke for:

- Multi-account portfolio reports (this skill is single-account).
- Pricing or commercial questions (out of scope for the data we have).
- Anything not backed by the four `fixtures/*.csv` files in this repo.

## Prerequisites (verify before running)

1. Working directory contains the plugin layout (`pyproject.toml` declares `name = "gtm-cs-ai-automations"`). If you're at the monorepo root, the CLI is invoked as `uv run --package gtm-cs-ai-automations gtm-cs <account_id>`. If you're in the plugin subdir, `uv run gtm-cs <account_id>` works.
2. Fixtures exist at `gtm-cs-ai-automations/fixtures/*.csv` (4 files). If any are missing, run `uv run --package gtm-cs-ai-automations python scripts/seed.py` first.
3. Dependencies are synced. If `uv sync` hasn't been run since the last `pyproject.toml` change, run it before invoking the CLI.

## Steps

1. **Confirm the input.** Echo back `Processing account <account_id>` so the user can verify before we spend compute on it. If the input doesn't match the `A###` pattern, ask the user to clarify.

2. **Run the CLI**:
   ```bash
   uv run --package gtm-cs-ai-automations gtm-cs <account_id>
   ```
   This prints a JSON object on stdout. Capture it.

3. **Synthesize the markdown brief** in this exact shape:

   ```
   ## <account.name> — Account Health (as of <as_of>)

   **Plan**: <account.plan> · **MRR**: $<account.mrr> · **Started**: <account.started_at>
   **CSM**: <account.csm_email> · **Industry**: <account.industry> · **Active projects**: <account.project_count>

   ### Adoption (last 90 days)
   - Events: <adoption.events_last_90d> (prior 90: <adoption.events_prev_90d>) — **<adoption.trend>**
   - Top features: <comma-separated list of adoption.top_features_last_90d, "<feature> (<event_count>)">

   ### Top active tickets
   <For each of tickets.top_3: "- [<priority>] <summary> (opened <opened_at>, <status>)">
   <If tickets.top_3 is empty: "- None">

   ### Expansion signals (last 90 days)
   <If list is non-empty: "<count> signals: <comma-separated signal_type strings>">
   <If empty: "None">

   ### Churn risk: <churn_risk.score>/10
   <churn_risk.reasoning>

   ### Recommended QBR talking points
   <Generate 3 numbered talking points, grounded in the data above. Each should be one sentence. Examples of what to ground them in: feature gaps (if a top feature is absent), high-priority unresolved tickets, expansion signals worth reinforcing, churn risk drivers worth addressing.>
   ```

4. **If `churn_risk.escalate` is true** (score ≥ 7), prepend the brief with a single banner line:

   > ⚠️ **ESCALATE** — churn risk ≥ 7. Loop in CS leadership before the QBR.

5. **Surface failures from the CLI verbatim.** If the CLI exits non-zero, show the stderr to the user and explain — most commonly: `AccountNotFound` (typo in account_id), or missing fixtures (suggest running `scripts/seed.py`).

## Output shape (verbatim example for an account with mid-tier churn risk)

```
## Cascade Construction — Account Health (as of 2026-05-16)

**Plan**: growth · **MRR**: $4,200 · **Started**: 2024-09-12
**CSM**: csm3@example.com · **Industry**: general_contractor · **Active projects**: 24

### Adoption (last 90 days)
- Events: 38 (prior 90: 71) — **declining_sharply**
- Top features: schedule_builder (14), resource_forecast (11), reports_export (7)

### Top active tickets
- [high] Resource forecast off by 12 headcount (opened 2026-04-22, open)
- [normal] Reports export timing out for project 18 (opened 2026-05-02, pending)

### Expansion signals (last 90 days)
None

### Churn risk: 5/10
usage down >50% vs prior 90 days; 1 active high/urgent ticket; no expansion signals in 90 days

### Recommended QBR talking points
1. Acknowledge the adoption dip and ask what changed — usage in `resource_forecast` dropped most sharply, suggesting team workflow changes worth probing.
2. Get a status on the high-priority `Resource forecast off by 12 headcount` ticket and commit to a resolution date before the next QBR.
3. With 24 active projects but no expansion signals in 90 days, surface the `skills_matrix` and `mobile_app` features (low current usage) as candidates for the next quarter.
```

## Failure handling

- **`AccountNotFound`**: surface the error, suggest typo check, list the first 5 valid `account_id` values from `fixtures/accounts.csv`.
- **Fixtures missing**: run `uv run --package gtm-cs-ai-automations python scripts/seed.py`, then retry.
- **`uv` not installed**: tell the user to install [uv](https://docs.astral.sh/uv/) (`brew install uv`).
- **CLI prints malformed JSON**: do NOT improvise a brief. Show the stderr and ask for guidance.

## Helpful files in this skill directory

- (None yet — the CLI logic lives in `../../src/gtm_cs/cli.py`. The fixtures live in `../../fixtures/`.)
