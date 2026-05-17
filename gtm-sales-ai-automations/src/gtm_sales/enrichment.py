"""Fixture-backed company enrichment for the sales-call-prep skill.

The lookup pipeline:
  1. Exact case-insensitive name match against fixtures/companies.json.
  2. If no exact match, fuzzy match (substring + difflib similarity).
  3. If still nothing, return a structured "unknown" response listing the
     top close-name candidates so the skill can ask the user to clarify.

The function signature and return shape are deliberately what a real HTTP
enrichment client (SEC EDGAR, Apollo, Clearbit) would expose, so the
fixture-reader is swappable with no downstream changes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

DEFAULT_FIXTURE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "companies.json"
FUZZY_THRESHOLD = 0.5
TOP_N_CANDIDATES = 3


@dataclass(frozen=True)
class EnrichmentResult:
    """Structured result of a company lookup.

    `found=True` means we have data and `company` is populated.
    `found=False` means no match — `candidates` lists close names so the
    caller can prompt the user to clarify.
    """

    name: str
    found: bool
    company: dict | None
    candidates: list[str]
    match_type: str  # "exact" | "fuzzy" | "none"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "found": self.found,
            "company": self.company,
            "candidates": self.candidates,
            "match_type": self.match_type,
            "source": "fixture",
        }


def lookup(name: str, fixture_path: Path | None = None) -> EnrichmentResult:
    """Look up a company by name in the fixture data."""
    if not name or not name.strip():
        return EnrichmentResult(
            name=name,
            found=False,
            company=None,
            candidates=[],
            match_type="none",
        )

    companies = _load_companies(fixture_path or DEFAULT_FIXTURE)
    needle = name.strip().lower()

    # Stage 1: exact case-insensitive match
    for c in companies:
        if c["name"].lower() == needle:
            return EnrichmentResult(
                name=name,
                found=True,
                company=c,
                candidates=[],
                match_type="exact",
            )

    # Stage 2: fuzzy substring + similarity match
    scored = []
    for c in companies:
        candidate_name = c["name"].lower()
        substring_bonus = 0.25 if needle in candidate_name else 0.0
        similarity = SequenceMatcher(None, needle, candidate_name).ratio()
        score = similarity + substring_bonus
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_company = scored[0]
    if best_score >= FUZZY_THRESHOLD:
        return EnrichmentResult(
            name=name,
            found=True,
            company=best_company,
            candidates=[],
            match_type="fuzzy",
        )

    # Stage 3: no match — return top candidate names so the caller can clarify
    return EnrichmentResult(
        name=name,
        found=False,
        company=None,
        candidates=[c["name"] for _, c in scored[:TOP_N_CANDIDATES]],
        match_type="none",
    )


def _load_companies(fixture_path: Path) -> list[dict]:
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Companies fixture not found at {fixture_path}. "
            "Ensure fixtures/companies.json is present in the plugin directory."
        )
    return json.loads(fixture_path.read_text())
