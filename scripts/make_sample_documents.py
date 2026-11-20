"""Generate demo documents from the synthetic data: a bank-style PDF statement and a
photographed-looking quotation for sewing machines. Everything is fictional.

Run:  python scripts/make_sample_documents.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DATA = Path(__file__).resolve().parent.parent / "data"
CSV_IN = DATA / "sample_statement_sunita.csv"
PDF_OUT = DATA / "sample_statement_sunita.pdf"
IMG_OUT = DATA / "sample_quotation_photo.jpg"


def make_pdf() -> Path:
    with open(CSV_IN, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(PDF_OUT), pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Account statement (synthetic demo)")
    story = [
        Paragraph("<b>Demo Co-operative Bank</b> &nbsp; (fictional, for CreditSetu demo only)", styles["Title"]),
        Paragraph("Statement of account · Savings · A/c XXXXXX4821 · Sunita Tailoring Works", styles["Normal"]),
        Paragraph("Period: 01-09-2025 to 31-10-2026 · Branch: Bhilwara", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]
    table = [["Date", "Narration", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"]]
    for r in rows:
        amt = f"{float(r['amount']):,.2f}"
        table.append([r["date"], r["description"][:52],
                      amt if r["type"] == "DR" else "", amt if r["type"] == "CR" else "",
                      f"{float(r['balance']):,.2f}"])
    t = Table(table, colWidths=[22 * mm, 88 * mm, 25 * mm, 25 * mm, 26 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 7),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16233F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]))
    story.append(t)
    doc.build(story)
    return PDF_OUT


def _font(size: int, bold: bool = False):
    candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def make_quotation_photo() -> Path:
    rng = random.Random(3)
    w, h = 1100, 1400
    img = Image.new("RGB", (w, h), (250, 248, 240))
    d = ImageDraw.Draw(img)
    y = 70
    d.text((70, y), "SHREE SAI SEWING MACHINE CO.", font=_font(44, True), fill=(20, 20, 60)); y += 60
    d.text((70, y), "Station Road, Bhilwara · Ph 98XXXXXX10", font=_font(26), fill=(60, 60, 60)); y += 50
    d.line((70, y, w - 70, y), fill=(40, 40, 40), width=3); y += 30
    d.text((70, y), "QUOTATION", font=_font(38, True), fill=(20, 20, 20))
    d.text((w - 420, y + 6), "Date: 14-11-2026", font=_font(28), fill=(20, 20, 20)); y += 70
    d.text((70, y), "To: Sunita Tailoring Works", font=_font(28), fill=(20, 20, 20)); y += 70
    items = [("Industrial lockstitch sewing machine", 2, 38500),
             ("Overlock machine, 4 thread", 1, 26000),
             ("Motor, table and stand (set)", 3, 4500),
             ("Installation and training", 1, 2500)]
    d.text((70, y), "Item", font=_font(28, True), fill=(20, 20, 20))
    d.text((640, y), "Qty", font=_font(28, True), fill=(20, 20, 20))
    d.text((820, y), "Amount", font=_font(28, True), fill=(20, 20, 20)); y += 50
    total = 0
    for name, qty, rate in items:
        amount = qty * rate
        total += amount
        d.text((70, y), name, font=_font(26), fill=(30, 30, 30))
        d.text((655, y), str(qty), font=_font(26), fill=(30, 30, 30))
        d.text((820, y), f"Rs {amount:,}", font=_font(26), fill=(30, 30, 30)); y += 48
    y += 20
    d.line((560, y, w - 70, y), fill=(40, 40, 40), width=2); y += 25
    d.text((560, y), "Grand Total", font=_font(32, True), fill=(20, 20, 20))
    d.text((820, y), f"Rs {total:,}", font=_font(32, True), fill=(20, 20, 20)); y += 90
    d.text((70, y), "Valid for 30 days. GST extra as applicable.", font=_font(24), fill=(70, 70, 70))
    d.text((w - 360, h - 160), "For Shree Sai Sewing", font=_font(24), fill=(70, 70, 70))

    # Make it look photographed: slight rotation, blur, uneven light.
    img = img.rotate(rng.uniform(-2.0, 2.0), expand=True, fillcolor=(205, 195, 175))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    shade = Image.new("L", img.size, 0)
    ImageDraw.Draw(shade).ellipse((-300, -300, img.size[0] + 200, img.size[1] + 400), fill=40)
    img = Image.composite(img, Image.new("RGB", img.size, (180, 170, 150)), Image.eval(shade, lambda v: 255 - v // 2))
    img.save(IMG_OUT, quality=82)
    return IMG_OUT


if __name__ == "__main__":
    print("Wrote", make_pdf())
    print("Wrote", make_quotation_photo())
