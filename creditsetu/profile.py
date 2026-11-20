"""Turn transactions into a cash-flow profile a lender (and the owner) can understand."""

from __future__ import annotations

import calendar
from collections import defaultdict
from statistics import mean, pstdev

from .models import CashFlowProfile, Transaction
from .statement import BOUNCE_PATTERN

DIGITAL_MODES = {"UPI", "NEFT", "IMPS", "CHEQUE"}


def build_profile(txns: list[Transaction]) -> CashFlowProfile:
    inflow = defaultdict(float)
    outflow = defaultdict(float)
    payers = defaultdict(set)
    digital_in = 0.0
    total_in = 0.0
    bounced = 0

    for t in txns:
        key = f"{t.date.year:04d}-{t.date.month:02d}"
        inflow.setdefault(key, 0.0)
        outflow.setdefault(key, 0.0)
        if BOUNCE_PATTERN.search(t.description):
            bounced += 1
        if t.direction == "CR":
            inflow[key] += t.amount
            total_in += t.amount
            if t.mode in DIGITAL_MODES:
                digital_in += t.amount
            if t.counterparty:
                payers[key].add(t.counterparty.lower())
        else:
            outflow[key] += t.amount

    months = sorted(inflow.keys())
    monthly = [{"month": m, "inflow": round(inflow[m], 2), "outflow": round(outflow[m], 2)} for m in months]
    inflows = [inflow[m] for m in months]
    outflows = [outflow[m] for m in months]
    avg_in = mean(inflows) if inflows else 0.0
    avg_out = mean(outflows) if outflows else 0.0
    cv = (pstdev(inflows) / avg_in) if avg_in > 0 and len(inflows) > 1 else 1.0

    # Seasonality: average inflow by calendar month, then the top and bottom two.
    by_cal = defaultdict(list)
    for m in months:
        by_cal[int(m[5:7])].append(inflow[m])
    cal_avg = sorted(((mean(v), k) for k, v in by_cal.items()), reverse=True)
    peak = [calendar.month_name[k] for _, k in cal_avg[:2]]
    low = [calendar.month_name[k] for _, k in cal_avg[-2:]][::-1]

    return CashFlowProfile(
        months=len(months),
        start=months[0] if months else "",
        end=months[-1] if months else "",
        avg_monthly_inflow=round(avg_in, 2),
        avg_monthly_outflow=round(avg_out, 2),
        avg_monthly_surplus=round(avg_in - avg_out, 2),
        inflow_cv=round(cv, 3),
        avg_payers_per_month=round(mean(len(payers[m]) for m in months), 1) if months else 0.0,
        digital_share=round(digital_in / total_in, 3) if total_in else 0.0,
        bounced_count=bounced,
        peak_months=peak,
        low_months=low,
        monthly=monthly,
    )
