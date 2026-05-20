"""Tests for the pure analytics functions used by the Model Context Protocol tools."""

from __future__ import annotations

from datetime import date

from gtm_sales_leadership import analytics
from gtm_sales_leadership.data import load_opps, reset_cache


def setup_function() -> None:
    reset_cache()


def test_roll_up_forecast_totals() -> None:
    res = analytics.roll_up_forecast(load_opps())
    assert res["total_deals"] == 40
    assert res["total_arr"] == 2_340_000
    assert res["commit_arr"] == 656_000
    assert res["commit_plus_best_case_arr"] == 1_269_000


def test_roll_up_forecast_owner_filter() -> None:
    res = analytics.roll_up_forecast(load_opps(), owner="J. Torres")
    assert res["total_deals"] == 14
    assert res["total_arr"] == 1_218_000


def test_roll_up_forecast_period_end_filter() -> None:
    # 13 deals with close_date <= 2026-05-31: 11 future-dated + 2 overdue
    # (OPP-023 $22k close 2026-04-15, OPP-024 $24k close 2026-04-22)
    # Total: $938k future + $46k overdue = $984k
    res = analytics.roll_up_forecast(load_opps(), period_end=date(2026, 5, 31))
    assert res["total_deals"] == 13
    assert res["total_arr"] == 984_000


def test_list_deals_closing_by_sorted_ascending() -> None:
    res = analytics.list_deals_closing_by(load_opps(), period_end=date(2026, 5, 31))
    assert res["deal_count"] == 13
    close_dates = [d["close_date"] for d in res["deals"]]
    assert close_dates == sorted(close_dates)


def test_rank_deals_by_risk_top_5_contains_known_stale_deals() -> None:
    res = analytics.rank_deals_by_risk(load_opps(), top_n=5)
    ids = {d["opportunity_id"] for d in res["deals"]}
    # OPP-023 (Proposal, 31d stale, blank next_step, overdue, single-threaded,
    #          Pipeline) — highest scorer
    # OPP-019 (Negotiation, 23d stale, blank next_step, Best Case)
    # OPP-020 (Negotiation, 26d stale, blank next_step, Best Case)
    assert "OPP-023" in ids  # highest scorer
    assert "OPP-020" in ids
    assert "OPP-019" in ids


def test_rank_deals_by_risk_factors_explain_score() -> None:
    res = analytics.rank_deals_by_risk(load_opps(), top_n=10)
    for d in res["deals"]:
        assert d["risk_score"] > 0
        assert len(d["risk_factors"]) > 0


def test_roll_up_by_owner_known_totals() -> None:
    res = analytics.roll_up_by_owner(load_opps())
    by_name = {r["owner_name"]: r for r in res["owners"]}
    assert by_name["J. Torres"]["deals"] == 14
    assert by_name["J. Torres"]["raw_arr"] == 1_218_000
    assert by_name["A. Patel"]["deals"] == 14
    assert by_name["A. Patel"]["raw_arr"] == 643_000
    assert by_name["M. Singh"]["deals"] == 12
    assert by_name["M. Singh"]["raw_arr"] == 479_000


def test_roll_up_by_owner_sorted_by_weighted_desc() -> None:
    res = analytics.roll_up_by_owner(load_opps())
    weighted = [r["weighted_arr"] for r in res["owners"]]
    assert weighted == sorted(weighted, reverse=True)
