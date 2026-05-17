"""Validate marketplace.json, each plugin.json, and every SKILL.md frontmatter.

Exit 0 if all valid, non-zero otherwise. Run from the monorepo root:

    python scripts/validate_manifests.py

Zero third-party dependencies — designed to run under `uv run --no-project`
or plain `python` without installing anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    failures: list[str] = []
    failures += _validate_marketplace()
    failures += _validate_plugins()
    failures += _validate_skills()

    if failures:
        print("Manifest validation FAILED:")
        for line in failures:
            print(f"  - {line}")
        return 1

    print("All manifests valid.")
    return 0


def _validate_marketplace() -> list[str]:
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    if not path.exists():
        return [f"missing {path.relative_to(REPO_ROOT)}"]
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path.relative_to(REPO_ROOT)} invalid JSON: {e}"]

    failures: list[str] = []
    for field in ("name", "plugins"):
        if field not in data:
            failures.append(f"{path.relative_to(REPO_ROOT)} missing '{field}'")
    for i, p in enumerate(data.get("plugins", [])):
        if "name" not in p or "source" not in p:
            failures.append(
                f"{path.relative_to(REPO_ROOT)} plugins[{i}] missing 'name' or 'source'"
            )
        src = p.get("source", "")
        if src.startswith("./"):
            target = REPO_ROOT / src[2:] / ".claude-plugin" / "plugin.json"
            if not target.exists():
                failures.append(
                    f"{path.relative_to(REPO_ROOT)} plugins[{i}].source -> "
                    f"{target.relative_to(REPO_ROOT)} does not exist"
                )
    return failures


def _validate_plugins() -> list[str]:
    failures: list[str] = []
    for plugin_json in REPO_ROOT.glob("*/.claude-plugin/plugin.json"):
        rel = plugin_json.relative_to(REPO_ROOT)
        try:
            data = json.loads(plugin_json.read_text())
        except json.JSONDecodeError as e:
            failures.append(f"{rel} invalid JSON: {e}")
            continue
        for field in ("name", "version", "description"):
            if field not in data:
                failures.append(f"{rel} missing '{field}'")
    return failures


def _validate_skills() -> list[str]:
    failures: list[str] = []
    for skill_md in REPO_ROOT.glob("*/.claude/skills/*/SKILL.md"):
        rel = skill_md.relative_to(REPO_ROOT)
        content = skill_md.read_text()
        if not content.startswith("---\n"):
            failures.append(f"{rel} missing YAML frontmatter")
            continue
        try:
            end = content.index("\n---", 4)
        except ValueError:
            failures.append(f"{rel} unterminated frontmatter block")
            continue
        fm = _parse_frontmatter(content[4:end])
        for field in ("name", "description"):
            if not fm.get(field):
                failures.append(f"{rel} frontmatter missing '{field}'")
    return failures


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a SKILL.md YAML frontmatter block into a flat dict.

    Intentionally minimal: handles only single-line `key: value` entries,
    which is all our skill frontmatter ever uses. Avoids a pyyaml dependency
    so this script runs under `uv run --no-project` with zero installs.
    """
    fm: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        fm[key.strip()] = value.strip()
    return fm


if __name__ == "__main__":
    sys.exit(main())
