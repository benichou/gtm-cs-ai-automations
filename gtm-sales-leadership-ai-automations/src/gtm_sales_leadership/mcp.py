"""Model Context Protocol server for sales-leadership pipeline questions.

Exposes 4 tools answering the specific aggregation questions a VP Sales asks
every Monday morning. Each tool is a thin wrapper around the pure functions in
`analytics.py`; tool docstrings are what Claude reads as the tool description.

Run:
    gtm-sales-leadership-mcp --stdio              # default (subprocess transport)
    gtm-sales-leadership-mcp --http --port 8766   # streamable-http transport
    gtm-sales-leadership-mcp --self-check         # boot + introspect + exit 0 for CI
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date

from mcp.server.fastmcp import FastMCP

from gtm_sales_leadership import analytics
from gtm_sales_leadership.data import load_opps

mcp = FastMCP("gtm-sales-leadership")


@mcp.tool()
def roll_up_forecast(period_end: str | None = None, owner: str | None = None) -> dict:
    """Aggregate open pipeline ARR by forecast_category (Commit / Best Case / Pipeline / Omitted).

    Use this to answer "what's my forecast?" or "where will we land this period?".
    Returns raw ARR, probability-weighted ARR, and deal count per category, plus
    Commit and Commit+Best Case totals at the top level.

    Args:
        period_end: Optional ISO date (YYYY-MM-DD). Restrict to deals with
                    close_date ≤ this date — e.g. end of current month.
        owner: Optional AE name (e.g. "J. Torres") to scope to one rep.
    """
    period = _parse_date(period_end, "period_end")
    return analytics.roll_up_forecast(load_opps(), period_end=period, owner=owner)


@mcp.tool()
def list_deals_closing_by(period_end: str) -> dict:
    """Return open deals with close_date ≤ period_end, sorted by close_date ascending.

    Use this to answer "what's closing this month?" or "what do I need to inspect
    this week?". Each deal includes stage, ARR, days_since_activity, next_step,
    forecast_category, and owner.

    Args:
        period_end: ISO date (YYYY-MM-DD) — only deals closing on or before this
                    date are returned. Required.
    """
    period = _parse_date(period_end, "period_end")
    if period is None:
        raise ValueError("period_end is required (ISO YYYY-MM-DD).")
    return analytics.list_deals_closing_by(load_opps(), period_end=period)


@mcp.tool()
def rank_deals_by_risk(top_n: int = 10) -> dict:
    """Return the top-N open deals most at risk of slipping, with scored reasons.

    Use this to answer "which deals should I personally inspect?" or "where could
    the forecast slip?". Each deal in the response carries a transparent
    `risk_score` (0–10) and a `risk_factors` list explaining the score (stale,
    overdue, blank next_step on late-stage, single-threaded, in-forecast).

    Args:
        top_n: How many deals to return (default 10). Pass a smaller number for
               an exec-level shortlist.
    """
    if top_n < 1:
        raise ValueError(f"top_n must be >= 1, got {top_n}")
    return analytics.rank_deals_by_risk(load_opps(), top_n=top_n)


@mcp.tool()
def roll_up_by_owner() -> dict:
    """Per-AE scorecard: deal count, raw + weighted ARR, late-stage and risk counts.

    Use this to answer "how are my reps doing?" or "who needs coaching?". Each
    row includes Commit ARR, Best Case ARR, late-stage deal count, and three
    risk counters (stale, overdue, zero-activity). Sorted by weighted ARR
    descending so the highest-contribution rep is first.
    """
    return analytics.roll_up_by_owner(load_opps())


# ── server boilerplate ──────────────────────────────────────────────────────


def _parse_date(value: str | None, field: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise ValueError(f"{field} must be ISO YYYY-MM-DD, got {value!r}") from e


EXPECTED_TOOLS = {
    "roll_up_forecast",
    "list_deals_closing_by",
    "rank_deals_by_risk",
    "roll_up_by_owner",
}


def main() -> int:
    parser = argparse.ArgumentParser(prog="gtm-sales-leadership-mcp", description=__doc__)
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument(
        "--stdio", action="store_true", help="Run with stdio transport (default)"
    )
    transport.add_argument("--http", action="store_true", help="Run with streamable-http transport")
    parser.add_argument("--host", default="127.0.0.1", help="Host for --http mode")
    parser.add_argument("--port", type=int, default=8766, help="Port for --http mode")
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
    except Exception as e:  # pragma: no cover - defensive
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
