"""Small, transparent language understanding for English, Hindi and Hinglish.

No model is needed: owners describe their business in short sentences, and the facts we
need (trade, amount, new or running, yes/no answers) are recognisable from keywords and
number patterns. When the Claude agent is switched on, it does this job instead.
"""

from __future__ import annotations

import re
from typing import Optional

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

NUMBER_WORDS = {
    "ek": 1, "एक": 1, "one": 1, "do": 2, "दो": 2, "two": 2, "teen": 3, "तीन": 3, "three": 3,
    "char": 4, "chaar": 4, "चार": 4, "four": 4, "paanch": 5, "panch": 5, "पाँच": 5, "पांच": 5, "five": 5,
    "chhe": 6, "chhah": 6, "छह": 6, "छः": 6, "six": 6, "saat": 7, "सात": 7, "seven": 7,
    "aath": 8, "आठ": 8, "eight": 8, "nau": 9, "नौ": 9, "nine": 9, "das": 10, "दस": 10, "ten": 10,
    "pandrah": 15, "पंद्रह": 15, "fifteen": 15, "bees": 20, "बीस": 20, "twenty": 20,
    "pachas": 50, "pachaas": 50, "पचास": 50, "fifty": 50,
    "dedh": 1.5, "डेढ़": 1.5, "डेढ": 1.5, "dhai": 2.5, "dhaai": 2.5, "ढाई": 2.5,
    "half": 0.5, "aadha": 0.5, "आधा": 0.5,
}
UNITS = [
    (r"crore|cr|करोड़|करोड", 10_000_000),
    (r"lakhs?|lacs?|lac|lakh|l\b|लाख", 100_000),
    (r"thousand|hazaa?r|हज़ार|हजार|k\b", 1_000),
]

TRADES = {
    "tailor": ["tailor", "darzi", "darji", "silai", "sewing", "stitching", "boutique", "दर्जी", "सिलाई", "टेलर"],
    "barber": ["barber", "salon", "nai\\b", "naai", "hair cut", "haircut", "नाई", "सैलून"],
    "carpenter": ["carpenter", "furniture", "badhai", "barhai", "बढ़ई", "फ़र्नीचर", "फर्नीचर"],
    "mason": ["mason", "rajmistri", "raj mistri", "राजमिस्त्री", "मिस्त्री"],
    "cobbler": ["cobbler", "shoe", "footwear", "mochi", "मोची", "जूते"],
    "potter": ["potter", "pottery", "kumhar", "कुम्हार", "मिट्टी के बर्तन"],
    "blacksmith": ["blacksmith", "lohar", "लोहार"],
    "goldsmith": ["goldsmith", "sonar", "jeweller", "jeweler", "सुनार"],
    "washerman": ["washerman", "dhobi", "laundry", "धोबी", "लॉन्ड्री"],
    "garland_maker": ["garland", "mala", "flower shop", "माला", "फूल"],
    "basket_mat_broom_maker": ["basket", "broom", "jhadu", "mat weaving", "टोकरी", "झाड़ू"],
    "doll_toy_maker": ["toy", "doll", "khilona", "खिलौने", "खिलौना"],
    "fishing_net_maker": ["fishing net", "jaal", "जाल"],
    "kirana": ["kirana", "grocery", "general store", "shop", "dukan", "किराना", "दुकान"],
    "fabrication": ["fabrication", "welding", "fabricator", "वेल्डिंग", "फैब्रिकेशन"],
    "dairy": ["dairy", "milk", "cow", "buffalo", "doodh", "डेयरी", "दूध", "भैंस", "गाय"],
    "food_stall": ["food", "dhaba", "catering", "tiffin", "stall", "chai", "ढाबा", "खाना", "चाय"],
    "beauty_parlour": ["beauty", "parlour", "parlor", "ब्यूटी", "पार्लर"],
    "repair_shop": ["repair", "mobile", "electronics", "मरम्मत", "रिपेयर", "मोबाइल"],
}
TRADE_SECTOR = {
    "tailor": "manufacturing", "carpenter": "manufacturing", "cobbler": "manufacturing", "potter": "manufacturing",
    "blacksmith": "manufacturing", "goldsmith": "manufacturing", "basket_mat_broom_maker": "manufacturing",
    "doll_toy_maker": "manufacturing", "fishing_net_maker": "manufacturing", "fabrication": "manufacturing",
    "garland_maker": "manufacturing", "barber": "services", "washerman": "services", "mason": "services",
    "beauty_parlour": "services", "repair_shop": "services", "food_stall": "services",
    "kirana": "trading", "dairy": "allied_agriculture",
}
VISHWAKARMA_TRADES = {"tailor", "carpenter", "boat_maker", "armourer", "blacksmith", "hammer_toolkit_maker",
                      "locksmith", "goldsmith", "potter", "sculptor", "stone_breaker", "cobbler", "mason",
                      "basket_mat_broom_maker", "doll_toy_maker", "barber", "garland_maker", "washerman",
                      "fishing_net_maker"}

