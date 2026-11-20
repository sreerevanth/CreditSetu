"""CreditSetu: a borrower-side agent that connects small businesses to formal credit and schemes.

The core is deliberately deterministic:
- ``statement``  reads a bank or UPI statement into transactions
- ``profile``    turns transactions into cash-flow metrics
- ``schemes``    checks encoded scheme rules and returns cited results
- ``score``      computes an explainable readiness score that never sees protected attributes
- ``application`` drafts a loan file for the owner to review and approve
- ``explain``    writes plain-language summaries (template-based, optionally via an LLM)
"""

__version__ = "0.1.0"
