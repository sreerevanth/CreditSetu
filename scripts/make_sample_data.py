"""Generate a synthetic 14-month bank statement for the demo persona, Sunita.

Everything here is made up. The numbers are shaped to look like a small tailoring
unit: many small UPI payments from customers, a festive/wedding peak, a monsoon dip,
regular payments to a fabric supplier, rent and helpers' wages.

Run:  python scripts/make_sample_data.py
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "sample_statement_sunita.csv"

SEASON = {1: 1.05, 2: 1.10, 3: 0.95, 4: 1.00, 5: 1.05, 6: 0.88, 7: 0.78,
          8: 0.82, 9: 0.95, 10: 1.20, 11: 1.22, 12: 1.08}
BASE_INFLOW = 64000

FIRST = ["Ravi", "Pooja", "Anita", "Meena", "Kavita", "Suresh", "Rekha", "Sunil", "Asha", "Neha",
         "Geeta", "Rahul", "Priya", "Lata", "Ramesh", "Sita", "Vijay", "Usha", "Deepa", "Manoj",
         "Savita", "Arjun", "Nisha", "Kiran", "Shobha", "Ajay", "Rani", "Mohan", "Seema", "Gopal"]
LAST = ["Kumar", "Sharma", "Verma", "Yadav", "Patel", "Singh", "Gupta", "Devi", "Jain", "Mishra"]
BANKS = ["okaxis", "oksbi", "ybl", "okhdfcbank", "paytm", "ibl"]


def month_starts(start: date, count: int):
    y, m = start.year, start.month
    for _ in range(count):
        yield date(y, m, 1)
        m += 1
        if m == 13:
            y, m = y + 1, 1


def days_in_month(d: date) -> int:
    nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return (nxt - timedelta(days=1)).day


def main(seed: int = 7) -> Path:
    rng = random.Random(seed)
    customers = [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in range(160)]
    rows = []
    balance = 12500.0

    for ms in month_starts(date(2025, 9, 1), 14):
        n_days = days_in_month(ms)
        target_in = BASE_INFLOW * SEASON[ms.month] * rng.uniform(0.95, 1.05)
        cash_part = target_in * 0.14
        upi_part = target_in - cash_part
        month_rows = []

        # Many small UPI receipts from customers
        received = 0.0
        while received < upi_part:
            amt = round(rng.choice([250, 350, 450, 600, 800, 950, 1200, 1500, 1800, 2200, 2800, 3500]) * rng.uniform(0.9, 1.1))
            name = rng.choice(customers)
            day = rng.randint(1, n_days)
            vpa = f"{name.split()[0].lower()}{rng.randint(10, 99)}@{rng.choice(BANKS)}"
            month_rows.append((ms.replace(day=day), f"UPI/CR/{rng.randint(10**11, 10**12 - 1)}/{name.upper()}/{vpa}",
                               amt, "CR", "UPI", name))
            received += amt

        # Weekly cash deposits
        for week_day in (7, 14, 21, 28):
            if week_day <= n_days:
                amt = round(cash_part / 4, -1)
                month_rows.append((ms.replace(day=week_day), "CASH DEPOSIT BY SELF", amt, "CR", "CASH", ""))

        # Outflows
        fabric_total = target_in * 0.27
        for d, share in ((3, 0.45), (16, 0.55)):
            month_rows.append((ms.replace(day=d), "UPI/DR/SHREE GANESH TEXTILES/fabric", round(fabric_total * share, -1), "DR", "UPI", "Shree Ganesh Textiles"))
        month_rows.append((ms.replace(day=5), "UPI/DR/SHOP RENT/RAMESH AGARWAL", 6000, "DR", "UPI", "Ramesh Agarwal"))
        month_rows.append((ms.replace(day=10), "UPI/DR/BHARAT ELECTRICITY BILL", round(rng.uniform(1100, 1900), -1), "DR", "UPI", "Electricity Board"))
        month_rows.append((ms.replace(day=1), "ATM CASH WDL helpers wages", 6000, "DR", "ATM", ""))
        month_rows.append((ms.replace(day=15), "ATM CASH WDL helpers wages", 6000, "DR", "ATM", ""))
        month_rows.append((ms.replace(day=12), "UPI/DR/JIO PREPAID RECHARGE", 299, "DR", "UPI", "Jio"))
        month_rows.append((ms.replace(day=min(20, n_days)), "UPI/DR/THREAD AND BUTTONS/LAXMI STORES", round(rng.uniform(900, 1600), -1), "DR", "UPI", "Laxmi Stores"))
        month_rows.append((ms.replace(day=min(25, n_days)), "UPI/DR/HOUSEHOLD/KIRANA", round(rng.uniform(2500, 3500), -1), "DR", "UPI", "Kirana"))

        month_rows.sort(key=lambda r: (r[0], r[3] == "DR"))
        for d, desc, amt, typ, mode, party in month_rows:
            balance += amt if typ == "CR" else -amt
            rows.append([d.strftime("%d-%m-%Y"), desc, f"{amt:.2f}", typ, mode, party, f"{balance:.2f}"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "description", "amount", "type", "mode", "counterparty", "balance"])
        w.writerows(rows)
    return OUT


if __name__ == "__main__":
    path = main()
    print(f"Wrote {path}")
