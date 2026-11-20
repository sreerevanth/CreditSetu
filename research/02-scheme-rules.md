# 02 · Scheme rules

The rules the CreditSetu eligibility engine encodes, written out in plain language with their sources. The machine-readable version is [`data/schemes.json`](../data/schemes.json). If the two ever disagree, the official source wins.

Checked November 2026. Rules change, so each scheme lists a **Verify** note where the status is moving.

---

## 1. Pradhan Mantri MUDRA Yojana (PMMY)

**What it is:** collateral-free loans through banks, NBFCs and MFIs for income-generating micro enterprises in manufacturing, trading and services, including activities allied to agriculture (poultry, dairy, beekeeping). Both term loans and working capital are covered.

| Category | Loan amount |
|---|---|
| Shishu | up to ₹50,000 |
| Kishore | above ₹50,000 and up to ₹5 lakh |
| Tarun | above ₹5 lakh and up to ₹10 lakh |
| Tarun Plus | above ₹10 lakh and up to ₹20 lakh, for borrowers who have availed and successfully repaid a Tarun loan |

**Rules the engine checks**

- The enterprise is non-corporate and non-farm (allied agriculture is allowed)
- The requested amount falls in a category's range
- Tarun Plus only: a previous Tarun loan has been repaid
- No declared default with a bank or financial institution

**Guarantee:** MUDRA loans are guaranteed through the **Credit Guarantee Fund for Micro Units (CGFMU)**, not CGTMSE. In November 2026 the Union Cabinet approved continuing CGFMU for five years, to 31 March 2031.

**How to apply:** at a lender branch, or online through JanSamarth or Udyamimitra.

