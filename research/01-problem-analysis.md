# 01 · Problem analysis

## The brief

Hackathon theme **MSME Finance and Compliance**, problem statement **3.2**:

> Viable small businesses cannot reach formal credit or the schemes meant for them.

The brief tags the problem **Agentic AI**. Its key points:

- **Who:** viable small businesses such as tailors, fabricators, dairy units and SHG-run enterprises. They often have steady income visible in UPI flows, but not the paperwork banks recognise (ITRs, audited statements).
- **Pain:** they miss an estimated 70–80% of the schemes they qualify for. A loan needs 15–20 documents and months of follow-up. Middlemen take 10–15% of the loan. Without ITRs, many turn to moneylenders at 24–36%. Expensive working capital eats margins, and growth is postponed season after season.
- **Other stakeholders:** bank branches and NBFCs, District Industries Centres (DICs) and scheme agencies, business correspondents and agents, SHG federations.
- **Hard constraints:**
  1. Every eligibility claim must cite its source.
  2. Risk assessment must be calibrated, fair across gender and region, and explainable.
  3. Financial data is used only with consent.
  4. The entrepreneur approves every application.
- **Also noted:** every incomplete file costs lenders time.

## Root causes

| Root cause | What it looks like on the ground | What CreditSetu does about it |
|---|---|---|
| **Information gap** | Owners don't know which schemes exist or which one fits. Scheme rules are spread across ministry sites, bank pages and PDFs. | Matches the owner to schemes and explains why, citing the rule |
| **Paperwork gap** | No ITR or audited accounts. Income is real but informal. | Builds a profile from bank and UPI statements the owner already has |
| **Process gap** | 15–20 documents, repeated branch visits, files rejected as incomplete | Checklist of missing documents, pre-filled application, follow-up tracking |
| **Trust gap** | Owners rely on agents who charge 10–15%. Lenders distrust thin files. | Transparent, cited outputs both sides can check |
| **Assessment gap** | Collateral-based lending excludes asset-light micro units | An explainable cash-flow score, using the same kind of signal regulators are pushing lenders toward (see [04](04-landscape.md)) |

## Size of the problem

- SIDBI's May 2025 report (prepared with Crisil, survey of 2,097 MSMEs in 19 sectors) puts the MSME sector's **addressable credit gap at about 24%, roughly ₹30 lakh crore**. ([SIDBI](https://www.sidbi.in/blog/the-msme-credit-gap-in-india-what-does-the-data-say))
- The same report finds the gap is **higher for women-owned MSMEs (about 35%)** and for services (about 27%). Readymade garments is one of the sectors it flags as needing targeted help. ([Drishti summary of the SIDBI report](https://www.drishtiias.com/pdf/1755156312.pdf), [Outlook Business](https://www.outlookbusiness.com/planet/industry/sidbi-msme-credit-gap-digital-lending))
- A NITI Aayog report on MSME competitiveness estimates that a much larger share of MSME credit, about ₹80 lakh crore, is met by informal sources, often at 30–60% a year. ([Entrepreneur India](https://www.entrepreneur.com/en-in/news-and-trends/indias-inr-80-lakh-crore-credit-problem-for-msmes/491098))

These two figures measure different things (an addressable gap versus informal borrowing), so the pitch uses the SIDBI figure.

**Why this matters for the design:** the gap is widest for women-owned businesses, so the fairness constraint isn't box-ticking. A model trained on past lending data could easily reproduce the gap. That is one reason the readiness score is rule-based and tested for invariance (see [05](05-design-decisions.md)).

## What "success" means

For the hackathon prototype:

- An owner with only a bank or UPI statement gets a cited list of schemes they fit, an explained readiness score, and a draft application, in one session.
- Every eligibility answer shows the rule and its source link.
- Changing gender or region, with everything else the same, never changes the score.

For a pilot (see the roadmap in the main README):

- Share of applications that reach sanction, and time to sanction, compared with a control group
- Share of files the branch accepts as complete on first submission
- Owner understanding: can they explain back why they qualified?
