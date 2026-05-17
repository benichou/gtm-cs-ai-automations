#!/usr/bin/env bash
# PostToolUse audit hook for gtm-marketing-ai-automations.
#
# Fires after Claude Code uses the Write tool. Reads a JSON event from stdin
# describing what was just written, and appends one structured JSON line to
# output/audit.jsonl. Exits 0 unconditionally so it never blocks the write
# even if logging fails — an audit-log writer must not be in the critical path.
#
# Wired up via .claude/settings.json -> hooks.PostToolUse[*].matcher = "Write".
set -euo pipefail

HOOK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLUGIN_ROOT="$( cd "$HOOK_DIR/.." && pwd )"
OUTPUT_DIR="$PLUGIN_ROOT/output"
AUDIT_FILE="$OUTPUT_DIR/audit.jsonl"

mkdir -p "$OUTPUT_DIR"

# Capture the full event JSON from Claude Code's pipe first, then pass it to
# python via an env var. We can't use a python heredoc that reads stdin
# directly because the heredoc itself replaces stdin with its body.
EVENT_JSON="$(cat || true)"

EVENT_JSON="$EVENT_JSON" AUDIT_FILE="$AUDIT_FILE" python3 <<'PY' || true
import json
import os
import sys
from datetime import datetime, timezone

audit_path = os.environ["AUDIT_FILE"]
raw = os.environ.get("EVENT_JSON", "")
if not raw.strip():
    sys.exit(0)

try:
    event = json.loads(raw)
except json.JSONDecodeError:
    with open(audit_path, "a") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "error": "malformed event",
            "raw_head": raw[:200],
        }) + "\n")
    sys.exit(0)

tool_input = event.get("tool_input") or {}
file_path = tool_input.get("file_path") or tool_input.get("path")
content = tool_input.get("content") or ""

# Crude brand-voice score inline so the audit log is self-contained — no MCP
# round-trip from a hook script (that would be a layering violation). The
# skill-level audit re-scores with the real tool later.
BANNED = {
    "leverage", "synergize", "synergy", "synergies",
    "thought leadership", "best-in-class", "industry-leading",
    "world-class", "deep dive", "ecosystem", "value proposition",
}
PREFERRED = {
    "crew", "schedule", "subcontractor", "subs", "project",
    "field", "headcount", "workforce", "general contractor",
}
lower = (content or "").lower()
# Pad with spaces so the simple " w " word-boundary check works at edges.
padded = f" {lower} "
banned_hits = sorted({w for w in BANNED if f" {w} " in padded or f" {w}." in padded or f" {w}," in padded})
preferred_hits = sorted({w for w in PREFERRED if f" {w} " in padded or f" {w}." in padded or f" {w}," in padded})
score = max(0.0, min(1.0, 0.8 - 0.1 * len(banned_hits) + 0.05 * len(preferred_hits)))

entry = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "tool": event.get("tool_name"),
    "path": file_path,
    "char_count": len(content) if isinstance(content, str) else None,
    "brand_voice_score": round(score, 2),
    "banned_hits": banned_hits,
    "preferred_hits": preferred_hits,
}

with open(audit_path, "a") as f:
    f.write(json.dumps(entry) + "\n")
PY

exit 0
