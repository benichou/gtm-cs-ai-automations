---
name: marketing-repurpose
description: Repurpose a long-form marketing asset into channel-specific outputs (LinkedIn post, sales one-pager, customer email) with brand-voice grounding. Trigger when the user types the /repurpose slash command or asks to "repurpose / adapt / break down / turn this into" a marketing asset into multiple channel outputs, or asks for "social / LinkedIn / email / one-pager versions" of a blog post or transcript. Reads the source via the gtm-marketing Model Context Protocol server, grounds output in the Bridgit style guide, writes three artifacts to disk, then chains into the marketing-brand-audit skill for a post-write scoring pass.
---

# marketing-repurpose skill

This skill orchestrates the end-to-end content-repurposing workflow for a marketer. It is the orchestrator step — it generates the three artifacts and writes them to disk. The post-write quality check is handled by the sibling `marketing-brand-audit` skill, which this skill chains into at the end.

## When to use

Invoke this skill when the user:

- Types the `/repurpose <path>` slash command.
- Asks to "repurpose / adapt / break down / turn this into" a marketing asset into multiple channel outputs.
- Asks for "social / LinkedIn / email / one-pager versions" of a long-form piece.

Do NOT invoke for:

- Single-channel rewrites (just edit the asset; this skill is multi-channel).
- Editing existing artifacts (use the `marketing-brand-audit` skill alone if the user wants to re-score an existing artifact without regenerating).

## Prerequisites (verify before running)

1. The `gtm-marketing` Model Context Protocol server is registered. Confirm via `/mcp` that it shows healthy with 3 tools. If not, see this plugin's `README.md` for the settings.json snippet to register it.
2. The source asset exists at the path the user provided. If `extract_asset_text` returns a `FileNotFoundError`, surface that to the user and ask for the correct path.
3. The `output/` directory in the plugin root is writable. The audit hook (configured in `.claude/settings.json`) will append to `output/audit.jsonl` after each write — no setup needed beyond making sure the directory exists or can be created.

## Steps

1. **Confirm the input.** Echo back `Repurposing <path> into 3 channel outputs`. If the path doesn't look like a markdown or text file, ask for confirmation.

2. **Extract the asset text.** Call `extract_asset_text(path=<the user's path>)`. The result has `text`, `word_count`, and `char_count`. If the word count is under 200, warn the user the source is short and the repurposed outputs will be thin.

3. **Load the brand voice context.** Call `lookup_style_guide` for the following sections, in this order:
   - `lookup_style_guide("tone")`
   - `lookup_style_guide("structure")`
   - `lookup_style_guide("banned-phrases")`
   - `lookup_style_guide("preferred-phrases")`
   Hold the returned content in working context — every generated artifact must respect these.

4. **Generate the LinkedIn post.** 3-5 short sentences, no emojis, no hashtags, no "👇" tricks. Open with a specific observation from the source, not a claim. End with one question. Write the result to `output/linkedin.md` using the Write tool.

5. **Generate the sales-enablement one-pager.** Three sections: *The problem* / *How we solve it* / *Proof from a customer*. Stay under one printed page (~500 words). One concrete customer outcome with a real number. Write to `output/onepager.md`.

6. **Generate the customer email.** Subject line under 60 characters. Body of 3-5 sentences. One specific reference, one observation, one clear next step. Sign-off "Thanks, <name>" (use a placeholder if no name given). Write to `output/email.md`.

7. **Acknowledge the audit log.** After all three writes, tell the user explicitly: *"All three artifacts written. The audit hook has logged each one to `output/audit.jsonl`."* Do not write to the audit log manually — the hook does it.

8. **Chain into the audit skill.** Tell the user: *"Running brand-voice audit on the three artifacts now."* Then call the `marketing-brand-audit` skill, passing it the three output paths.

9. **Assemble the final response** in this shape:

   ```
   ## Repurpose complete — <as_of>

   Generated 3 channel artifacts from `<source path>` (<word_count> words):
   - `output/linkedin.md` — <one-sentence summary>
   - `output/onepager.md` — <one-sentence summary>
   - `output/email.md` — <one-sentence summary>

   ### Brand-voice audit
   <results from the marketing-brand-audit skill>

   ### Audit log
   3 entries written to `output/audit.jsonl`.

   ### Source preview (first 200 chars)
   <first 200 chars of extracted text>
   ```

## Failure handling

- **`gtm-marketing` server not registered**: surface the settings snippet from this plugin's `README.md` and ask the user to register the server and restart Claude Code. Do NOT fall back to running Bash commands manually.
- **`extract_asset_text` returns `FileNotFoundError`**: tell the user the path wasn't found, suggest checking the working directory.
- **One of the artifact writes fails**: continue with the remaining artifacts but flag the failed one clearly in the final response.
- **The audit hook didn't fire**: do NOT manually append to `audit.jsonl`. Tell the user the hook isn't configured properly and point them to the plugin's `hooks/README.md` for the correct settings snippet.

## Helpful files in this skill directory

- `README.md` — human-readable docs for this skill explaining the runtime flow + the hook composition pattern.
