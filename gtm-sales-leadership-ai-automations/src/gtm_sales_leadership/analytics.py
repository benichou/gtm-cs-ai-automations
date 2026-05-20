"""Pure aggregation functions for sales-leadership pipeline questions.

Each function takes a list of normalized opportunity dicts (the output of
`data.load_opps`) and returns a JSON-serializable summary. No I/O, no
side effects — easy to unit-test against a fixed list.

The four functions map 1:1 to the four Model Context Protocol tools in
`mcp.py`, which are themselves thin wrappers.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from gtm_sales_leadership.data import AS_OF, LATE_STAGES

FORECAST_CATEGORIES = ["Commit", "Best Case", "Pipeline", "Omitted"]


def roll_up_forecast(
    opps: list[dict],
    period_end: date | None = None,
    owner: str | None = None,
) -> dict:
    """Aggregate open pipeline by forecast_category.

    Optionally filter to deals with close_date ≤ period_end and/or a single owner.
    Returns raw ARR, prob-weighted ARR, and deal count per category, plus totals.
    """
    filtered = _apply_filters(opps, period_end=period_end, owner=owner)
    by_cat: dict[str, dict] = {
        c: {"count": 0, "arr": 0, "weighted_arr": 0.0} for c in FORECAST_CATEGORIES
    }
    for o in filtered:
        cat = o["forecast_category"] if o["forecast_category"] in by_cat else "Pipeline"
        by_cat[cat]["count"] += 1
        by_cat[cat]["arr"] += o["arr"]
        by_cat[cat]["weighted_arr"] += o["weighted_arr"]

    breakdown = [{"forecast_category": c, **by_cat[c]} for c in FORECAST_CATEGORIES]
    return {
        "as_of": AS_OF.isoformat(),
        "filters": {
            "period_end": period_end.isoformat() if period_end else None,
            "owner": owner,
        },
        "total_deals": len(filtered),
        "total_arr": sum(o["arr"] for o in filtered),
        "total_weighted_arr": round(sum(o["weighted_arr"] for o in filtered), 2),
        "commit_arr": by_cat["Commit"]["arr"],
        "commit_plus_best_case_arr": by_cat["Commit"]["arr"] + by_cat["Best Case"]["arr"],
        "breakdown": breakdown,
    }


def list_deals_closing_by(opps: list[dict], period_end: date) -> dict:
    """Return open deals with close_date ≤ period_end, sorted by close_date ascending."""
    matched = [
        o for o in opps if o["close_date"] and date.fromisoformat(o["close_date"]) <= period_end
    ]
    matched.sort(key=lambda o: o["close_date"])
    return {
        "as_of": AS_OF.isoformat(),
        "period_end": period_end.isoformat(),
        "deal_count": len(matched),
        "total_arr": sum(o["arr"] for o in matched),
        "total_weighted_arr": round(sum(o["weighted_arr"] for o in matched), 2),
        "deals": [_deal_summary(o) for o in matched],
    }


def rank_deals_by_risk(opps: list[dict], top_n: int = 10) -> dict:
    """Return the top-N deals most in need of inspection, with score breakdown.

    Risk score is a transparent sum of five factors (max 10):
        +3  stale (no activity > 14 days)
        +3  overdue (close_date < AS_OF)
        +2  blank next_step on a late-stage deal
        +1  single-threaded (num_contacts = 1) on a late-stage deal
        +1  in forecast (Commit or Best Case — a slip hurts the number directly)

    Deals are returned sorted by risk_score desc, then ARR desc. Zero-score
    deals are excluded.
    """
    scored = []
    for o in opps:
        score, factors = _score_deal(o)
        if score > 0:
            scored.append({**_deal_summary(o), "risk_score": score, "risk_factors": factors})
    scored.sort(key=lambda d: (d["risk_score"], d["arr"]), reverse=True)
    top = scored[:top_n]
    return {
        "as_of": AS_OF.isoformat(),
        "scored_deals_total": len(scored),
        "top_n_arr": sum(d["arr"] for d in top),
        "top_n_weighted_arr": round(sum(d["weighted_arr"] for d in top), 2),
        "deals": top,
    }


def roll_up_by_owner(opps: list[dict]) -> dict:
    """Per-AE scorecard: deal count, raw + weighted ARR, late-stage and risk counts."""
    by_owner: dict[str, dict] = defaultdict(
        lambda: {
            "deals": 0,
            "raw_arr": 0,
            "weighted_arr": 0.0,
            "commit_arr": 0,
            "best_case_arr": 0,
            "late_stage_deals": 0,
            "stale_deals": 0,
            "overdue_deals": 0,
            "zero_activity_deals": 0,
        }
    )
    for o in opps:
        b = by_owner[o["owner_name"]]
        b["deals"] += 1
        b["raw_arr"] += o["arr"]
        b["weighted_arr"] += o["weighted_arr"]
        if o["forecast_category"] == "Commit":
            b["commit_arr"] += o["arr"]
        if o["forecast_category"] == "Best Case":
            b["best_case_arr"] += o["arr"]
        if o["stage"] in LATE_STAGES:
            b["late_stage_deals"] += 1
        if o["is_stale"]:
            b["stale_deals"] += 1
        if o["is_overdue"]:
            b["overdue_deals"] += 1
        if o["is_zero_activity"]:
            b["zero_activity_deals"] += 1

    rows = [
        {"owner_name": name, **{**b, "weighted_arr": round(b["weighted_arr"], 2)}}
        for name, b in by_owner.items()
    ]
    rows.sort(key=lambda r: r["weighted_arr"], reverse=True)
    return {"as_of": AS_OF.isoformat(), "owners": rows}


# ── helpers ─────────────────────────────────────────────────────────────────


def _apply_filters(opps: list[dict], period_end: date | None, owner: str | None) -> list[dict]:
    out = opps
    if period_end is not None:
        out = [
            o for o in out if o["close_date"] and date.fromisoformat(o["close_date"]) <= period_end
        ]
    if owner:
        out = [o for o in out if o["owner_name"] == owner]
    return out


def _score_deal(o: dict) -> tuple[int, list[str]]:
    score = 0
    factors: list[str] = []
    if o["is_stale"]:
        score += 3
        factors.append(f"stale ({o['days_since_activity']}d no activity)")
    if o["is_overdue"]:
        score += 3
        factors.append(f"overdue (close was {o['close_date']})")
    if o["stage"] in LATE_STAGES and not o["next_step"]:
        score += 2
        factors.append("blank next_step on late-stage deal")
    if o["stage"] in LATE_STAGES and o["num_contacts"] == 1:
        score += 1
        factors.append("single-threaded (1 contact)")
    if o["forecast_category"] in ("Commit", "Best Case"):
        score += 1
        factors.append(f"in forecast ({o['forecast_category']})")
    return score, factors


def _deal_summary(o: dict) -> dict:
    return {
        "opportunity_id": o["opportunity_id"],
        "opportunity_name": o["opportunity_name"],
        "account_name": o["account_name"],
        "stage": o["stage"],
        "arr": o["arr"],
        "weighted_arr": round(o["weighted_arr"], 2),
        "close_date": o["close_date"],
        "days_since_activity": o["days_since_activity"],
        "owner_name": o["owner_name"],
        "probability": o["probability"],
        "forecast_category": o["forecast_category"],
        "next_step": o["next_step"],
        "num_contacts": o["num_contacts"],
    }
