"""Tests for asset text extraction."""

from __future__ import annotations

from pathlib import Path

import pytest
from gtm_marketing.extract import extract

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SAMPLE = PLUGIN_ROOT / "fixtures" / "sample-post.md"


def test_extract_returns_expected_shape() -> None:
    result = extract(SAMPLE)
    assert "path" in result
    assert "text" in result
    assert "word_count" in result
    assert "char_count" in result


def test_extract_sample_has_substantial_content() -> None:
    result = extract(SAMPLE)
    assert result["word_count"] > 500
    assert result["char_count"] > 3000


def test_extract_normalizes_whitespace() -> None:
    result = extract(SAMPLE)
    # No multi-blank-line runs
    assert "\n\n\n" not in result["text"]
    # No trailing spaces at end-of-line
    for line in result["text"].splitlines():
        assert line == line.rstrip()


def test_extract_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        extract("fixtures/this-file-does-not-exist.md")


def test_extract_accepts_string_path() -> None:
    result = extract(str(SAMPLE))
    assert result["word_count"] > 0
