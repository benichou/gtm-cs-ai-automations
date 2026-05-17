"""Fixture loading + data access helpers for the MCP tools.

All four tools in `mcp.py` read through `load_opps()`, so swapping the
fixture for a real data source (Salesforce, Snowflake, an internal API)
is a single-function change here. The tool signatures stay identical.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

DEFAULT_FIXTURE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "opps.json"
AS_OF = date(2026, 5, 17)


def load_opps(fixture_path: Path | None = None) -> list[dict]:
    """Return all opportunities from the fixture.

    The shape mirrors what a real CRM `SELECT *` would return:
    {
        opp_id, account_id, account_name, stage, amount, close_date,
        owner, last_activity_at, source
    }
    """
    path = fixture_path or DEFAULT_FIXTURE
    if not path.exists():
        raise FileNotFoundError(
            f"Opportunities fixture not found at {path}. "
            f"Run `gtm-revops-seed` (or `uv run --package gtm-revops-ai-automations "
            f"python scripts/seed.py`) to generate it."
        )
    return _cached_load(str(path))


@lru_cache(maxsize=4)
def _cached_load(path_str: str) -> list[dict]:
    return json.loads(Path(path_str).read_text())


def reset_cache() -> None:
    """Clear the cached fixture (used by tests after regenerating data)."""
    _cached_load.cache_clear()


OPEN_STAGES = {"Discovery", "Qualification", "Proposal", "Negotiation"}
CLOSED_STAGES = {"Closed Won", "Closed Lost"}
