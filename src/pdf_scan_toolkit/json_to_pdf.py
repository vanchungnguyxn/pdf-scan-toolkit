from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .schemas import EMRRecord


def _gender_label(gender: str | None) -> str:
    if not gender:
        return "Khong ro"
    g = gender.lower()
    if g in {"male", "nam", "m"}:
        return "Nam"
    if g in {"female", "nu", "nữ", "f"}:
        return "Nu"
    return gender


def record_to_text_lines(record: EMRRecord) -> list[str]:
    """Build plain-text lines for PDF text layer (parser-friendly format)."""
    p = record.patient
    cs = record.clinical_summary
    lines = [
        "SYNTHETIC CLINICAL NOTE",
        f"Ma benh nhan: {p.patient_id}",
        f"Ho ten: {p.name}",
        f"Ngay sinh: {p.dob or 'Khong ro'}",
        f"Gioi tinh: {_gender_label(p.gender)}",
        "",
        "Tien su benh:",
    ]
    if cs.chronic_diseases:
        for item in cs.chronic_diseases:
            val = item.source.evidence_text.lstrip("- ").strip() if item.source.evidence_text else item.value
            lines.append(f"- {val}")
    else:
        lines.append("- Khong ghi nhan tien su benh man tinh.")

    lines.extend(["", "Di ung:"])
    if cs.allergies:
        for item in cs.allergies:
            val = item.value
            if "di ung" not in val.lower():
                val = f"Di ung {val}"
            lines.append(f"- {val}" if not val.startswith("-") else val)
    else:
        lines.append("- Khong ghi nhan di ung.")

    lines.extend(["", "Thuoc dang dung:"])
    if cs.active_medications:
        for item in cs.active_medications:
            lines.append(f"- {item.value}")
    else:
        lines.append("- Khong co thuoc dang dung.")

    lines.extend(["", "Xet nghiem:"])
    if cs.abnormal_labs:
        for lab in cs.abnormal_labs:
            flag = "cao" if lab.interpretation == "high" else "thap" if lab.interpretation == "low" else "bat thuong"
            unit = f" {lab.unit}" if lab.unit else ""
            ref = f", tham chieu {lab.reference_range}" if lab.reference_range else ""
            lines.append(f"{lab.test_name}: {lab.value}{unit}{ref}, {flag}.")
    else:
        lines.append("- Khong co chi so bat thuong.")

    return lines


def _draw_lines(c: canvas.Canvas, lines: list[str], x: int = 20, y_start: int = 280, line_gap: int = 8) -> None:
    y = y_start
    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(x * mm, y * mm, line[:120])
        y -= line_gap
        if y < 20:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = y_start


def emr_record_to_pdf(record: EMRRecord, output_path: str | Path) -> Path:
    """Convert EMRRecord JSON to a text-layer PDF using reportlab."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = record_to_text_lines(record)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle(f"EMR {record.patient.patient_id}")
    _draw_lines(c, lines)
    c.save()
    return output_path


def json_file_to_pdf(json_path: str | Path, output_path: str | Path | None = None) -> Path:
    json_path = Path(json_path)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    record = EMRRecord.model_validate(data)
    if output_path is None:
        output_path = json_path.with_suffix(".pdf")
    return emr_record_to_pdf(record, output_path)


def convert_json_dir_to_pdf(input_dir: str | Path, output_dir: str | Path) -> list[Path]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for json_file in sorted(input_dir.glob("*.json")):
        out_pdf = output_dir / f"{json_file.stem}.pdf"
        json_file_to_pdf(json_file, out_pdf)
        written.append(out_pdf)
    return written
