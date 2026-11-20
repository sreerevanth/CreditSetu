"""Synthetic bank statements for demos and the seeded bank-officer queue.

Everything generated here is fictional. Each business type has its own rhythm:
how much comes in, how seasonal it is, how much arrives as cash, and what goes out.
"""

from __future__ import annotations

import io
import csv
import random
from dataclasses import dataclass, field
from datetime import date, timedelta

FIRST = ["Ravi", "Pooja", "Anita", "Meena", "Kavita", "Suresh", "Rekha", "Sunil", "Asha", "Neha",
         "Geeta", "Rahul", "Priya", "Lata", "Ramesh", "Sita", "Vijay", "Usha", "Deepa", "Manoj",
         "Savita", "Arjun", "Nisha", "Kiran", "Shobha", "Ajay", "Rani", "Mohan", "Seema", "Gopal"]
LAST = ["Kumar", "Sharma", "Verma", "Yadav", "Patel", "Singh", "Gupta", "Devi", "Jain", "Mishra",
        "Reddy", "Nair", "Das", "Khan", "Pillai"]
BANKS = ["okaxis", "oksbi", "ybl", "okhdfcbank", "paytm", "ibl"]


@dataclass
class BusinessRhythm:
    base_inflow: float = 60000
    season: dict = field(default_factory=lambda: {m: 1.0 for m in range(1, 13)})
    cash_share: float = 0.15
    ticket_sizes: tuple = (250, 400, 600, 900, 1200, 1800, 2500, 3500)
    n_customers: int = 150
    supplier: str = "Main Supplier"
    supplier_share: float = 0.30
    rent: float = 6000
    wages: float = 12000
    household: tuple = (2500, 3500)
    existing_emi: float = 0
    bounces: int = 0
    noise: float = 0.05
    months: int = 12


def _month_starts(start: date, count: int):
    y, m = start.year, start.month
    for _ in range(count):
        yield date(y, m, 1)
        m += 1
        if m == 13:
            y, m = y + 1, 1


def _days(d: date) -> int:
    nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return (nxt - timedelta(days=1)).day


def generate_statement(r: BusinessRhythm, *, months: int = 12, start: date = date(2025, 11, 1),
                       seed: int = 1, opening: float = 10000) -> bytes:
    rng = random.Random(seed)
    customers = [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in range(r.n_customers)]
    rows, balance = [], opening
    bounce_months = set(rng.sample(range(months), min(r.bounces, months)))

    for i, ms in enumerate(_month_starts(start, months)):
        n = _days(ms)
        target = r.base_inflow * r.season.get(ms.month, 1.0) * rng.uniform(1 - r.noise, 1 + r.noise)
        cash, digital = target * r.cash_share, target * (1 - r.cash_share)
        month = []
        got = 0.0
        while got < digital:
            amt = round(rng.choice(r.ticket_sizes) * rng.uniform(0.9, 1.1))
            name = rng.choice(customers)
            vpa = f"{name.split()[0].lower()}{rng.randint(10, 99)}@{rng.choice(BANKS)}"
            month.append((ms.replace(day=rng.randint(1, n)), f"UPI/CR/{rng.randint(10**11, 10**12 - 1)}/{name.upper()}/{vpa}",
                          amt, "CR", "UPI", name))
            got += amt
        for d in (7, 14, 21, 28):
            month.append((ms.replace(day=min(d, n)), "CASH DEPOSIT BY SELF", round(cash / 4, -1), "CR", "CASH", ""))

        sup = target * r.supplier_share
        month.append((ms.replace(day=3), f"UPI/DR/{r.supplier.upper()}", round(sup * 0.5, -1), "DR", "UPI", r.supplier))
        month.append((ms.replace(day=17), f"UPI/DR/{r.supplier.upper()}", round(sup * 0.5, -1), "DR", "UPI", r.supplier))
        if r.rent:
            month.append((ms.replace(day=5), "UPI/DR/SHOP RENT", r.rent, "DR", "UPI", "Landlord"))
        if r.wages:
            month.append((ms.replace(day=1), "ATM CASH WDL wages", r.wages / 2, "DR", "ATM", ""))
            month.append((ms.replace(day=15), "ATM CASH WDL wages", r.wages / 2, "DR", "ATM", ""))
        month.append((ms.replace(day=10), "UPI/DR/ELECTRICITY BILL", round(rng.uniform(900, 2200), -1), "DR", "UPI", "Electricity Board"))
        month.append((ms.replace(day=min(25, n)), "UPI/DR/HOUSEHOLD/KIRANA", round(rng.uniform(*r.household), -1), "DR", "UPI", "Kirana"))
        if r.existing_emi:
            month.append((ms.replace(day=8), "NACH DR LOAN EMI", r.existing_emi, "DR", "OTHER", "Lender"))
            if i in bounce_months:
                month.append((ms.replace(day=8), "NACH RTN INSUFFICIENT FUNDS CHG", 590, "DR", "OTHER", "Lender"))

        month.sort(key=lambda x: (x[0], x[3] == "DR"))
        for d, desc, amt, typ, mode, party in month:
            balance += amt if typ == "CR" else -amt
            rows.append([d.strftime("%d-%m-%Y"), desc, f"{amt:.2f}", typ, mode, party, f"{balance:.2f}"])

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "description", "amount", "type", "mode", "counterparty", "balance"])
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


WEDDING = {1: 1.05, 2: 1.1, 3: 0.95, 4: 1.0, 5: 1.05, 6: 0.88, 7: 0.78, 8: 0.82, 9: 0.95, 10: 1.2, 11: 1.22, 12: 1.08}
FLAT = {m: 1.0 for m in range(1, 13)}
DAIRY = {1: 1.1, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.85, 6: 0.85, 7: 0.95, 8: 1.0, 9: 1.0, 10: 1.05, 11: 1.1, 12: 1.1}
HARVEST = {1: 0.9, 2: 0.9, 3: 1.2, 4: 1.3, 5: 1.0, 6: 0.8, 7: 0.7, 8: 0.75, 9: 0.9, 10: 1.25, 11: 1.3, 12: 1.0}
