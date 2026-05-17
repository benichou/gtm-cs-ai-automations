"""gtm-sales-enrich CLI: look up a company in the fixture and print structured JSON.

Usage:
    gtm-sales-enrich "Foundry Contractors"

The sales-call-prep skill (in .claude/skills/sales-call-prep/SKILL.md) calls
this CLI as Step 2 of its runbook. The structured JSON returned here feeds
the discovery-question generation and the email draft.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gtm_sales.enrichment import lookup


def main() -> int:
    parser = argparse.ArgumentParser(prog="gtm-sales-enrich", description=__doc__)
    parser.add_argument("company_name", help="The target company name, e.g. 'Foundry Contractors'")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Path to the companies fixture JSON. Defaults to ../fixtures/companies.json.",
    )
    args = parser.parse_args()

    result = lookup(args.company_name, fixture_path=args.fixture)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.found else 1


if __name__ == "__main__":
    sys.exit(main())
