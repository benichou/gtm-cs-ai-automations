"""Smoke tests for the gtm-cs CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from gtm_cs.cli import AccountNotFound, build_brief

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = PLUGIN_ROOT / "fixtures"
SEED_SCRIPT = PLUGIN_ROOT / "scripts" / "seed.py"


@pytest.fixture(scope="session", autouse=True)
def _seed_fixtures() -> None:
    """Generate fixtures once for the test session if missing."""
    needed = [
        FIXTURES / "accounts.csv",
        FIXTURES / "usage_events.csv",
        FIXTURES / "support_tickets.csv",
        FIXTURES / "expansion_signals.csv",
    ]
    if all(f.exists() for f in needed):
        return
    subprocess.run(
        [sys.executable, str(SEED_SCRIPT)],
        cwd=PLUGIN_ROOT,
        check=True,
    )


def test_build_brief_returns_expected_shape() -> None:
    brief = build_brief("A001", FIXTURES, as_of=date(2026, 5, 16))
    assert brief["account_id"] == "A001"
    assert set(brief.keys()) == {
        "account_id",
        "account",
        "as_of",
        "adoption",
        "tickets",
        "expansion_signals_last_90d",
        "churn_risk",
    }
    assert set(brief["account"].keys()) >= {
        "name",
        "plan",
        "mrr",
        "csm_email",
        "started_at",
        "industry",
        "project_count",
    }
    assert 0 <= brief["churn_risk"]["score"] <= 10
    assert isinstance(brief["churn_risk"]["escalate"], bool)


def test_unknown_account_raises() -> None:
    with pytest.raises(AccountNotFound):
        build_brief("A999", FIXTURES, as_of=date(2026, 5, 16))


def test_adoption_trend_is_a_known_label() -> None:
    brief = build_brief("A001", FIXTURES, as_of=date(2026, 5, 16))
    assert brief["adoption"]["trend"] in {
        "growing",
        "steady",
        "declining",
        "declining_sharply",
        "new_account",
        "no_activity",
    }


def test_cli_prints_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    """End-to-end: invoke the CLI's main() and confirm stdout is valid JSON."""
    import gtm_cs.cli as cli

    original_argv = sys.argv
    sys.argv = ["gtm-cs", "A001"]
    try:
        rc = cli.main()
    finally:
        sys.argv = original_argv

    assert rc == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["account_id"] == "A001"
