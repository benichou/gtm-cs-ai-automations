# CLAUDE.md — GTM AI Automations

This file is read by Claude Code at session start. It describes the repo's purpose, structure, conventions, and the rules to follow when building new plugins.

---

## What this repo is

A **Claude Code plugin marketplace** — a monorepo of four GTM-focused plugins, each demonstrating one additional Claude Code primitive over the previous one. The goal is a single screen-sharable repo that exercises all five Claude Code primitives end-to-end.

All data is synthetic. The "Bridgit" company framing is a persona for interview prep; nothing here originates from real Bridgit systems.

### Plugins at a glance

| Plugin | Team served | What it does | Primitives introduced |
|---|---|---|---|
| `gtm-cs-ai-automations` | Customer Success | Given an `account_id`, runs a Python CLI that joins four CSV fixtures (accounts, events, tickets, expansion signals), computes a churn-risk score, and returns structured JSON. Claude formats the JSON into a QBR-ready 1-page account health brief with adoption trend, top tickets, expansion signals, churn risk score, and 3 talking points. | Skill + CLI |
| `gtm-sales-ai-automations` | Sales / AE | Given a company name, runs a Python enrichment CLI that fuzzy-matches against a fixture of construction-industry companies and returns firmographic data (industry, headcount, revenue, recent events, pain points). Claude generates 5 tailored discovery questions and a draft follow-up email written in the AE's persona voice. | Slash command + Skill + CLI |
| `gtm-revops-ai-automations` | Revenue Operations | Exposes 4 MCP tools over a persistent background server: pipeline roll-up by stage or owner, data quality scan (missing dates, negative amounts, orphan accounts), stale-deal detection, and open-opportunity listing. Claude assembles a Monday-morning pipeline review from the tool results. | MCP server (stdio + HTTP) + Skill |
| `gtm-marketing-ai-automations` | Marketing | Reads a long-form asset via MCP, grounds output in the brand style guide (also via MCP), writes 3 channel-specific artifacts (LinkedIn post, sales one-pager, customer email), then scores each against brand-voice rules. A PostToolUse hook fires on every file write and appends a JSON audit-log entry — guaranteed regardless of what Claude does. | MCP server + 2 Skills + Slash command + PostToolUse hook |

---

## The five Claude Code primitives — taxonomy

Every plugin in this repo is built from some subset of these five primitives. Know which one fits before writing any code.

| Primitive | What it is | Right choice when… |
|---|---|---|
| **Skill** (`SKILL.md`) | A workflow Claude follows automatically when a natural-language question matches the skill's `description:` frontmatter | The user will ask in plain English; you want Claude to own the full workflow |
| **Slash command** (`.claude/commands/*.md`) | A shortcut the user types explicitly, e.g. `/prep-call Foundry` | The workflow is repetitive and keyboard-efficient beats re-typing; use as a thin pass-through that delegates to a skill |
| **CLI program** (invoked via Bash tool) | A deterministic Python program Claude runs via `uv run` | One input → one structured-JSON output; the operation is pure data transformation with no need for Claude to call back into it |
| **MCP server** (`.claude/settings.json` → `mcpServers`) | A background service exposing a menu of tools Claude can pick from | Multiple related operations against the same data source, or you want the capability reusable across agents/clients |
| **Hook** (`.claude/settings.json` → `hooks`) | A shell command that fires automatically on a Claude Code event (e.g. `PostToolUse`) | Something must happen 100% of the time with no user action — audit logs, safety checks, governance |

**Decision shortcut:** one operation against data → CLI. Multiple operations against the same data → MCP server. Must happen every time → hook. User asks in plain English → skill. User types a shortcut → slash command that delegates to the skill.

---

## Repo structure

```
gtm-cs-ai-automations/                        ← monorepo root / working directory
├── CLAUDE.md                                 ← this file
├── README.md                                 ← human-facing docs + verification tests
├── pyproject.toml                            ← uv workspace declaration (lists all 4 plugins)
├── uv.lock
├── scripts/
│   └── validate_manifests.py                ← validates SKILL.md frontmatter + plugin.json + marketplace.json
├── .claude-plugin/
│   └── marketplace.json                     ← indexes all plugins for /plugin marketplace add
├── .claude/                                 ← umbrella-level config (mirrors everything for root-session use)
│   ├── settings.json                        ← ALL MCP servers + hooks registered here
│   ├── commands/                            ← slash commands mirrored from plugin subdirs
│   └── skills/                             ← skills mirrored from plugin subdirs
│
├── gtm-cs-ai-automations/                   ← Plugin 1 · CS · QBR account health brief (skill + CLI)
├── gtm-sales-ai-automations/                ← Plugin 2 · Sales · discovery call prep (slash command + skill + CLI)
├── gtm-revops-ai-automations/               ← Plugin 3 · RevOps · pipeline review (MCP server + skill)
└── gtm-marketing-ai-automations/            ← Plugin 4 · Marketing · content repurpose + audit (MCP server + 2 skills + slash command + hook)
```

