# gtm-marketing-ai-automations (plugin)

The portfolio centerpiece. A Claude Code plugin that repurposes a long-form marketing asset into three channel-specific outputs (LinkedIn post, sales one-pager, customer email) with brand-voice grounding and a runtime-guaranteed audit log.

## Primitives in scope

This is the **composition plugin** — every Claude Code primitive is here:

| Primitive | Instance |
| --- | --- |
| Plugin | The bundle itself (`.claude-plugin/plugin.json`) |
| Slash command | `/repurpose <path>` — the user-facing entry point |
| Skill | `marketing-repurpose` — the orchestrator runbook |
| Skill | `marketing-brand-audit` — the post-write scoring check |
| Model Context Protocol server | `gtm-marketing` — 3 tools (extract asset text, score brand voice, look up style guide) |
| **Hook** | **NEW** — `PostToolUse` on the `Write` tool, writing `output/audit.jsonl` |

## What's new vs. earlier plugins

The hook is the only primitive earlier plugins didn't use. Everything else is reused. The hook is what makes the audit log a **runtime guarantee** rather than a workflow suggestion. The language model can forget steps in a runbook; hooks don't.

## Quickstart

```bash
# From the monorepo root
uv sync

# Smoke-check the MCP server
uv run --package gtm-marketing-ai-automations gtm-marketing-mcp --self-check

# Test the audit hook directly (no Claude Code involved)
echo '{"tool_name":"Write","tool_input":{"file_path":"output/test.md","content":"Crew scheduling across projects."}}' \
  | bash gtm-marketing-ai-automations/hooks/audit.sh
cat gtm-marketing-ai-automations/output/audit.jsonl

# Run the test suite
cd gtm-marketing-ai-automations && uv run pytest -v
```

## Registering the plugin in Claude Code

The plugin ships its own `.claude/settings.json` registering both the MCP server and the hook. Start Claude Code with that file:

```bash
cd /Users/franck.benichou/projects/personal/repos/gtm-cs-ai-automations
claude --strict-mcp-config \
       --mcp-config gtm-marketing-ai-automations/.claude/settings.json
```

`/mcp` should show `gtm-marketing · ✓ connected · 3 tools`.

## Using the plugin

In Claude Code, type:

```
/repurpose gtm-marketing-ai-automations/fixtures/sample-post.md
```

Or in plain English:

```
Repurpose the sample post into LinkedIn, one-pager, and email versions
```

You'll get back:
1. Three generated artifacts in `output/` (linkedin.md, onepager.md, email.md)
2. A brand-voice audit summary
3. Three lines in `output/audit.jsonl` — the runtime-guaranteed audit log

## File layout

```
gtm-marketing-ai-automations/
├── .claude-plugin/plugin.json
├── commands/repurpose.md            ← slash command (plugin-style path)
├── .claude/
│   ├── commands/repurpose.md        ← project-style path for dev mode
│   ├── settings.json                ← MCP server + hook registration
│   └── skills/
│       ├── marketing-repurpose/{SKILL.md, README.md}
│       └── marketing-brand-audit/{SKILL.md, README.md}
├── src/gtm_marketing/
│   ├── __init__.py
│   ├── mcp.py                       ← FastMCP server with 3 tools + CLI
│   ├── brand.py                     ← brand-voice scoring + style-guide lookup
│   └── extract.py                   ← asset text extraction
├── hooks/
│   ├── audit.sh                     ← PostToolUse hook script
│   └── README.md                    ← explains the hook in plain English
├── fixtures/
│   ├── style_guide.md               ← Bridgit brand voice spec
│   └── sample-post.md               ← long-form sample for /repurpose
├── output/                          ← gitignored; generated artifacts + audit.jsonl
├── tests/
│   ├── test_brand.py
│   ├── test_extract.py
│   ├── test_mcp_smoke.py
│   └── test_hook.py
├── pyproject.toml                   ← workspace member
└── README.md                        ← this file
```

## Interview talk-track for this plugin

> *This is the plugin where every Claude Code primitive composes. The slash command is the user-facing entry. The skill is the workflow brain. The Model Context Protocol server gives me capabilities reusable across plugins — read assets, score brand voice, look up style. The Write tool is built into Claude Code. And the PostToolUse hook is what makes the audit log a runtime guarantee instead of a workflow suggestion. Marketing leadership wants every AI-generated artifact auditable — that's not a 'usually' requirement, it's an 'always' requirement, which means the audit step belongs in a hook, not in the runbook.*
