# gtm-sales-leadership-ai-automations

Sales-leadership pipeline-health automation. Answers the specific aggregation questions a VP Sales asks every Monday morning, grounded in the current pipeline export.

## What it ships

A Model Context Protocol server exposing **4 sales-health tools**, plus **4 focused skills** that route to them.

| Skill | Tool | Question it answers |
|---|---|---|
| `gtm-sales-forecast` | `roll_up_forecast` | "Will I hit my number this period?" |
| `gtm-sales-closing-soon` | `list_deals_closing_by` | "What's closing this month?" |
| `gtm-sales-at-risk` | `rank_deals_by_risk` | "Which deals should I personally inspect?" |
| `gtm-sales-rep-scorecard` | `roll_up_by_owner` | "How are my reps doing?" |

Each skill is single-purpose and delegates to one MCP tool — composable through natural language ("first the forecast, then the at-risk list, then the rep scorecard").

## Data

The plugin reads `fixtures/pipeline_export.csv`. The fixture is a cleaned export of the Bridgit interview pipeline data — `arr` is integer USD, all dates are ISO `YYYY-MM-DD`, and the `as_of` anchor (2026-04-28) is hardcoded in `src/gtm_sales_leadership/data.py`. Swapping in a real CRM source is a one-function change in `data.load_opps`.

## Run locally

```bash
uv sync --all-extras

# Smoke-check the MCP server (boots, lists registered tools, exits 0)
uv run --package gtm-sales-leadership-ai-automations gtm-sales-leadership-mcp --self-check

# Tests
uv run pytest --rootdir=gtm-sales-leadership-ai-automations -q

# Lint
uv run ruff check gtm-sales-leadership-ai-automations/src gtm-sales-leadership-ai-automations/tests
```

## Risk score (used by `rank_deals_by_risk`)

Transparent, additive — max 10:

| Factor | Points |
|---|---|
| Stale (no activity > 14d) | +3 |
| Overdue (close_date < as_of) | +3 |
| Blank `next_step` on late-stage deal | +2 |
| Single-threaded (`num_contacts == 1`) on late-stage deal | +1 |
| In forecast (Commit or Best Case) | +1 |

Risk reasons are returned alongside the score so a Sales VP can read the *why*, not just the rank.
