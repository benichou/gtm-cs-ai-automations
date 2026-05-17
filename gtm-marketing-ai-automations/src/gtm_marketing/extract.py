"""Asset text extraction.

Reads a markdown or plain-text file from disk, normalizes whitespace,
returns the cleaned text + a word count. The MCP `extract_asset_text` tool
calls into here.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent


def extract(path: str | Path) -> dict:
    """Read an asset file and return its normalized text + word count."""
    resolved = _resolve(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Asset not found at {resolved}")

    raw = resolved.read_text()
    cleaned = _normalize(raw)
    return {
        "path": str(resolved),
        "text": cleaned,
        "word_count": len(cleaned.split()),
        "char_count": len(cleaned),
    }


def _resolve(path: str | Path) -> Path:
    """Resolve a path either as absolute or relative to the plugin root."""
    p = Path(path)
    if p.is_absolute():
        return p
    # Try relative to current working directory first, then plugin root.
    cwd_candidate = Path.cwd() / p
    if cwd_candidate.exists():
        return cwd_candidate
    return PLUGIN_ROOT / p


def _normalize(text: str) -> str:
    """Collapse whitespace, strip trailing spaces per line, drop blank-line runs."""
    lines = [line.rstrip() for line in text.splitlines()]
    out: list[str] = []
    blank = False
    for line in lines:
        if line.strip() == "":
            if blank:
                continue
            blank = True
            out.append("")
        else:
            blank = False
            # Collapse runs of internal whitespace
            out.append(re.sub(r"[ \t]+", " ", line))
    return "\n".join(out).strip()
