"""Generate a synthetic opportunities fixture.

Outputs `fixtures/opps.json` with 300 deterministic rows shaped like a
real customer-relationship-management database export. The data deliberately
includes a small number of data-quality issues (missing close dates,
negative amounts, orphan account references) so the `check_data_quality`
tool has realistic things to find.

Run: `uv run --package gtm-revops-ai-automations gtm-revops-seed`
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260517
NUM_OPPS = 300
AS_OF = date(2026, 5, 17)

STAGES_WEIGHTED = [
    ("Discovery", 0.18),
    ("Qualification", 0.22),
    ("Proposal", 0.18),
    ("Negotiation", 0.12),
    ("Closed Won", 0.15),
    ("Closed Lost", 0.15),
]
OWNERS = [
    "Sarah Chen",
    "Marcus Rivera",
    "Priya Patel",
    "Jamal Washington",
    "Hannah Lindqvist",
    "Diego Moreno",
]
SOURCES = ["inbound_marketing", "outbound_sales", "partner_referral", "customer_referral", "event"]

ACCOUNT_NAMES = [
    "Foundry Contractors",
    "Cascade Construction Group",
    "Granite Peak Builders",
    "Northstar Civil Engineering",
    "Apex Construction Managers",
    "Heartland Build Partners",
    "Pacific Trident Industries",
    "Ridgeway Specialty Trades",
    "Skyline Federal Builders",
    "Bedrock Foundations LLC",
    "Westbound Infrastructure",
    "Cornerstone Design-Build",
    "Anchor Construction Holdings",
    "Summit Mechanical",
    "Ironwood Civil",
    "Bluepeak Builders",
    "Trident Underground",
    "Keystone Federal",
    "Redwood Roofing",
    "Pacific Glass & Glazing",
]


def main() -> None:
    rng = random.Random(SEED)
    plugin_root = Path(__file__).resolve().parent.parent.parent
    fixtures_dir = plugin_root / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    rows: list[dict] = []
    for i in range(1, NUM_OPPS + 1):
        rows.append(_generate_opp(rng, i))

    # Inject deliberate data-quality issues so `check_data_quality` has work.
    _inject_quality_issues(rng, rows)

    out_path = fixtures_dir / "opps.json"
    out_path.write_text(json.dumps(rows, indent=2))
    print(f"wrote {len(rows)} rows -> {out_path}")


def _generate_opp(rng: random.Random, idx: int) -> dict:
    stage = _weighted_choice(rng, STAGES_WEIGHTED)
    account_name = rng.choice(ACCOUNT_NAMES)
    account_id = f"A{ACCOUNT_NAMES.index(account_name) + 1:03d}"
    amount = rng.choices(
        [
            rng.randint(5_000, 25_000),
            rng.randint(25_000, 100_000),
            rng.randint(100_000, 300_000),
            rng.randint(300_000, 750_000),
        ],
        weights=[0.4, 0.35, 0.2, 0.05],
    )[0]
    # Close date: open stages skew future, closed stages skew past
    if stage in {"Closed Won", "Closed Lost"}:
        close_date = AS_OF - timedelta(days=rng.randint(0, 120))
    else:
        close_date = AS_OF + timedelta(days=rng.randint(7, 180))
    # Last activity skew: 70% recent (<30 days), 30% stale
    if rng.random() < 0.7:
        last_activity = AS_OF - timedelta(days=rng.randint(0, 29))
    else:
        last_activity = AS_OF - timedelta(days=rng.randint(30, 180))
    return {
        "opp_id": f"O{idx:04d}",
        "account_id": account_id,
        "account_name": account_name,
        "stage": stage,
        "amount": amount,
        "close_date": close_date.isoformat(),
        "owner": rng.choice(OWNERS),
        "last_activity_at": last_activity.isoformat(),
        "source": rng.choice(SOURCES),
    }


def _inject_quality_issues(rng: random.Random, rows: list[dict]) -> None:
    """Mutate a handful of rows to surface realistic data-quality issues."""
    # 5 rows: missing close_date
    for idx in rng.sample(range(len(rows)), 5):
        rows[idx]["close_date"] = None
    # 3 rows: negative amount (data entry typo)
    for idx in rng.sample(range(len(rows)), 3):
        rows[idx]["amount"] = -rows[idx]["amount"]
    # 4 rows: orphan account_id (account was deleted but opp still references it)
    for idx in rng.sample(range(len(rows)), 4):
        rows[idx]["account_id"] = "A999"
        rows[idx]["account_name"] = "[DELETED]"


def _weighted_choice(rng: random.Random, choices: list[tuple[str, float]]) -> str:
    names = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return rng.choices(names, weights=weights)[0]


if __name__ == "__main__":
    main()