### Plugin internal layout (canonical shape)

```
gtm-<slug>-ai-automations/
├── pyproject.toml                           ← declares package name, scripts (CLI entry points, MCP entry point)
├── README.md                                ← human-facing tour of the plugin
├── .claude-plugin/
│   └── plugin.json                         ← name, version, description, author, homepage
├── .claude/
│   ├── settings.json                       ← MCP server + hooks scoped to this plugin (for plugin-level launches)
│   ├── commands/                           ← slash command definitions (*.md) if the plugin has any
│   └── skills/
│       └── <skill-name>/
│           ├── SKILL.md                    ← the runbook Claude reads at runtime
│           └── README.md                   ← human docs (not read by Claude)
├── src/
│   └── gtm_<slug>/                         ← Python package (hyphens → underscores)
│       ├── __init__.py
│       ├── cli.py                          ← CLI entry point (if plugin uses CLI primitive)
│       └── mcp.py                          ← MCP server entry point (if plugin uses MCP primitive)
├── fixtures/                               ← synthetic data files (CSV, JSON, Markdown)
├── hooks/                                  ← hook shell scripts (if plugin uses hook primitive)
│   └── audit.sh
├── tests/
│   └── test_*.py
└── output/                                 ← runtime-generated artifacts (gitignored except for demo purposes)
```

---

## Naming conventions

The existing four plugins are named after GTM teams (`cs`, `sales`, `revops`, `marketing`). **A new plugin does not have to follow that pattern.** If the task being automated is more descriptive than the team that owns it, name the plugin after the task (e.g. `gtm-deal-scoring-ai-automations`, `gtm-onboarding-health-ai-automations`). The `gtm-` prefix and `-ai-automations` suffix are fixed; the middle segment (`<slug>`) should be the most descriptive label for what the plugin actually does.

| Thing | Convention | Team-named example | Task-named example |
|---|---|---|---|
| Plugin directory | `gtm-<slug>-ai-automations` | `gtm-revops-ai-automations` | `gtm-deal-scoring-ai-automations` |
| Python package name | `gtm-<slug>-ai-automations` (in `pyproject.toml`) | `gtm-revops-ai-automations` | `gtm-deal-scoring-ai-automations` |
| Python module | `gtm_<slug>` (hyphens → underscores) | `gtm_revops` | `gtm_deal_scoring` |
| MCP server key in `settings.json` | `gtm-<slug>` | `gtm-revops` | `gtm-deal-scoring` |
| MCP entry-point script | `gtm-<slug>-mcp` | `gtm-revops-mcp` | `gtm-deal-scoring-mcp` |
| CLI entry-point script | `gtm-<slug>` or `gtm-<slug>-<verb>` | `gtm-cs`, `gtm-sales-enrich` | `gtm-deal-score`, `gtm-deal-scoring-seed` |
| Skill name (SKILL.md `name:`) | `gtm-<slug>-<workflow>` | `gtm-revops-pipeline-review` | `gtm-deal-scoring-review` |
| Slash command file | `<verb>-<noun>.md` or `<verb>.md` | `prep-call.md`, `repurpose.md` | `score-deal.md` |

---

## The root `.claude/` — why it exists and how to keep it in sync

Claude Code scans `<cwd>/.claude/` for skills, commands, settings, and hooks. When Claude is launched from the **monorepo root**, it only sees `.claude/` at that level — it does not recurse into plugin subdirectories.

The root `.claude/` is therefore a **mirror** of every plugin's `.claude/` contents, assembled into one place so a single root-level session has access to everything.

**Rule: whenever you add or change a skill, slash command, MCP server, or hook in a plugin subdirectory, you must also update the root `.claude/` accordingly.**

| Plugin change | Root `.claude/` update required |
|---|---|
| New or edited `SKILL.md` | Copy to `.claude/skills/<skill-name>/SKILL.md` |
| New or edited `README.md` in a skill dir | Copy to `.claude/skills/<skill-name>/README.md` |
| New or edited slash command `*.md` | Copy to `.claude/commands/<filename>.md` |
| New MCP server | Add entry to `.claude/settings.json` under `mcpServers` |
| New hook | Add entry to `.claude/settings.json` under `hooks`; use `${CLAUDE_PROJECT_DIR}/<plugin-dir>/hooks/<script>.sh` as the command path |

