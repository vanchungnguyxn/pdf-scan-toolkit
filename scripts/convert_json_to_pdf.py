from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.json_to_pdf import convert_json_dir_to_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert EMR JSON files to text-layer PDFs.")
    parser.add_argument("--input", default="data/synthetic_json_samples", help="Input JSON directory")
    parser.add_argument("--output", default="data/synthetic_pdf_samples", help="Output PDF directory")
    args = parser.parse_args()
    paths = convert_json_dir_to_pdf(args.input, args.output)
    print(f"Converted {len(paths)} JSON files to PDF in {args.output}")


if __name__ == "__main__":
    main()
