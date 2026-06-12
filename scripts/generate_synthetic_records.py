from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.synthesize_records import synthesize_from_templates


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic EMR JSON from templates.")
    parser.add_argument("--template", default="data/json_samples", help="Template JSON directory")
    parser.add_argument("--output", default="data/synthetic_json_samples", help="Output directory")
    parser.add_argument("--count", type=int, default=3, help="Number of records to generate")
    args = parser.parse_args()
    paths = synthesize_from_templates(args.template, args.output, count=args.count)
    print(f"Generated {len(paths)} synthetic records in {args.output}")


if __name__ == "__main__":
    main()
