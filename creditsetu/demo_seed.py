"""Seed the bank-officer queue with fictional, owner-approved files so the dashboard
looks like a real Monday morning. Every file runs through the real engine."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from . import store
from .case import build_package, submission_kwargs
from .models import Applicant
from .statement import read_statement
from .synthetic import DAIRY, FLAT, HARVEST, WEDDING, BusinessRhythm, generate_statement

SUNITA_CSV = Path(__file__).resolve().parent.parent / "data" / "sample_statement_sunita.csv"

DEMO_CASES = [
    # (applicant, rhythm, have_docs, status, note, days_ago)
    (Applicant(business_name="Sunita Tailoring Works", owner_name="Sunita", trade="tailor", sector="manufacturing",
               is_new_unit=False, years_in_business=4, loan_amount=300000, age=34, has_default=False,
               udyam_registered=False, vishwakarma_trained=True, prior_scheme_loan=False,
               loan_purpose="Two sewing machines and fabric stock before wedding season",
               district="Bhilwara", state="Rajasthan"),
     None, {"aadhaar", "pan", "bank_statement", "quotation"}, "under_review",
     "Cash flow looks steady. Please complete Udyam registration; we can then proceed.", 2),
    (Applicant(business_name="Patel Fabrication", owner_name="Ramesh Patel", trade="fabrication", sector="manufacturing",
               is_new_unit=False, years_in_business=7, loan_amount=650000, age=41, has_default=False,
               udyam_registered=True, loan_purpose="Welding machine and working capital",
               district="Rajkot", state="Gujarat"),
     BusinessRhythm(base_inflow=145000, season=FLAT, cash_share=0.10, ticket_sizes=(2500, 4000, 6500, 9000, 15000),
                    n_customers=60, supplier="Steel Traders", supplier_share=0.42, rent=12000, wages=30000,
                    household=(5000, 7000)),
     {"aadhaar", "pan", "bank_statement", "business_proof", "udyam", "quotation", "photo"}, "sanctioned",
     "Sanctioned under MUDRA Tarun. Visit the branch to sign documents.", 9),
    (Applicant(business_name="Lakshmi Dairy", owner_name="Lakshmi Devi", trade="dairy", sector="allied_agriculture",
               is_new_unit=False, years_in_business=3, loan_amount=350000, age=38, has_default=False,
               udyam_registered=True, loan_purpose="Two milch animals and a chaff cutter",
               district="Karnal", state="Haryana"),
     BusinessRhythm(base_inflow=52000, season=DAIRY, cash_share=0.55, ticket_sizes=(3000, 4500, 6000, 9000),
                    n_customers=14, supplier="Cattle Feed Depot", supplier_share=0.45, rent=0, wages=6000),
     {"aadhaar", "pan", "bank_statement", "udyam"}, "documents_requested",
     "Please share the quotation for the animals and a photograph.", 5),
    (Applicant(business_name="Anand Mobile Repairs", owner_name="Anand Kumar", trade="repair_shop", sector="services",
               is_new_unit=False, years_in_business=2, loan_amount=150000, age=27, has_default=False,
               udyam_registered=False, loan_purpose="Testing equipment and spare parts stock",
               district="Patna", state="Bihar"),
     BusinessRhythm(base_inflow=48000, season=FLAT, cash_share=0.20, ticket_sizes=(200, 350, 500, 800, 1500),
                    n_customers=120, supplier="Spares Wholesale", supplier_share=0.35, rent=5000, wages=8000,
                    existing_emi=3200, bounces=2, noise=0.25, months=7),
     {"aadhaar", "pan", "bank_statement"}, "received", "", 0),
    (Applicant(business_name="Meena Kirana Store", owner_name="Meena Reddy", trade="kirana", sector="trading",
               is_new_unit=False, years_in_business=6, loan_amount=400000, age=45, has_default=False,
               udyam_registered=True, loan_purpose="Stock for festive season and a refrigerator",
               district="Guntur", state="Andhra Pradesh"),
     BusinessRhythm(base_inflow=118000, season=HARVEST, cash_share=0.25, ticket_sizes=(80, 150, 250, 400, 700, 1200),
                    n_customers=220, supplier="FMCG Distributor", supplier_share=0.66, rent=7000, wages=6000),
     {"aadhaar", "pan", "bank_statement", "udyam", "business_proof"}, "received", "", 1),
    (Applicant(business_name="Gopal Salon", owner_name="Gopal Nai", trade="barber", sector="services",
               is_new_unit=False, years_in_business=10, loan_amount=100000, age=36, has_default=False,
               udyam_registered=False, vishwakarma_trained=True, prior_scheme_loan=False,
               loan_purpose="New chairs and equipment", district="Varanasi", state="Uttar Pradesh"),
     BusinessRhythm(base_inflow=38000, season=WEDDING, cash_share=0.40, ticket_sizes=(80, 120, 200, 350, 600),
                    n_customers=200, supplier="Salon Supplies", supplier_share=0.12, rent=4000, wages=7000),
     {"aadhaar", "pan", "bank_statement"}, "under_review", "PM Vishwakarma route looks right; verifying training certificate.", 3),
]


def seed(path: Optional[Path] = None, force: bool = False) -> int:
    """Insert the demo files if the store is empty (or ``force``). Returns files added."""
    if store.count(path) and not force:
        return 0
    if force:
        store.reset(path)
    rng = random.Random(42)
    added = 0
    for i, (applicant, rhythm, have, status, note, days) in enumerate(DEMO_CASES):
        if rhythm is None:
            txns = read_statement(SUNITA_CSV)
        else:
            txns = read_statement(generate_statement(rhythm, months=rhythm.months, seed=100 + i))
        pkg = build_package(applicant, txns, have)
        ref = store.submit(**submission_kwargs(pkg), source="demo", path=path, ref=store.new_ref(rng))
        store.backdate(ref, days, path)
        if status != "received":
            if status != "under_review":
                store.update_status(ref, "under_review", "Picked up for review.", path=path)
            store.update_status(ref, status, note, path=path)
        added += 1
    return added
