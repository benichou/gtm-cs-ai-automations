"""Convenience entry point that delegates to gtm_revops.seed.main().

This lets you run the seeder either as `uv run gtm-revops-seed` (CLI script
declared in pyproject.toml) or as `uv run python scripts/seed.py` (direct
script invocation). Both paths run the same code.
"""

from __future__ import annotations

from gtm_revops.seed import main

if __name__ == "__main__":
    main()
