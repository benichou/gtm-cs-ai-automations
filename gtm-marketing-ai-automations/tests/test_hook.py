"""Test the PostToolUse audit hook script.

We pipe a synthetic event JSON to hooks/audit.sh, then assert the audit
log file has a new line with the expected shape.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "audit.sh"


def test_hook_appends_audit_log_line(tmp_path: Path) -> None:
    """Run the hook against a fake event and verify it appends a valid JSON line.

    We point the hook at a tmp_path-based plugin root by setting up a minimal
    structure with hooks/audit.sh symlinked + an empty output/ dir.
    """
    # Set up a sandbox plugin root with the same layout the hook expects
    sandbox = tmp_path / "plugin"
    sandbox.mkdir()
    (sandbox / "hooks").mkdir()
    (sandbox / "output").mkdir()
    # Copy the hook script so its self-resolved PLUGIN_ROOT lands in sandbox
    hook_copy = sandbox / "hooks" / "audit.sh"
    hook_copy.write_text(HOOK_SCRIPT.read_text())
    hook_copy.chmod(0o755)

    event = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(sandbox / "output" / "linkedin.md"),
            "content": "The crew schedule for our field operations across each project.",
        },
        "tool_result": "ok",
    }

    result = subprocess.run(
        ["bash", str(hook_copy)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"

    audit_log = sandbox / "output" / "audit.jsonl"
    assert audit_log.exists()
    lines = audit_log.read_text().strip().splitlines()
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["tool"] == "Write"
    assert entry["path"].endswith("linkedin.md")
    assert "brand_voice_score" in entry
    assert 0.0 <= entry["brand_voice_score"] <= 1.0
    assert "crew" in entry["preferred_hits"]
    assert "schedule" in entry["preferred_hits"]


def test_hook_handles_malformed_json(tmp_path: Path) -> None:
    """Hook should exit 0 and log a marker line if input is malformed."""
    sandbox = tmp_path / "plugin"
    sandbox.mkdir()
    (sandbox / "hooks").mkdir()
    (sandbox / "output").mkdir()
    hook_copy = sandbox / "hooks" / "audit.sh"
    hook_copy.write_text(HOOK_SCRIPT.read_text())
    hook_copy.chmod(0o755)

    result = subprocess.run(
        ["bash", str(hook_copy)],
        input="this is not json",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0  # never block the write

    audit_log = sandbox / "output" / "audit.jsonl"
    assert audit_log.exists()
    entry = json.loads(audit_log.read_text().strip().splitlines()[0])
    assert "error" in entry


def test_hook_exits_zero_on_empty_stdin(tmp_path: Path) -> None:
    """No input should be a no-op exit-0, not a crash."""
    sandbox = tmp_path / "plugin"
    sandbox.mkdir()
    (sandbox / "hooks").mkdir()
    (sandbox / "output").mkdir()
    hook_copy = sandbox / "hooks" / "audit.sh"
    hook_copy.write_text(HOOK_SCRIPT.read_text())
    hook_copy.chmod(0o755)

    result = subprocess.run(
        ["bash", str(hook_copy)],
        input="",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
