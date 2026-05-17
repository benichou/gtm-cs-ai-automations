"""End-to-end smoke test of the MCP server's tool registry.

This exercises the actual FastMCP plumbing (not just the underlying Python
functions in test_tools.py). If a tool fails to register — bad type hints,
duplicate names, decorator misuse — this test catches it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SELF_CHECK_CMD = [
    sys.executable,
    "-m",
    "gtm_revops.mcp",
    "--self-check",
]


def test_self_check_returns_zero_and_lists_all_tools() -> None:
    """The --self-check CLI flag boots the server, introspects tools, and exits 0."""
    result = subprocess.run(
        SELF_CHECK_CMD,
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    assert "SELF-CHECK OK" in result.stdout
    for tool_name in (
        "list_open_opps",
        "check_data_quality",
        "roll_up_pipeline",
        "flag_stale_opps",
    ):
        assert tool_name in result.stdout, f"missing tool {tool_name} in: {result.stdout}"
