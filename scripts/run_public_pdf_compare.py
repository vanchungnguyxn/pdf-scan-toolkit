from __future__ import annotations

"""Download public synthetic medical-style PDFs and run the scanner comparison.

Usage:
    python scripts/run_public_pdf_compare.py
    python scripts/run_public_pdf_compare.py --skip-download
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PUBLIC_PDF_DIR = ROOT / "data" / "public_pdf_samples"
PUBLIC_JSON_DIR = ROOT / "data" / "public_json_outputs"
PUBLIC_RAW_DIR = ROOT / "data" / "public_extracted_raw"
PUBLIC_REPORT_DIR = ROOT / "data" / "public_demo_outputs"


def run(cmd: list[str]) -> int:
    print("$ " + " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run comparison on public synthetic medical-style PDFs.")
    parser.add_argument("--skip-download", action="store_true", help="Use existing files in data/public_pdf_samples")
    parser.add_argument("--count", type=int, default=2, help="Files per difficulty level to download")
    args = parser.parse_args()

    if not args.skip_download:
        code = run([sys.executable, "scripts/download_public_pdfs.py", "--count", str(args.count)])
        if code not in (0, 2):
            return code

    pdf_files = sorted(PUBLIC_PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No public PDFs found. Put files into data/public_pdf_samples or run scripts/download_public_pdfs.py on a machine with internet.")
        return 2

    sys.path.insert(0, str(SRC))
    from pdf_scan_toolkit.run_pdf_scan_demo import run_demo

    summary = run_demo(
        input_dir=PUBLIC_PDF_DIR,
        output_dir=PUBLIC_JSON_DIR,
        raw_dir=PUBLIC_RAW_DIR,
        report_dir=PUBLIC_REPORT_DIR,
    )
    print("Public PDF comparison completed.")
    print(f"PDF files: {summary['pdf_count']}")
    print(f"JSON outputs: {summary['json_count']}")
    print(f"Report: {summary['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
