"""Model Context Protocol server for marketing content-repurposing tooling.

Exposes 3 tools:
  - extract_asset_text(path)        — read + normalize a markdown/text asset
  - score_brand_voice(text)         — heuristic score 0.0-1.0 against Bridgit voice
  - lookup_style_guide(section)     — return a named section of the style guide

Run:
    gtm-marketing-mcp --stdio              # default
    gtm-marketing-mcp --http --port 8766   # streamable-http on localhost
    gtm-marketing-mcp --self-check         # boot + introspect for CI
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from mcp.server.fastmcp import FastMCP

from gtm_marketing.brand import lookup_style_guide_section, score_brand_voice
from gtm_marketing.extract import extract

mcp = FastMCP("gtm-marketing")


@mcp.tool()
def extract_asset_text(path: str) -> dict:
    """Read a long-form marketing asset (markdown or plain text) and return its normalized text.

    Args:
        path: Path to the asset file. Absolute, or relative to the current
              working directory, or relative to the plugin root.

    Returns:
        {path, text, word_count, char_count}
    """
    return extract(path)


@mcp.tool()
def score_brand_voice_tool(text: str) -> dict:
    """Score a piece of text against the Bridgit brand voice (0.0 worst, 1.0 best).

    Args:
        text: The text to evaluate.

    Returns:
        {score, banned_hits, preferred_hits, reasoning} — score in [0,1], with
        reasoning explaining the heuristic verdict.
    """
    return score_brand_voice(text)


# Expose with the friendlier public name expected by callers / runbooks.
score_brand_voice_tool.__name__ = "score_brand_voice"


@mcp.tool()
def lookup_style_guide(section: str) -> dict:
    """Return a named section of the Bridgit style guide.

    Args:
        section: Section heading from the style guide, e.g. "tone",
                 "banned-phrases", "preferred-phrases", "structure".

    Returns:
        {section, found, content, available} — if `found` is false, `available`
        lists the section names present in the guide so the caller can retry.
    """
    return lookup_style_guide_section(section)


EXPECTED_TOOLS = {"extract_asset_text", "score_brand_voice_tool", "lookup_style_guide"}


def main() -> int:
    parser = argparse.ArgumentParser(prog="gtm-marketing-mcp", description=__doc__)
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument(
        "--stdio", action="store_true", help="Run with stdio transport (default)"
    )
    transport.add_argument("--http", action="store_true", help="Run with streamable-http transport")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host for --http mode (default 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8766, help="Port for --http mode (default 8766)"
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Boot, introspect registered tools, exit 0 if all present; for CI",
    )
    args = parser.parse_args()

    if args.self_check:
        return _self_check()

    if args.http:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
        return 0

    mcp.run()
    return 0


def _self_check() -> int:
    try:
        tools = asyncio.run(mcp.list_tools())
    except Exception as e:  # pragma: no cover
        print(f"SELF-CHECK FAIL: could not list tools: {e}", file=sys.stderr)
        return 1
    actual = {t.name for t in tools}
    missing = EXPECTED_TOOLS - actual
    extra = actual - EXPECTED_TOOLS
    if missing or extra:
        print(
            f"SELF-CHECK FAIL: missing={sorted(missing)} extra={sorted(extra)}",
            file=sys.stderr,
        )
        return 1
    print(f"SELF-CHECK OK: {len(actual)} tools registered: {sorted(actual)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
