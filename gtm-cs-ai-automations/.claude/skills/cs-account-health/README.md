# cs-account-health (skill)

A workflow Claude follows automatically when a Customer Success Manager asks for a Quarterly Business Review brief, an account health summary, or any similar single-account context request.

This README is for human readers. The file Claude actually reads at runtime is `SKILL.md` next to it.

## What this directory contains

| File | Purpose |
| --- | --- |
| `SKILL.md` | The runbook Claude reads at runtime. The frontmatter (the `---` block at the top) describes *when* the skill should fire; the body describes *what* Claude should do once it does. |
| `README.md` | This file. Documentation for humans. Not read by Claude at runtime. |

The skill itself contains no Python code. The deterministic data work lives in `../../../src/gtm_cs/cli.py`, and the synthetic data the program reads lives in `../../../fixtures/`.

## What the skill does in plain English

A Customer Success Manager — the person at Bridgit responsible for keeping a roster of customer accounts happy and renewing — has a Quarterly Business Review with one of her accounts tomorrow morning. That's a recurring once-a-quarter meeting where she and the customer review what's been working and where the relationship is heading next quarter. Prep typically eats four to six hours per meeting.

She opens Claude Code in the repository folder and asks in plain English: *"Give me a QBR brief for account A007."* About 90 seconds later she has a one-page markdown document with adoption trend, top open support tickets, churn-risk score, expansion signals, and three suggested talking points. She walks into the meeting prepared.

## When this skill fires

When Claude Code starts in a directory, it scans every `SKILL.md` file under `.claude/skills/` and reads each one's `description:` line. Those descriptions become the routing signal — Claude reads your question and decides which (if any) skill best matches it.

This skill's description deliberately includes these trigger phrases:

- *summarize*
- *review*
- *prep QBR for*
- *generate health brief for*
- a literal account identifier pattern (e.g., `A007`, `A042`)
- the words *context*, *status*, or *talking points* when paired with an account ID

Examples of prompts that route to this skill:

- *"Give me a Quarterly Business Review brief for account A007"*
- *"Summarize account A042"*
- *"What's the health of A030?"*
- *"Generate a health brief for A015"*

Examples that should **not** route to this skill:

- *"What's the weather in Paris?"*
- *"How do I migrate the database?"*
- *"Tell me about Anthropic"* (no account ID, no QBR / health / summarize keyword)

If a phrasing you expect to route doesn't, that's a description tuning problem — edit the `description:` line in `SKILL.md` to include the new phrasing.

## End-to-end flow when the skill fires

1. **Claude reads the runbook in `SKILL.md`.** The numbered steps in `## Steps` describe exactly what to do.

2. **Claude confirms the input.** It echoes `Processing account <account_id>` so the user can sanity-check the ID before any compute is spent.

3. **Claude runs the Python program via the Bash tool.** The command is literally:
   ```
   uv run --package gtm-cs-ai-automations gtm-cs <account_id>
   ```
   The program (defined in `../../../src/gtm_cs/cli.py`) reads the four data files in `../../../fixtures/`, joins them on `account_id`, computes a churn-risk score, and prints structured data to standard output.

4. **Claude reads the structured data from the tool result.** The output of the Bash call comes back to Claude as a tool-result message.

5. **Claude formats the markdown brief.** The exact output shape is specified in `SKILL.md` under `## Output shape`. The angle-bracket placeholders in that template (like `<account.name>`, `<adoption.trend>`, `<churn_risk.score>`) are filled in by Claude by reading the structured data and substituting the matching field.

6. **Claude generates three Quarterly Business Review talking points.** This is the only step where Claude does original writing — the runbook explicitly asks Claude to *generate* (not substitute) three sentences grounded in the data above.

7. **If the churn-risk score is 7 or higher**, Claude prepends an ESCALATE banner to the top of the brief so the Customer Success Manager doesn't miss it.

The key idea: **Python does the math, Claude does the writing.** Large language models are bad at deterministic operations like "join these four tables and count rows" — they get arithmetic wrong and skip rows. Python (with pandas) is fast and exact for that part. Claude is great at "given this structured data, write three talking points a Customer Success Manager should raise tomorrow" — that's a judgment call, which is what language models are actually good at.

