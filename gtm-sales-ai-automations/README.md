# gtm-sales-ai-automations (plugin)

A Claude Code plugin for Account Executives selling Bridgit's workforce-planning product to general contractors. Given a target company name, produces three artifacts in one response: a short company brief, five tailored discovery questions, and a draft follow-up email in the Account Executive's voice.

## Primitives in scope

- ✅ Claude Code **plugin** (the install unit, via `/plugin install`)
- ✅ Claude Code **slash command** (`/prep-call <company>`) — the primary entry point
- ✅ Claude Code **skill** (`sales-call-prep`) — also reachable via plain-English questions
- ✅ Python program (`gtm-sales-enrich`) — fixture-backed company lookup with fuzzy match
- ❌ No MCP server (data is on disk — see Plugin 3 for that primitive)
- ❌ No hooks (no governance requirement here — see Plugin 4 for that primitive)

This plugin is intentionally one step heavier than Plugin 1 (CS): it adds the slash-command primitive and the dual entry-point pattern (slash command + skill working together).

## Two ways to invoke it

**Slash command (preferred for repeat use):**
```
/prep-call Foundry Contractors
```

**Plain English (also works):**
```
Help me prep for the call with Foundry Contractors
```

Both routes converge on the same `sales-call-prep` skill, which orchestrates the workflow.

## Quickstart

```bash
# From the monorepo root
uv sync

# Test the enrichment program directly
uv run --package gtm-sales-ai-automations gtm-sales-enrich "Foundry Contractors"
```

Or, inside a Claude Code session anywhere in this monorepo (start with `claude --strict-mcp-config --mcp-config .claude/settings.json` from the umbrella root to isolate this repo's plugins from any other Claude Code config the user may have), either type the slash command or ask in plain English.

## How the lookup works

The plugin uses a **fixtures-only** data source — `fixtures/companies.json` holds 13 hand-crafted company entries shaped like what a real enrichment service (SEC EDGAR, Apollo, Clearbit) would return.

The matching logic in `src/gtm_sales/enrichment.py`:
1. Exact case-insensitive name match.
2. If no exact match, fuzzy substring + similarity match (uses Python's stdlib `difflib`).
3. If still nothing, returns a structured "unknown" response so the skill can downgrade gracefully (ask the user to confirm the name or proceed with generic questions).

The design point: the function signature and return shape would match a real HTTP enrichment client. Swap the fixture-reader for a `requests.get(...)` call and nothing else in the plugin changes. Fixture today, live API tomorrow.

## File layout

```
gtm-sales-ai-automations/
├── .claude-plugin/plugin.json         ← plugin manifest
├── commands/
│   └── prep-call.md                   ← slash command definition
├── .claude/skills/sales-call-prep/
│   ├── SKILL.md                       ← skill manifest + runbook
│   └── README.md                      ← human docs for the skill
├── src/gtm_sales/
│   ├── __init__.py
│   ├── cli.py                         ← `gtm-sales-enrich` CLI
│   └── enrichment.py                  ← fixture lookup + fuzzy match
├── fixtures/
│   ├── companies.json                 ← 13 company entries
│   └── persona.md                     ← AE voice for email drafts
├── tests/
│   └── test_enrichment.py
├── pyproject.toml                     ← uv workspace member
└── README.md                          ← this file
```
