"""Read bank or UPI statements into a list of Transactions.

Supports two layouts:

1. CreditSetu's simple CSV: ``date, description, amount, type (CR/DR), mode, counterparty, balance``
2. A common Indian bank export: ``Date, Narration, Withdrawal Amt., Deposit Amt., Closing Balance``
   (column names are matched loosely, so similar exports work too)
"""

from __future__ import annotations

import io
import re
from typing import IO, Union

import pandas as pd

from .models import Transaction

_MODE_PATTERNS = [
    ("UPI", re.compile(r"\bUPI\b", re.I)),
    ("NEFT", re.compile(r"\bNEFT\b", re.I)),
    ("IMPS", re.compile(r"\bIMPS\b", re.I)),
    ("ATM", re.compile(r"\bATM\b|\bATW\b|CASH ?WDL|NWD", re.I)),
    ("CASH", re.compile(r"CASH ?DEP|\bBY CASH\b|\bCDM\b", re.I)),
    ("CHEQUE", re.compile(r"\bCHQ\b|CHEQUE|\bCLG\b", re.I)),
]

BOUNCE_PATTERN = re.compile(r"RETURN|BOUNCE|INSUFF|REVERSAL|DISHONOU?R|ECS RTN|NACH RTN", re.I)


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", str(name).lower())


def _find(columns, *candidates):
    normalized = {_norm(c): c for c in columns}
    for cand in candidates:
        for key, original in normalized.items():
            if cand in key:
                return original
    return None


def detect_mode(text: str) -> str:
    for mode, pattern in _MODE_PATTERNS:
        if pattern.search(text or ""):
            return mode
    return "OTHER"


def _counterparty_from_narration(text: str) -> str:
    """Best-effort payer/payee name from a narration like 'UPI/CR/123456/RAVI KUMAR/okaxis'."""
    parts = [p.strip() for p in re.split(r"[/-]", text or "") if p.strip()]
    for part in parts:
        if re.search(r"[A-Za-z]{3,}", part) and part.upper() not in {"UPI", "CR", "DR", "NEFT", "IMPS", "P2A", "P2M"}:
            return part.title()
    return ""


def _to_number(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    text = str(value).replace(",", "").replace("₹", "").strip()
    if text in {"", "-", "nan", "None"}:
        return 0.0
    return float(text)


def read_statement(source: Union[str, bytes, IO]) -> list[Transaction]:
    """Read a CSV statement from a path, raw bytes or a file-like object."""
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    df = pd.read_csv(source)
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns

    date_col = _find(cols, "date", "txndate", "valuedate")
    desc_col = _find(cols, "description", "narration", "particulars", "remarks", "details")
    if date_col is None or desc_col is None:
        raise ValueError("Couldn't find a date and a description/narration column in this statement.")

    amount_col = _find(cols, "amount")
    type_col = _find(cols, "type", "drcr", "crdr")
    debit_col = _find(cols, "withdrawal", "debit")
    credit_col = _find(cols, "deposit", "credit")
    mode_col = _find(cols, "mode", "channel")
    party_col = _find(cols, "counterparty", "payee", "payer", "name")
    bal_col = _find(cols, "balance")

    txns: list[Transaction] = []
    for _, row in df.iterrows():
        date = pd.to_datetime(row[date_col], dayfirst=True, errors="coerce")
        if pd.isna(date):
            continue
        desc = str(row[desc_col])

        if amount_col is not None and type_col is not None:
            amount = abs(_to_number(row[amount_col]))
            direction = "CR" if str(row[type_col]).strip().upper().startswith("C") else "DR"
        elif debit_col is not None or credit_col is not None:
            cr = _to_number(row[credit_col]) if credit_col is not None else 0.0
            dr = _to_number(row[debit_col]) if debit_col is not None else 0.0
            if cr > 0:
                amount, direction = cr, "CR"
            elif dr > 0:
                amount, direction = dr, "DR"
            else:
                continue
        elif amount_col is not None:
            value = _to_number(row[amount_col])
            amount, direction = abs(value), ("CR" if value >= 0 else "DR")
        else:
            raise ValueError("Couldn't find amount columns (amount + type, or withdrawal/deposit).")

        if amount == 0:
            continue

        mode = str(row[mode_col]).strip().upper() if mode_col is not None and pd.notna(row[mode_col]) else detect_mode(desc)
        party = str(row[party_col]).strip() if party_col is not None and pd.notna(row[party_col]) else _counterparty_from_narration(desc)
        balance = _to_number(row[bal_col]) if bal_col is not None else None

        txns.append(Transaction(date=date.date(), description=desc, amount=amount,
                                direction=direction, mode=mode, counterparty=party, balance=balance))

    if not txns:
        raise ValueError("No transactions found in this statement.")
    txns.sort(key=lambda t: t.date)
    return txns
