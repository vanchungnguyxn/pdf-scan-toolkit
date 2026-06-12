from __future__ import annotations

import argparse
import json
from pathlib import Path

from .json_to_pdf import convert_json_dir_to_pdf
from .run_pdf_scan_demo import run_demo
from .schemas import EMRRecord
from .synthesize_records import synthesize_from_templates


def _compare_records(original: EMRRecord, roundtrip: EMRRecord) -> dict:
    checks = {
        "patient_id_match": original.patient.patient_id == roundtrip.patient.patient_id,
        "name_match": original.patient.name == roundtrip.patient.name,
        "allergy_count_ok": len(roundtrip.clinical_summary.allergies) >= 1,
        "medication_count_ok": len(roundtrip.clinical_summary.active_medications) >= 1,
        "abnormal_lab_count_ok": len(roundtrip.clinical_summary.abnormal_labs) >= 1,
    }
    orig_meds = {m.value.lower() for m in original.clinical_summary.active_medications}
    rt_meds = " ".join(m.value.lower() for m in roundtrip.clinical_summary.active_medications)
    checks["medication_overlap"] = any(m.split()[0] in rt_meds for m in orig_meds if m)

    orig_allergy = " ".join(a.value.lower() for a in original.clinical_summary.allergies)
    rt_allergy = " ".join(a.value.lower() for a in roundtrip.clinical_summary.allergies)
    checks["allergy_overlap"] = any(
        token in rt_allergy
        for token in orig_allergy.split()
        if len(token) > 4 and token not in {"allergy", "active"}
    )

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    return {
        "patient_id": original.patient.patient_id,
        "checks": checks,
        "passed": passed,
        "total": total,
        "status": "PASS" if passed == total else ("PARTIAL" if passed >= total - 1 else "FAIL"),
    }


def run_closed_loop(
    template_dir: str | Path = "data/json_samples",
    synthetic_json_dir: str | Path = "data/synthetic_json_samples",
    synthetic_pdf_dir: str | Path = "data/synthetic_pdf_samples",
    roundtrip_json_dir: str | Path = "data/roundtrip_json_samples",
    roundtrip_raw_dir: str | Path = "data/roundtrip_extracted_raw",
    report_dir: str | Path = "data/roundtrip_outputs",
    count: int = 3,
) -> dict:
    template_dir = Path(template_dir)
    synthetic_json_dir = Path(synthetic_json_dir)
    synthetic_pdf_dir = Path(synthetic_pdf_dir)
    roundtrip_json_dir = Path(roundtrip_json_dir)
    roundtrip_raw_dir = Path(roundtrip_raw_dir)
    report_dir = Path(report_dir)

    # Step 1: synthesize JSON from templates
    synth_paths = synthesize_from_templates(template_dir, synthetic_json_dir, count=count)

    # Step 2: JSON -> PDF
    pdf_paths = convert_json_dir_to_pdf(synthetic_json_dir, synthetic_pdf_dir)

    # Step 3: PDF -> JSON roundtrip
    demo_summary = run_demo(
        input_dir=synthetic_pdf_dir,
        output_dir=roundtrip_json_dir,
        raw_dir=roundtrip_raw_dir,
        report_dir=report_dir,
    )

    # Step 4: compare original synthetic vs roundtrip
    comparisons: list[dict] = []
    for synth_path in synth_paths:
        rt_path = roundtrip_json_dir / synth_path.name
        if not rt_path.exists():
            comparisons.append({
                "file": synth_path.name,
                "status": "FAIL",
                "error": "Roundtrip JSON not produced",
            })
            continue
        original = EMRRecord.model_validate(json.loads(synth_path.read_text(encoding="utf-8")))
        roundtrip = EMRRecord.model_validate(json.loads(rt_path.read_text(encoding="utf-8")))
        comp = _compare_records(original, roundtrip)
        comp["file"] = synth_path.name
        comparisons.append(comp)

    pass_count = sum(1 for c in comparisons if c.get("status") in {"PASS", "PARTIAL"})
    closed_loop_summary = {
        "synthetic_count": len(synth_paths),
        "pdf_count": len(pdf_paths),
        "roundtrip_json_count": demo_summary["json_count"],
        "comparisons": comparisons,
        "pass_count": pass_count,
        "total_count": len(comparisons),
        "report_path": str(report_dir / "pdf_scan_report.md"),
        "demo_summary": demo_summary,
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "closed_loop_summary.json").write_text(
        json.dumps(closed_loop_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return closed_loop_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JSON -> PDF -> JSON closed-loop demo.")
    parser.add_argument("--count", type=int, default=3, help="Number of synthetic records")
    parser.add_argument("--template", default="data/json_samples", help="Template JSON directory")
    parser.add_argument("--synthetic-json", default="data/synthetic_json_samples")
    parser.add_argument("--synthetic-pdf", default="data/synthetic_pdf_samples")
    parser.add_argument("--roundtrip-json", default="data/roundtrip_json_samples")
    parser.add_argument("--roundtrip-raw", default="data/roundtrip_extracted_raw")
    parser.add_argument("--report", default="data/roundtrip_outputs")
    args = parser.parse_args()

    summary = run_closed_loop(
        template_dir=args.template,
        synthetic_json_dir=args.synthetic_json,
        synthetic_pdf_dir=args.synthetic_pdf,
        roundtrip_json_dir=args.roundtrip_json,
        roundtrip_raw_dir=args.roundtrip_raw,
        report_dir=args.report,
        count=args.count,
    )
    print("Closed-loop demo completed.")
    print(f"Synthetic JSON: {summary['synthetic_count']}")
    print(f"Synthetic PDF: {summary['pdf_count']}")
    print(f"Roundtrip JSON: {summary['roundtrip_json_count']}")
    print(f"Comparisons pass/partial: {summary['pass_count']}/{summary['total_count']}")
    print(f"Summary: {Path(args.report) / 'closed_loop_summary.json'}")


if __name__ == "__main__":
    main()
