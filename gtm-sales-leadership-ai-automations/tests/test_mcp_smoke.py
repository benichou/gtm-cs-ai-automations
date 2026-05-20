"""Smoke test: the FastMCP server boots and registers all 4 expected tools."""

from __future__ import annotations

import asyncio

from gtm_sales_leadership.mcp import EXPECTED_TOOLS, mcp


def test_all_expected_tools_registered() -> None:
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS, (
        f"missing={EXPECTED_TOOLS - names} extra={names - EXPECTED_TOOLS}"
    )