---

## Adding a new plugin — checklist

Follow this order. Do not skip steps.

1. **Create the plugin directory** named `gtm-<slug>-ai-automations/` at the monorepo root.

2. **Add it to the uv workspace** — append to `members` in the root `pyproject.toml`:
   ```toml
   [tool.uv.workspace]
   members = [
       "gtm-cs-ai-automations",
       "gtm-sales-ai-automations",
       "gtm-revops-ai-automations",
       "gtm-marketing-ai-automations",
       "gtm-<slug>-ai-automations",   ← add here
   ]
   ```

3. **Write the plugin's `pyproject.toml`** — declare the package name, Python source layout, dependencies, and CLI/MCP entry-point scripts.

4. **Build the Python source** under `src/gtm_<slug>/`. Follow the primitive selection guide above. CLI programs print structured JSON to stdout. MCP tools are plain functions decorated with `@mcp.tool()` — type hints become the argument schema, docstrings become tool descriptions.

5. **Write fixtures** under `fixtures/` if the plugin needs synthetic data. Add a seed script if the fixture is generated.

6. **Write the skill(s)** — create `.claude/skills/<skill-name>/SKILL.md` using this frontmatter:
   ```yaml
   ---
   name: <skill-name>
   description: <one-line trigger description — this is what Claude matches against>
   ---
   ```
   The description must include all natural-language phrasings that should route to this skill. Include a README.md for human readers.

7. **Write slash commands** (if any) in `.claude/commands/<name>.md` using this frontmatter:
   ```yaml
   ---
   description: <one-line description>
   argument-hint: <hint shown in the UI>
   ---
   ```
   Slash commands should be thin — they expand `$1` and delegate to the skill, not reimplement the workflow.

8. **Write `plugin.json`** at `.claude-plugin/plugin.json`:
   ```json
   {
     "name": "gtm-<slug>-ai-automations",
     "version": "0.1.0",
     "description": "...",
     "author": { "name": "Franck Benichou" },
     "homepage": "https://github.com/benichou/gtm-cs-ai-automations"
   }
   ```

9. **Register the plugin in the marketplace** — add an entry to `.claude-plugin/marketplace.json` at the monorepo root.

10. **Write plugin-scoped `.claude/settings.json`** if the plugin has an MCP server or hook. This is used when launching Claude scoped to just this plugin.

11. **Mirror everything to the root `.claude/`** — see the sync table above.

12. **Write tests** under `tests/`. At minimum: a smoke test that the CLI/MCP entry point runs without error, and unit tests for the core logic.

13. **Run validation**:
    ```bash
    uv sync --all-extras
    uv run --no-project python scripts/validate_manifests.py
    uv run pytest --rootdir=gtm-<slug>-ai-automations -q
    uv run ruff check gtm-<slug>-ai-automations/src gtm-<slug>-ai-automations/tests
    ```

---

## Development workflow

```bash
# Install all plugins into shared virtualenv
uv sync --all-extras

# Run a specific plugin's CLI
uv run --package gtm-cs-ai-automations gtm-cs A007
uv run --package gtm-sales-ai-automations gtm-sales-enrich "Foundry Contractors"
uv run --package gtm-revops-ai-automations gtm-revops-mcp --self-check
uv run --package gtm-marketing-ai-automations gtm-marketing-mcp --self-check

# Run tests for a specific plugin
uv run pytest --rootdir=gtm-<slug>-ai-automations -q

# Lint a specific plugin
uv run ruff check gtm-<slug>-ai-automations/src gtm-<slug>-ai-automations/tests

# Validate all manifests (SKILL.md frontmatter, plugin.json, marketplace.json)
uv run --no-project python scripts/validate_manifests.py

# Launch Claude Code with all plugins loaded from monorepo root
claude --strict-mcp-config --mcp-config .claude/settings.json
```

---

## SKILL.md rules

- The `name:` slug must be unique across all skills in the repo.
- The `description:` line is the routing signal — write it to match every phrase a real user would type, not just the canonical one.
- Steps must be numbered and deterministic. Claude follows them in order.
- CLI invocations must use `uv run --package <plugin-name> <script>` so they work from any directory in the monorepo.
- Never fabricate data — if a CLI call fails or returns no results, surface the error verbatim.
- The output shape section must include a verbatim example; Claude uses it as the template.

---

## Python best practices

All Python in this repo follows PEP 8 and is enforced by `ruff`. These rules apply to every new plugin.

