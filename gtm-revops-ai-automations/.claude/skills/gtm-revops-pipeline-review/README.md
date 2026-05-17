# gtm-revops-pipeline-review (skill)

A workflow Claude follows when a Revenue Operations analyst asks for a pipeline review, a pipeline roll-up, a data quality scan, or a stale-deal report. Orchestrates the four tools exposed by the **gtm-revops Model Context Protocol server** and assembles a Monday-morning pipeline summary in markdown.

This README is for human readers. The file Claude actually reads at runtime is `SKILL.md` next to it.

## What this directory contains

| File | Purpose |
| --- | --- |
| `SKILL.md` | The runbook Claude reads at runtime. Frontmatter describes *when* the skill should fire; the body describes *what* Claude should do once it does. |
| `README.md` | This file. Documentation for humans. Not read by Claude at runtime. |

The skill itself contains no Python code. The deterministic data work lives in the **Model Context Protocol server** at `../../../src/gtm_revops/mcp.py`, and the synthetic data the server reads lives in `../../../fixtures/opps.json`.

## The new primitive — a Model Context Protocol server

This plugin introduces a primitive the earlier plugins didn't use: a **Model Context Protocol server**. The earlier plugins (`gtm-cs-ai-automations`, `gtm-sales-ai-automations`) have Claude execute a one-shot Python program in a terminal via the Bash tool. That works when the workflow has a single deterministic transformation (give me a brief for an account, prep a discovery call for a company).

This plugin's workflow is different: a Revenue Operations analyst has **many related questions** ("show open deals", "spot bad data", "summarize by stage", "find what's stuck"), and each one is a different operation against the same underlying data. The right primitive for that shape is a Model Context Protocol server — a small background service that exposes a menu of operations Claude can pick from.

The server lives at `../../../src/gtm_revops/mcp.py`. It exposes four tools:

| Tool | Returns |
| --- | --- |
| `list_open_opps(stage?)` | Open opportunities, optionally filtered by stage |
| `check_data_quality()` | Pipeline-hygiene issues grouped by category |
| `roll_up_pipeline(group_by)` | Open pipeline value + count, grouped by stage or owner |
| `flag_stale_opps(days=30)` | Open deals with no activity in the last N days, sorted by oldest first |

Each tool is a plain Python function decorated with `@mcp.tool()`. The function signature becomes the argument schema Claude sees. The docstring becomes the description. The return value is serialized to JSON automatically. That's the entire authoring model.

## End-to-end flow when the skill fires

1. **Claude reads the runbook in `SKILL.md`.**
2. **Claude verifies the `gtm-revops` Model Context Protocol server is registered.** If not, surfaces the settings snippet for the user to add.
3. **Claude calls `roll_up_pipeline(group_by="stage")`** to get the headline pipeline numbers.
4. **Claude calls `check_data_quality()`** to surface hygiene issues.
5. **Claude calls `flag_stale_opps(days=30)`** to find deals that haven't moved in a month.
6. **Claude assembles the three sections** into a markdown pipeline review with formatted dollar amounts, a top-5 stale-deal list, and 3 recommended actions grounded in what the data showed.

Underneath, Claude isn't running anything via Bash — every tool call goes over the Model Context Protocol channel to the running server, which reads `fixtures/opps.json` and returns structured JSON.

## How the two transports work

The server can be invoked two ways. The wire protocol is identical in both cases — only how Claude Code connects to the server differs.

### Standard input/output (default for local development)

Claude Code starts the server as a child process and talks to it through standard input and standard output. Configure in `.claude/settings.json` or `.claude/settings.local.json`:

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

When Claude Code starts, it spawns the subprocess automatically. The user never sees the server start.

### Streamable HTTP (the "remote" demo)

You run the server yourself in a terminal:

```bash
uv run --package gtm-revops-ai-automations gtm-revops-mcp --http --port 8765
```

Then point Claude Code at the running service via settings:

