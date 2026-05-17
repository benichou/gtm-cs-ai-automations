"""gtm-cs CLI: produce an account-health JSON brief for a Customer Success Manager.

Usage:
    gtm-cs <account_id>

Reads ../fixtures/*.csv (relative to the plugin root) and prints a JSON object
to stdout. The Claude Code skill at .claude/skills/cs-account-health/SKILL.md
calls this CLI and uses the JSON to compose the human-readable markdown brief.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

AS_OF = date(2026, 5, 16)
RECENT_WINDOW_DAYS = 90


def main() -> int:
    parser = argparse.ArgumentParser(prog="gtm-cs", description=__doc__)
    parser.add_argument("account_id", help="The account_id to summarize, e.g. A007")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Path to the fixtures directory. Defaults to ../fixtures relative to this file.",
    )
    args = parser.parse_args()

    fixtures = args.fixtures or _default_fixtures_dir()
    try:
        brief = build_brief(args.account_id, fixtures, as_of=AS_OF)
    except AccountNotFound as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2

    print(json.dumps(brief, indent=2, default=str))
    return 0


class AccountNotFound(Exception):
    pass


def build_brief(account_id: str, fixtures_dir: Path, as_of: date) -> dict:
    """Return the structured brief for a single account.

    The shape is stable — the SKILL.md instructs Claude to format these
    fields into a 1-page markdown brief.
    """
    accounts = pd.read_csv(fixtures_dir / "accounts.csv", parse_dates=["started_at"])
    account = accounts[accounts["account_id"] == account_id]
    if account.empty:
        raise AccountNotFound(f"No account found with account_id={account_id!r}")
    account_row = account.iloc[0].to_dict()

    usage = pd.read_csv(fixtures_dir / "usage_events.csv", parse_dates=["event_date"])
    tickets = pd.read_csv(fixtures_dir / "support_tickets.csv", parse_dates=["opened_at"])
    signals = pd.read_csv(fixtures_dir / "expansion_signals.csv", parse_dates=["signal_date"])

    cutoff_recent = pd.Timestamp(as_of) - pd.Timedelta(days=RECENT_WINDOW_DAYS)
    cutoff_prev = cutoff_recent - pd.Timedelta(days=RECENT_WINDOW_DAYS)

    acct_usage = usage[usage["account_id"] == account_id]
    recent_usage = acct_usage[acct_usage["event_date"] >= cutoff_recent]
    prev_usage = acct_usage[
        (acct_usage["event_date"] >= cutoff_prev) & (acct_usage["event_date"] < cutoff_recent)
    ]
    adoption_trend = _trend(recent_usage, prev_usage)

    acct_tickets = tickets[tickets["account_id"] == account_id]
    active_tickets = acct_tickets[acct_tickets["status"].isin(["open", "pending"])]
    top_active = (
        active_tickets.sort_values(
            ["priority", "opened_at"],
            key=lambda s: (
                s.map({"urgent": 0, "high": 1, "normal": 2, "low": 3})
                if s.name == "priority"
                else s
            ),
        )
        .head(3)
        .to_dict("records")
    )

    acct_signals = signals[
        (signals["account_id"] == account_id) & (signals["signal_date"] >= cutoff_recent)
    ]

    churn_risk, churn_reasoning = _churn_risk(
        recent_usage=recent_usage,
        prev_usage=prev_usage,
        active_tickets=active_tickets,
        signals_recent=acct_signals,
    )

    return {
        "account_id": account_id,
        "account": {
            "name": account_row["name"],
            "plan": account_row["plan"],
            "mrr": int(account_row["mrr"]),
            "csm_email": account_row["csm_email"],
            "started_at": _date_str(account_row["started_at"]),
            "industry": account_row["industry"],
            "project_count": int(account_row["project_count"]),
        },
        "as_of": as_of.isoformat(),
        "adoption": {
            "events_last_90d": int(len(recent_usage)),
            "events_prev_90d": int(len(prev_usage)),
            "trend": adoption_trend,
            "top_features_last_90d": _top_features(recent_usage),
        },
        "tickets": {
            "total_active": int(len(active_tickets)),
            "top_3": [_ticket_row(t) for t in top_active],
        },
        "expansion_signals_last_90d": [_signal_row(s) for s in acct_signals.to_dict("records")],
        "churn_risk": {
            "score": churn_risk,
            "reasoning": churn_reasoning,
            "escalate": churn_risk >= 7,
        },
    }


def _trend(recent: pd.DataFrame, prev: pd.DataFrame) -> str:
    r, p = len(recent), len(prev)
    if p == 0:
        return "new_account" if r > 0 else "no_activity"
    delta = (r - p) / p
    if delta >= 0.10:
        return "growing"
    if delta <= -0.20:
        return "declining_sharply"
    if delta <= -0.05:
        return "declining"
    return "steady"


def _churn_risk(
    *,
    recent_usage: pd.DataFrame,
    prev_usage: pd.DataFrame,
    active_tickets: pd.DataFrame,
    signals_recent: pd.DataFrame,
) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []

    if len(recent_usage) == 0:
        score += 5
        reasons.append("no usage in last 90 days")
    elif len(prev_usage) > 0 and len(recent_usage) / max(len(prev_usage), 1) < 0.5:
        score += 3
        reasons.append("usage down >50% vs prior 90 days")

    urgent = active_tickets[active_tickets["priority"].isin(["urgent", "high"])]
    if len(urgent) >= 2:
        score += 2
        reasons.append(f"{len(urgent)} active high/urgent tickets")
    elif len(urgent) == 1:
        score += 1
        reasons.append("1 active high/urgent ticket")

    if len(signals_recent) == 0:
        score += 1
        reasons.append("no expansion signals in 90 days")
    elif len(signals_recent) >= 3:
        score = max(0, score - 1)
        reasons.append(f"{len(signals_recent)} expansion signals in 90 days (positive)")

    score = min(10, score)
    if not reasons:
        reasons.append("no risk indicators")
    return score, "; ".join(reasons)


def _top_features(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    grouped = df.groupby("feature").size().sort_values(ascending=False).head(3)
    return [{"feature": f, "event_count": int(c)} for f, c in grouped.items()]


def _ticket_row(t: dict) -> dict:
    return {
        "ticket_id": t["ticket_id"],
        "opened_at": _date_str(t["opened_at"]),
        "priority": t["priority"],
        "status": t["status"],
        "summary": t["summary"],
    }


def _signal_row(s: dict) -> dict:
    return {
        "signal_date": _date_str(s["signal_date"]),
        "signal_type": s["signal_type"],
        "value": int(s["value"]),
    }


def _date_str(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _default_fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "fixtures"


if __name__ == "__main__":
    sys.exit(main())
