"""Explainable loan-readiness score (0–100), in English or Hindi.

Fairness by construction: ``readiness_score`` only accepts cash-flow metrics,
registration status and a declared-default flag. It has no way to see gender,
caste category, religion or region. ``tests/test_fairness.py`` checks this.

The weights are judgement-based and NOT yet calibrated on repayment outcomes;
the result says so (``calibrated=False``).
"""

from __future__ import annotations

from typing import Optional

from .models import CashFlowProfile, ReadinessScore, ScoreFactor

MONTHS_HI = {"January": "जनवरी", "February": "फ़रवरी", "March": "मार्च", "April": "अप्रैल", "May": "मई",
             "June": "जून", "July": "जुलाई", "August": "अगस्त", "September": "सितंबर",
             "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर"}

TXT = {
    "en": {
        "stability": "Income stability",
        "stability_m": "Monthly income varies by about {cv}% around its average (busiest: {peak}; slowest: {low}).",
        "stability_i": "Steadier monthly income helps. Plan EMI dates after your busy months, and keep some savings for slow months.",
        "track": "Track record",
        "track_m": "{m} months of statement history.",
        "track_i": "Share a longer statement (12 months or more) if you have one.",
        "repay": "Repayment capacity",
        "repay_none": "Money out is equal to or more than money in, so there's no surplus to pay an EMI from.",
        "repay_m": "The estimated EMI of {emi} is {pct}% of your average monthly surplus of {surplus}.",
        "repay_i": "A longer tenure, a smaller first loan, or a cheaper scheme (such as a 5% PM Vishwakarma loan) lowers the EMI.",
        "customers": "Customer base",
        "customers_m": "About {n} different customers pay you each month.",
        "customers_i": "Income from many customers is seen as lower risk than income from a few.",
        "digital": "Digital footprint",
        "digital_m": "{pct}% of your income arrives by UPI or bank transfer.",
        "digital_i": "Ask customers to pay by UPI. Digital payments are proof of income a bank can see.",
        "reg": "Formal registration",
        "reg_yes": "Registered on Udyam / Udyam Assist.",
        "reg_no": "Not yet registered on Udyam.",
        "reg_unknown": "Udyam registration not confirmed.",
        "reg_i": "Register on Udyam (free, online). If you don't have a PAN or GST, a designated agency can register you on the Udyam Assist Platform.",
        "clean": "Clean record",
        "clean_ok": "No default declared.",
        "clean_bad": "Declared an existing default.",
        "clean_unknown": "Default status not confirmed.",
        "clean_bounce": "{n} bounced or returned payments in the statement.",
        "clean_i": "Avoid bounced payments by keeping a small buffer before EMI or cheque dates.",
        "band_hi": "Strong", "band_mid": "Good, with a few fixes", "band_lo": "Needs work first",
    },
    "hi": {
        "stability": "आय में स्थिरता",
        "stability_m": "हर महीने की आय औसत से लगभग {cv}% ऊपर-नीचे होती है (सबसे अच्छे महीने: {peak}; सबसे धीमे: {low})।",
        "stability_i": "महीने की आय जितनी स्थिर, उतना अच्छा। किस्त की तारीख़ अच्छे महीनों के बाद रखें और धीमे महीनों के लिए थोड़ी बचत रखें।",
        "track": "कारोबार का रिकॉर्ड",
        "track_m": "{m} महीने का बैंक स्टेटमेंट।",
        "track_i": "अगर हो तो लंबा स्टेटमेंट (12 महीने या ज़्यादा) दें।",
        "repay": "किस्त चुकाने की क्षमता",
        "repay_none": "जितना पैसा आता है, उतना या उससे ज़्यादा ख़र्च होता है, इसलिए किस्त के लिए बचत नहीं बचती।",
        "repay_m": "अनुमानित किस्त (EMI) {emi} है, जो आपकी औसत मासिक बचत {surplus} का {pct}% है।",
        "repay_i": "लंबी अवधि, छोटा पहला लोन, या सस्ती योजना (जैसे 5% वाला पीएम विश्वकर्मा लोन) किस्त कम करती है।",
        "customers": "ग्राहकों की संख्या",
        "customers_m": "हर महीने लगभग {n} अलग-अलग ग्राहक आपको भुगतान करते हैं।",
        "customers_i": "कई ग्राहकों से आने वाली आय को कम जोखिम वाला माना जाता है।",
        "digital": "डिजिटल लेन-देन",
        "digital_m": "आपकी {pct}% आय UPI या बैंक ट्रांसफ़र से आती है।",
        "digital_i": "ग्राहकों से UPI से भुगतान लें। डिजिटल भुगतान आय का ऐसा सबूत है जिसे बैंक देख सकता है।",
        "reg": "उद्यम पंजीकरण",
        "reg_yes": "उद्यम / उद्यम असिस्ट पर पंजीकृत।",
        "reg_no": "अभी उद्यम पर पंजीकरण नहीं है।",
        "reg_unknown": "उद्यम पंजीकरण की पुष्टि नहीं हुई।",
        "reg_i": "उद्यम पर पंजीकरण करें (मुफ़्त, ऑनलाइन)। अगर PAN या GST नहीं है, तो कोई अधिकृत एजेंसी उद्यम असिस्ट प्लेटफ़ॉर्म पर पंजीकरण कर सकती है।",
        "clean": "साफ़ रिकॉर्ड",
        "clean_ok": "कोई बकाया लोन नहीं बताया।",
        "clean_bad": "एक बकाया (डिफ़ॉल्ट) लोन बताया।",
        "clean_unknown": "बकाया लोन की पुष्टि नहीं हुई।",
        "clean_bounce": "स्टेटमेंट में {n} बाउंस या वापस हुए भुगतान।",
        "clean_i": "किस्त या चेक की तारीख़ से पहले खाते में थोड़ा पैसा रखें, ताकि भुगतान बाउंस न हो।",
        "band_hi": "मज़बूत", "band_mid": "अच्छा, कुछ सुधार के साथ", "band_lo": "पहले कुछ सुधार ज़रूरी",
    },
}


