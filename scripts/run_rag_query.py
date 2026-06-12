from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdf_scan_toolkit.rag_pipeline import query_rag


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline RAG query over EMR JSON records.")
    parser.add_argument("--input", default="data/roundtrip_json_samples", help="EMR JSON directory")
    parser.add_argument("--patient-id", default=None, help="Filter by patient ID")
    parser.add_argument("--question", required=True, help="Clinical question")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--output", default=None, help="Optional path to write JSON result")
    args = parser.parse_args()

    result = query_rag(
        input_dir=args.input,
        question=args.question,
        patient_id=args.patient_id,
        top_k=args.top_k,
    )
    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    print(out_json)
    if args.output:
        Path(args.output).write_text(out_json, encoding="utf-8")


if __name__ == "__main__":
    main()
