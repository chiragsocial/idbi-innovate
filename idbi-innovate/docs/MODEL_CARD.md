# Model Card — MSME Financial Health Card

_Governance artefact for the IDBI Innovate 2026 credit-decisioning prototype._
_Following the spirit of Google's Model Cards + RBI model-governance expectations._

## 1. Overview
A decision-**support** system that scores MSME / individual credit applicants — especially
**New-to-Credit (NTC)** and **New-to-Bank (NTB)** — using alternate data, and returns an
explainable RAG recommendation to a human underwriter. It combines:
- a **rule-based pillar scorecard** (6 pillars → unified 0–100 score, adaptive weighting), and
- a **gradient-boosted probability-of-default (PD) model** for sharp risk ranking.

## 2. Intended use
- **In scope:** underwriter decision support for MSME/retail asset loans; lead triage;
  surfacing credit-invisible-but-creditworthy borrowers.
- **Out of scope:** fully automated approve/decline without human review; use as the sole
  basis of an adverse decision. The **human underwriter makes the final credit decision.**

## 3. Data
- Trained on a **synthetic** MSME dataset (5,000 applicants across 9 personas) generated to
  mirror real alternate-data structure (GST, UPI, Account Aggregator, EPFO, electricity,
  fuel, FASTag, Udyam, bureau). Base default rate **≈10.8%**.
- On the bank's sandbox, the synthetic feed is swapped for consented real data via AA/ULI.
- **Leakage guard:** identifiers and all ground-truth latent columns are excluded from features.

## 4. Features
62 features across the six pillars: Revenue & Scale, Cash-Flow Health, Operational Vitality,
Stability & Formalization, Credit Discipline, and Identity & Data Reliability (the last feeds
data-confidence, not the score). Missing-not-at-random handled via availability flags +
median imputation.

## 5. Performance (honest metrics — never raw accuracy on imbalanced data)
| Metric | Baseline logistic (portable) | Gradient-boosted (personal-laptop target) |
|---|---|---|
| AUC-ROC | 0.685 | ~0.72–0.78 (expected) |
| Gini | 0.370 | ~0.44–0.56 |
| KS | 0.274 | higher |
Calibration monotonic by decile. Rule-based score also validated: default rate falls
monotonically with score; RAG bands separate **4% / 9% / 18%** default (GREEN/AMBER/RED).

## 6. Fairness / disparate-impact (see `ml/artifacts/fairness.json`)
Four-fifths (80%) rule on approval rates:
- **New-to-Credit parity: DI 0.912 — PASS.** NTC approval 85.4% vs non-NTC 77.9%, with equal
  default rates (11.0% vs 10.6%). We do **not** penalise the credit-invisible.
- **Geography: DI 0.939 — PASS.** The rule-based decision layer uses **no geographic
  attribute**, so location does not drive the recommendation.
- **Segment: DI 0.642 — REVIEW, but risk-justified.** Lower approval for gig (60%, 16% default)
  vs manufacturer (93%, 8%) tracks *actual* default risk, not bias; segment is a legitimate
  business-risk dimension, not a protected class. Mitigation: monitor, and keep segment
  effects tied to observed default experience.

## 7. Explainability
Every score ships with **deterministic reason codes** (templated from explicit driver values —
no LLM in the decision path) and, on the trained model, **SHAP attributions mapped to the same
six pillars**. Rule-based and model-based explanations are designed to corroborate each other.

## 8. Human oversight
The system never auto-approves. Thin-file / low-confidence / cross-source-inconsistent cases
are routed to **REVIEW** (never auto-rejected). Output is a recommendation + evidence; the
underwriter decides and can override.

## 9. Limitations
- Synthetic training data — real-world calibration required on sandbox data before production.
- Alternate-data sources can be gamed or stale; the cross-validation engine mitigates but does
  not eliminate this.
- PD probabilities are calibrated on synthetic distributions; recalibrate on real data.

## 10. Monitoring plan (production)
Population Stability Index (PSI) on features/score; periodic AUC/KS re-check; ongoing
disparate-impact monitoring; drift alerts; scheduled recalibration; human-override tracking.

## 11. Regulatory alignment
RBI AI/ML governance expectations, fair-lending, and DPDP Act 2023 — see `docs/COMPLIANCE.md`.
