# marketing-brand-audit (skill)

A post-write quality check that re-scores marketing artifacts against the Bridgit brand voice via the `score_brand_voice` Model Context Protocol tool. Produces a summary table with one row per artifact. Called automatically by `marketing-repurpose` at the end of its runbook, or invoked standalone for re-scoring existing files.

This README is for human readers. The file Claude reads at runtime is `SKILL.md` next to it.

## Why two skills in one plugin

Plugin 4 ships two skills (`marketing-repurpose` + `marketing-brand-audit`) because they serve two different jobs:

- **`marketing-repurpose`** — generates the artifacts. Heavyweight orchestrator. Calls many tools, writes files.
- **`marketing-brand-audit`** — scores existing artifacts. Lightweight checker. Only reads and scores.

Splitting them lets the orchestrator chain into the auditor at the end of its workflow, AND lets a user re-run the audit standalone on existing files without re-generating everything. That re-runnability is the whole reason these are separate skills instead of one big one.

## End-to-end flow

```
Trigger: either marketing-repurpose chains in, OR user asks "audit my artifacts"
        |
        v
Skill identifies paths to audit (passed-in, listed by user, or `output/*.md`)
        |
        v
For each path:
   - Read the file content via Read tool
   - Call score_brand_voice(content) via the gtm-marketing MCP server
   - Capture {score, banned_hits, preferred_hits}
        |
        v
Compose a markdown summary table.
For any artifact below threshold (0.7): list the specific revision needed.
```

## Why the audit hook is a separate concern from this skill

The hook (`hooks/audit.sh`) writes `output/audit.jsonl` automatically on every `Write` tool call — that's the governance log marketing leadership requires.

This skill (`marketing-brand-audit`) is the qualitative checker — does the artifact actually meet the brand voice bar?

The two layers are independent on purpose:
- The hook guarantees *a record exists* of every artifact.
- The skill verifies *the quality* of the artifact and flags below-threshold ones for revision.

If the hook fails to fire, that's a governance bug. If this skill flags an artifact below threshold, that's a quality bug. Different teams care about each.
