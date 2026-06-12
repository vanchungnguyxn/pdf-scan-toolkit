from __future__ import annotations

import json
from pathlib import Path

from .schemas import EMRRecord


def evaluate_extraction(
    golden_path: str | Path = "eval/golden_extraction.json",
    synthetic_dir: str | Path = "data/synthetic_json_samples",
    roundtrip_dir: str | Path = "data/roundtrip_json_samples",
) -> dict:
    golden_path = Path(golden_path)
    synthetic_dir = Path(synthetic_dir)
    roundtrip_dir = Path(roundtrip_dir)

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    results: list[dict] = []
    passed = 0

    for case in golden.get("cases", []):
        fname = case["synthetic_file"]
        synth_path = synthetic_dir / fname
        rt_path = roundtrip_dir / fname
        detail: dict = {"file": fname, "checks": {}, "status": "FAIL"}

        if not synth_path.exists():
            detail["error"] = f"Missing synthetic file: {synth_path}"
            results.append(detail)
            continue
        if not rt_path.exists():
            detail["error"] = f"Missing roundtrip file: {rt_path}"
            results.append(detail)
            continue

        original = EMRRecord.model_validate(json.loads(synth_path.read_text(encoding="utf-8")))
        roundtrip = EMRRecord.model_validate(json.loads(rt_path.read_text(encoding="utf-8")))

        checks = {
            "patient_id": roundtrip.patient.patient_id == case["expected_patient_id"],
            "allergies": len(roundtrip.clinical_summary.allergies) >= case.get("min_allergies", 1),
            "medications": len(roundtrip.clinical_summary.active_medications) >= case.get("min_medications", 1),
            "abnormal_labs": len(roundtrip.clinical_summary.abnormal_labs) >= case.get("min_abnormal_labs", 1),
        }
        med_text = " ".join(m.value.lower() for m in roundtrip.clinical_summary.active_medications)
        required = case.get("required_medication_terms", [])
        checks["medication_terms"] = all(term.lower() in med_text for term in required) if required else True
        checks["roundtrip_parsed"] = roundtrip.patient.patient_id == original.patient.patient_id

        detail["checks"] = checks
        detail["status"] = "PASS" if all(checks.values()) else "FAIL"
        if detail["status"] == "PASS":
            passed += 1
        results.append(detail)

    total = len(results)
    return {
        "metric": "extraction_pass_rate",
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total * 100, 2) if total else 0.0,
        "results": results,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate PDF extraction roundtrip quality.")
    parser.add_argument("--golden", default="eval/golden_extraction.json")
    parser.add_argument("--synthetic", default="data/synthetic_json_samples")
    parser.add_argument("--roundtrip", default="data/roundtrip_json_samples")
    parser.add_argument("--output", default="eval/results/extraction_eval.json")
    args = parser.parse_args()

    report = evaluate_extraction(args.golden, args.synthetic, args.roundtrip)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extraction evaluation: {report['passed']}/{report['total']} passed ({report['pass_rate']}%)")
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
