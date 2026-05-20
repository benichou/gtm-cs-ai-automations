"""Pipeline export loader for the sales-leadership Model Context Protocol tools.

All four tools in `mcp.py` read through `load_opps()`. Swapping the CSV
fixture for a real CRM source (Salesforce, HubSpot, an internal API) is a
one-function change here — tool signatures stay identical.
"""

from __future__ import annotations

import csv
from datetime import date
from functools import lru_cache
from pathlib import Path

DEFAULT_FIXTURE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "pipeline_export.csv"

# Export "as of" date. Stale, overdue, and days-since-activity calculations are
# anchored on this date — not today's wall clock — so reruns on the same export
# are reproducible.
AS_OF = date(2026, 4, 28)

LATE_STAGES = {"Proposal", "Negotiation"}
STALE_THRESHOLD_DAYS = 14


def load_opps(fixture_path: Path | None = None) -> list[dict]:
    """Return normalized open opportunities with derived risk flags.

    Each row gets four derived fields the analytics layer uses directly:
        weighted_arr (float):    arr * probability / 100
        is_overdue (bool):       close_date < AS_OF
        is_stale (bool):         days_since_activity > STALE_THRESHOLD_DAYS
        is_zero_activity (bool): last_activity_date is null
    """
    path = fixture_path or DEFAULT_FIXTURE
    if not path.exists():
        raise FileNotFoundError(f"Pipeline fixture not found at {path}")
    return _cached_load(str(path))


@lru_cache(maxsize=4)
def _cached_load(path_str: str) -> list[dict]:
    with Path(path_str).open(newline="", encoding="utf-8") as fh:
        return [_normalize(row) for row in csv.DictReader(fh)]


def _normalize(row: dict[str, str]) -> dict:
    arr = _to_int(row["arr"]) or 0
    probability = _to_int(row["probability"]) or 0
    days_since_activity = _to_int(row["days_since_activity"])

    return {
        "opportunity_id": row["opportunity_id"],
        "opportunity_name": row["opportunity_name"],
        "account_name": row["account_name"],
        "account_segment": row["account_segment"],
        "stage": row["stage"],
        "arr": arr,
        "close_date": row["close_date"] or None,
        "last_activity_date": row["last_activity_date"] or None,
        "days_since_activity": days_since_activity,
        "owner_name": row["owner_name"],
        "probability": probability,
        "forecast_category": row["forecast_category"],
        "next_step": (row["next_step"].strip() or None) if row["next_step"] else None,
        "num_contacts": _to_int(row["num_contacts"]) or 0,
        "created_date": row["created_date"] or None,
        # Derived flags
        "weighted_arr": arr * probability / 100,
        "is_overdue": _to_date(row["close_date"]) is not None
        and _to_date(row["close_date"]) < AS_OF,
        "is_stale": days_since_activity is not None and days_since_activity > STALE_THRESHOLD_DAYS,
        "is_zero_activity": not row["last_activity_date"],
    }


def _to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def _to_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def reset_cache() -> None:
    """Clear the cached fixture (used by tests after swapping data)."""
    _cached_load.cache_clear()
