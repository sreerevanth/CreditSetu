# 04 · Landscape

What already exists, and where CreditSetu fits. The short version: India has built strong **rails** (portals, consent-based data sharing, lending interfaces). What's missing is a trusted **guide** that sits on the owner's side, speaks their language, and turns those rails into a finished application.

## Government portals and public infrastructure

| What | What it does | Gap CreditSetu fills |
|---|---|---|
| **JanSamarth** (national portal for credit-linked government schemes) | Launched June 2022. Brings credit-linked central schemes onto one portal across agriculture, livelihood, education, business, housing and more; checks eligibility, gives in-principle approval and routes the application to a bank. The Department of Financial Services lists 15 schemes; a June 2026 PIB document says 16. | The owner has to know to go there and answer its questions alone. CreditSetu works from documents the owner already has, explains each result with a cited rule, and can hand off to JanSamarth for the application. |
| **Udyamimitra** (SIDBI) | Online portal for MUDRA and other MSME loan applications, with hand-holding agencies | Same: a destination, not a guide |
| **Udyam Assist Platform** | Formalises informal micro enterprises without PAN/GST through designated agencies; certificate counts for priority sector lending | CreditSetu can recommend it as a fix and help the owner through it |
| **Account Aggregator (AA)** | RBI framework for consent-based sharing of financial data between institutions. GSTN is being added as a data provider, which is expected to push cash-flow-based MSME lending further. | CreditSetu's production version should fetch statements through AA instead of uploads. Same consent principle, stronger rails. |
| **Unified Lending Interface (ULI)** | RBI's digital public infrastructure for loan origination: consent-based access to verified borrower data for lenders. In 2026 the RBI Governor urged banks to use ULI and AA to widen MSME credit. | Lender-side infrastructure. CreditSetu is the borrower-side companion that gets the owner ready. |
| **OCEN** (Open Credit Enablement Network) | Open API framework connecting lenders, loan service providers and data providers for cash-flow-based MSME credit. It explicitly has a role for a **borrower agent** acting for the borrower. | CreditSetu is a natural fit for that borrower-agent role. |

## Private players

| Type | Examples | Gap |
|---|---|---|
| **Digital MSME lenders and NBFCs** | Lendingkart, FlexiLoans, Indifi and similar | They lend their own products. They aren't neutral about government schemes, and rates are often far higher than scheme-backed loans. |
| **Bank scheme pages and eligibility checkers** | SBI, HDFC, Bank of Baroda and others | Each covers its own products; nobody compares across schemes for the owner |
| **Informal agents** | Local loan "fixers" | Charge 10–15% of the loan, opaque, sometimes exploitative. This is the incumbent CreditSetu replaces. |

## Positioning

CreditSetu is **not a lender and not another portal**. It is a **borrower-side agent**:

1. **Neutral:** recommends the cheapest fitting option, including 5% PM Vishwakarma loans that a lender's own app would never suggest.
2. **Starts from what the owner has:** a UPI or bank statement, invoice photos, voice in their language.
3. **Explainable:** every match cites its rule; every score shows its factors.
4. **Finishes the job:** produces a complete file, then hands off to the lender, JanSamarth or Udyamimitra.

## Implications for the roadmap

- **Prototype (now):** statement upload and a local rules file, to prove the reasoning and the explanations.
- **Pilot:** keep uploads, add the hand-off to JanSamarth / Udyamimitra, and partner with one SHG federation and one bank branch.
- **Scale:** fetch data through Account Aggregator; integrate as a borrower agent on OCEN/ULI-connected lender flows.

**Sources:** see [sources.md](sources.md), section "Landscape".