```json
{
  "mcpServers": {
    "gtm-revops": {
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

The protocol over the HTTP transport is identical to the standard-input/output transport. Same tools, same schemas, same JSON-RPC messages — just delivered over HTTP instead of standard input/output. To deploy the server publicly (Fly.io, Cloudflare Workers, etc.), you containerize this exact code; only the URL Claude Code points at changes.

## The contract Claude sees from each tool

The Model Context Protocol exposes each tool's metadata to Claude as a schema. For `roll_up_pipeline`, what Claude actually receives:

```json
{
  "name": "roll_up_pipeline",
  "description": "Aggregate open pipeline value and deal count, grouped by stage or owner.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "group_by": {
        "type": "string",
        "enum": ["stage", "owner"],
        "default": "stage"
      }
    }
  }
}
```

That schema is **generated automatically** from the function signature in `mcp.py`:

```python
def roll_up_pipeline(group_by: Literal["stage", "owner"] = "stage") -> dict:
    """Aggregate open pipeline value and deal count, grouped by stage or owner."""
    ...
```

The `Literal["stage", "owner"]` type hint becomes the `enum` in the schema. The default value becomes the `default`. The docstring becomes the `description`. Claude uses all of this to decide when and how to call the tool. That's why type hints + docstrings matter in MCP-tool code — they're not documentation, they're the API contract.

## Where to make common changes

| You want to... | Edit this file |
| --- | --- |
| Add a new trigger phrase so different phrasings route to this skill | `description:` in `SKILL.md` frontmatter |
| Change the structure or sections of the pipeline review | `## Steps` step 5 of `SKILL.md` |
| Add a new tool to the server | `../../../src/gtm_revops/mcp.py` (define a new `@mcp.tool()`-decorated function) and `EXPECTED_TOOLS` in the same file |
| Change a tool's data shape | The tool function in `mcp.py`. Also update the placeholders in `SKILL.md`'s `## Output shape` section. |
| Regenerate the synthetic data with different distributions | `../../../src/gtm_revops/seed.py` |
| Swap the fixture for a real data source | `load_opps()` in `../../../src/gtm_revops/data.py` — replace the JSON read with a database query or API call. Tool signatures stay identical. |

## Verifying changes after editing

From the plugin root (`gtm-cs-ai-automations/gtm-revops-ai-automations/`):

```bash
# Run unit tests
uv run pytest -v

# Smoke-check the server boots and registers all 4 tools
uv run gtm-revops-mcp --self-check

# Inspect tools interactively via the official MCP inspector
uv run mcp dev src/gtm_revops/mcp.py
```

From the monorepo root:

```bash
# Validate SKILL.md + plugin.json + marketplace.json
uv run --no-project python scripts/validate_manifests.py
```

For a full end-to-end test, register the server in your Claude Code settings (see "How the two transports work" above), open a fresh Claude Code session with `claude --strict-mcp-config --mcp-config /path/to/your/settings.json`, and ask in plain English: *"How's the pipeline looking?"*

## Design choice — why a Model Context Protocol server, not just a Python program

This is the design question you'll be asked about in the interview. The crisp answer:

- **Plugins 1 and 2** each had a *single* deterministic operation against a data source. A Python program called via the Bash tool is the right primitive for that shape — one input, one output, one program per workflow.
- **Plugin 3** has *four* related operations against the same data, and the Revenue Operations analyst will pick different ones depending on what they're asking. Wrapping each operation as a separate Python program would be ugly — they'd share a lot of code, and Claude would need to memorize which program does what.
- **A Model Context Protocol server** is the right primitive: Claude sees a clean menu of operations with proper schemas, the server is reusable from any other plugin/agent/large-language-model client that speaks the protocol, and the capability is decoupled from the application.

The talk-track in one breath: *"a Python program called via Bash is good for one operation against a data source; a Model Context Protocol server is good for several related operations against the same data, especially if you want the capability to be reusable across multiple consumers."*
