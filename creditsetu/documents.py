"""Read the documents owners actually have: PDF or CSV bank statements, and photos of
quotations or invoices.

- PDF statements: tables are extracted with pdfplumber and passed through the same
  column matching as CSV exports. If a PDF has no ruled table, a line-by-line text
  fallback looks for "date ... amount ... balance" rows.
- Photos: on-device OCR (RapidOCR, ONNX) reads the text; we group it into rows and pull
  out the vendor, date, line items and grand total. Nothing is sent to a server.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

import pandas as pd

from .models import Transaction
from .statement import read_statement

DATE_RE = re.compile(r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b")
AMOUNT_RE = re.compile(r"(?:rs\.?|inr|₹)?\s*([0-9]{1,3}(?:[,.][0-9]{2,3})+(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)", re.I)


# ----------------------------------------------------------------- statements
def read_statement_file(name: str, data: bytes) -> list[Transaction]:
    """Read a statement from an uploaded file's name and bytes (CSV or PDF)."""
    lower = (name or "").lower()
    if lower.endswith(".pdf") or data[:4] == b"%PDF":
        return read_pdf_statement(data)
    return read_statement(data)


def read_pdf_statement(data: bytes) -> list[Transaction]:
    import pdfplumber

    header: Optional[list[str]] = None
    rows: list[list[str]] = []
    text_lines: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for raw in table:
                    cells = [(c or "").replace("\n", " ").strip() for c in raw]
                    if not any(cells):
                        continue
                    joined = " ".join(cells).lower()
                    if ("date" in joined and ("narration" in joined or "description" in joined
                                              or "particulars" in joined)):
                        header = header or cells
                        continue
                    if DATE_RE.search(cells[0] or ""):
                        rows.append(cells)
            text_lines.extend((page.extract_text() or "").splitlines())

    if header and rows:
        width = len(header)
        rows = [r[:width] + [""] * (width - len(r)) for r in rows]
        df = pd.DataFrame(rows, columns=header)
        return read_statement(df.to_csv(index=False).encode("utf-8"))
    return _statement_from_text(text_lines)


def _statement_from_text(lines: list[str]) -> list[Transaction]:
    """Fallback for PDFs without tables: 'DD-MM-YYYY narration ... amount balance'.

    Direction is inferred from the change in balance between consecutive rows.
    """
    parsed = []
    for line in lines:
        m = DATE_RE.match(line.strip())
        if not m:
            continue
        nums = [n for n in AMOUNT_RE.findall(line[m.end():]) if re.search(r"[.,]", n)]
        if len(nums) < 2:
            continue
        amount, balance = _num(nums[-2]), _num(nums[-1])
        narration = line[m.end():].split(nums[-2])[0].strip()
        parsed.append((m.group(1), narration, amount, balance))
    if not parsed:
        raise ValueError("Couldn't find any transactions in this PDF. Try the CSV export from your bank.")
    out = ["date,description,amount,type,balance"]
    prev_bal = None
    for date, narration, amount, balance in parsed:
        direction = "CR" if prev_bal is None or balance >= prev_bal else "DR"
        prev_bal = balance
        out.append(f"{date},\"{narration.replace(chr(34), '')}\",{amount},{direction},{balance}")
    return read_statement("\n".join(out).encode("utf-8"))


def _num(text: str) -> float:
    t = text.strip().lower().replace("rs", "").replace("₹", "").replace(" ", "")
    # "77.000" written with a dot as thousands separator
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    t = t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return 0.0


# ----------------------------------------------------------------- photos
@dataclass
class QuotationReading:
    vendor: str = ""
    date: str = ""
    items: list = field(default_factory=list)   # [(description, amount)]
    total: Optional[float] = None
    lines: list = field(default_factory=list)   # raw OCR lines, top to bottom
    confidence: float = 0.0


@lru_cache(maxsize=1)
def _ocr_engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


def ocr_lines(image_bytes: bytes) -> list[tuple[str, float, float, float]]:
    """Return [(text, confidence, x, y)] using on-device OCR."""
    from PIL import Image
    import numpy as np

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if max(img.size) > 2000:
        img.thumbnail((2000, 2000))
    result, _ = _ocr_engine()(np.array(img))
    out = []
    for box, text, conf in result or []:
        out.append((str(text), float(conf), float(box[0][0]), float(box[0][1])))
    return out


def _rows(lines: list[tuple[str, float, float, float]], tol: float = 28) -> list[list[tuple]]:
    rows: list[list[tuple]] = []
    for item in sorted(lines, key=lambda r: r[3]):
        if rows and abs(rows[-1][0][3] - item[3]) <= tol:
            rows[-1].append(item)
        else:
            rows.append([item])
    return [sorted(r, key=lambda i: i[2]) for r in rows]


def parse_quotation(lines: list[tuple[str, float, float, float]]) -> QuotationReading:
    reading = QuotationReading(lines=[l[0] for l in sorted(lines, key=lambda r: r[3])])
    if not lines:
        return reading
    reading.confidence = round(sum(l[1] for l in lines) / len(lines), 2)
    reading.vendor = reading.lines[0].strip()
    for text in reading.lines:
        m = DATE_RE.search(text)
        if m:
            reading.date = m.group(1)
            break

    def money(text: str) -> Optional[float]:
        if not re.search(r"rs|₹|inr|\d[,.]\d{3}", text, re.I):
            return None
        nums = [_num(n) for n in AMOUNT_RE.findall(text)]
        nums = [n for n in nums if n >= 10]
        return nums[-1] if nums else None

    for row in _rows(lines):
        texts = [r[0] for r in row]
        joined = " ".join(texts)
        amount = next((money(t) for t in reversed(texts) if money(t)), None)
        if amount is None:
            continue
        if re.search(r"total|कुल|net\s*amount|amount\s*payable", joined, re.I):
            reading.total = amount
        elif not DATE_RE.search(joined):
            desc = " ".join(t for t in texts if money(t) is None and not re.fullmatch(r"\d{1,3}", t.strip()))
            if desc:
                reading.items.append((_spaced(desc), amount))
    if reading.total is None and reading.items:
        reading.total = sum(a for _, a in reading.items)
    return reading


def _spaced(text: str) -> str:
    """OCR sometimes drops spaces ('Overlockmachine,4thread'); add them back after punctuation."""
    text = re.sub(r",(?=\S)", ", ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_quotation_image(image_bytes: bytes) -> QuotationReading:
    return parse_quotation(ocr_lines(image_bytes))
