"""End-to-end smoke test of the gtm-marketing MCP server's tool registry."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SELF_CHECK_CMD = [
    sys.executable,
    "-m",
    "gtm_marketing.mcp",
    "--self-check",
]


def test_self_check_returns_zero_and_lists_all_tools() -> None:
    result = subprocess.run(
        SELF_CHECK_CMD,
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    assert "SELF-CHECK OK" in result.stdout
    for tool_name in (
        "extract_asset_text",
        "score_brand_voice_tool",
        "lookup_style_guide",
    ):
        assert tool_name in result.stdout
