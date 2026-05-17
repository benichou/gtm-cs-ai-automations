"""Brand-voice scoring + style-guide lookup.

The scoring function is intentionally simple — banned-phrase penalties +
preferred-phrase bonuses — because this is a demo of the *hook + audit*
pattern, not a brand-voice classifier. In production, you'd replace
`score_brand_voice` with a real model call (or an embedding-similarity
score against approved exemplars) and the rest of the plugin would not
change.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
STYLE_GUIDE_PATH = PLUGIN_ROOT / "fixtures" / "style_guide.md"

BANNED_PHRASES = [
    "leverage",
    "synergize",
    "synergy",
    "synergies",
    "circle back",
    "touch base",
    "thought leadership",
    "best-in-class",
    "industry-leading",
    "world-class",
    "deep dive",
    "ecosystem",
    "value proposition",
]
PREFERRED_PHRASES = [
    "crew",
    "schedule",
    "subcontractor",
    "subs",
    "project",
    "field",
    "headcount",
    "workforce",
    "general contractor",
]


def score_brand_voice(text: str) -> dict:
    """Score `text` 0.0-1.0 against the Bridgit brand voice heuristic."""
    if not text or not text.strip():
        return {"score": 0.0, "banned_hits": [], "preferred_hits": [], "reasoning": "empty text"}

    lower = text.lower()
    banned_hits = [p for p in BANNED_PHRASES if _contains_word(lower, p)]
    preferred_hits = [p for p in PREFERRED_PHRASES if _contains_word(lower, p)]

    # Start at 0.8 (neutral baseline). -0.1 per banned hit, +0.05 per preferred hit.
    raw = 0.8 - (0.1 * len(banned_hits)) + (0.05 * len(preferred_hits))
    score = max(0.0, min(1.0, raw))

    if banned_hits and preferred_hits:
        reasoning = (
            f"{len(banned_hits)} banned phrase(s) detected; "
            f"{len(preferred_hits)} preferred phrase(s) found"
        )
    elif banned_hits:
        reasoning = f"{len(banned_hits)} banned phrase(s) detected"
    elif preferred_hits:
        reasoning = f"{len(preferred_hits)} preferred phrase(s) found"
    else:
        reasoning = "no banned or preferred phrases matched"

    return {
        "score": round(score, 2),
        "banned_hits": banned_hits,
        "preferred_hits": preferred_hits,
        "reasoning": reasoning,
    }


def lookup_style_guide_section(section: str) -> dict:
    """Return a named section of the style guide.

    Sections are identified by markdown level-2 headings (## <name>).
    Returns {section, content, found}. If the section isn't present,
    returns the list of available sections in `available`.
    """
    if not STYLE_GUIDE_PATH.exists():
        raise FileNotFoundError(
            f"Style guide not found at {STYLE_GUIDE_PATH}. "
            f"Ensure fixtures/style_guide.md is present in the plugin directory."
        )
    text = STYLE_GUIDE_PATH.read_text()
    sections = _split_sections(text)
    section_key = section.strip().lower()
    if section_key not in sections:
        return {
            "section": section,
            "found": False,
            "content": None,
            "available": sorted(sections.keys()),
        }
    return {
        "section": section,
        "found": True,
        "content": sections[section_key],
        "available": sorted(sections.keys()),
    }


def _split_sections(text: str) -> dict[str, str]:
    """Parse a markdown doc into {lowercase-heading: content} pairs at H2 level."""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_body: list[str] = []

    for raw_line in text.splitlines():
        if raw_line.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_body).strip()
            current_heading = raw_line[3:].strip().lower()
            current_body = []
        elif current_heading is not None:
            current_body.append(raw_line)
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_body).strip()
    return sections


def _contains_word(haystack: str, phrase: str) -> bool:
    """Word-boundary check so 'leverage' matches but 'overleveraged' doesn't."""
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.search(pattern, haystack) is not None
