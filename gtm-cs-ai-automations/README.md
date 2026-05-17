# gtm-cs-ai-automations (plugin)

A Claude Code plugin for Customer Success Managers. Given an `account_id`, produces a QBR-ready 1-page brief covering adoption trend, top active tickets, churn-risk score, expansion signals, and 3 talking points.

## Primitives in scope

- ✅ Claude Code **skill** (`cs-account-health`)
- ✅ Python CLI (`gtm-cs <account_id>` → JSON)
- ❌ No slash command (a CSM asks in natural language; no need for `/cmd` shortcut)
- ❌ No plugin-level distribution surface beyond `plugin.json` (we want the skill to auto-route, not require explicit `/install` per use)
- ❌ No MCP server (data is on disk — Claude can read files directly via the CLI)
- ❌ No hooks (no governance requirement here; we'll add them in `gtm-marketing-ai-automations`)

This intentional minimalism is the point of Repo 1: see how far a skill + CLI alone can take you before reaching for heavier primitives.

## Quickstart

```bash
# from the monorepo root
uv sync
uv run --package gtm-cs-ai-automations python scripts/seed.py  # generate fixtures
uv run --package gtm-cs-ai-automations gtm-cs A007             # one-shot brief
```

Or, inside a Claude Code session anywhere in this monorepo, ask in natural language:

> "Can you give me a QBR brief for account A007?"

Claude reads `.claude/skills/cs-account-health/SKILL.md` and decides the skill applies.

## File layout

```
gtm-cs-ai-automations/
├── .claude-plugin/plugin.json     ← plugin manifest (name, version, description)
├── .claude/skills/
│   └── cs-account-health/
│       └── SKILL.md               ← skill manifest + runbook
├── src/gtm_cs/
│   ├── __init__.py
│   └── cli.py                     ← `gtm-cs` CLI
├── scripts/
│   └── seed.py                    ← generates fixtures/*.csv
├── fixtures/                      ← gitignored; generated
├── tests/
│   └── test_cli.py
├── pyproject.toml                 ← uv workspace member
└── README.md                      ← this file
```
