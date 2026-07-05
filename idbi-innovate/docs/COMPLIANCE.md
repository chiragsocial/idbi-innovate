# Compliance, Consent & Data Governance

How the MSME Financial Health Card aligns with India's regulatory expectations. The AMA
mentors were explicit: the solution must stay within RBI/regulatory norms, keep the human
underwriter in control, and treat data reliability seriously. This document maps our design to
those requirements.

## 1. Consent-first data (Account Aggregator)
- All financial data is pulled **only with the borrower's explicit consent** through the
  RBI-regulated **Account Aggregator** framework — never scraped or inferred without permission.
- Consent is **purpose-bound** ("MSME credit assessment") and **time-bound** to the application.
- The `/rails/aa/{id}` endpoint models the consent artefact and records an **audit-trail entry**.

## 2. Data minimisation & purpose limitation (DPDP Act 2023)
- We gather only sources **relevant to the applicant's segment**, and the **adaptive weighting**
  down-weights sources we don't need — we do not hoard data "just in case."
- Each score records **which sources were used** (`sources_used`) and a **data-confidence** figure,
  supporting a defensible, minimal data footprint.

## 3. Human-in-the-loop (no automated adverse action)
- Per the AMA mandate, **the AI never decides** — it recommends. Credit approval/decline rests
  with the underwriter.
- Thin-file, low-confidence, and cross-source-inconsistent cases are routed to **REVIEW**, never
  auto-rejected. This avoids automated adverse action against the credit-invisible.

## 4. Right to explanation (auditable, deterministic)
- Every decision carries **plain-language reason codes generated deterministically** from explicit
  driver values — reproducible and defensible to a regulator or an appeal.
- The optional LLM (Gemini) **only rephrases** this output; it is architecturally excluded from the
  scoring decision, so no black-box generative model influences credit outcomes.

## 5. Data reliability & fraud resistance
- The **cross-validation engine** independently estimates business size from multiple sources
  (GST vs UPI vs bank) and **flags disagreement** — directly addressing the mentors' "wrong account
  number → false data" concern.
- **MNRL** (Mobile Number Revocation List) checks flag stale/invalid contact identities.
- Identity/reliability signals lower **data-confidence** and route to review rather than silently
  inflating a score.

## 6. Fairness / non-discrimination
- Disparate-impact monitoring (four-fifths rule) is built in (`ml/fairness.py`).
- **New-to-Credit parity** is demonstrated (DI 0.912). The **decision layer is geography-blind**
  (DI 0.939). Segment differences track observed default risk, not protected characteristics.
- No protected attributes (caste, religion, gender) are used or collected.

## 7. Security & deployment
- Deployable **on-prem or on the bank's AWS sandbox** (containerised); no dependency on external
  compute for the credit decision.
- Secrets (optional LLM key) via environment/secret store, never in code. CORS locked to the
  approved frontend origin in production.

## 8. Model governance
- Documented in `docs/MODEL_CARD.md`: intended use, metrics, limitations, monitoring (PSI, AUC/KS
  re-checks, drift, recalibration), and human-override tracking.

## 9. Ecosystem alignment
- Built to plug into **AA** (consent + data), **OCEN** (lender/borrower/LSP protocol), and **ULI**
  (RBI unified data aggregation) — the standardised public rails, not proprietary scraping.

---
_Summary: consent-first, data-minimising, human-in-the-loop, deterministic-and-explainable,
fairness-monitored, and ecosystem-aligned — the properties a regulated bank needs before it can
deploy an AI credit model._
