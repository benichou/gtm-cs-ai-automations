# GTM AI Automations — Claude Code Plugin Marketplace

> **Personal portfolio project.** Built for AI Technical PM interview preparation,
> 2026-05-16 to 2026-05-19. All data is synthetic. Not affiliated with, endorsed by,
> or representative of any current or former employer. The "Bridgit" framing is a
> persona for the interview prep; nothing in this repo originates from Bridgit
> systems or anyone associated with Bridgit.

A monorepo of five Claude Code plugins covering AI automations for go-to-market teams. The first four layer on one more primitive than the previous one, ending with a composition centerpiece that uses all five; the fifth (sales-leadership) demonstrates how to fan one Model Context Protocol server out to multiple single-purpose skills.

| Plugin | Team | Primitives |
| --- | --- | --- |
| [`gtm-cs-ai-automations`](./gtm-cs-ai-automations) | Customer Success | skill + CLI |
| [`gtm-sales-ai-automations`](./gtm-sales-ai-automations) | Sales | plugin + slash command + skill + fixture-backed enrichment |
| [`gtm-revops-ai-automations`](./gtm-revops-ai-automations) | RevOps | Model Context Protocol server (stdio + HTTP) + skill |
| [`gtm-marketing-ai-automations`](./gtm-marketing-ai-automations) | Marketing | plugin + slash command + 2 skills + MCP server + **PostToolUse audit hook** (composition centerpiece) |
| [`gtm-sales-leadership-ai-automations`](./gtm-sales-leadership-ai-automations) | Sales leadership | Model Context Protocol server (4 tools) + 4 single-purpose skills |

---

## Install as a Claude Code plugin

This repo is also a Claude Code **plugin marketplace** — every plugin above can be added via the `/plugin` flow inside Claude Code. If you only want to *use* the plugins (not develop them), this is the path.

### Prerequisites

