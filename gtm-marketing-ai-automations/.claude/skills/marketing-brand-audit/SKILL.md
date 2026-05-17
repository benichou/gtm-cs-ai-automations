---
name: marketing-brand-audit
description: Score generated marketing artifacts against the Bridgit brand voice and flag anything below threshold for revision. Trigger when the user asks to "audit / score / check / review brand voice" of one or more files, or when the marketing-repurpose skill chains into this skill at the end of its workflow. Reads each file's content, calls score_brand_voice via the gtm-marketing Model Context Protocol server, and produces a summary table with one row per artifact.
---

# marketing-brand-audit skill

This skill is the post-write quality check for the marketing-repurpose workflow. It can also be invoked standalone if the user already has artifacts on disk they want re-scored.

## When to use

Invoke this skill when:

- The `marketing-repurpose` skill chains into this skill at the end of its runbook (the most common path).
- The user asks to "audit / score / check / review the brand voice" of one or more files.
- The user has artifacts at known paths and wants a re-scoring without regenerating.

Do NOT invoke for:

- The initial generation of artifacts (use `marketing-repurpose`).
- Scoring text that isn't yet on disk — call the `score_brand_voice` MCP tool directly instead.

## Prerequisites

1. The `gtm-marketing` Model Context Protocol server is registered (see `/mcp`).
2. The files to audit exist and are readable.

## Steps

1. **Identify the paths to audit.** Either:
   - The calling `marketing-repurpose` skill passed three paths explicitly.
   - The user listed paths in their request.
   - Default to all markdown files in `output/` if neither.

2. **For each path:**
   - Read the file via the Read tool (so the brand-voice score reflects what was actually written).
   - Call `score_brand_voice` on the file's contents via the MCP server.
   - Capture the score, banned-phrase hits, and preferred-phrase hits.

3. **Produce a summary table** in this shape:

   ```
   ### Brand-voice audit results

   | Artifact | Score | Status | Banned phrases | Preferred phrases |
   |---|---|---|---|---|
   | output/linkedin.md | 0.85 | ✓ Pass | — | crew, schedule, field |
   | output/onepager.md | 0.65 | ⚠ Below threshold | leverage | crew, schedule |
   | output/email.md | 0.90 | ✓ Pass | — | crew, schedule, headcount |

   Threshold: 0.70. <N> artifact(s) below threshold need revision.
   ```

4. **For any artifact below 0.7, list the specific revision needed.** Example:

   > `output/onepager.md` (0.65): remove "leverage" — see the banned-phrases section of the style guide. Suggested alternatives: "use", "rely on", "tap".

## Failure handling

- **No paths provided and `output/` is empty**: tell the user nothing to audit, suggest running `/repurpose <path>` first.
- **A file can't be read**: skip it and surface the error in the summary.
- **The MCP server's `score_brand_voice` tool fails**: surface the error; do not invent a score.
