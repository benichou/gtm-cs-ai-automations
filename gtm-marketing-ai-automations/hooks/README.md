# hooks/ — the PostToolUse audit hook

This directory contains the audit hook for the gtm-marketing-ai-automations plugin. The hook is what makes the audit log a **runtime guarantee** rather than a thing the workflow has to remember to do.

## What's a hook, plain English

A **hook** is a shell command Claude Code runs *automatically* before or after Claude uses a tool. The user doesn't trigger it. Claude doesn't ask for it. The runtime fires it on its own based on configuration.

For this plugin we wire one hook:
- **Event**: `PostToolUse` (fires after the tool succeeds)
- **Matcher**: `Write` (only fires when Claude uses the built-in Write tool, not for other tools)
- **Command**: `hooks/audit.sh` (the script in this directory)

Configured in `.claude/settings.json` at the plugin root:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/hooks/audit.sh" }
        ]
      }
    ]
  }
}
```

`${CLAUDE_PROJECT_DIR}` is Claude Code's environment variable for the working directory of the session.

## What `audit.sh` does

When the hook fires, Claude Code:
1. Pipes an event JSON to the script's standard input. The JSON looks like:
   ```json
   {
     "tool_name": "Write",
     "tool_input": {
       "file_path": "/abs/path/to/output/linkedin.md",
       "content": "<full content of the file that was written>"
     },
     "tool_result": "<success message>"
   }
   ```
2. Runs the script. The script can return non-zero to signal an error, but for audit logging we always exit 0 — an audit logger must not be in the critical path of the user's workflow.

`audit.sh` reads the JSON, extracts `file_path` and `content`, computes a crude brand-voice score inline (using the same banned/preferred word lists as the MCP tool), and appends one structured JSON line to `output/audit.jsonl`:

```json
{
  "ts": "2026-05-17T09:42:11.503Z",
  "tool": "Write",
  "path": "/abs/path/to/output/linkedin.md",
  "char_count": 412,
  "brand_voice_score": 0.85,
  "banned_hits": [],
  "preferred_hits": ["crew", "schedule", "field"]
}
```

Marketing leadership can `cat output/audit.jsonl | jq .` to review every AI-generated artifact for the day.

## Why a hook instead of a skill step

The whole point. The `marketing-repurpose` skill *could* include "step 7: append to the audit log" in its runbook. But:

1. Claude sometimes forgets steps when the runbook is long.
2. The audit log must be written even if a user invokes the workflow through a path the SKILL.md author didn't anticipate.
3. The audit log is a governance contract, not a workflow detail. It should be enforced by the runtime, not by the language model.

By moving the audit to a `PostToolUse` hook on the `Write` tool, the audit log is guaranteed regardless of how the file got written. Claude doesn't even know the hook is running.

## How to test the hook in isolation

Echo a fake event JSON to the script and check the audit log:

```bash
cd gtm-marketing-ai-automations
echo '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "output/test.md",
    "content": "Testing the audit hook with crew, schedule, and field words."
  }
}' | bash hooks/audit.sh

cat output/audit.jsonl
```

You should see one new JSON line with `path`, `brand_voice_score`, and the hit lists.

## What does NOT belong in a hook

Hooks should be:
- Fast (run on every tool call — slow hooks degrade Claude Code's responsiveness)
- Idempotent (safe to run twice if Claude Code retries)
- Side-effect-tolerant (the hook can't undo what just happened)
- Non-network-blocking (a hook timing out blocks every subsequent tool use)

This audit hook is local-file-write only — no network calls, no external services, no expensive computation. That's the right shape.

If you want to do something heavy with the audit data (post to a webhook, write to a database, etc.), the right pattern is to let the hook do the *minimum* — append to a local file — and have a separate process tail that file and ship records downstream asynchronously.
