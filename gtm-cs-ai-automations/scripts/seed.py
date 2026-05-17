"""Generate synthetic fixtures for the gtm-cs-ai-automations plugin.

Outputs four CSVs to ../fixtures/:
- accounts.csv         (50 rows)
- usage_events.csv     (~5000 rows)
- support_tickets.csv  (~200 rows)
- expansion_signals.csv (~80 rows)

The data is shaped to resemble a B2B SaaS customer base where customers are
general contractors using a workforce-planning product. Run from the plugin
root: `uv run python scripts/seed.py`.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260516
NUM_ACCOUNTS = 50
NUM_USAGE_EVENTS = 5000
NUM_TICKETS = 200
NUM_SIGNALS = 80
FEATURES = [
    "schedule_builder",
    "resource_forecast",
    "project_pipeline",
    "person_profile",
    "reports_export",
    "calendar_sync",
    "skills_matrix",
    "mobile_app",
]
PLANS = ["starter", "growth", "enterprise"]
TICKET_PRIORITIES = ["low", "normal", "high", "urgent"]
TICKET_STATUSES = ["open", "pending", "resolved", "closed"]
SIGNAL_TYPES = [
    "asked_about_pricing",
    "invited_new_user",
    "exported_report",
    "viewed_upgrade_page",
    "scheduled_demo",
]
INDUSTRIES = [
    "general_contractor",
    "specialty_contractor",
    "construction_management",
    "design_build",
    "civil_engineering",
]


def main() -> None:
    rng = random.Random(SEED)
    plugin_root = Path(__file__).resolve().parent.parent
    fixtures = plugin_root / "fixtures"
    fixtures.mkdir(exist_ok=True)

    today = date(2026, 5, 16)

    accounts = _generate_accounts(rng, today)
    _write_csv(fixtures / "accounts.csv", accounts)
    print(f"wrote {len(accounts)} rows -> {fixtures / 'accounts.csv'}")

    usage = _generate_usage_events(rng, accounts, today)
    _write_csv(fixtures / "usage_events.csv", usage)
    print(f"wrote {len(usage)} rows -> {fixtures / 'usage_events.csv'}")

    tickets = _generate_tickets(rng, accounts, today)
    _write_csv(fixtures / "support_tickets.csv", tickets)
    print(f"wrote {len(tickets)} rows -> {fixtures / 'support_tickets.csv'}")

    signals = _generate_signals(rng, accounts, today)
    _write_csv(fixtures / "expansion_signals.csv", signals)
    print(f"wrote {len(signals)} rows -> {fixtures / 'expansion_signals.csv'}")


def _generate_accounts(rng: random.Random, today: date) -> list[dict]:
    rows = []
    for i in range(NUM_ACCOUNTS):
        plan = rng.choices(PLANS, weights=[0.4, 0.4, 0.2])[0]
        mrr = {"starter": (500, 2000), "growth": (2000, 8000), "enterprise": (8000, 30000)}[plan]
        started_days_ago = rng.randint(60, 1200)
        rows.append(
            {
                "account_id": f"A{i + 1:03d}",
                "name": _fake_company_name(rng),
                "mrr": rng.randint(*mrr),
                "plan": plan,
                "csm_email": f"csm{rng.randint(1, 6)}@example.com",
                "started_at": (today - timedelta(days=started_days_ago)).isoformat(),
                "industry": rng.choice(INDUSTRIES),
                "project_count": rng.randint(3, 80),
            }
        )
    return rows


def _generate_usage_events(rng: random.Random, accounts: list[dict], today: date) -> list[dict]:
    rows = []
    # Bias: a few accounts will be near-silent (churn risk); most have steady usage.
    silent_accounts = set(rng.sample([a["account_id"] for a in accounts], k=8))
    for _ in range(NUM_USAGE_EVENTS):
        acct = rng.choice(accounts)
        # Silent accounts mostly have events in the older window (pre-90 days)
        if acct["account_id"] in silent_accounts:
            days_ago = rng.randint(90, 365)
        else:
            days_ago = rng.randint(0, 180)
        event_date = today - timedelta(days=days_ago)
        rows.append(
            {
                "account_id": acct["account_id"],
                "event_date": event_date.isoformat(),
                "feature": rng.choice(FEATURES),
                "user_count": rng.randint(1, 25),
            }
        )
    return rows


def _generate_tickets(rng: random.Random, accounts: list[dict], today: date) -> list[dict]:
    rows = []
    for i in range(NUM_TICKETS):
        acct = rng.choice(accounts)
        opened_days_ago = rng.randint(0, 120)
        priority = rng.choices(TICKET_PRIORITIES, weights=[0.4, 0.4, 0.15, 0.05])[0]
        status = rng.choices(TICKET_STATUSES, weights=[0.25, 0.15, 0.4, 0.2])[0]
        rows.append(
            {
                "ticket_id": f"T{i + 1:04d}",
                "account_id": acct["account_id"],
                "opened_at": (today - timedelta(days=opened_days_ago)).isoformat(),
                "status": status,
                "priority": priority,
                "summary": _fake_ticket_summary(rng),
            }
        )
    return rows


def _generate_signals(rng: random.Random, accounts: list[dict], today: date) -> list[dict]:
    rows = []
    for _ in range(NUM_SIGNALS):
        acct = rng.choice(accounts)
        days_ago = rng.randint(0, 90)
        rows.append(
            {
                "account_id": acct["account_id"],
                "signal_date": (today - timedelta(days=days_ago)).isoformat(),
                "signal_type": rng.choice(SIGNAL_TYPES),
                "value": rng.randint(1, 5),
            }
        )
    return rows


def _fake_company_name(rng: random.Random) -> str:
    first = rng.choice(
        [
            "Cascade",
            "Summit",
            "Ironwood",
            "Northstar",
            "Granite",
            "Redwood",
            "Pacific",
            "Cornerstone",
            "Apex",
            "Keystone",
            "Bluepeak",
            "Stoneridge",
            "Ridgeway",
            "Heartland",
            "Foundry",
            "Skyline",
            "Anchor",
            "Trident",
            "Bedrock",
            "Westbound",
        ]
    )
    second = rng.choice(
        ["Construction", "Builders", "Contractors", "Group", "Partners", "Industries"]
    )
    return f"{first} {second}"


def _fake_ticket_summary(rng: random.Random) -> str:
    templates = [
        "Schedule view not loading for project {n}",
        "Resource forecast off by {n} headcount",
        "Calendar sync failing intermittently",
        "Mobile app crash when opening person profile",
        "Reports export timing out for project {n}",
        "Skills matrix not reflecting recent edits",
        "Permission error when inviting user",
        "Slow load times on pipeline page",
    ]
    return rng.choice(templates).format(n=rng.randint(1, 50))


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
