# IDBI Innovate 2026 — MSME Financial Health Card
### Track 03: Financial Inclusion / Digital Lending / Credit Decisioning
_Living design document — updated as we go._

---

## 1. Problem
Banks assess MSME creditworthiness using traditional documents (ITR, audited balance sheet/P&L, bank statements, collateral, credit-bureau score). New-to-Credit (NTC) and New-to-Bank (NTB) MSMEs lack these → they are **"credit-invisible"** → high rejection rates, missed viable borrowers, slow financial inclusion. Yet these businesses generate rich **alternate data** (GST, UPI, EPF, electricity, fuel, etc.). No unified framework exists to turn that data into a reliable credit assessment.

## 2. Solution (one line)
An **MSME Financial Health Card**: ingests alternate data via India's AA/OCEN/ULI rails, computes a **multi-pillar financial-health score**, and presents the loan officer a **traffic-light (RAG) recommendation with clear reasons** — so the bank can confidently approve good borrowers it was previously blind to, while the final decision stays with the human underwriter.

## 3. Guardrails / requirements (from the AMA — non-negotiable)
- **Decision-support, NOT auto-approve.** AI gives score + reason + logic; **the underwriter decides.** Human stays in the loop.
- **Output = RAG (Red/Amber/Green) + risk bucket** (High/Med/Low), in loan-officer language.
- **Never auto-reject thin-file / NTC applicants.** Fall back to physical proxies to estimate turnover.
- **Explainability is mandatory** — plain-language "why" per factor (banks can't deploy a black box).
- **Data reliability / cross-validation** — don't trust a single source (SMS data flagged as unreliable alone).
- **Hybrid scoring** — component sub-scores → unified score, adjusted by segment/locality.
- **Compliance** — RBI AI norms, DPDP Act 2023, data minimization, consent via AA. KYC/Aadhaar/MNRL for identity.
- **Deployment** — AWS-first (their sandbox is AWS); also on-prem deployable. GCP only if API-reachable.
- **Metrics** — never report raw accuracy on imbalanced default data. Use precision/recall, AUC-ROC, KS, Gini.
- IDBI has **no LLM/AI in production yet** (all UAT) → clean explainable-ML story lands well.

## 4. Borrower personas (drive which data connectors activate)
Manufacturer · Trader/Wholesaler · Transport/Logistics · Services · Retail/Kirana · Agri · Gig worker · Salaried individual · Professional (doctor/CA/lawyer).

## 5. Data source catalog (modular connectors)
Each source is a plug-in that outputs standardized features. Personas activate different bundles.

**A. Identity & existence:** Aadhaar/eKYC, PAN, Udyam (MSME reg — category, vintage, activity), Shop&Est/trade license, CIN/GSTIN, MNRL (mobile validity).
**B. Revenue & activity:** GST returns, UPI/POS/payment-gateway settlements, bank statements (AA), e-invoices & e-way bills, marketplace/ONDC seller data.
**C. Physical/operational proxies:** electricity consumption, fuel purchases, FASTag/toll, rent, water, raw-material/supplier invoices.
**D. Workforce/formalization:** EPFO, ESIC, professional tax, payroll.
**E. Assets/wealth:** VAHAN/RTO vehicles, land/property records (via ULI), MF/demat & insurance (via AA).
**F. Behavioral/digital footprint:** utility & mobile bill-payment punctuality, recharge consistency, geo-location, platform reputation. (SMS data = cross-check only, unreliable alone.)
**G. Sector packs:** Agri (land/crop/mandi/satellite/FPO), Transport (FASTag/VAHAN/fuel), Gig (platform earnings + UPI), Salaried (salary credits/EPF/Form16), Professionals (council reg + receipts).

## 6. Scoring pillars (sources → 6 pillars → unified score)
Each pillar produces a 0–100 sub-score.

1. **Revenue & Scale** — GST turnover & trend, UPI/POS inflows, marketplace sales, e-invoices/e-way bills, bank credits.
2. **Cash-Flow Health** — inflow/outflow (AA), UPI velocity, volatility, buffer days, seasonality, expense discipline.
3. **Operational Vitality** (physical proxies) — electricity trend, fuel, FASTag, raw-material purchases, utilities.
4. **Stability & Formalization** — vintage (Udyam), EPFO/ESIC headcount & payroll consistency, professional tax, registration.
5. **Credit Discipline & Obligations** — bureau history (if any), existing EMIs, bounce/return rate, bill-payment & tax-filing punctuality, GST filing regularity.
6. **Identity & Data Reliability** — KYC/Aadhaar/PAN match, MNRL, cross-source consistency, coverage completeness.

## 7. Adaptive weighting (the core "hybrid / thin-file" logic)
**Principle: gather all available + consented + segment-relevant sources; then adaptively re-weight based on what actually arrived.** Not a strict waterfall; not blind "pull everything."

For each pillar p:
```
effective_weight(p) = base_weight(segment, p) × coverage(p) × reliability(p)
```
then renormalize so Σ effective_weight = 1.
```
unified_score = Σ_p effective_weight(p) × subscore(p)
```
- `base_weight` differs by segment (e.g. manufacturer weights Operational Vitality high; salaried weights Cash-Flow/Stability).
- `coverage(p)` ∈ [0,1] = how much of the pillar's data we actually have. Missing source → coverage drops → weight redistributes to other pillars (never auto-reject).
- `reliability(p)` ∈ [0,1] from cross-validation + MNRL + source trust.
- **Thin-file behavior:** thin GST/UPI lowers Revenue/Cash-Flow coverage → weight automatically flows to Operational Vitality (electricity/fuel) & Stability. The system leans harder on proxies it already has.

**Cross-validation / data-confidence:** independently estimate business scale from GST vs UPI vs bank inflows; if estimates agree → high confidence; if they diverge beyond threshold (CV) → lower confidence, flag for underwriter, and shrink the weight of scale-derived pillars. Surface a **data-confidence badge** ("score based on 6 of 9 sources; high confidence").

**Refinement (implemented):** the *Identity & Data Reliability* pillar is computed and displayed but **excluded from the unified-score composition** — it feeds data-confidence, reliability multipliers and flags instead. Including it as a positive pillar put a ~100-point floor on every applicant and compressed the score range upward. The 5 credit pillars drive the score; validated: default rate falls monotonically with score, and RAG bands separate 4%/9%/18% default.

## 8. Output → underwriter cockpit
- **RAG band** 🔴/🟡/🟢 + risk bucket (High/Med/Low).
- **Unified score** + **pillar radar** (strengths vs risks).
- **"Why" panel** — plain-language top +/− drivers (SHAP-style, pillar & feature level).
- **Suggested credit limit** (recommendation, not command).
- **Data-confidence badge** + list of "add these consents/sources to sharpen the score."
- Thin-file → verdict is **"Review"** with what-would-improve-it, never silent reject.

## 9. Ecosystem & architecture (to design for, mock in demo)
- **AA (Account Aggregator)** — consent + data-sharing layer (bank statements, deposits).
- **OCEN (Open Credit Enablement Network)** — lender/borrower/LSP API protocol ("UPI for credit").
- **ULI (Unified Lending Interface)** — RBI data-aggregation platform (GST, land records, Aadhaar…).
- Design: modular connectors → feature store → scoring engine → explainability → cockpit API/UI. AWS-deployable; connectors swap synthetic feed ↔ real sandbox APIs.

## 10. Data for building
- **Now:** generate a realistic **synthetic MSME dataset** (thousands of profiles across personas, each with GST/UPI/EPF/electricity/fuel patterns + a default label). Train & demo on it.
- **After shortlisting:** IDBI provides sandbox APIs + synthetic banking datasets + AWS + mentors. Architecture swaps the synthetic feed for real APIs.

## 11. Evaluation story
- Model quality: AUC-ROC, KS, Gini, precision/recall @ operating point; calibration.
- Inclusion impact: "% of traditionally-rejected MSMEs we can now safely approve," approval-rate lift at fixed risk.
- Explainability + compliance narrative.

## 12. Open decisions
- Stack (leaning: FastAPI scoring API + React/Next.js cockpit; Streamlit = faster but less product-grade).
- Timeline / rounds & deadline (confirm from platform).
- Depth of AA/OCEN/ULI mocking for the prototype.

## Appendix — glossary
MSME, NTC (New to Credit), NTB (New to Bank), GST, UPI, AA, OCEN, ULI, EPFO, ESIC, Udyam, KYC, Aadhaar, MNRL, VAHAN, FASTag, ONDC, DPDP Act, SHAP, RAG, KS statistic, Gini.
