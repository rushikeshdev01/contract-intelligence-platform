"""
Reference glossary of Indian statutes commonly relevant to commercial contract
risk. This is given to the Risk Analyzer as grounding context so it can cite a
real, specific statute/section when relevant — rather than inventing one or
giving a vague "this may not be legally sound" comment.

This is informational grounding only, not a substitute for legal advice.
"""

INDIAN_LEGAL_REFERENCES = """
- Indian Contract Act, 1872 — Section 23: an agreement is void if its
  consideration or object is unlawful (relevant to unusually one-sided or
  unconscionable clauses).
- Indian Contract Act, 1872 — Section 27: any agreement that restrains a
  person from carrying on a lawful profession, trade, or business is void to
  that extent (directly relevant to non-compete clauses, which are largely
  unenforceable in India except in narrow circumstances like the sale of
  goodwill).
- Indian Contract Act, 1872 — Section 73/74: compensation for breach is
  limited to reasonable compensation, and stipulated penalty clauses are
  capped at what is "reasonable," not automatically enforced at face value
  (relevant to liquidated damages / penalty clauses).
- Indian Contract Act, 1872 — Section 124/125: rules governing indemnity
  and guarantee contracts (relevant to indemnification clauses).
- Information Technology Act, 2000 — Section 43A: bodies handling sensitive
  personal data must implement reasonable security practices, with liability
  for negligence causing wrongful loss (relevant to data-handling /
  confidentiality clauses in SaaS and vendor agreements).
- Specific Relief Act, 1963: governs when specific performance (forcing a
  party to actually perform, not just pay damages) can be sought — relevant
  to termination and remedy clauses.
- Arbitration and Conciliation Act, 1996: governs the enforceability of
  arbitration/dispute-resolution clauses if the contract specifies
  arbitration.
"""