YES = r"\b(yes|yeah|yep|haan|haa|han|ha|ji|ji haan|sure|done|kiya|hai|hain|ok|okay)\b|हाँ|हां|जी|किया|है"
NO = r"\b(no|nope|nahi|nahin|nai|na|not|never|nope)\b|नहीं|नही|ना\b"


def normalize(text: str) -> str:
    return (text or "").translate(DEVANAGARI_DIGITS).strip()


def parse_amount(text: str) -> Optional[int]:
    t = normalize(text).lower().replace(",", "")
    for unit_re, mult in UNITS:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:" + unit_re + r")", t)
        if m:
            return int(float(m.group(1)) * mult)
        words = "|".join(sorted((re.escape(w) for w in NUMBER_WORDS), key=len, reverse=True))
        m = re.search(r"(?<!\w)(" + words + r")\s*(?:" + unit_re + r")", t)
        if m:
            return int(NUMBER_WORDS[m.group(1)] * mult)
    m = re.search(r"(?:₹|rs\.?|inr)\s*(\d{4,9})", t)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{5,9})\b", t)
    if m:
        return int(m.group(1))
    return None


def find_trade(text: str) -> Optional[str]:
    t = normalize(text).lower()
    for trade, words in TRADES.items():
        for w in words:
            if re.search(w if "\\b" in w else re.escape(w), t):
                return trade
    return None


def yes_no(text: str) -> Optional[bool]:
    t = normalize(text).lower()
    has_no, has_yes = bool(re.search(NO, t)), bool(re.search(YES, t))
    if has_no:
        return False
    if has_yes:
        return True
    return None


def find_new_unit(text: str) -> Optional[bool]:
    t = normalize(text).lower()
    if re.search(r"\b(new|start|starting|naya|nayi|naye|shuru|open a|opening)\b|शुरू|नया|नई|नए", t):
        return True
    if re.search(r"\b(running|existing|already|chal raha|chal rahi|chalta|purana|since)\b|चल रहा|चल रही|पुराना|\d+\s*(years?|yrs|saal)|साल से", t):
        return False
    return None


def find_years(text: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?|saal|साल|varsh|वर्ष)", normalize(text).lower())
    return float(m.group(1)) if m else None


def find_age(text: str) -> Optional[int]:
    t = normalize(text).lower()
    m = re.search(r"(?:age|umar|umr|उम्र)\D{0,6}(\d{2})", t) or re.search(r"(\d{2})\s*(?:years? old|saal ki|saal ka|साल की|साल का)", t)
    return int(m.group(1)) if m else None


def find_gender(text: str) -> Optional[str]:
    t = normalize(text).lower()
    if re.search(r"\b(woman|female|lady|mahila|aurat|she)\b|महिला|औरत", t):
        return "female"
    if re.search(r"\b(man|male|aadmi|purush|he)\b|पुरुष|आदमी", t):
        return "male"
    return None


def find_category(text: str) -> Optional[str]:
    t = normalize(text).lower()
    if re.search(r"\bsc\b|scheduled caste|अनुसूचित जाति", t):
        return "sc"
    if re.search(r"\bst\b|scheduled tribe|अनुसूचित जनजाति", t):
        return "st"
    if re.search(r"\bobc\b|ओबीसी|पिछड़ा", t):
        return "obc"
    if re.search(r"\bgeneral\b|सामान्य", t):
        return "general"
    return None


def find_area(text: str) -> Optional[str]:
    t = normalize(text).lower()
    if re.search(r"\b(village|gaon|gaanv|rural)\b|गाँव|गांव|ग्रामीण", t):
        return "rural"
    if re.search(r"\b(city|shahar|town|urban)\b|शहर|कस्बा", t):
        return "urban"
    return None


def find_name(text: str) -> Optional[str]:
    m = re.search(r"(?:my name is|this is|mera naam|मेरा नाम)\s+([A-Za-zऀ-ॿ]+(?:\s+[A-Za-zऀ-ॿ]+)?)",
                  normalize(text), re.I)
    if m:
        name = re.sub(r"\s+(hai|है|and|aur)$", "", m.group(1).strip(), flags=re.I)
        if name.lower() not in {"a", "an", "the", "tailor", "barber"} and not find_trade(name):
            return name.title()
    return None


def extract_facts(text: str) -> dict:
    """Pull every fact we can recognise out of one message."""
    facts = {}
    trade = find_trade(text)
    if trade:
        facts["trade"] = trade
        facts["sector"] = TRADE_SECTOR.get(trade, "services")
    amount = parse_amount(text)
    if amount and amount >= 5000:
        facts["loan_amount"] = amount
    new = find_new_unit(text)
    if new is not None:
        facts["is_new_unit"] = new
    years = None if find_age(text) else find_years(text)
    if years is not None:
        facts["years_in_business"] = years
        facts.setdefault("is_new_unit", years < 0.5)
    for key, fn in (("age", find_age), ("gender", find_gender), ("social_category", find_category),
                    ("area", find_area), ("owner_name", find_name)):
        value = fn(text)
        if value:
            facts[key] = value
    if re.search(r"udyam|उद्यम", normalize(text).lower()):
        yn = yes_no(text)
        if yn is not None:
            facts["udyam_registered"] = yn
    return facts