def emi(principal: float, annual_rate_pct: float, months: int) -> float:
    """Equated monthly instalment for a reducing-balance loan."""
    if principal <= 0 or months <= 0:
        return 0.0
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return principal / months
    growth = (1 + r) ** months
    return principal * r * growth / (growth - 1)


def _inr(x: float) -> str:
    """Indian digit grouping: 1234567 -> ₹12,34,567."""
    n = int(round(x))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups) + "," + tail
    return f"{sign}₹{s}"


def readiness_score(profile: CashFlowProfile, *, udyam_registered: Optional[bool],
                    has_default: Optional[bool], monthly_emi: float, lang: str = "en") -> ReadinessScore:
    t = TXT["hi" if lang == "hi" else "en"]

    def months(names):
        return ", ".join(MONTHS_HI.get(n, n) if lang == "hi" else n for n in names)

    factors: list[ScoreFactor] = []

    # 1. Income stability (25)
    cv = profile.inflow_cv
    pts = 25 if cv <= 0.20 else 18 if cv <= 0.35 else 10 if cv <= 0.50 else 4
    factors.append(ScoreFactor(t["stability"], pts, 25,
                               t["stability_m"].format(cv=round(cv * 100), peak=months(profile.peak_months),
                                                       low=months(profile.low_months)),
                               "" if pts == 25 else t["stability_i"]))

    # 2. Track record (15)
    m = profile.months
    pts = 15 if m >= 12 else 8 if m >= 6 else 3
    factors.append(ScoreFactor(t["track"], pts, 15, t["track_m"].format(m=m), "" if pts == 15 else t["track_i"]))

    # 3. Repayment capacity (25)
    surplus = profile.avg_monthly_surplus
    ratio = (monthly_emi / surplus) if surplus > 0 else None
    if ratio is None:
        pts, measured = 0, t["repay_none"]
    else:
        pts = 25 if ratio <= 0.35 else 15 if ratio <= 0.50 else 8 if ratio <= 0.70 else 2
        measured = t["repay_m"].format(emi=_inr(monthly_emi), pct=round(ratio * 100), surplus=_inr(surplus))
    factors.append(ScoreFactor(t["repay"], pts, 25, measured, "" if pts == 25 else t["repay_i"]))

    # 4. Customer base (10)
    payers = profile.avg_payers_per_month
    pts = 10 if payers >= 25 else 6 if payers >= 10 else 2
    factors.append(ScoreFactor(t["customers"], pts, 10, t["customers_m"].format(n=round(payers)),
                               "" if pts == 10 else t["customers_i"]))

    # 5. Digital footprint (10)
    share = profile.digital_share
    pts = 10 if share >= 0.60 else 5 if share >= 0.30 else 1
    factors.append(ScoreFactor(t["digital"], pts, 10, t["digital_m"].format(pct=round(share * 100)),
                               "" if pts == 10 else t["digital_i"]))

    # 6. Formal registration (10)
    if udyam_registered:
        factors.append(ScoreFactor(t["reg"], 10, 10, t["reg_yes"], ""))
    else:
        factors.append(ScoreFactor(t["reg"], 0, 10,
                                   t["reg_no"] if udyam_registered is False else t["reg_unknown"], t["reg_i"]))

    # 7. Clean record (5, can go negative for bounces)
    pts = 5 if has_default is False else 0
    pts = max(pts - 3 * profile.bounced_count, -10)
    status = t["clean_ok"] if has_default is False else t["clean_bad"] if has_default else t["clean_unknown"]
    factors.append(ScoreFactor(t["clean"], pts, 5, f"{status} {t['clean_bounce'].format(n=profile.bounced_count)}",
                               "" if pts == 5 else t["clean_i"]))

    total = int(max(0, min(100, round(sum(f.points for f in factors)))))
    band = t["band_hi"] if total >= 75 else t["band_mid"] if total >= 55 else t["band_lo"]
    return ReadinessScore(total=total, band=band, factors=factors, emi=round(monthly_emi, 2),
                          emi_to_surplus=round(ratio, 3) if ratio is not None else None, calibrated=False)


def plan_emi(plan: list[dict]) -> float:
    return sum(emi(p["amount"], p["rate"] or 10.0, p["tenure_months"] or 36) for p in plan)
