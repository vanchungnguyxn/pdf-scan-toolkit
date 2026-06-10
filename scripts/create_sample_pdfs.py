from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "pdf_samples"
OUT.mkdir(parents=True, exist_ok=True)


def draw_lines(c: canvas.Canvas, lines: list[str], x: int = 20, y_start: int = 280, line_gap: int = 8) -> None:
    y = y_start
    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(x * mm, y * mm, line)
        y -= line_gap
        if y < 20:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = y_start


def create_text_pdf() -> None:
    path = OUT / "patient_001_text.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Patient 001 Text PDF")
    lines = [
        "CLINICAL NOTE - TEXT PDF",
        "Ma benh nhan: PT-001",
        "Ho ten: Nguyen Van A",
        "Ngay sinh: 1968-03-12",
        "Gioi tinh: Nam",
        "",
        "Tien su benh:",
        "- Tang huyet ap tu nam 2020, dang dieu tri on dinh.",
        "- Dai thao duong type 2 tu nam 2021.",
        "",
        "Di ung:",
        "- Di ung Penicillin, phan ung noi man do.",
        "",
        "Thuoc dang dung:",
        "- Metformin 500mg, uong 2 lan/ngay.",
        "- Amlodipine 5mg, uong 1 lan/ngay.",
        "",
        "Xet nghiem:",
        "Glucose: 9.8 mmol/L, tham chieu 3.9-5.6, cao.",
        "Creatinine: 150 umol/L, tham chieu 60-110, cao.",
    ]
    draw_lines(c, lines)
    c.save()


def create_table_pdf() -> None:
    path = OUT / "patient_002_table.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("LAB AND MEDICATION PDF - TABLE LAYOUT", styles["Title"]))
    story.append(Paragraph("Ma benh nhan: PT-002", styles["Normal"]))
    story.append(Paragraph("Ho ten: Tran Thi B", styles["Normal"]))
    story.append(Paragraph("Ngay sinh: 1975-07-20", styles["Normal"]))
    story.append(Paragraph("Gioi tinh: Nu", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Tien su benh: Tang huyet ap; Suy than man tinh CKD stage 3.", styles["Normal"]))
    story.append(Paragraph("Di ung: Khong ghi nhan di ung thuoc trong ho so nay.", styles["Normal"]))
    story.append(Spacer(1, 12))

    med_data = [
        ["Medication", "Dose", "Frequency", "Status"],
        ["Losartan", "50mg", "1 lan/ngay", "active"],
        ["Atorvastatin", "20mg", "1 lan toi", "active"],
    ]
    med_table = Table(med_data, colWidths=[45*mm, 35*mm, 45*mm, 35*mm])
    med_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    story.append(Paragraph("Thuoc dang dung", styles["Heading2"]))
    story.append(med_table)
    story.append(Spacer(1, 12))

    lab_data = [
        ["Test", "Value", "Unit", "Reference Range", "Flag"],
        ["Glucose", "5.2", "mmol/L", "3.9-5.6", "Normal"],
        ["Creatinine", "180", "umol/L", "60-110", "High"],
        ["eGFR", "42", "mL/min", "90-120", "Low"],
    ]
    lab_table = Table(lab_data, colWidths=[35*mm, 25*mm, 25*mm, 45*mm, 25*mm])
    lab_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    story.append(Paragraph("Ket qua xet nghiem", styles["Heading2"]))
    story.append(lab_table)
    doc.build(story)


def create_scanned_image_pdf() -> None:
    # Image-only PDF: no text layer. This simulates a scanned EMR PDF.
    img_path = OUT / "patient_003_scanned_image_page.png"
    pdf_path = OUT / "patient_003_scanned_image.pdf"
    width, height = 1240, 1754  # approx A4 at 150dpi
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 32)
        title_font = ImageFont.truetype("DejaVuSans.ttf", 42)
    except Exception:
        font = ImageFont.load_default()
        title_font = font
    lines = [
        "SCANNED CLINICAL NOTE - IMAGE ONLY PDF",
        "Ma benh nhan: PT-003",
        "Ho ten: Le Van C",
        "Ngay sinh: 1980-11-02",
        "Gioi tinh: Nam",
        "Tien su benh: Hen phe quan.",
        "Di ung: Di ung Aspirin, kho tho.",
        "Thuoc dang dung: Insulin 10 UI truoc bua sang.",
        "Xet nghiem: HbA1c: 8.2 %, tham chieu 4.0-5.6, cao.",
    ]
    y = 100
    draw.text((80, y), lines[0], fill="black", font=title_font)
    y += 90
    for line in lines[1:]:
        draw.text((90, y), line, fill="black", font=font)
        y += 62
    image.save(img_path)
    image.save(pdf_path, "PDF", resolution=150)
    img_path.unlink(missing_ok=True)


def create_mixed_pdf() -> None:
    path = OUT / "patient_004_mixed.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Patient 004 Mixed PDF")
    lines = [
        "MIXED PDF - PAGE 1 HAS TEXT LAYER",
        "Ma benh nhan: PT-004",
        "Ho ten: Pham Thi D",
        "Ngay sinh: 1990-04-15",
        "Gioi tinh: Nu",
        "Tien su benh: Dai thao duong thai ky nam 2024.",
        "Di ung: Di ung hai san, noi me day.",
        "Thuoc dang dung:",
        "- Metformin 500mg, uong 1 lan/ngay.",
    ]
    draw_lines(c, lines)
    c.showPage()

    # Page 2 is an embedded image, so page 2 has no text layer.
    width, height = 900, 600
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    draw.text((40, 50), "PAGE 2 SCANNED LAB IMAGE", fill="black", font=font)
    draw.text((40, 120), "Glucose: 10.5 mmol/L, tham chieu 3.9-5.6, cao.", fill="black", font=font)
    tmp = OUT / "_mixed_page2.png"
    image.save(tmp)
    c.drawImage(str(tmp), 20*mm, 150*mm, width=170*mm, height=110*mm)
    c.save()
    tmp.unlink(missing_ok=True)


def main() -> None:
    create_text_pdf()
    create_table_pdf()
    create_scanned_image_pdf()
    create_mixed_pdf()
    print(f"Created sample PDFs in {OUT}")


if __name__ == "__main__":
    main()