**Sources:** [Department of Financial Services – PMMY](https://financialservices.gov.in/index.php/pradhan-mantri-mudra-yojana-pmmy) · [myScheme – PMMY](https://myscheme.gov.in/schemes/pmmy) · [PIB factsheet, Apr 2026](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/apr/doc202648842601.pdf) · [CGFMU continuation, Nov 2026](https://newsonair.gov.in/union-cabinet-approves-continuation-of-credit-guarantee-fund-for-micro-units-under-pm-mudra-yojana-till-march-2031/)

---

## 2. PM Vishwakarma

**What it is:** support for traditional artisans and craftspeople in 18 listed trades, including **Tailor (Darzi)**, Barber, Washerman, Mason, Carpenter, Garland maker, Basket/Mat/Broom maker, Doll and Toy maker and Fishing net maker.

**Credit support**

| Tranche | Amount | Tenure | Condition |
|---|---|---|---|
| 1st | up to ₹1 lakh | 18 months | basic skill training completed |
| 2nd | up to ₹2 lakh | 30 months | 1st tranche availed, standard loan account, and digital transactions adopted or advanced training done |

- Collateral-free, at a **concessional 5% a year**. The Government of India pays lenders up to 8% interest subvention and bears the credit guarantee fee.
- Also: a toolkit incentive of up to ₹15,000 (e-vouchers), and ₹1 per digital transaction up to 100 transactions a month.

**Rules the engine checks**

- The owner's trade is one of the 18 listed trades
- Basic training done (for tranche 1); asks if unknown
- Prior loans under similar self-employment credit schemes (such as PMEGP, PM SVANidhi or MUDRA) in recent years. **Verify** the exact exclusion and any exceptions on the official portal; the engine asks the owner and marks the result "needs info" rather than guessing.

**Why it matters for CreditSetu:** for a tailor like Sunita, PM Vishwakarma at 5% can be much cheaper than a regular MUDRA loan for the first ₹1 lakh. An assistant that only knows MUDRA would miss it. This is exactly the "missed schemes" problem in the brief.

**Sources:** [myScheme – PM Vishwakarma](https://myscheme.gov.in/schemes/pmv) · [PIB factsheet, Sep 2025](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/sep/doc2025916638501.pdf) · [Bank of Baroda – PM Vishwakarma](https://bankofbaroda.in/business-banking/msme-banking/loans-and-advances/pm-vishwakarma-scheme)

---

## 3. Prime Minister's Employment Generation Programme (PMEGP)

**What it is:** a credit-linked subsidy for **setting up new** non-farm micro enterprises, run through KVIC.

| Beneficiary category | Own contribution | Subsidy, urban | Subsidy, rural |
|---|---|---|---|
| General | 10% | 15% | 25% |
| Special (SC/ST/OBC/minorities/women/ex-servicemen/PwD/transgender/NER/hill and border areas/aspirational districts) | 5% | 25% | 35% |

- Maximum project cost: **₹50 lakh for manufacturing, ₹20 lakh for business/service units**
- Applicant must be 18 or older. Only one person per family (self and spouse) can avail it.
- **New units only.** An existing business can't use the margin-money subsidy, except for the separate 2nd loan for upgrading existing PMEGP/REGP/MUDRA units.

**Rules the engine checks:** new unit, project cost within the sector cap, age 18+, applicant category and location (for the subsidy rate only).

**Verify:** PMEGP was approved to 31 March 2026. A government reply in Parliament said continuation for the next five years was under consideration, and some sources report it continuing in 2026-27 on a new portal (pmegp.msme.gov.in). The engine flags PMEGP results with this note until continuation is confirmed.

**Sources:** [myScheme – PMEGP](https://myscheme.gov.in/schemes/pmegp) · [SBI – PMEGP](https://sbi.co.in/web/agri-rural/pmegp) · [Bank of Maharashtra – PMEGP](https://bankofmaharashtra.bank.in/pmegp) · [Kashmir Life on continuation status](https://kashmirlife.net/pmegp-subsidy-release-put-on-hold-pending-scheme-extension-approval-jammu-kashmir-had-1-46-lakh-beneficiaries-centre-446210/)

---

## 4. Stand-Up India

**What it is:** bank loans for **SC/ST and/or women entrepreneurs** to set up a **greenfield (first-time) enterprise** in manufacturing, services, trading or activities allied to agriculture.

- Composite loan (term loan plus working capital) **from ₹10 lakh to ₹1 crore**
- Borrower must be 18 or older. In a non-individual enterprise, at least 51% of the shareholding and controlling stake must be held by SC/ST and/or women.
- Borrower must not be in default to any bank or financial institution.
- In November 2026 the Union Cabinet approved continuing Stand-Up India to 31 March 2031.

**Rules the engine checks:** greenfield, amount ₹10 lakh–₹1 crore, owner category, age, no default.

**Sources:** [myScheme – Stand-Up India](https://myscheme.gov.in/schemes/sui) · [SBI – Stand-Up India](https://sbi.co.in/web/get-business-product-information/stand-up-india) · [Continuation, Nov 2026](https://newsonair.gov.in/union-cabinet-approves-continuation-of-credit-guarantee-fund-for-micro-units-under-pm-mudra-yojana-till-march-2031/)

---

## 5. CGTMSE (Credit Guarantee Fund Trust for Micro and Small Enterprises)

**What it is:** a guarantee **to the lender**, not a loan. Set up by the Ministry of MSME and SIDBI, it lets lenders give collateral-free credit to micro and small enterprises without third-party guarantees.

- Guarantee ceiling raised to **₹10 crore** per borrower (from ₹5 crore, effective April 2025)
- Covers new and existing micro and small enterprises in manufacturing, services and trading
- Coverage is typically 75–85% of the amount in default, **raised to 90% for women-led enterprises**
- The lender applies. The owner can ask the branch to use it.

**How the engine uses it:** shown as a "via lender" result for eligible micro and small enterprises on non-MUDRA loans, with a note that MUDRA loans use CGFMU instead.

**Sources:** [cgtmse.in](https://www.cgtmse.in) · [DC-MSME – Credit Guarantee Scheme](https://dcmsme.gov.in/CLCS_TUS_Scheme/Credit_Guarantee_Scheme/Scheme_Guidelines.aspx) · [Goa MSME – CGTMSE](https://msme.goa.gov.in/home/Scheme-Details/Credit-Guarantee-Scheme-for-Micro-&-Small-Enterprises-(CGTMSE))

---

## Formalisation: Udyam and Udyam Assist

Not a loan scheme, but often the first fix CreditSetu suggests.

- **Udyam Registration** is the MSME registration. Bank loans to registered MSMEs count as priority sector lending.
- The **Udyam Assist Platform (UAP)**, launched January 2023 and built by SIDBI, registers **informal micro enterprises that lack a PAN or GST registration** through designated agencies. Its certificate is treated on a par with Udyam registration for priority sector lending.
- A parliamentary answer reported **2.75 crore** informal micro enterprises formalised through UAP by August 2025, **over 62% of them owned by women**.

**Sources:** [RBI notification on UAP, May 2023](https://rbi.org.in/scripts/NotificationUser.aspx?Id=12500) · [SIDBI – Udyam Assist Platform](https://www.sidbi.in/udyam-assist-platform) · [Lok Sabha answer AU4662](https://eparlib.sansad.in/bitstream/123456789/2996638/1/AU4662_idgGA5.pdf)

---

## Worked example: Sunita (tailor, existing unit, needs ₹3 lakh)

| Scheme | Engine result | Reason |
|---|---|---|
| PM Vishwakarma | **Likely eligible (needs info)** | Tailor is a listed trade. Tranche 1 is up to ₹1 lakh at 5%, after basic training. Needs her answer on prior scheme loans. |
| MUDRA Kishore | **Eligible** | Non-farm micro unit; ₹3 lakh is within the Kishore range (above ₹50,000, up to ₹5 lakh). |
| CGFMU | **Applies with MUDRA** | MUDRA loans are guaranteed through CGFMU. |
| PMEGP | **Not a fit** | Her unit already exists; PMEGP subsidy is for new units. |
| Stand-Up India | **Not a fit** | Loans start at ₹10 lakh and are for greenfield units only. |

A sensible plan for her: PM Vishwakarma tranche 1 for ₹1 lakh at 5%, plus a MUDRA Kishore loan for the rest. The agent proposes this; Sunita decides.
