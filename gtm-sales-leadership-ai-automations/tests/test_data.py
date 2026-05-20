"""Tests for the pipeline-export loader."""

from __future__ import annotations

from datetime import date

from gtm_sales_leadership.data import AS_OF, load_opps, reset_cache


def setup_function() -> None:
    reset_cache()


def test_loads_40_rows() -> None:
    assert len(load_opps()) == 40


def test_as_of_is_april_28_2026() -> None:
    assert AS_OF == date(2026, 4, 28)


def test_arr_is_int() -> None:
    opps = load_opps()
    assert all(isinstance(o["arr"], int) for o in opps)
    # OPP-001 from the cleaned fixture is $112,000
    o001 = next(o for o in opps if o["opportunity_id"] == "OPP-001")
    assert o001["arr"] == 112_000


def test_dates_are_iso_strings() -> None:
    opps = load_opps()
    for o in opps:
        for field in ("close_date", "last_activity_date", "created_date"):
            value = o[field]
            if value is None:
                continue
            # date.fromisoformat raises if not ISO YYYY-MM-DD
            date.fromisoformat(value)


def test_weighted_arr_derived() -> None:
    o = next(o for o in load_opps() if o["opportunity_id"] == "OPP-001")
    assert o["weighted_arr"] == 112_000 * 85 / 100


def test_overdue_flag() -> None:
    # OPP-023 close_date was 2026-04-15 — before AS_OF=2026-04-28
    o023 = next(o for o in load_opps() if o["opportunity_id"] == "OPP-023")
    assert o023["is_overdue"] is True


def test_stale_flag() -> None:
    # OPP-020 has 26 days since activity > 14d threshold
    o020 = next(o for o in load_opps() if o["opportunity_id"] == "OPP-020")
    assert o020["is_stale"] is True


def test_zero_activity_flag() -> None:
    # OPP-017 has no last_activity_date in the source data
    o017 = next(o for o in load_opps() if o["opportunity_id"] == "OPP-017")
    assert o017["is_zero_activity"] is True
    assert o017["last_activity_date"] is None
