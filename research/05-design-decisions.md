# 05 · Design decisions

Each decision below traces back to a constraint in the brief.

## 1. Eligibility comes from encoded rules with citations, not from the LLM

**Constraint:** every eligibility claim must cite its source.

- Scheme rules live in [`data/schemes.json`](../data/schemes.json). Each criterion has a plain-language description, the check it performs, and a source URL.
- The engine evaluates criteria deterministically and returns **eligible / not a fit / needs info**, with the list of criteria passed and failed, and their sources.
- An LLM may *rephrase* results (for example into Hindi), but it is never the source of truth for eligibility. In production, rules would be maintained by a reviewer and kept in sync with the official guideline documents, with retrieval over those documents used to suggest updates.

**Why:** rules change and LLMs make things up. A cited, deterministic check can be audited by a branch manager and corrected in one place.

## 2. "Needs info" is a first-class answer

If a rule depends on something the agent doesn't know (for example whether the owner has done PM Vishwakarma basic training), the engine asks instead of guessing. This keeps the "cite your source" promise honest: no claim is made without the fact behind it.

## 3. The readiness score is rule-based and explainable

**Constraint:** risk assessment must be calibrated, fair across gender and region, and explainable.

The score (0–100) adds up a small number of factors, each with a stated reason:

| Factor | Max points | Signal |
|---|---|---|
| Income stability | 25 | Month-to-month variation in inflows |
| Track record | 15 | Months of statement history |
| Repayment capacity | 25 | Proposed EMI as a share of average monthly surplus |
| Customer base | 10 | Distinct payers per month |
| Digital footprint | 10 | Share of inflows that arrive digitally |
| Formal registration | 10 | Udyam or Udyam Assist registration |
| Clean record | 5 | No declared default; minus points for bounced or returned payments |

Every factor shows the owner **what it measured, the points it gave, and how to improve it**.

**Why not a trained model?** There's no labelled repayment data in a hackathon, and a model trained on past approvals could learn the historical bias against women-owned businesses (whose credit gap is the widest; see [01](01-problem-analysis.md)). A transparent rule-based score is a better starting point. With pilot data, the weights can be **calibrated** against real repayment outcomes, while keeping the same factors and explanations.

**Calibration caveat:** the prototype's weights are judgement-based, not yet calibrated. The app says so.

## 4. Fairness: protected attributes never enter the score

- Gender, caste category, religion and region are **never inputs** to the score function. Its signature only accepts cash-flow metrics and registration status.
- Some **scheme rules** legitimately depend on them (Stand-Up India is for SC/ST and women; PMEGP gives special-category applicants a higher subsidy). These are used **only for eligibility**, where the scheme itself requires them, and the UI says so.
- An automated test (`tests/test_fairness.py`) runs the same business through the score with every combination of gender, category and region, and fails if the score changes at all.
- **Proxy check:** factors are cash-flow based, but proxies can still creep in (for example, region can correlate with digital adoption). In a pilot we'd monitor score distributions and approval rates by gender and region, and review any gap.

## 5. Consent first, revocable, minimal

**Constraint:** financial data used only with consent.

- The first screen lists exactly what data is used and why. Nothing is read until the owner agrees.
- The prototype processes everything in the session: nothing is stored or sent anywhere. "Revoke consent" clears the session.
- Production: fetch statements through the Account Aggregator framework, which is consent-based by design, and keep only derived metrics.

## 6. The owner approves every application

**Constraint:** the entrepreneur approves every application.

- The agent prepares a draft. It never submits.
- The final screen shows the full draft and requires an explicit approval checkbox before the file can be downloaded. In the prototype, submission is simulated.

## 7. Built for the owner's reality

- **WhatsApp and voice in production:** owners already use WhatsApp; forms are the barrier.
- **Hindi and regional languages:** the prototype includes an English/Hindi summary; production would add more languages.
- **Works with partial data:** a statement alone is enough to start. Other documents improve the result.
