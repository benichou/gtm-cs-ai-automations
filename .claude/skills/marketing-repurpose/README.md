# marketing-repurpose (skill)

The orchestrator skill for the content-repurposing workflow. Takes a long-form marketing asset, generates three channel-specific outputs (LinkedIn post, sales one-pager, customer email), writes them to disk, and chains into `marketing-brand-audit` for a post-write quality check. The audit log is produced automatically by a PostToolUse hook on each file write — the skill does not write to the log directly.

This README is for human readers. The file Claude reads at runtime is `SKILL.md` next to it.

## What this directory contains

| File | Purpose |
| --- | --- |
| `SKILL.md` | Runbook Claude reads at runtime |
| `README.md` | This file — human docs |

## The composition pattern this skill demonstrates

This is the plugin where every Claude Code primitive composes:

```
User types: /repurpose fixtures/sample-post.md
        |
        v
Slash command (commands/repurpose.md)
   Expands $1 -> "fixtures/sample-post.md", sends prompt to Claude
        |
        v
Claude routes to skill: marketing-repurpose (this skill)
        |
        v
Skill runbook:
   1. Call extract_asset_text via the gtm-marketing MCP server
   2. Call lookup_style_guide (4 sections) via the MCP server
   3. Generate LinkedIn post -> Write tool
        |   <-- PostToolUse hook fires
        |   <-- hook script reads { tool_name, file_path } from stdin
        |   <-- appends { timestamp, path, score } to output/audit.jsonl
   4. Generate one-pager -> Write tool -> hook fires
   5. Generate email -> Write tool -> hook fires
   6. Chain into marketing-brand-audit skill (post-write check)
        |
        v
Final response: 3 artifacts on disk + audit-log confirmation + scoring summary
```

## What's new here vs. the earlier plugins

The hook is the only thing this plugin has that the earlier ones don't. Everything else (plugin, slash command, skill, MCP server) you've seen.

The hook makes governance **runtime-guaranteed** instead of **runbook-suggested**. In the earlier plugins, if a skill needs to log something, the SKILL.md tells Claude to do it. That works most of the time. Hooks are how you make it work *every* time, including when Claude forgets a step, mis-reads the runbook, or is invoked through a path the SKILL.md author didn't anticipate.

For an AI TPM, this is the "keep the AI workspace healthy" surface from the JD made concrete. If marketing leadership says *"every AI-generated marketing artifact must be auditable,"* a hook is the right primitive — it removes the language model from the trust path.

## End-to-end flow when the skill fires (turn-by-turn)

**Phase 0 — before the user types anything.** Claude Code reads `.claude/settings.json` and finds:
- An MCP server entry for `gtm-marketing` (so the 3 tools become available)
- A hooks entry: `PostToolUse` matching the `Write` tool, running `hooks/audit.sh`

Both are now active for the session.

**Phase 1 — Claude routes.** The user types `/repurpose fixtures/sample-post.md`. The slash command expands and sends a prompt to Claude. Claude reads the prompt, matches the `marketing-repurpose` skill description, loads this skill's runbook.

**Phase 2 — Claude extracts the asset.** Claude calls `extract_asset_text("fixtures/sample-post.md")` over the MCP protocol. The server reads the file, normalizes whitespace, returns `{text, word_count, char_count}`. Claude reads the response into context.

**Phase 3 — Claude loads brand context.** Four calls to `lookup_style_guide` for the sections tone, structure, banned-phrases, preferred-phrases. Each returns a markdown chunk Claude now has in context.

**Phase 4 — Claude generates and writes the LinkedIn post.** Claude composes a 3-5 sentence LinkedIn post grounded in the source text and the style guide. Then it uses the built-in `Write` tool to save it to `output/linkedin.md`. The moment that write completes, **Claude Code automatically runs the PostToolUse hook**:

```
[Write tool returns]
        |
        v
Claude Code: "PostToolUse hook matches the Write tool. Run hooks/audit.sh."
        |
        v
Hook script receives JSON on stdin:
   { tool_name: "Write", tool_input: { file_path: "output/linkedin.md", content: "..." } }
        |
        v
Script extracts file_path, computes a brand-voice score from the file content,
appends one JSON line to output/audit.jsonl:
   { timestamp: "2026-05-17T09:42:11Z",
     tool: "Write",
     path: "output/linkedin.md",
     brand_voice_score: 0.85 }
```

Claude never sees the hook run. The hook never blocks the write. They are completely independent.

**Phase 5 — same as Phase 4, twice more.** The one-pager and the email. Each write triggers the hook. Three lines now in `output/audit.jsonl`.

**Phase 6 — Claude chains into the audit skill.** Per the runbook, Claude invokes `marketing-brand-audit` and passes it the three output paths. That skill calls `score_brand_voice` for each file's contents and reports back which (if any) are below the 0.7 threshold.

**Phase 7 — Claude composes the final response.** Three artifacts, three audit-log entries, the audit-skill summary. Mia sees a clean handoff.

## Why this is the interview centerpiece

The composition of all five primitives in one workflow is what makes this plugin worth showing on the screenshare. The talk-track:

> *"The slash command is the user-facing entry point. The skill is the workflow brain. The Model Context Protocol server gives me the capabilities I need to read assets, look up the style guide, and score brand voice — composable across other plugins or other AI clients. The Write tool is built into Claude Code. And the PostToolUse hook is what makes the audit log a runtime guarantee instead of a workflow suggestion. Five primitives, one composed workflow, deterministic governance."*

## Where to make common changes

| You want to... | Edit this file |
| --- | --- |
| Add a new trigger phrase so a different phrasing routes here | `description:` field in `SKILL.md` |
| Change the channel mix (e.g., add a tweet thread) | `## Steps` section of `SKILL.md` |
| Change the brand voice the artifacts target | `../../../fixtures/style_guide.md` |
| Change what the audit hook records | `../../../hooks/audit.sh` |
| Swap the brand-voice scoring for a real LLM call | `score_brand_voice` in `../../../src/gtm_marketing/brand.py` |
