from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "advanced_pdf_samples"
OUT.mkdir(parents=True, exist_ok=True)


def _font(size: int):
    for name in ["DejaVuSans.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _draw_text_pdf(path: Path, lines: list[str], title: str = "PDF") -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle(title)
    c.setFont("Helvetica", 11)
    y = 282
    for line in lines:
        c.drawString(18 * mm, y * mm, line)
        y -= 7
        if y < 18:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = 282
    c.save()


def create_dense_text_pdf() -> None:
    lines = [
        "ADVANCED TEXT PDF - DENSE CLINICAL NOTE",
        "Patient ID: ADV-001",
        "Name: Nguyen Van Advanced",
        "DOB: 1962-06-22",
        "Gender: Male",
        "Clinical history: Hypertension diagnosed in 2018; Diabetes type 2 since 2020.",
        "Allergy: Penicillin - rash and facial swelling.",
        "Current medication: Metformin 500mg twice daily.",
        "Current medication: Amlodipine 5mg once daily.",
        "Laboratory results: Glucose: 11.2 mmol/L, reference 3.9-5.6, high.",
        "Laboratory results: Creatinine: 145 umol/L, reference 60-110, high.",
        "Doctor note: Patient needs follow-up; this demo does not provide medical advice.",
    ]
    _draw_text_pdf(OUT / "advanced_001_text_dense.pdf", lines, "Advanced Dense Text")


def create_grid_table_pdf() -> None:
    path = OUT / "advanced_002_grid_table.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("ADVANCED TABLE PDF - GRID LAB + MEDICATION", styles["Title"]),
        Paragraph("Patient ID: ADV-002", styles["Normal"]),
        Paragraph("Name: Tran Thi Table", styles["Normal"]),
        Paragraph("DOB: 1970-01-09", styles["Normal"]),
        Paragraph("Gender: Female", styles["Normal"]),
        Paragraph("Clinical history: Chronic kidney disease CKD stage 3; Hypertension.", styles["Normal"]),
        Paragraph("Allergy: No known drug allergy recorded.", styles["Normal"]),
        Spacer(1, 10),
    ]
    meds = [
        ["Medication", "Dose", "Frequency", "Status"],
        ["Losartan", "50mg", "once daily", "active"],
        ["Atorvastatin", "20mg", "night", "active"],
    ]
    med_table = Table(meds, colWidths=[45 * mm, 30 * mm, 45 * mm, 35 * mm])
    med_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    story += [Paragraph("Current Medications", styles["Heading2"]), med_table, Spacer(1, 12)]
    labs = [
        ["Test", "Value", "Unit", "Reference Range", "Flag"],
        ["Glucose", "5.3", "mmol/L", "3.9-5.6", "Normal"],
        ["Creatinine", "190", "umol/L", "60-110", "High"],
        ["eGFR", "38", "mL/min", "90-120", "Low"],
        ["HbA1c", "8.5", "%", "4.0-5.6", "High"],
    ]
    lab_table = Table(labs, colWidths=[36 * mm, 25 * mm, 28 * mm, 45 * mm, 24 * mm])
    lab_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    story += [Paragraph("Laboratory Results", styles["Heading2"]), lab_table]
    doc.build(story)


def _create_image_page(lines: list[str], noisy: bool = False, rotate: float = 0.0) -> Image.Image:
    width, height = 1240, 1754
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(42)
    font = _font(30)
    y = 90
    draw.text((80, y), lines[0], fill="black", font=title_font)
    y += 85
    for line in lines[1:]:
        draw.text((85, y), line, fill="black", font=font)
        y += 58
    if noisy:
        pixels = image.load()
        random.seed(42)
        for _ in range(10000):
            x = random.randrange(width)
            y = random.randrange(height)
            value = random.randrange(180, 256)
            pixels[x, y] = (value, value, value)
        image = image.filter(ImageFilter.SMOOTH_MORE)
    if rotate:
        image = image.rotate(rotate, expand=True, fillcolor="white")
    return image