## The contract between SKILL.md and the Python program

The skill assumes the Python program prints structured data to standard output with this exact shape (see `../../../src/gtm_cs/cli.py::build_brief`):

```json
{
  "account_id": "A007",
  "account": {
    "name": "...", "plan": "...", "mrr": 0, "csm_email": "...",
    "started_at": "...", "industry": "...", "project_count": 0
  },
  "as_of": "2026-05-16",
  "adoption": {
    "events_last_90d": 0,
    "events_prev_90d": 0,
    "trend": "growing|steady|declining|declining_sharply|new_account|no_activity",
    "top_features_last_90d": [{"feature": "...", "event_count": 0}, ...]
  },
  "tickets": {
    "total_active": 0,
    "top_3": [{"ticket_id": "...", "opened_at": "...", "priority": "...",
               "status": "...", "summary": "..."}, ...]
  },
  "expansion_signals_last_90d": [...],
  "churn_risk": {"score": 0, "reasoning": "...", "escalate": false}
}
```

If you change the keys returned by the Python program, you must also update the angle-bracket placeholders in `SKILL.md`'s `## Output shape` section, or Claude will end up with placeholders it can't fill from the data.

## Where to make common changes

| You want to... | Edit this file |
| --- | --- |
| Add a new trigger phrase so a different phrasing routes to the skill | `description:` field in `SKILL.md` frontmatter |
| Change the markdown shape of the brief | `## Output shape` section of `SKILL.md` |
| Change the data the brief is grounded in (e.g., add a metric) | `build_brief()` in `../../../src/gtm_cs/cli.py` |
| Change the churn-risk scoring formula | `_churn_risk()` in `../../../src/gtm_cs/cli.py` |
| Change the escalation threshold (currently 7) | `_churn_risk()` in `../../../src/gtm_cs/cli.py` *and* step 4 of `## Steps` in `SKILL.md` |
| Regenerate the synthetic test data | `../../../scripts/seed.py` |

## Verifying changes after editing

From the plugin root (`gtm-cs-ai-automations/gtm-cs-ai-automations/`):

```bash
# Run the unit tests for the Python program
uv run pytest -v

# Spot-check the program directly
uv run gtm-cs A007
```

From the monorepo root (`gtm-cs-ai-automations/`):

```bash
# Validate that the SKILL.md frontmatter is still well-formed
uv run --no-project python scripts/validate_manifests.py
```

Then open a fresh Claude Code session with `claude --strict-mcp-config` (the flag isolates this session from any globally-configured external tool servers) and ask in plain English. The skill should still auto-route and the brief should still come back in the expected shape.

## Design choice — why only a skill plus a Python program for this plugin

A Claude Code plugin can ship up to five different primitive types. This plugin uses only two of them, and the reasoning is intentional:

- **A skill** (✅ used) — a workflow Claude runs on its own when a user's natural-language question matches the description. The right primitive when the user asks in plain English, which a Customer Success Manager will.
- **A slash command** (❌ skipped) — a shortcut the user explicitly types, like `/qbr A007`. A Customer Success Manager won't memorize a shortcut; she'll just ask. So skill auto-routing fits her workflow better.
- **A Model Context Protocol server** (❌ skipped) — an external program that exposes functions Claude can call. The right primitive when Claude needs to touch a live system (a customer-relationship management database, a data warehouse, an internal API). Here, all the data is on disk as CSV files — the Python program can read them directly.
- **Hooks** (❌ skipped) — shell commands that run automatically before or after each tool Claude uses. The right primitive when something has to happen 100% of the time (audit logs, safety checks, sensitive-content redaction). No such requirement here.
- **The plugin packaging** (✅ used) — `.claude-plugin/plugin.json` makes the whole bundle installable via the marketplace.

The sibling plugins in this monorepo (`gtm-sales-ai-automations`, `gtm-revops-ai-automations`, `gtm-marketing-ai-automations`) add those other primitives where they actually fit the use case. See the umbrella `../../../../README.md` for the full curriculum sequence and the rationale behind each plugin's primitive choices.
