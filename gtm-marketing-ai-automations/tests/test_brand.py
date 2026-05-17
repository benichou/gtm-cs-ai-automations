"""Tests for brand-voice scoring and style-guide lookup."""

from __future__ import annotations

from gtm_marketing.brand import (
    BANNED_PHRASES,
    PREFERRED_PHRASES,
    lookup_style_guide_section,
    score_brand_voice,
)


def test_score_empty_text_returns_zero() -> None:
    result = score_brand_voice("")
    assert result["score"] == 0.0
    assert result["reasoning"] == "empty text"


def test_score_neutral_text_lands_at_baseline() -> None:
    result = score_brand_voice("This is some neutral sentence with no special words.")
    # Baseline is 0.8 — no banned, no preferred
    assert 0.79 <= result["score"] <= 0.81
    assert result["banned_hits"] == []
    assert result["preferred_hits"] == []


def test_score_penalizes_banned_phrases() -> None:
    text = "We need to leverage our synergy with the ecosystem."
    result = score_brand_voice(text)
    assert result["score"] < 0.8
    assert "leverage" in result["banned_hits"]
    assert "synergy" in result["banned_hits"]
    assert "ecosystem" in result["banned_hits"]


def test_score_rewards_preferred_phrases() -> None:
    text = "The crew schedule for the project requires headcount planning."
    result = score_brand_voice(text)
    assert result["score"] > 0.8
    assert "crew" in result["preferred_hits"]
    assert "schedule" in result["preferred_hits"]
    assert "project" in result["preferred_hits"]
    assert "headcount" in result["preferred_hits"]


def test_score_clamps_to_unit_interval() -> None:
    # Many banned words — score should clamp to 0.0
    banned_blob = " ".join(BANNED_PHRASES * 3)
    result = score_brand_voice(banned_blob)
    assert 0.0 <= result["score"] <= 1.0
    # Many preferred words — score should clamp to 1.0
    preferred_blob = " ".join(PREFERRED_PHRASES * 10)
    result = score_brand_voice(preferred_blob)
    assert 0.0 <= result["score"] <= 1.0


def test_score_word_boundary_avoids_false_positives() -> None:
    # "overleveraged" should NOT count as a hit for "leverage"
    text = "Operations were overleveraged before the restructuring."
    result = score_brand_voice(text)
    assert "leverage" not in result["banned_hits"]


def test_lookup_known_section_returns_content() -> None:
    result = lookup_style_guide_section("tone")
    assert result["found"] is True
    assert result["content"] is not None
    assert len(result["content"]) > 50


def test_lookup_unknown_section_returns_available() -> None:
    result = lookup_style_guide_section("not-a-real-section")
    assert result["found"] is False
    assert result["content"] is None
    assert len(result["available"]) > 0


def test_lookup_section_is_case_insensitive() -> None:
    a = lookup_style_guide_section("Tone")
    b = lookup_style_guide_section("TONE")
    assert a["found"] is True
    assert b["found"] is True
    assert a["content"] == b["content"]