def create_noisy_scan_pdf() -> None:
    lines = [
        "ADVANCED SCANNED PDF - IMAGE ONLY",
        "Patient ID: ADV-003",
        "Name: Le Van Scan",
        "DOB: 1981-12-02",
        "Gender: Male",
        "Clinical history: Asthma since childhood.",
        "Allergy: Aspirin - shortness of breath.",
        "Current medication: Insulin 10 UI before breakfast.",
        "Lab: HbA1c: 8.2 %, reference 4.0-5.6, high.",
    ]
    image = _create_image_page(lines, noisy=True)
    image.save(OUT / "advanced_003_noisy_scan.pdf", "PDF", resolution=150)


def create_rotated_scan_pdf() -> None:
    lines = [
        "ADVANCED ROTATED SCAN PDF",
        "Patient ID: ADV-004",
        "Name: Pham Thi Rotated",
        "DOB: 1990-04-15",
        "Gender: Female",
        "Clinical history: Diabetes type 2.",
        "Allergy: Seafood - urticaria.",
        "Current medication: Metformin 500mg once daily.",
        "Glucose: 10.5 mmol/L, reference 3.9-5.6, high.",
    ]
    image = _create_image_page(lines, noisy=False, rotate=3.5)
    image.save(OUT / "advanced_004_rotated_scan.pdf", "PDF", resolution=150)


def create_two_column_pdf() -> None:
    path = OUT / "advanced_005_two_column.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Advanced Two Column")
    c.setFont("Helvetica-Bold", 15)
    c.drawString(18 * mm, 280 * mm, "ADVANCED TWO-COLUMN CLINICAL SUMMARY")
    c.setFont("Helvetica", 10)
    left = [
        "Patient ID: ADV-005",
        "Name: Hoang Van Columns",
        "DOB: 1965-08-30",
        "Gender: Male",
        "Clinical history:",
        "- Hypertension since 2017.",
        "- Chronic kidney disease CKD.",
        "Allergy: Penicillin - rash.",
    ]
    right = [
        "Current medication:",
        "- Losartan 50mg once daily.",
        "- Amlodipine 5mg once daily.",
        "Laboratory results:",
        "Creatinine: 170 umol/L, reference 60-110, high.",
        "eGFR: 45 mL/min, reference 90-120, low.",
    ]
    y = 260
    for line in left:
        c.drawString(18 * mm, y * mm, line)
        y -= 8
    y = 260
    for line in right:
        c.drawString(110 * mm, y * mm, line)
        y -= 8
    c.save()


def create_mixed_text_scan_pdf() -> None:
    path = OUT / "advanced_006_mixed_text_scan.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Advanced Mixed Text Scan")
    c.setFont("Helvetica", 11)
    lines = [
        "ADVANCED MIXED PDF - PAGE 1 TEXT",
        "Patient ID: ADV-006",
        "Name: Dang Thi Mixed",
        "DOB: 1988-09-09",
        "Gender: Female",
        "Clinical history: Diabetes type 2; Hypertension.",
        "Allergy: Sulfa drug - rash.",
        "Current medication: Metformin 500mg twice daily.",
    ]
    y = 280
    for line in lines:
        c.drawString(18 * mm, y * mm, line)
        y -= 8
    c.showPage()
    image = _create_image_page([
        "PAGE 2 SCANNED LAB IMAGE",
        "Glucose: 12.1 mmol/L, reference 3.9-5.6, high.",
        "Creatinine: 135 umol/L, reference 60-110, high.",
        "HbA1c: 9.1 %, reference 4.0-5.6, high.",
    ], noisy=True)
    tmp = OUT / "_mixed_scan_page.png"
    image.save(tmp)
    c.drawImage(str(tmp), 15 * mm, 60 * mm, width=180 * mm, height=220 * mm)
    c.save()
    tmp.unlink(missing_ok=True)


def main() -> None:
    create_dense_text_pdf()
    create_grid_table_pdf()
    create_noisy_scan_pdf()
    create_rotated_scan_pdf()
    create_two_column_pdf()
    create_mixed_text_scan_pdf()
    print(f"Created advanced sample PDFs in {OUT}")


if __name__ == "__main__":
    main()
