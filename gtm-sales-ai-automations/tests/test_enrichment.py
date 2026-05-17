"""Tests for the gtm-sales enrichment + CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from gtm_sales.enrichment import lookup

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = PLUGIN_ROOT / "fixtures" / "companies.json"


def test_exact_match_returns_company() -> None:
    result = lookup("Foundry Contractors", fixture_path=FIXTURE)
    assert result.found is True
    assert result.match_type == "exact"
    assert result.company is not None
    assert result.company["name"] == "Foundry Contractors"
    assert result.company["industry"] == "general_contractor"


def test_case_insensitive_exact_match() -> None:
    result = lookup("foundry CONTRACTORS", fixture_path=FIXTURE)
    assert result.found is True
    assert result.match_type == "exact"


def test_fuzzy_match_on_partial_name() -> None:
    result = lookup("Foundry", fixture_path=FIXTURE)
    assert result.found is True
    assert result.match_type == "fuzzy"
    assert result.company is not None
    assert result.company["name"] == "Foundry Contractors"


def test_no_match_returns_candidates() -> None:
    result = lookup("Globex Megacorp", fixture_path=FIXTURE)
    assert result.found is False
    assert result.match_type == "none"
    assert result.company is None
    assert 1 <= len(result.candidates) <= 3
    # candidates should be drawn from the fixture
    fixture_names = {c["name"] for c in json.loads(FIXTURE.read_text())}
    for candidate in result.candidates:
        assert candidate in fixture_names


def test_empty_input_returns_unknown() -> None:
    result = lookup("", fixture_path=FIXTURE)
    assert result.found is False
    assert result.match_type == "none"


def test_whitespace_input_returns_unknown() -> None:
    result = lookup("   ", fixture_path=FIXTURE)
    assert result.found is False


def test_result_to_dict_includes_source() -> None:
    result = lookup("Foundry Contractors", fixture_path=FIXTURE)
    payload = result.to_dict()
    assert payload["source"] == "fixture"
    assert payload["found"] is True
    assert "company" in payload


def test_cli_prints_valid_json_for_known_company(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """End-to-end smoke test of the CLI."""
    import gtm_sales.cli as cli

    original_argv = sys.argv
    sys.argv = ["gtm-sales-enrich", "Foundry Contractors"]
    try:
        rc = cli.main()
    finally:
        sys.argv = original_argv

    assert rc == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["found"] is True
    assert payload["company"]["name"] == "Foundry Contractors"


def test_cli_returns_nonzero_for_unknown_company(
    capsys: pytest.CaptureFixture[str],
) -> None:
    import gtm_sales.cli as cli

    original_argv = sys.argv
    sys.argv = ["gtm-sales-enrich", "Globex Megacorp"]
    try:
        rc = cli.main()
    finally:
        sys.argv = original_argv

    assert rc == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["found"] is False
    assert "candidates" in payload


def test_fixture_has_expected_minimum_count() -> None:
    """Sanity check that someone hasn't accidentally emptied the fixture."""
    companies = json.loads(FIXTURE.read_text())
    assert len(companies) >= 10, "expected at least 10 company fixtures"


def test_every_fixture_entry_has_required_fields() -> None:
    companies = json.loads(FIXTURE.read_text())
    required = {
        "name",
        "type",
        "industry",
        "headcount_band",
        "revenue_band",
        "headquarters",
        "founded_year",
        "regions_active",
        "recent_events",
        "notable_projects",
        "pain_points_inferred",
        "source",
    }
    for company in companies:
        missing = required - set(company.keys())
        assert not missing, f"{company.get('name', '?')} missing fields: {missing}"