### Style and formatting

- Line length: **100 characters** (configured in root `pyproject.toml` under `[tool.ruff]`).
- Indentation: **4 spaces**. No tabs.
- Blank lines: 2 blank lines between top-level definitions (functions, classes); 1 blank line between methods.
- Imports: stdlib first, then third-party, then local — each group separated by a blank line. Use `ruff` with `isort` rules (the `I` rule set is already enabled).
- String quotes: double quotes preferred (ruff default).

### Type hints

All public functions must have type annotations on every parameter and the return type:

```python
def roll_up_pipeline(group_by: Literal["stage", "owner"] = "stage") -> dict:
    ...
```

Use `from __future__ import annotations` at the top of files that use forward references. Prefer the built-in generics (`list[str]`, `dict[str, int]`) over `typing.List`, `typing.Dict` (Python 3.10+ style, enabled by `UP` ruff rule set).

### Docstrings

- One-line docstrings for simple functions; no period at the end of a one-liner.
- MCP tool functions **must** have a docstring — it becomes the tool description Claude sees in the schema. Write it as an imperative phrase: `"Aggregate open pipeline value and deal count, grouped by stage or owner."`.
- Do not write docstrings that just restate the function name or parameters.

### Module structure

Each plugin's Python package follows this internal layout:

```
src/gtm_<slug>/
├── __init__.py          ← empty or re-exports public API only
├── cli.py               ← argparse / typer entry point; thin — delegates to domain modules
├── mcp.py               ← FastMCP server; thin — delegates to domain modules
├── data.py              ← data loading / IO (reads fixtures, writes output)
└── <domain>.py          ← pure business logic with no I/O side effects (easy to unit test)
```

Keep `cli.py` and `mcp.py` thin. Business logic belongs in domain modules so it can be unit-tested without invoking the CLI or spawning an MCP server.

### Error handling

- CLI programs must exit with a non-zero status code on error and print a human-readable message to `stderr`. Do not print tracebacks to `stdout`.
- MCP tools must raise a descriptive `ValueError` or `RuntimeError` on bad input. Do not swallow exceptions silently.
- Skills surface CLI `stderr` and MCP exceptions verbatim to the user — never fabricate a result when a tool call fails.

### Testing

- One test file per source module: `tests/test_<module>.py`.
- Use `pytest`. No `unittest.TestCase` classes.
- At minimum: unit tests for the core logic module, a smoke test that the CLI entry point runs and exits 0 on a valid input, and (for MCP plugins) a smoke test that the server registers the expected tools.
- Do not mock the filesystem for fixture-reading tests — use `tmp_path` (pytest built-in) or point at the real fixtures directory.
- Test function names: `test_<what>_<condition>` e.g. `test_roll_up_pipeline_by_stage`, `test_flag_stale_opps_returns_sorted`.

### Linting and formatting commands

```bash
# Check for lint errors
uv run ruff check gtm-<slug>-ai-automations/src gtm-<slug>-ai-automations/tests

# Auto-fix safe issues
uv run ruff check --fix gtm-<slug>-ai-automations/src gtm-<slug>-ai-automations/tests

# Format
uv run ruff format gtm-<slug>-ai-automations/src gtm-<slug>-ai-automations/tests

# Check formatting without writing (CI mode)
uv run ruff format --check gtm-<slug>-ai-automations/src gtm-<slug>-ai-automations/tests
```

Pre-commit hooks run `ruff check` and `ruff format --check` automatically on every `git commit`. Run `pre-commit install` once after cloning to enable them.

---

## What not to do

- Do not hardcode absolute paths in SKILL.md steps or slash command bodies. Use `uv run --package <name>` — it resolves correctly from any working directory inside the monorepo.
- Do not add a new MCP server to a plugin's `.claude/settings.json` without also adding it to the root `.claude/settings.json`.
- Do not add a new skill or slash command without mirroring it to the root `.claude/skills/` or `.claude/commands/`.
- Do not add a new workspace member without registering it in the root `pyproject.toml` and the root `.claude-plugin/marketplace.json`.
- Do not have a slash command reimplement a skill's workflow — the command must delegate to the skill via natural language.
- Do not invent data in a skill if a tool call fails. Surface the error.
- Do not put business logic in `cli.py` or `mcp.py` — keep them thin and delegate to domain modules.
- Do not use `typing.List`, `typing.Dict`, or other deprecated generic aliases — use built-in `list`, `dict` directly.
- Do not write docstrings on MCP tools that describe the parameters instead of the tool's purpose — Claude reads the docstring as the tool description.
