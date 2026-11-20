"""Setu, the offline CreditSetu agent.

A conversational agent that needs no API key. It gathers facts through chat (English,
Hindi or Hinglish), reads documents, calls the same deterministic tools as the rest of
the app (profile, scheme engine, score, application drafter) and answers follow-up
questions. It never decides eligibility on its own and never submits without the
owner pressing "Approve".

Replies are plain dicts so the UI can render them as chat bubbles and cards:
    {"kind": "text" | "profile" | "schemes" | "score" | "application" | "submitted",
     "text": str, "quick": [str, ...]}
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from ..case import Analysis, analyze, build_package
from ..models import Applicant
from ..schemes import load_rules
from ..score import _inr
from .nlu import TRADE_SECTOR, VISHWAKARMA_TRADES, extract_facts, find_trade, normalize, parse_amount, yes_no

S = {
    "en": {
        "hello": "Namaste! I'm **Setu**. I help small businesses find the loans and government schemes meant for them, and prepare the application.\n\nTell me what work you do and how much money you need. For example: *“I'm a tailor and need ₹3 lakh for machines.”*",
        "hello_quick": ["I'm a tailor and need ₹3 lakh", "Show me the demo (Sunita)", "Which schemes exist?", "Is my data safe?"],
        "q_trade": "What work do you do? For example tailoring, dairy, a kirana shop, or mobile repair.",
        "q_trade_quick": ["Tailor", "Dairy", "Kirana shop", "Mobile repair"],
        "q_amount": "How much money do you need, roughly?",
        "q_amount_quick": ["₹50,000", "₹1 lakh", "₹3 lakh", "₹10 lakh"],
        "q_new": "Is your business already running, or are you starting a new one?",
        "q_new_quick": ["Already running", "Starting a new one"],
        "q_statement": "Please share your **bank or UPI statement** (PDF or CSV) with the 📎 upload box below the chat. I only read it in this session; nothing is stored.\n\nNo statement handy? Use the sample one.",
        "q_statement_quick": ["Use the sample statement"],
        "q_udyam": "Is your business registered on **Udyam** (the free MSME registration)?",
        "q_udyam_quick": ["Yes", "No", "Not sure"],
        "q_default": "Do you have any loan you haven't been able to repay (a default)?",
        "q_default_quick": ["No", "Yes"],
        "q_age": "How old are you? Every scheme needs the owner to be at least 18.",
        "q_age_quick": ["18 or older", "Under 18"],
        "q_trained": "Good news: as a {trade}, you may qualify for **PM Vishwakarma**, a collateral-free loan at **5%**. Have you done its basic skill training?",
        "q_trained_quick": ["Yes", "No", "What is PM Vishwakarma?"],
        "q_prior": "In the last few years, have you taken a loan under PMEGP, PM SVANidhi or MUDRA?",
        "q_prior_quick": ["No", "Yes"],
        "q_category": "One more, only because a scheme needs it: **Stand-Up India** is reserved by law for **women and SC/ST** entrepreneurs starting a new business. Does either apply? This never affects your score.",
        "q_category_quick": ["I'm a woman", "SC/ST", "Neither", "Skip"],
        "q_owner": "What name should go on the application?",
        "q_business": "And what is your business called?",
        "got": "Got it: {facts}.",
        "statement_ok": "Thanks! I read **{n} transactions** from {name}.",
        "analyzing": "Here's what I found. Every scheme result links to the official rule it's based on.",
        "after": "What would you like to do next?",
        "after_quick": ["Prepare my application", "How can I improve my score?", "Why not Stand-Up India?", "What documents do I need?"],
        "app_ready": "Your application is ready for you to review. I've marked the documents you still need. When you're happy, press **Approve and send to bank**. Nothing is sent before that.",
        "app_quick": ["What documents do I need?", "How can I improve my score?"],
        "submitted": "Sent! Your reference number is **{ref}**. You can track it any time on the *Track application* page. I'll show the bank's updates there.",
        "quote_ok": "I read your quotation from **{vendor}**: total **{total}**. I've added it to your documents{amount_note}.",
        "quote_amount_note": " and set your loan need to {total}",
        "quote_fail": "I couldn't read a total from that photo. Try a clearer, straight-on photo in good light.",
        "unknown": "Sorry, I didn't catch that. You can tell me about your business, ask about a scheme (MUDRA, PM Vishwakarma, PMEGP, Stand-Up India, CGTMSE), or ask what documents you need.",
        "privacy": "Your statement is read **only in this session**, to check schemes and prepare your file. Nothing is stored or shared until you press *Approve and send to bank*. Your gender, caste category and location are used **only** for schemes that the law reserves for certain groups, and **never** in your score.",
        "schemes_list": "I check these schemes:\n\n{rows}\n\nTell me about your business and I'll check which ones fit.",
        "why_not_none": "That scheme isn't ruled out for you.",
        "why_not": "**{name}** isn't a fit because:\n\n{rows}",
        "need_more": "I need a few details first.",
        "improve": "The quickest ways to raise your score:\n\n{rows}",
        "improve_none": "Your score is already at the top for every factor.",
        "docs": "For your application:\n\n{rows}\n\nYou can upload a **photo of a quotation** for your machines or stock and I'll read it.",
        "emi": "Your suggested plan:\n\n{rows}\n\nEstimated total EMI: **{emi} a month**. The bank sets the final rate.",
        "restart": "Okay, let's start again.",
        "status_words": {"eligible": "✅ you qualify", "needs_info": "🟡 likely, needs one answer", "not_fit": "❌ not a fit"},
        "trade_names": {"tailor": "tailor", "barber": "barber", "carpenter": "carpenter", "dairy": "dairy farmer"},
        "yes": "yes", "no": "no",
        "fact_names": {"trade": "work", "loan_amount": "amount", "is_new_unit": "business", "owner_name": "name",
                       "udyam_registered": "Udyam", "years_in_business": "years running", "gender": "gender", "area": "area",
                       "age": "age"},
        "new_words": {True: "new business", False: "already running"},
    },
    "hi": {
        "hello": "नमस्ते! मैं **सेतु** हूँ। मैं छोटे कारोबारियों को उनके लिए बने लोन और सरकारी योजनाएँ ढूँढने और आवेदन तैयार करने में मदद करता हूँ।\n\nबताइए आप क्या काम करते हैं और आपको कितने पैसे चाहिए। जैसे: *“मैं दर्जी हूँ, मशीनों के लिए ₹3 लाख चाहिए।”*",
        "hello_quick": ["मैं दर्जी हूँ, ₹3 लाख चाहिए", "डेमो दिखाइए (सुनीता)", "कौन-सी योजनाएँ हैं?", "क्या मेरा डेटा सुरक्षित है?"],
        "q_trade": "आप क्या काम करते हैं? जैसे सिलाई, डेयरी, किराना दुकान या मोबाइल रिपेयर।",
        "q_trade_quick": ["दर्जी", "डेयरी", "किराना दुकान", "मोबाइल रिपेयर"],
        "q_amount": "आपको लगभग कितने पैसे चाहिए?",
        "q_amount_quick": ["₹50,000", "₹1 लाख", "₹3 लाख", "₹10 लाख"],
        "q_new": "आपका कारोबार पहले से चल रहा है, या आप नया शुरू कर रहे हैं?",
        "q_new_quick": ["पहले से चल रहा है", "नया शुरू कर रहे हैं"],
        "q_statement": "कृपया अपना **बैंक या UPI स्टेटमेंट** (PDF या CSV) चैट के नीचे 📎 अपलोड बॉक्स से दें। मैं इसे सिर्फ़ इसी सेशन में पढ़ता हूँ; कुछ भी सेव नहीं होता।\n\nस्टेटमेंट पास नहीं है? सैंपल स्टेटमेंट इस्तेमाल करें।",
        "q_statement_quick": ["सैंपल स्टेटमेंट इस्तेमाल करें"],
        "q_udyam": "क्या आपका कारोबार **उद्यम** (मुफ़्त MSME पंजीकरण) पर पंजीकृत है?",
        "q_udyam_quick": ["हाँ", "नहीं", "पता नहीं"],
        "q_default": "क्या आपका कोई लोन है जिसे आप चुका नहीं पाए (डिफ़ॉल्ट)?",
        "q_default_quick": ["नहीं", "हाँ"],
        "q_age": "आपकी उम्र कितनी है? हर योजना के लिए उम्र कम से कम 18 साल होनी चाहिए।",
        "q_age_quick": ["18 या ज़्यादा", "18 से कम"],
        "q_trained": "अच्छी ख़बर: {trade} होने के नाते आप **पीएम विश्वकर्मा** के लिए पात्र हो सकते हैं, जिसमें बिना गारंटी का लोन सिर्फ़ **5%** ब्याज पर मिलता है। क्या आपने इसकी बुनियादी ट्रेनिंग की है?",
        "q_trained_quick": ["हाँ", "नहीं", "पीएम विश्वकर्मा क्या है?"],
        "q_prior": "पिछले कुछ सालों में क्या आपने PMEGP, पीएम स्वनिधि या मुद्रा से लोन लिया है?",
        "q_prior_quick": ["नहीं", "हाँ"],
        "q_category": "एक और सवाल, सिर्फ़ इसलिए कि एक योजना को इसकी ज़रूरत है: **स्टैंड-अप इंडिया** क़ानून के तहत नया कारोबार शुरू करने वाली **महिलाओं और SC/ST** उद्यमियों के लिए है। क्या इनमें से कोई आप पर लागू होता है? इसका आपके स्कोर पर कोई असर नहीं होता।",
        "q_category_quick": ["मैं महिला हूँ", "SC/ST", "कोई नहीं", "छोड़ें"],
        "q_owner": "आवेदन पर कौन-सा नाम लिखा जाए?",
        "q_business": "और आपके कारोबार का नाम क्या है?",
        "got": "समझ गया: {facts}।",
        "statement_ok": "धन्यवाद! मैंने {name} से **{n} लेन-देन** पढ़े।",
        "analyzing": "यह रहा नतीजा। हर योजना के नतीजे के साथ उसका आधिकारिक नियम दिया है।",
        "after": "आगे क्या करना चाहेंगे?",
        "after_quick": ["मेरा आवेदन तैयार करें", "स्कोर कैसे बढ़ाऊँ?", "स्टैंड-अप इंडिया क्यों नहीं?", "कौन-से दस्तावेज़ चाहिए?"],
        "app_ready": "आपका आवेदन जाँचने के लिए तैयार है। जो दस्तावेज़ अभी चाहिए, वे मैंने चिह्नित कर दिए हैं। संतुष्ट हों तो **मंज़ूर करें और बैंक को भेजें** दबाएँ। उससे पहले कुछ नहीं भेजा जाएगा। (बैंक के लिए आवेदन अंग्रेज़ी में बनता है।)",
        "app_quick": ["कौन-से दस्तावेज़ चाहिए?", "स्कोर कैसे बढ़ाऊँ?"],
        "submitted": "भेज दिया! आपका रेफ़रेंस नंबर **{ref}** है। आप इसे कभी भी *आवेदन ट्रैक करें* पेज पर देख सकते हैं। बैंक के अपडेट वहीं दिखेंगे।",
        "quote_ok": "मैंने **{vendor}** का कोटेशन पढ़ा: कुल **{total}**। इसे आपके दस्तावेज़ों में जोड़ दिया है{amount_note}।",
        "quote_amount_note": " और आपकी लोन ज़रूरत {total} कर दी है",
        "quote_fail": "उस फ़ोटो से कुल रक़म नहीं पढ़ पाया। अच्छी रोशनी में सीधी, साफ़ फ़ोटो लें।",
        "unknown": "माफ़ कीजिए, समझ नहीं पाया। आप अपने कारोबार के बारे में बता सकते हैं, किसी योजना (मुद्रा, पीएम विश्वकर्मा, PMEGP, स्टैंड-अप इंडिया, CGTMSE) के बारे में पूछ सकते हैं, या पूछ सकते हैं कि कौन-से दस्तावेज़ चाहिए।",
        "privacy": "आपका स्टेटमेंट **सिर्फ़ इसी सेशन में** पढ़ा जाता है, योजनाएँ जाँचने और आवेदन बनाने के लिए। जब तक आप *मंज़ूर करें और बैंक को भेजें* नहीं दबाते, कुछ भी सेव या साझा नहीं होता। आपका लिंग, जाति वर्ग और जगह **सिर्फ़** उन योजनाओं के लिए इस्तेमाल होते हैं जो क़ानून के तहत कुछ समूहों के लिए हैं, और आपके स्कोर में **कभी नहीं**।",
        "schemes_list": "मैं ये योजनाएँ जाँचता हूँ:\n\n{rows}\n\nअपने कारोबार के बारे में बताइए, मैं देखूँगा कौन-सी आपके लिए सही हैं।",
        "why_not_none": "वह योजना आपके लिए बाहर नहीं हुई है।",
        "why_not": "**{name}** आपके लिए सही नहीं है, क्योंकि:\n\n{rows}",
        "need_more": "पहले कुछ जानकारी चाहिए।",
        "improve": "स्कोर बढ़ाने के सबसे आसान तरीक़े:\n\n{rows}",
        "improve_none": "आपका स्कोर हर पहलू में पहले से सबसे ऊपर है।",
        "docs": "आपके आवेदन के लिए:\n\n{rows}\n\nआप मशीन या माल के **कोटेशन की फ़ोटो** अपलोड कर सकते हैं, मैं उसे पढ़ लूँगा।",
        "emi": "आपकी सुझाई गई योजना:\n\n{rows}\n\nकुल अनुमानित किस्त: **{emi} महीना**। अंतिम ब्याज दर बैंक तय करेगा।",
        "restart": "ठीक है, फिर से शुरू करते हैं।",
        "status_words": {"eligible": "✅ आप पात्र हैं", "needs_info": "🟡 शायद, एक जवाब चाहिए", "not_fit": "❌ उपयुक्त नहीं"},
        "trade_names": {"tailor": "दर्जी", "barber": "नाई", "carpenter": "बढ़ई", "dairy": "डेयरी किसान", "mason": "राजमिस्त्री",
                        "cobbler": "मोची", "potter": "कुम्हार", "washerman": "धोबी", "goldsmith": "सुनार", "blacksmith": "लोहार"},
        "yes": "हाँ", "no": "नहीं",
        "fact_names": {"trade": "काम", "loan_amount": "रक़म", "is_new_unit": "कारोबार", "owner_name": "नाम",
                       "udyam_registered": "उद्यम", "years_in_business": "कितने साल से", "gender": "लिंग", "area": "इलाक़ा",
                       "age": "उम्र"},
        "new_words": {True: "नया कारोबार", False: "पहले से चल रहा"},
    },
}

SCHEME_WORDS = {
    "pm_vishwakarma_t1": r"vishwakarma|विश्वकर्मा",
    "pmmy_kishore": r"mudra|मुद्रा",
    "pmegp": r"pmegp|पीएमईजीपी",
    "stand_up_india": r"stand.?up|स्टैंड.?अप",
    "cgtmse": r"cgtmse",
    "cgfmu": r"cgfmu",
}


@dataclass
class CaseState:
    applicant: Applicant = field(default_factory=lambda: Applicant(enterprise_size="micro"))
    txns: Optional[list] = None
    statement_name: str = ""
    have_docs: set = field(default_factory=lambda: {"aadhaar", "pan"})
    quotation: Optional[object] = None
    lang: str = "en"
    pending: Optional[str] = None
    asked: set = field(default_factory=set)
    analysis: Optional[Analysis] = None
    stage: str = "collect"          # collect | analyzed | application | submitted
    package: Optional[object] = None
    submitted_ref: str = ""


QUESTION_ORDER = ["trade", "loan_amount", "is_new_unit", "statement", "udyam_registered", "has_default",
                  "age", "vishwakarma_trained", "prior_scheme_loan", "category"]


class OfflineAgent:
    def __init__(self, state: CaseState):
        self.s = state

    # ------------------------------------------------------------ helpers
    @property
    def t(self) -> dict:
        return S["hi" if self.s.lang == "hi" else "en"]

    def _reply(self, text: str, kind: str = "text", quick: Optional[list] = None) -> dict:
        return {"kind": kind, "text": text, "quick": quick or []}

    def _needed(self) -> Optional[str]:
        a = self.s.applicant
        for key in QUESTION_ORDER:
            if key in self.s.asked and key not in ("statement",):
                continue
            if key == "trade" and not a.trade:
                return key
            if key == "loan_amount" and not a.loan_amount:
                return key
            if key == "is_new_unit" and a.is_new_unit is None:
                return key
            if key == "statement" and self.s.txns is None:
                return key
            if key == "udyam_registered" and a.udyam_registered is None:
                return key
            if key == "has_default" and a.has_default is None:
                return key
            if key == "age" and a.age is None:
                return key
            if key == "vishwakarma_trained" and a.trade in VISHWAKARMA_TRADES and a.vishwakarma_trained is None:
                return key
            if key == "prior_scheme_loan" and a.trade in VISHWAKARMA_TRADES and a.prior_scheme_loan is None:
                return key
            if (key == "category" and a.is_new_unit and (a.loan_amount or 0) >= 1_000_000
                    and a.gender is None and a.social_category is None):
                return key
        return None

    def _ask(self, key: str) -> dict:
        self.s.pending = key
        t = self.t
        if key == "trade":
            return self._reply(t["q_trade"], quick=t["q_trade_quick"])
        if key == "loan_amount":
            return self._reply(t["q_amount"], quick=t["q_amount_quick"])
        if key == "is_new_unit":
            return self._reply(t["q_new"], quick=t["q_new_quick"])
        if key == "statement":
            return self._reply(t["q_statement"], quick=t["q_statement_quick"])
        if key == "udyam_registered":
            return self._reply(t["q_udyam"], quick=t["q_udyam_quick"])
        if key == "has_default":
            return self._reply(t["q_default"], quick=t["q_default_quick"])
        if key == "age":
            return self._reply(t["q_age"], quick=t["q_age_quick"])
        if key == "vishwakarma_trained":
            trade = t["trade_names"].get(self.s.applicant.trade, self.s.applicant.trade)
            return self._reply(t["q_trained"].format(trade=trade), quick=t["q_trained_quick"])
        if key == "prior_scheme_loan":
            return self._reply(t["q_prior"], quick=t["q_prior_quick"])
        if key == "category":
            return self._reply(t["q_category"], quick=t["q_category_quick"])
        if key == "owner_name":
            return self._reply(t["q_owner"])
        if key == "business_name":
            return self._reply(t["q_business"])
        raise ValueError(key)

    def _describe(self, facts: dict) -> str:
        t = self.t
        parts = []
        for k, v in facts.items():
            if k in ("sector",):
                continue
            label = t["fact_names"].get(k)
            if not label:
                continue
            if k == "loan_amount":
                v = _inr(v)
            elif k == "trade":
                v = t["trade_names"].get(v, v.replace("_", " "))
            elif k == "is_new_unit":
                v = t["new_words"][v]
            elif isinstance(v, bool):
                v = t["yes"] if v else t["no"]
            elif isinstance(v, float):
                v = f"{v:g}"
            parts.append(f"{label}: **{v}**")
        return ", ".join(parts)

    def _apply(self, facts: dict) -> None:
        for k, v in facts.items():
            setattr(self.s.applicant, k, v)
        self.s.analysis = None  # facts changed: results must be recomputed

    # ------------------------------------------------------------ analysis
    def _analyze(self) -> list[dict]:
        self.s.analysis = analyze(self.s.applicant, self.s.txns, self.s.lang)
        self.s.stage = "analyzed"
        t = self.t
        return [
            self._reply(t["analyzing"]),
            self._reply("", kind="profile"),
            self._reply("", kind="schemes"),
            self._reply("", kind="score"),
            self._reply(t["after"], quick=t["after_quick"]),
        ]

    def _continue(self, prefix: Optional[list] = None) -> list[dict]:
        out = list(prefix or [])
        nxt = self._needed()
        if nxt:
            out.append(self._ask(nxt))
        elif self.s.stage == "collect" or self.s.analysis is None:
            self.s.pending = None
            out.extend(self._analyze())
        return out

    # ------------------------------------------------------------ events
    def start(self) -> list[dict]:
        return [self._reply(self.t["hello"], quick=self.t["hello_quick"])]

    def load_demo(self) -> list[dict]:
        from pathlib import Path
        from ..statement import read_statement
        sample = Path(__file__).resolve().parents[2] / "data" / "sample_statement_sunita.csv"
        self.s.applicant = Applicant(
            business_name="Sunita Tailoring Works", owner_name="Sunita", trade="tailor", sector="manufacturing",
            enterprise_size="micro", is_new_unit=False, years_in_business=4, loan_amount=300000,
            loan_purpose="Two sewing machines and fabric stock before wedding season", age=34, has_default=False,
            udyam_registered=False, vishwakarma_trained=None, prior_scheme_loan=False,
            district="Bhilwara", state="Rajasthan")
        self.s.txns = read_statement(sample)
        self.s.statement_name = "sample statement" if self.s.lang == "en" else "सैंपल स्टेटमेंट"
        self.s.have_docs.add("bank_statement")
        self.s.asked = {"vishwakarma_trained"}
        intro = ("Loaded the demo: **Sunita**, a tailor in Bhilwara with a 4-year-old unit, needs **₹3 lakh** for "
                 "two machines and fabric stock. Her 14-month statement is synthetic.") if self.s.lang == "en" else \
                ("डेमो लोड हो गया: **सुनीता**, भीलवाड़ा में 4 साल से सिलाई यूनिट चलाती हैं, उन्हें दो मशीनों और कपड़े के "
                 "लिए **₹3 लाख** चाहिए। उनका 14 महीने का स्टेटमेंट काल्पनिक (synthetic) है।")
        return self._continue([self._reply(intro)])

    def statement_loaded(self, txns: list, name: str) -> list[dict]:
        self.s.txns = txns
        self.s.statement_name = name
        self.s.have_docs.add("bank_statement")
        self.s.analysis = None
        if self.s.stage != "collect":
            self.s.stage = "collect"
        return self._continue([self._reply(self.t["statement_ok"].format(n=len(txns), name=name))])

    def quotation_loaded(self, reading) -> list[dict]:
        t = self.t
        if not reading or not reading.total:
            return [self._reply(t["quote_fail"])]
        self.s.quotation = reading
        self.s.have_docs.add("quotation")
        note = ""
        if not self.s.applicant.loan_amount:
            self.s.applicant.loan_amount = int(reading.total)
            note = t["quote_amount_note"].format(total=_inr(reading.total))
        if not self.s.applicant.loan_purpose and reading.items:
            self.s.applicant.loan_purpose = ", ".join(d for d, _ in reading.items[:3])
        out = [self._reply(t["quote_ok"].format(vendor=reading.vendor.title(), total=_inr(reading.total),
                                                amount_note=note),
                           quick=t["after_quick"] if self.s.stage == "analyzed" else [])]
        if self.s.stage == "collect":
            return self._continue(out)
        if self.s.stage == "application":
            return out + self._prepare_application()
        return out

    def approve_and_submit(self) -> list[dict]:
        from .. import store
        from ..case import submission_kwargs
        pkg = build_package(self.s.applicant, self.s.txns, self.s.have_docs)
        ref = store.submit(**submission_kwargs(pkg))
        self.s.submitted_ref = ref
        self.s.stage = "submitted"
        return [self._reply(self.t["submitted"].format(ref=ref), kind="submitted")]

    # ------------------------------------------------------------ intents
    def _intent(self, text: str) -> Optional[list[dict]]:
        t, low = self.t, normalize(text).lower()
        if re.search(r"start over|restart|reset|फिर से शुरू|dobara", low):
            lang = self.s.lang
            self.__init__(CaseState(lang=lang))
            self.s = CaseState(lang=lang)
            return [self._reply(t["restart"])] + self.start()
        if re.search(r"\bdemo\b|डेमो", low):
            return self.load_demo()
        if re.search(r"sample statement|सैंपल", low):
            from pathlib import Path
            from ..statement import read_statement
            sample = Path(__file__).resolve().parents[2] / "data" / "sample_statement_sunita.csv"
            return self.statement_loaded(read_statement(sample), "sample statement" if self.s.lang == "en" else "सैंपल स्टेटमेंट")
        if re.search(r"safe|privacy|data|सुरक्षित|डेटा|surakshit", low):
            return [self._reply(t["privacy"])] + self._continue()
        if re.search(r"which schemes|what schemes|schemes exist|kaun.?si yojana|कौन-सी योजना|कौन सी योजना", low):
            rules = load_rules()
            rows = "\n".join(f"- **{(r.get('name_hi') if self.s.lang == 'hi' else r['name'])}**: "
                             f"{(r.get('summary_hi') if self.s.lang == 'hi' else r['summary'])}"
                             for r in rules["schemes"] if r["id"] not in ("pmmy_shishu", "pmmy_tarun", "pmmy_tarun_plus"))
            return [self._reply(t["schemes_list"].format(rows=rows))] + self._continue()
        if re.search(r"why not|kyon nahi|kyu nahi|क्यों नहीं|kyun nahi", low):
            sid = next((sid for sid, pat in SCHEME_WORDS.items() if re.search(pat, low)), None)
            return self._why_not(sid)
        if re.search(r"what is|kya hai|क्या है|tell me about|batao|बताइए|explain", low):
            sid = next((sid for sid, pat in SCHEME_WORDS.items() if re.search(pat, low)), None)
            if sid:
                return [self._scheme_info(sid)] + ([self._ask(self.s.pending)] if self.s.pending else [])
        if re.search(r"improve|score kaise|स्कोर कैसे|badha|बढ़ा", low):
            return self._improve()
        if re.search(r"document|dastavez|दस्तावेज़|दस्तावेज|kagaz|कागज़|papers", low):
            return self._documents()
        if re.search(r"\bemi\b|kist|किस्त|interest|byaj|ब्याज", low):
            return self._emi()
        if re.search(r"prepare|application|aavedan|आवेदन|apply", low):
            return self._prepare_application()
        return None

    def _scheme_info(self, sid: str) -> dict:
        rule = next(r for r in load_rules()["schemes"] if r["id"] == sid)
        hi = self.s.lang == "hi"
        name = rule.get("name_hi") if hi else rule["name"]
        summary = rule.get("summary_hi") if hi else rule["summary"]
        benefit = rule.get("benefit_hi") if hi else rule["benefit"]
        src = " · ".join(f"[{s['title']}]({s['url']})" for s in rule["sources"])
        return self._reply(f"**{name}**: {summary}\n\n{benefit}\n\n{'स्रोत' if hi else 'Sources'}: {src}")

    def _need_analysis(self) -> Optional[list[dict]]:
        if self.s.analysis is None:
            if self._needed():
                return [self._reply(self.t["need_more"])] + self._continue()
            self._analyze()
        return None

    def _why_not(self, sid: Optional[str]) -> list[dict]:
        early = self._need_analysis()
        if early:
            return early
        t = self.t
        res = next((r for r in self.s.analysis.results if sid and r.scheme_id == sid), None)
        if res is None or res.status != "not_fit":
            if sid:
                return [self._reply(t["why_not_none"]), self._scheme_info(sid)]
            res = next((r for r in self.s.analysis.results if r.status == "not_fit"), None)
            if res is None:
                return [self._reply(t["why_not_none"])]
        rows = "\n".join(f"- ❌ {c.text} — [{c.source_title}]({c.source_url})" for c in res.criteria if c.status == "fail")
        return [self._reply(t["why_not"].format(name=res.name, rows=rows), quick=t["after_quick"])]

    def _improve(self) -> list[dict]:
        early = self._need_analysis()
        if early:
            return early
        t = self.t
        fixes = sorted((f for f in self.s.analysis.score.factors if f.improve), key=lambda f: f.points - f.max_points)
        if not fixes:
            return [self._reply(t["improve_none"])]
        rows = "\n".join(f"- **{f.name}** ({f.points:g}/{f.max_points:g}): {f.improve}" for f in fixes[:3])
        return [self._reply(t["improve"].format(rows=rows), quick=t["after_quick"])]

    def _documents(self) -> list[dict]:
        from ..application import document_checklist
        t = self.t
        plan = self.s.analysis.plan if self.s.analysis else []
        items = document_checklist(self.s.applicant, self.s.have_docs, plan)
        icon = {"have": "✅", "missing": "⬜", "ready": "✨"}
        labels_hi = {"aadhaar": "आधार कार्ड", "pan": "PAN कार्ड", "bank_statement": "पिछले 6–12 महीने का बैंक स्टेटमेंट",
                     "business_proof": "कारोबार के पते का सबूत (किरायानामा या बिजली बिल)", "photo": "हाल की पासपोर्ट फ़ोटो",
                     "udyam": "उद्यम पंजीकरण प्रमाणपत्र (या उद्यम असिस्ट प्रमाणपत्र)", "quotation": "मशीन या माल का कोटेशन",
                     "vishwakarma_cert": "पीएम विश्वकर्मा प्रमाणपत्र और ट्रेनिंग पूरी होने का सबूत",
                     "cashflow_summary": "आपके स्टेटमेंट से नकदी प्रवाह का सारांश (CreditSetu बनाएगा)",
                     "project_report": "छोटी प्रोजेक्ट रिपोर्ट (CreditSetu ड्राफ़्ट बनाएगा)"}
        rows = "\n".join(f"- {icon[i['status']]} {labels_hi.get(i['key'], i['label']) if self.s.lang == 'hi' else i['label']}"
                         for i in items)
        return [self._reply(t["docs"].format(rows=rows), quick=t["app_quick"] if self.s.stage == "application" else t["after_quick"])]

    def _emi(self) -> list[dict]:
        early = self._need_analysis()
        if early:
            return early
        t = self.t
        a = self.s.analysis
        unit = "महीने" if self.s.lang == "hi" else "months"
        rows = "\n".join(f"- **{p['name']}**: {_inr(p['amount'])} @ ~{p['rate']:g}% · {p['tenure_months']} {unit}" for p in a.plan)
        return [self._reply(t["emi"].format(rows=rows, emi=_inr(a.score.emi)), quick=t["after_quick"])]

    def _prepare_application(self) -> list[dict]:
        early = self._need_analysis()
        if early:
            return early
        if not self.s.applicant.owner_name:
            return [self._ask("owner_name")]
        if not self.s.applicant.business_name:
            return [self._ask("business_name")]
        self.s.pending = None
        self.s.package = build_package(self.s.applicant, self.s.txns, self.s.have_docs)
        self.s.stage = "application"
        return [self._reply(self.t["app_ready"], kind="application", quick=self.t["app_quick"])]

    # ------------------------------------------------------------ main entry
    def handle(self, text: str) -> list[dict]:
        text = (text or "").strip()
        if not text:
            return []
        pending = self.s.pending

        # Free-text answers for names
        if pending in ("owner_name", "business_name"):
            setattr(self.s.applicant, pending, text.strip().title() if text.isascii() else text.strip())
            self.s.pending = None
            return self._prepare_application()

        intent = self._intent(text)
        if intent is not None:
            return intent

        facts = extract_facts(text)
        # Answers to the pending question
        yn = yes_no(text)
        low = normalize(text).lower()
        unsure = bool(re.search(r"not sure|pata nahi|पता नहीं|don't know|skip|छोड़ें|neither|कोई नहीं", low))
        if pending == "trade" and "trade" not in facts and len(text) > 1:
            facts["trade"] = find_trade(text) or "other"
            facts["sector"] = TRADE_SECTOR.get(facts["trade"], "services")
        if pending == "loan_amount" and "loan_amount" not in facts:
            amt = parse_amount(text)
            if amt:
                facts["loan_amount"] = amt
        if pending == "is_new_unit" and "is_new_unit" not in facts and yn is not None:
            facts["is_new_unit"] = yn
        if pending == "age" and "age" not in facts:
            if re.search(r"under 18|18 से कम|below 18", low):
                facts["age"] = 17
            elif re.search(r"18 or older|18 या ज़्यादा|above 18|over 18|adult", low):
                facts["age"] = 18
            else:
                m = re.search(r"\b(\d{2})\b", low)
                if m:
                    facts["age"] = int(m.group(1))
        if pending in ("udyam_registered", "has_default", "vishwakarma_trained", "prior_scheme_loan"):
            if unsure:
                self.s.asked.add(pending)
            elif yn is not None:
                facts[pending] = yn
        if pending == "category":
            self.s.asked.add("category")
        if pending == "statement" and unsure:
            pass

        if not facts and not (pending and pending in self.s.asked):
            if pending:
                return [self._reply(self.t["unknown"]), self._ask(pending)]
            return [self._reply(self.t["unknown"], quick=self.t["after_quick"] if self.s.analysis else self.t["hello_quick"])]

        self._apply(facts)
        if self.s.stage in ("analyzed", "application", "submitted") and facts:
            self.s.stage = "collect"
        prefix = [self._reply(self.t["got"].format(facts=self._describe(facts)))] if self._describe(facts) else []
        return self._continue(prefix)
