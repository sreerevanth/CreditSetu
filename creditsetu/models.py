"""Plain data structures shared across the engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Applicant:
    """What the owner tells us about the business and the loan they need.

    ``None`` means "not answered". The scheme engine treats unanswered facts as
    "needs info" rather than guessing.

    Protected attributes (gender, social_category, area) are collected ONLY because
    some schemes are reserved by law for certain groups. They are used for scheme
    eligibility and never passed to the readiness score.
    """

    business_name: str = ""
    owner_name: str = ""
    trade: Optional[str] = None            # e.g. "tailor"; see TRADES
    sector: Optional[str] = None           # manufacturing | trading | services | allied_agriculture
    enterprise_size: Optional[str] = "micro"
    is_new_unit: Optional[bool] = None
    years_in_business: Optional[float] = None
    loan_amount: Optional[int] = None
    loan_purpose: str = ""
    age: Optional[int] = None
    has_default: Optional[bool] = None
    udyam_registered: Optional[bool] = None
    prior_tarun_repaid: Optional[bool] = None
    vishwakarma_trained: Optional[bool] = None
    prior_scheme_loan: Optional[bool] = None
    # Used for scheme eligibility only, never for scoring:
    gender: Optional[str] = None           # female | male | other
    social_category: Optional[str] = None  # general | obc | sc | st
    area: Optional[str] = None             # urban | rural
    district: str = ""
    state: str = ""

    def as_facts(self) -> dict:
        return asdict(self)


@dataclass
class Transaction:
    date: "object"        # datetime.date
    description: str
    amount: float         # always positive
    direction: str        # "CR" (money in) or "DR" (money out)
    mode: str             # UPI | NEFT | IMPS | CASH | ATM | CHEQUE | OTHER
    counterparty: str = ""
    balance: Optional[float] = None


@dataclass
class CashFlowProfile:
    months: int
    start: str
    end: str
    avg_monthly_inflow: float
    avg_monthly_outflow: float
    avg_monthly_surplus: float
    inflow_cv: float                 # coefficient of variation of monthly inflows
    avg_payers_per_month: float
    digital_share: float             # share of inflow value that arrived digitally
    bounced_count: int
    peak_months: list
    low_months: list
    monthly: list = field(default_factory=list)   # [{"month": "2026-01", "inflow": .., "outflow": ..}]


@dataclass
class CriterionResult:
    text: str
    status: str            # "pass" | "fail" | "unknown"
    source_title: str
    source_url: str
    fix: str = ""


@dataclass
class SchemeResult:
    scheme_id: str
    scheme: str
    name: str
    kind: str              # loan | guarantee
    status: str            # eligible | needs_info | not_fit
    summary: str
    benefit: str
    apply_via: str
    criteria: list
    covers_amount: Optional[int] = None
    indicative_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    status_note: str = ""


@dataclass
class ScoreFactor:
    name: str
    points: float
    max_points: float
    measured: str          # what we measured, in plain words
    improve: str = ""      # how to improve it, if it isn't maxed


@dataclass
class ReadinessScore:
    total: int
    band: str
    factors: list
    emi: float
    emi_to_surplus: Optional[float]
    calibrated: bool = False
