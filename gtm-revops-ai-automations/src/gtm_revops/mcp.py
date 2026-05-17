"""Model Context Protocol server for Revenue Operations pipeline tooling.

Exposes 4 tools that read from a fixture (today) or any real data source
(in production — see `data.load_opps` for the swap point).

Run:
    gtm-revops-mcp --stdio              # default: stdio transport (subprocess)
    gtm-revops-mcp --http --port 8765   # streamable-http transport on localhost
    gtm-revops-mcp --self-check         # boot + introspect tools + exit 0 for CI

Inspect interactively (after `uv sync`):
    uv run mcp dev src/gtm_revops/mcp.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import defaultdict
from datetime import date, timedelta
from typing import Literal

from mcp.server.fastmcp import FastMCP

from gtm_revops.data import AS_OF, OPEN_STAGES, load_opps

mcp = FastMCP("gtm-revops")


@mcp.tool()
def list_open_opps(stage: str | None = None) -> list[dict]:
    """List open opportunities (Discovery, Qualification, Proposal, Negotiation).

    Args:
        stage: Optional stage filter. Must be one of the open stages. If omitted,
               all open opportunities are returned.

    Returns:
        A list of opportunity dicts with fields: opp_id, account_id, account_name,
        stage, amount, close_date, owner, last_activity_at, source.
    """
    opps = [o for o in load_opps() if o["stage"] in OPEN_STAGES]
    if stage:
        opps = [o for o in opps if o["stage"] == stage]
    return opps


@mcp.tool()
def check_data_quality() -> dict:
    """Scan the pipeline for data hygiene issues.

    Returns a dict with three issue categories:
      - missing_close_date: opps with no close_date set
      - negative_amount: opps with amount < 0 (typically data-entry errors)
      - orphan_account: opps referencing an account_id flagged [DELETED]

    Each category contains a list of {opp_id, account_id, account_name,
    stage, amount, close_date, issue} so the caller can route fixes.
    """
    issues: dict[str, list[dict]] = {
        "missing_close_date": [],
        "negative_amount": [],
        "orphan_account": [],
    }
    for opp in load_opps():
        if opp.get("close_date") is None:
            issues["missing_close_date"].append({**_summary(opp), "issue": "close_date is null"})
        if (opp.get("amount") or 0) < 0:
            issues["negative_amount"].append({**_summary(opp), "issue": f"amount={opp['amount']}"})
        if opp.get("account_name") == "[DELETED]":
            issues["orphan_account"].append({**_summary(opp), "issue": "account record deleted"})

    return {
        "as_of": AS_OF.isoformat(),
        "total_issues": sum(len(v) for v in issues.values()),
        "by_category": {k: len(v) for k, v in issues.items()},
        "issues": issues,
    }


@mcp.tool()
def roll_up_pipeline(group_by: Literal["stage", "owner"] = "stage") -> dict:
    """Aggregate open pipeline value and deal count, grouped by stage or owner.

    Args:
        group_by: 'stage' (default) or 'owner'.

    Returns:
        {
          'as_of': '2026-05-17',
          'group_by': 'stage',
          'total_open_amount': 12_345_678,
          'total_open_count': 87,
          'breakdown': [
             {'group': 'Discovery', 'count': 32, 'amount': 3_200_000},
             ...
          ]
        }
    """
    if group_by not in {"stage", "owner"}:
        raise ValueError(f"group_by must be 'stage' or 'owner', got {group_by!r}")

    open_opps = [o for o in load_opps() if o["stage"] in OPEN_STAGES]
    by_group: dict[str, dict] = defaultdict(lambda: {"count": 0, "amount": 0})
    for opp in open_opps:
        key = opp[group_by]
        by_group[key]["count"] += 1
        # Skip negative amounts in roll-up (they're data-quality issues, not pipeline)
        amount = opp.get("amount") or 0
        if amount > 0:
            by_group[key]["amount"] += amount

    breakdown = sorted(
        ({"group": k, **v} for k, v in by_group.items()),
        key=lambda r: r["amount"],
        reverse=True,
    )
    return {
        "as_of": AS_OF.isoformat(),
        "group_by": group_by,
        "total_open_amount": sum(b["amount"] for b in breakdown),
        "total_open_count": sum(b["count"] for b in breakdown),
        "breakdown": breakdown,
    }


@mcp.tool()
def flag_stale_opps(days: int = 30) -> list[dict]:
    """Return open opportunities with no activity in the last N days.

    Args:
        days: Activity threshold in days. Default 30.

    Returns:
        A list of stale opportunities sorted by oldest activity first.
        Each entry includes a `days_since_activity` field for prioritization.
    """
    if days < 0:
        raise ValueError(f"days must be >= 0, got {days}")

    cutoff = AS_OF - timedelta(days=days)
    stale: list[dict] = []
    for opp in load_opps():
        if opp["stage"] not in OPEN_STAGES:
            continue
        last_activity = _parse_date(opp.get("last_activity_at"))
        if last_activity is None:
            continue
        if last_activity < cutoff:
            stale.append(
                {
                    **_summary(opp),
                    "owner": opp["owner"],
                    "last_activity_at": opp["last_activity_at"],
                    "days_since_activity": (AS_OF - last_activity).days,
                }
            )

    stale.sort(key=lambda o: o["days_since_activity"], reverse=True)
    return stale


def _summary(opp: dict) -> dict:
    return {
        "opp_id": opp["opp_id"],
        "account_id": opp.get("account_id"),
        "account_name": opp.get("account_name"),
        "stage": opp["stage"],
        "amount": opp.get("amount"),
        "close_date": opp.get("close_date"),
    }


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


EXPECTED_TOOLS = {
    "list_open_opps",
    "check_data_quality",
    "roll_up_pipeline",
    "flag_stale_opps",
}


def main() -> int:
    parser = argparse.ArgumentParser(prog="gtm-revops-mcp", description=__doc__)
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument(
        "--stdio",
        action="store_true",
        help="Run with stdio transport (default; for local subprocess use)",
    )
    transport.add_argument(
        "--http",
        action="store_true",
        help="Run with streamable-http transport on the given host/port",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host for --http mode (default 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Port for --http mode (default 8765)"
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

    # Default: stdio
    mcp.run()
    return 0


def _self_check() -> int:
    """Verify all expected tools registered correctly. Returns 0 on success, 1 on failure."""
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
