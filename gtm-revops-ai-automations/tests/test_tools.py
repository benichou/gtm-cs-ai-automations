"""Tests for the gtm-revops MCP tool functions.

These are unit tests against the *underlying Python functions*. The tools
themselves are also exercised end-to-end through the MCP transport via
the --self-check CLI flag (tested in test_mcp_smoke.py).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from gtm_revops.data import OPEN_STAGES, reset_cache
from gtm_revops.mcp import (
    check_data_quality,
    flag_stale_opps,
    list_open_opps,
    roll_up_pipeline,
)

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PLUGIN_ROOT / "fixtures" / "opps.json"
SEED_CMD = [sys.executable, "-m", "gtm_revops.seed"]


@pytest.fixture(scope="session", autouse=True)
def _seed_fixture() -> None:
    """Generate the opps fixture once for the test session if missing."""
    if FIXTURE.exists():
        return
    subprocess.run(SEED_CMD, cwd=PLUGIN_ROOT, check=True)
    reset_cache()


def test_list_open_opps_returns_only_open_stages() -> None:
    rows = list_open_opps()
    assert len(rows) > 0
    for r in rows:
        assert r["stage"] in OPEN_STAGES


def test_list_open_opps_filters_by_stage() -> None:
    rows = list_open_opps(stage="Negotiation")
    assert len(rows) > 0
    for r in rows:
        assert r["stage"] == "Negotiation"


def test_list_open_opps_unknown_stage_returns_empty() -> None:
    rows = list_open_opps(stage="NotARealStage")
    assert rows == []


def test_check_data_quality_finds_injected_issues() -> None:
    result = check_data_quality()
    assert result["total_issues"] > 0
    assert "missing_close_date" in result["issues"]
    assert "negative_amount" in result["issues"]
    assert "orphan_account" in result["issues"]
    # seed.py deliberately injects 5 / 3 / 4 of each:
    assert result["by_category"]["missing_close_date"] >= 5
    assert result["by_category"]["negative_amount"] >= 3
    assert result["by_category"]["orphan_account"] >= 4


def test_roll_up_pipeline_by_stage_has_expected_shape() -> None:
    result = roll_up_pipeline(group_by="stage")
    assert result["group_by"] == "stage"
    assert result["total_open_amount"] > 0
    assert result["total_open_count"] > 0
    assert len(result["breakdown"]) > 0
    seen_stages = {b["group"] for b in result["breakdown"]}
    assert seen_stages.issubset(OPEN_STAGES)


def test_roll_up_pipeline_by_owner_groups_by_owner() -> None:
    result = roll_up_pipeline(group_by="owner")
    assert result["group_by"] == "owner"
    assert len(result["breakdown"]) > 0


def test_roll_up_pipeline_excludes_negative_amounts() -> None:
    """Negative-amount deals are data-quality issues; they should not pollute the roll-up."""
    result = roll_up_pipeline(group_by="stage")
    assert result["total_open_amount"] > 0  # not negative


def test_roll_up_pipeline_rejects_invalid_group_by() -> None:
    with pytest.raises(ValueError):
        roll_up_pipeline(group_by="bogus")  # type: ignore[arg-type]


def test_flag_stale_opps_default_30_days() -> None:
    stale = flag_stale_opps()
    for opp in stale:
        assert opp["days_since_activity"] >= 30
        assert opp["stage"] in OPEN_STAGES


def test_flag_stale_opps_sorted_oldest_first() -> None:
    stale = flag_stale_opps(days=30)
    if len(stale) >= 2:
        for a, b in zip(stale, stale[1:], strict=False):
            assert a["days_since_activity"] >= b["days_since_activity"]


def test_flag_stale_opps_higher_threshold_returns_fewer() -> None:
    stale_30 = flag_stale_opps(days=30)
    stale_60 = flag_stale_opps(days=60)
    assert len(stale_60) <= len(stale_30)


def test_flag_stale_opps_rejects_negative_days() -> None:
    with pytest.raises(ValueError):
        flag_stale_opps(days=-1)


def test_fixture_has_expected_row_count() -> None:
    rows = json.loads(FIXTURE.read_text())
    assert len(rows) == 300


def test_every_fixture_row_has_required_fields() -> None:
    rows = json.loads(FIXTURE.read_text())
    required = {
        "opp_id",
        "account_id",
        "account_name",
        "stage",
        "amount",
        "close_date",
        "owner",
        "last_activity_at",
        "source",
    }
    for row in rows:
        missing = required - set(row.keys())
        assert not missing, f"{row.get('opp_id', '?')} missing fields: {missing}"
