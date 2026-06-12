from __future__ import annotations

import json
import random
from pathlib import Path

from .schemas import EMRRecord

# Deterministic variants for closed-loop demo (offline, no external data).
_SYNTHETIC_VARIANTS: list[dict] = [
    {
        "patient_id": "SYN-001",
        "name": "Nguyen Van Synthetic A",
        "dob": "1970-01-15",
        "gender": "Nam",
        "chronic": [
            "Tang huyet ap tu nam 2019, dang dieu tri on dinh.",
            "Dai thao duong type 2 tu nam 2020.",
        ],
        "allergy": "Di ung Penicillin, phan ung noi man do.",
        "medications": [
            "Metformin 500mg, uong 2 lan/ngay.",
            "Amlodipine 5mg, uong 1 lan/ngay.",
        ],
        "labs": [
            ("Glucose", "9.8", "mmol/L", "3.9-5.6", "cao"),
            ("Creatinine", "150", "umol/L", "60-110", "cao"),
        ],
    },
    {
        "patient_id": "SYN-002",
        "name": "Tran Thi Synthetic B",
        "dob": "1978-06-22",
        "gender": "Nu",
        "chronic": [
            "Tang huyet ap tu nam 2018.",
            "Suy than man tinh CKD stage 3.",
        ],
        "allergy": "Di ung Ibuprofen, noi me day.",
        "medications": [
            "Losartan 50mg, uong 1 lan/ngay.",
            "Atorvastatin 20mg, uong 1 lan toi.",
        ],
        "labs": [
            ("Creatinine", "180", "umol/L", "60-110", "cao"),
            ("eGFR", "42", "mL/min", "90-120", "thap"),
        ],
    },
    {
        "patient_id": "SYN-003",
        "name": "Le Van Synthetic C",
        "dob": "1985-11-08",
        "gender": "Nam",
        "chronic": ["Hen phe quan tu nam 2015."],
        "allergy": "Di ung Aspirin, kho tho.",
        "medications": ["Insulin 10 UI truoc bua sang."],
        "labs": [
            ("HbA1c", "8.2", "%", "4.0-5.6", "cao"),
        ],
    },
]


def _build_raw_text(variant: dict) -> str:
    lines = [
        "SYNTHETIC CLINICAL NOTE",
        f"Ma benh nhan: {variant['patient_id']}",
        f"Ho ten: {variant['name']}",
        f"Ngay sinh: {variant['dob']}",
        f"Gioi tinh: {variant['gender']}",
        "",
        "Tien su benh:",
    ]
    lines.extend(f"- {c}" for c in variant["chronic"])
    lines.extend(["", "Di ung:", f"- {variant['allergy']}"])
    lines.extend(["", "Thuoc dang dung:"])
    lines.extend(f"- {m}" for m in variant["medications"])
    lines.extend(["", "Xet nghiem:"])
    for test_name, value, unit, ref, flag in variant["labs"]:
        lines.append(f"{test_name}: {value} {unit}, tham chieu {ref}, {flag}.")
    return "\n".join(lines)


def _variant_to_record(variant: dict, source_pdf: str) -> EMRRecord:
    raw_text = _build_raw_text(variant)
    page = 1
    doc_id = "DOC-001"

    def src(evidence: str) -> dict:
        return {
            "document_id": doc_id,
            "page": page,
            "evidence_text": evidence,
        }

    allergies = [
        {
            "name": "Allergy",
            "value": variant["allergy"].replace("Di ung ", "").strip(),
            "status": "active",
            "source": src(f"- {variant['allergy']}"),
        }
    ]
    chronic = [
        {
            "name": "Chronic disease",
            "value": c,
            "status": "active",
            "source": src(f"- {c}"),
        }
        for c in variant["chronic"]
    ]
    meds = [
        {
            "name": "Active medication",
            "value": m,
            "status": "active",
            "source": src(f"- {m}"),
        }
        for m in variant["medications"]
    ]
    labs = []
    for test_name, value, unit, ref, flag in variant["labs"]:
        line = f"{test_name}: {value} {unit}, tham chieu {ref}, {flag}."
        interp = "high" if flag in {"cao", "high"} else "low" if flag in {"thap", "low"} else "abnormal"
        labs.append({
            "test_name": test_name,
            "value": value,
            "unit": unit,
            "reference_range": ref,
            "interpretation": interp,
            "source": src(line),
        })

    data = {
        "patient": {
            "patient_id": variant["patient_id"],
            "name": variant["name"],
            "dob": variant["dob"],
            "gender": variant["gender"],
        },
        "documents": [
            {
                "document_id": doc_id,
                "doc_type": "emr_pdf_page",
                "created_at": None,
                "source_pdf": source_pdf,
                "page": page,
                "raw_text": raw_text,
            }
        ],
        "clinical_summary": {
            "allergies": allergies,
            "chronic_diseases": chronic,
            "active_medications": meds,
            "abnormal_labs": labs,
        },
        "metadata": {
            "source_pdf": source_pdf,
            "parser": "synthetic_generator_v1",
            "synthetic": True,
        },
    }
    return EMRRecord.model_validate(data)


def synthesize_from_templates(
    template_dir: str | Path,
    output_dir: str | Path,
    count: int = 3,
    seed: int = 42,
) -> list[Path]:
    """Generate synthetic EMR JSON records inspired by templates in template_dir."""
    template_dir = Path(template_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    templates = sorted(template_dir.glob("*.json"))
    if not templates:
        raise FileNotFoundError(f"No JSON templates found in {template_dir}")

    random.seed(seed)
    written: list[Path] = []
    variants = _SYNTHETIC_VARIANTS[:count]
    if len(variants) < count:
        raise ValueError(f"Only {len(_SYNTHETIC_VARIANTS)} built-in variants available, requested {count}")

    for i, variant in enumerate(variants):
        # Use a template for structural reference (validates schema compatibility).
        template_path = templates[i % len(templates)]
        _ = json.loads(template_path.read_text(encoding="utf-8"))

        stem = f"syn-{i + 1:03d}_emr"
        source_pdf = f"{stem}.pdf"
        record = _variant_to_record(variant, source_pdf)
        out_path = output_dir / f"{stem}.json"
        out_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        written.append(out_path)

    return written
