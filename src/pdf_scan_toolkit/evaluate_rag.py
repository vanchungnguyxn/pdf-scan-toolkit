from __future__ import annotations

import json
from pathlib import Path

from .rag_pipeline import query_rag


def evaluate_rag(
    golden_path: str | Path = "eval/golden_rag.json",
    input_dir: str | Path = "data/roundtrip_json_samples",
) -> dict:
    golden_path = Path(golden_path)
    input_dir = Path(input_dir)

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    results: list[dict] = []
    passed = 0

    for case in golden.get("cases", []):
        patient_id = case["patient_id"]
        question = case["question"]
        result = query_rag(input_dir=input_dir, question=question, patient_id=patient_id)

        answer_lower = (result.get("answer") or "").lower()
        required = [t.lower() for t in case.get("required_answer_terms", [])]
        terms_ok = all(term in answer_lower for term in required)
        citations = result.get("citations") or []
        citations_ok = len(citations) >= case.get("min_citations", 1)
        citation_fields_ok = all(
            c.get("document_id") and c.get("page") and c.get("evidence_text")
            for c in citations
        )

        checks = {
            "required_terms": terms_ok,
            "has_citations": citations_ok,
            "citation_fields": citation_fields_ok,
        }
        status = "PASS" if all(checks.values()) else "FAIL"
        if status == "PASS":
            passed += 1

        results.append({
            "patient_id": patient_id,
            "question": question,
            "answer": result.get("answer"),
            "checks": checks,
            "status": status,
            "citations_count": len(citations),
        })

    total = len(results)
    return {
        "metric": "rag_pass_rate",
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total * 100, 2) if total else 0.0,
        "results": results,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate baseline RAG answers against golden cases.")
    parser.add_argument("--golden", default="eval/golden_rag.json")
    parser.add_argument("--input", default="data/roundtrip_json_samples")
    parser.add_argument("--output", default="eval/results/rag_eval.json")
    args = parser.parse_args()

    report = evaluate_rag(args.golden, args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"RAG evaluation: {report['passed']}/{report['total']} passed ({report['pass_rate']}%)")
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