- [Claude Code](https://claude.com/claude-code) installed (`claude --version` works).
- [`uv`](https://docs.astral.sh/uv/) installed — every plugin's CLI and Model Context Protocol server entry point runs under `uv run --package <name>`.

### Add the marketplace, install the plugins

Inside any Claude Code session:

```
/plugin marketplace add github:benichou/gtm-cs-ai-automations
/plugin install gtm-cs-ai-automations@benichou-ai-automations
/plugin install gtm-sales-ai-automations@benichou-ai-automations
/plugin install gtm-revops-ai-automations@benichou-ai-automations
/plugin install gtm-marketing-ai-automations@benichou-ai-automations
/plugin install gtm-sales-leadership-ai-automations@benichou-ai-automations
```

Install only the plugins you want — they're independent. The marketplace name `benichou-ai-automations` comes from `.claude-plugin/marketplace.json`.

### One-time Python install

The plugins' CLIs and Model Context Protocol servers are Python entry points declared in a `uv` workspace. Claude Code's plugin install machinery does **not** run `uv sync` for you — you have to do it once in the cloned marketplace directory so the entry points resolve:

```bash
# Marketplace clones land here by default:
cd ~/.claude/plugins/marketplaces/benichou/gtm-cs-ai-automations
uv sync --all-extras

# Plugins 1 and 3 need synthetic fixtures generated once:
uv run --package gtm-cs-ai-automations python gtm-cs-ai-automations/scripts/seed.py
uv run --package gtm-revops-ai-automations gtm-revops-seed
```

### Confirm install

Inside Claude Code, type `/mcp`. Depending on which plugins you installed, you should see some subset of:

```
gtm-revops            · ✓ connected · 4 tools
gtm-marketing         · ✓ connected · 3 tools
gtm-sales-leadership  · ✓ connected · 4 tools
```

Type `/` and your installed skills + slash commands should appear in the picker (e.g. `/prep-call`, `/repurpose`, plus the auto-routing skills listed in [Verification tests per plugin](#verification-tests-per-plugin)).

### Known install caveats

- **Plugin-internal `cwd` paths** — the MCP-server plugins (RevOps, Marketing, Sales-leadership) currently hardcode an absolute `cwd` in their `.claude/settings.json` that points to the maintainer's local checkout. If the marketplace clone lands somewhere else, edit those `cwd` fields to point at your clone, or use **Quickstart** (dev mode) below where the umbrella `.claude/settings.json` already resolves correctly.
- **No installer for Python deps** — if `uv sync` is not run after install, the MCP servers will fail to boot (`uv: command not found` style errors). This is the most common install failure mode.
- **Hooks fire globally once installed** — the Marketing plugin's `PostToolUse` audit hook runs on *every* `Write` tool call in any project you open with that plugin enabled. Uninstall the plugin if you don't want this.

---

## Quickstart — load everything in one Claude Code session

This monorepo is laid out so that opening Claude Code at the **umbrella root** with the right flags makes all five plugins simultaneously usable — all three Model Context Protocol servers connected, every skill auto-routable, both slash commands available, the audit hook live.

### One-time setup

```bash
# Clone (or `cd` if already cloned)
git clone https://github.com/benichou/gtm-cs-ai-automations.git
cd gtm-cs-ai-automations

# Install all five plugins and their dependencies into a shared virtual environment.
# This uses uv workspaces — every plugin is installed as an editable workspace member.
uv sync --all-extras

# Generate the synthetic fixtures used by Plugins 1 and 3 (only needed once).
uv run --package gtm-cs-ai-automations python gtm-cs-ai-automations/scripts/seed.py
uv run --package gtm-revops-ai-automations gtm-revops-seed
```

### Start Claude Code with all plugins loaded

```bash
cd /Users/franck.benichou/projects/personal/repos/gtm-cs-ai-automations
claude --strict-mcp-config --mcp-config .claude/settings.json
```

Two flags doing the work:

- **`--strict-mcp-config`** — isolates this repo's plugins, skills, Model Context Protocol servers, and hooks from any other Claude Code configuration the user may have. Tells Claude Code to ignore globally-configured Model Context Protocol servers, hooks, or settings inherited from `~/.claude/`, and use *only* what we point at with `--mcp-config`. The user's everyday Claude Code session stays untouched.
- **`--mcp-config .claude/settings.json`** — points at this repo's settings file, which registers both our Model Context Protocol servers and the audit hook.

### Confirm everything loaded

Inside Claude Code, type `/mcp`. You should see:

```
Manage MCP servers — 3 servers
  gtm-revops            · ✓ connected · 4 tools
  gtm-marketing         · ✓ connected · 3 tools
  gtm-sales-leadership  · ✓ connected · 4 tools
```

Type `/` and start typing a command name. You should see all skill + slash command entries: `/cs-account-health`, `/sales-call-prep`, `/gtm-revops-pipeline-review`, `/marketing-repurpose`, `/marketing-brand-audit`, `/gtm-sales-forecast`, `/gtm-sales-closing-soon`, `/gtm-sales-at-risk`, `/gtm-sales-rep-scorecard`, `/prep-call`, `/repurpose`.

That's the whole monorepo, live.

---

## Verification tests per plugin

Each plugin has a specific set of prompts that exercise its end-to-end behavior. Run them inside the same Claude Code session you started above. **Treat any unexpected output as a regression** — none of these should produce surprises.

### Plugin 1 · gtm-cs-ai-automations (skill + CLI)

| Prompt | Expected behavior |
| --- | --- |
| `Give me a Quarterly Business Review brief for account A007` | Claude routes to the `cs-account-health` skill, runs `uv run gtm-cs A007` via Bash, formats a 1-page markdown brief with all 5 sections (account header, adoption, top active tickets, expansion signals, churn risk, talking points). |
| `Summarize account A042` | Same skill, different account. Different account name, different numbers. |
| `What's the weather in Paris?` | Skill does **not** fire. Claude answers (or declines) normally. The description's trigger phrases shouldn't match unrelated questions. |
| `Show me account A999` | Skill fires, CLI returns `AccountNotFound`, Claude surfaces the error instead of fabricating a brief. |
| Find a high-risk account (see below), then ask for it | The brief should be prepended with `⚠️ **ESCALATE** — churn risk ≥ 7. Loop in CS leadership before the QBR.` |

To find a high-risk account from the terminal:

```bash
cd /Users/franck.benichou/projects/personal/repos/gtm-cs-ai-automations/gtm-cs-ai-automations
for i in $(seq -f "A%03g" 1 50); do
  score=$(uv run gtm-cs $i 2>/dev/null \
    | python -c 'import sys,json; print(json.load(sys.stdin)["churn_risk"]["score"])')
  echo "$i  $score"
done | sort -k2 -n -r | head -5
```

The top result is the account to ask for the ESCALATE banner test.

### Plugin 2 · gtm-sales-ai-automations (slash command + skill + persona)

| Prompt | Expected behavior |
| --- | --- |
| `/prep-call Foundry Contractors` | Slash command expands `$1` → `"Foundry Contractors"`, sends to Claude, Claude routes to `sales-call-prep`, runs `gtm-sales-enrich`, returns three sections: `### Company brief`, `### Discovery questions` (5 numbered), `### Draft follow-up email` (signed "Thanks, Sarah"). |
| `/prep-call foundry` | Same three artifacts, but the response opens with a note like *"exact name not found, proceeding with closest match Foundry Contractors"* — this tests the fuzzy-match branch. |
| `/prep-call Globex Megacorp` | No match. Claude lists 3 candidate names (Foundry Contractors, Cascade Construction Group, Apex Construction Managers) and asks which one you meant. **Must not fabricate.** |
| `Help me prep for the call with Cornerstone Design-Build` | Same workflow as the slash command, but reached via plain-English entry point. The 3-artifact shape should be identical. |

### Plugin 3 · gtm-revops-ai-automations (Model Context Protocol server)

| Prompt | Expected behavior |
| --- | --- |
| `How's the pipeline looking?` | Claude routes to `gtm-revops-pipeline-review` skill, calls `roll_up_pipeline(group_by="stage")`, then `check_data_quality()`, then `flag_stale_opps(days=30)`. Returns a 3-section Monday-morning review. Total open pipeline should be ~$19.5M across ~222 deals, exactly **12** hygiene issues (5+3+4 breakdown). |
| `Roll up the pipeline by owner` | Claude calls `roll_up_pipeline(group_by="owner")` — tests that Claude reads the tool schema's argument enum. Breakdown should be per sales rep. |
| `What data quality issues are in the pipeline?` | Single tool call to `check_data_quality()`. Should report exactly 12 issues: 5 missing close dates, 3 negative amounts, 4 orphan accounts. |
| `Show me deals stuck more than 60 days` | Claude calls `flag_stale_opps(days=60)`. Fewer deals than default 30-day threshold. Tests that Claude reads the docstring's `days` argument and tunes it. |

To smoke-check the server itself outside Claude Code:

```bash
uv run --package gtm-revops-ai-automations gtm-revops-mcp --self-check
# expected: "SELF-CHECK OK: 4 tools registered: [...]"
```

To inspect tools interactively in the official Model Context Protocol inspector:

```bash
uv run mcp dev gtm-revops-ai-automations/src/gtm_revops/mcp.py
```

### Plugin 4 · gtm-marketing-ai-automations (composition centerpiece + hook)

This plugin exercises every primitive in one workflow. The PostToolUse audit hook fires automatically on every file write — you don't have to ask for it.

| Step | Expected behavior |
| --- | --- |
| **Before testing** — clean prior runs | `rm -rf gtm-marketing-ai-automations/output/` so the run is fresh. |
| `/repurpose gtm-marketing-ai-automations/fixtures/sample-post.md` | Claude calls `extract_asset_text`, then `lookup_style_guide` four times (tone / structure / banned-phrases / preferred-phrases), then writes three files (`output/linkedin.md`, `output/onepager.md`, `output/email.md`), then chains into the `marketing-brand-audit` skill. The final response has 4 sections: artifact list, brand-voice audit table, audit-log confirmation, source preview. |
| **Verify the audit hook fired** | `cat gtm-marketing-ai-automations/output/audit.jsonl` — should contain exactly **3 lines**, one per file written. Each line has `ts`, `tool: "Write"`, `path`, `brand_voice_score`, `banned_hits`, `preferred_hits`. |
| **Verify the brand-audit skill ran** | The response should include a markdown table with one row per artifact, a score, and a Pass / Below-threshold status. Threshold is 0.7. |
| `Audit my generated artifacts again` | Re-runs `marketing-brand-audit` standalone on existing files in `output/`. Tests that the audit skill works without re-generating. |

To smoke-check the server + hook outside Claude Code:

```bash
# Server self-check
uv run --package gtm-marketing-ai-automations gtm-marketing-mcp --self-check
# expected: "SELF-CHECK OK: 3 tools registered: [...]"

# Hook smoke test — feed a fake event, check the audit log
rm -f gtm-marketing-ai-automations/output/audit.jsonl
echo '{"tool_name":"Write","tool_input":{"file_path":"output/test.md","content":"Crew schedule across the project with subs and field operations."}}' \
  | bash gtm-marketing-ai-automations/hooks/audit.sh
cat gtm-marketing-ai-automations/output/audit.jsonl
# expected: one JSON line with score 1.0 and preferred_hits including crew/schedule/subs/field
```

### Plugin 5 · gtm-sales-leadership-ai-automations (one MCP server → four focused skills)

Demonstrates the fan-out pattern: one Model Context Protocol server exposes four aggregation tools, each backed by a single-purpose skill so a Sales VP can ask the four Monday-morning questions in plain English.

| Prompt | Expected behavior |
| --- | --- |
| `What's my forecast?` | Routes to `gtm-sales-forecast`, calls `roll_up_forecast()`, returns a roll-up by Commit / Best Case / Pipeline / Omitted with weighted ARR and Commit+Best Case totals, plus one tactical observation. |
| `What's closing by end of May?` | Routes to `gtm-sales-closing-soon`, calls `list_deals_closing_by(period_end="2026-05-31")`, returns deals ordered by close date with stage and ARR. |
| `Which deals should I personally inspect this week?` | Routes to `gtm-sales-at-risk`, calls `rank_deals_by_risk()`, returns top-N deals with transparent additive risk score and reasons (stale, overdue, blank next-step, single-threaded). |
| `How are my reps doing?` | Routes to `gtm-sales-rep-scorecard`, calls `roll_up_by_owner()`, returns per-AE pipeline contribution and hygiene signals. |
| `What's the forecast for J. Torres?` | Same forecast skill but scoped to one owner — tests that Claude reads the tool's `owner` argument and forwards it. |

To smoke-check the server outside Claude Code:

```bash
uv run --package gtm-sales-leadership-ai-automations gtm-sales-leadership-mcp --self-check
# expected: "SELF-CHECK OK: 4 tools registered: [...]"
```

To inspect the tools in the Model Context Protocol inspector:

```bash
uv run mcp dev gtm-sales-leadership-ai-automations/src/gtm_sales_leadership/mcp.py
```

---

## What "passes" looks like across all five

If every test in the table above behaves as described, you have:

1. Three **Model Context Protocol servers** running over the standard-input/output transport, with 11 total tools registered between them.
2. Nine **skills** auto-routing from plain-English questions (one CS, one Sales, one RevOps, two Marketing, four Sales-leadership).
3. Two **slash commands** explicit-routing on typed shortcuts.
4. One **PostToolUse hook** producing a runtime-guaranteed audit log on every file write.
5. The **central marketplace manifest** ready for `/plugin marketplace add` by external users.

That's all five Claude Code primitives demonstrated in one screen-sharable repo.

---

## Develop

This is a [uv workspace](https://docs.astral.sh/uv/concepts/workspaces/). From the umbrella root:

```bash
uv sync --all-extras                                      # install everything
uv run --package <plugin-name> <command>                  # run a specific plugin's CLI
uv run pytest --rootdir=<plugin-name>                     # run a specific plugin's tests
```

### Pre-commit hooks (one-time setup)

Every commit runs `ruff check` (lint) and `ruff format --check` (format check) against staged Python files. To enable on a fresh clone:

```bash
# Install pre-commit at the system level (once per machine)
uv tool install pre-commit

# Install the git pre-commit hook into this repo (once per clone)
pre-commit install
```

After that, `git commit` automatically fails fast on style / lint issues before they reach CI. To run all hooks against all files manually:

```bash
pre-commit run --all-files
```

If a hook fails, the most common fixes are:

```bash
uv run ruff check --fix    # auto-resolve fixable lint issues
uv run ruff format         # canonicalize formatting in-place
```

To run all tests across all plugins:

```bash
for plugin in gtm-cs-ai-automations gtm-sales-ai-automations \
              gtm-revops-ai-automations gtm-marketing-ai-automations \
              gtm-sales-leadership-ai-automations; do
  echo "=== $plugin ==="
  uv run pytest "$plugin/tests" -q
done
```

> **Note:** several plugins share a `test_mcp_smoke.py` filename, so running `pytest` from the umbrella root without scoping by directory hits a module-name collision. The per-plugin loop above (passing the tests path explicitly) is the working pattern.

Linting:

```bash
for plugin in gtm-cs-ai-automations gtm-sales-ai-automations \
              gtm-revops-ai-automations gtm-marketing-ai-automations \
              gtm-sales-leadership-ai-automations; do
  echo "=== $plugin ==="
  uv run ruff check "$plugin/src" "$plugin/tests"
done
```

Manifest validation (marketplace, plugin.json files, SKILL.md frontmatter):

```bash
uv run --no-project python scripts/validate_manifests.py
```

---

## File layout

```
gtm-cs-ai-automations/                                    (umbrella / monorepo root)
├── .claude-plugin/marketplace.json                       (indexes all 5 plugins)
├── .claude/                                              (umbrella-level configuration)
│   ├── settings.json                                     (loads all 3 MCP servers + audit hook)
│   ├── commands/                                         (slash commands mirrored here for discovery)
│   │   ├── prep-call.md
│   │   └── repurpose.md
│   └── skills/                                           (all 9 skills mirrored here)
│       ├── cs-account-health/
│       ├── sales-call-prep/
│       ├── gtm-revops-pipeline-review/
│       ├── marketing-repurpose/
│       ├── marketing-brand-audit/
│       ├── gtm-sales-forecast/
│       ├── gtm-sales-closing-soon/
│       ├── gtm-sales-at-risk/
│       └── gtm-sales-rep-scorecard/
├── .github/workflows/ci.yml                              (matrix CI: lint + tests per plugin)
├── pyproject.toml                                        (uv workspace declaration)
├── README.md                                             (this file)
├── scripts/validate_manifests.py                         (zero-dep manifest validator)
├── gtm-cs-ai-automations/                                (Plugin 1)
├── gtm-sales-ai-automations/                             (Plugin 2)
├── gtm-revops-ai-automations/                            (Plugin 3)
├── gtm-marketing-ai-automations/                         (Plugin 4)
└── gtm-sales-leadership-ai-automations/                  (Plugin 5)
```

Each plugin subdirectory has its own README.md with a tour of what's inside.

---

## Why the umbrella-level mirrors exist

The skills and slash commands in each plugin's own `.claude/` directory are the canonical sources. The mirrors at the umbrella `.claude/` exist for one reason: Claude Code's discovery process scans `<cwd>/.claude/` for skills + commands, and starting Claude Code at the umbrella root would otherwise miss everything in the plugin subdirectories.

The mirroring is a developer-experience choice for this prep environment. In a real production deployment where users install plugins via `/plugin marketplace add github:benichou/gtm-cs-ai-automations` and then `/plugin install <plugin-name>`, the plugin-internal copies are what gets loaded by Claude Code's plugin-install machinery — no mirroring needed.

---

## Curriculum context

This repo is the deliverable for a 4-day interview prep curriculum laid out in [`../bridgit-interview-prep-plan.md`](../bridgit-interview-prep-plan.md). The progression is intentional:

- **Plugin 1 (CS)** — start with the smallest viable primitive (one skill + one CLI) to internalize how Claude Code discovers and runs a workflow.
- **Plugin 2 (Sales)** — add a slash command. Introduces the dual-entry-point pattern where typed shortcuts and natural-language questions both reach the same skill.
- **Plugin 3 (RevOps)** — add a Model Context Protocol server. Introduces the *menu-of-operations* model where Claude picks from registered tools instead of being told which command to run.
- **Plugin 4 (Marketing)** — compose everything. Adds the PostToolUse hook for runtime-guaranteed governance.
- **Plugin 5 (Sales leadership)** — demonstrate the fan-out pattern. One Model Context Protocol server, four narrowly-scoped skills, each answering one Monday-morning question for a Sales VP. Shows that "more skills per server" is a deliberate routing choice, not duplication.

