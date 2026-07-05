# Demo script — MSME Financial Health Card

A tight **4–5 minute** live/recorded walkthrough. Practise once; record a backup.

## Before you start
- Backend running (HF Space warmed, or `uvicorn … :8000` locally).
- Frontend open at the **Cockpit** with the showcase list visible.
- Have the **deck** (`docs/deck/index.html`) open in another tab for the intro/close.

---

## 0:00 — Hook (20s)
> “63 million MSMEs, a ₹20-lakh-crore credit gap — and the reason most are rejected isn’t that
> they’re risky. It’s that they’re **invisible** to the documents banks rely on. We make them
> visible using the data they already generate.”

## 0:20 — The money shot (75s)  ← lead with this, it lands hardest
1. In the showcase list, click **“Thin File NTC Fabrication”**.
2. Point to the **Traditional vs alternate-data** panel:
   > “Traditional lens — no bureau, thin GST — this borrower is rejected, invisible.”
   > “With alternate data — rising electricity, steady EPF payroll — the same borrower is an
   > **AMBER, reviewable, with a ₹5.4 lakh suggested limit**.”
3. Point to the **reason codes**:
   > “And it tells the underwriter exactly why — deterministic, auditable, no black box.”

## 1:35 — How it scores (60s)
1. Point to the **pillar radar + bars**:
   > “Six financial-health pillars. Notice the **weights** — this is adaptive: because GST is
   > thin here, the score leans on electricity and EPF instead. We never auto-reject a thin file.”
2. Point to the **PD chip** and confidence badge:
   > “A calibrated probability-of-default sits alongside the explainable score, with a
   > data-confidence rating.”

## 2:35 — What-if simulator (45s)  ← interactive wow
1. In **What-if**, click **“Request AA consent”** + **“Pull GST returns”** → **Simulate**.
   > “When the underwriter requests more consent, watch confidence jump 67% → 83%, risk fall,
   > and the suggested limit rise. The same business, now more confidently bankable.”

## 3:20 — Data reliability (30s)
1. Click **“Inconsistent Data”** in the list.
   > “We independently estimate revenue from GST, UPI and bank — and flag when they disagree.
   > This one’s routed to manual review. It directly answers the mentors’ ‘false data’ concern.”

## 3:50 — Impact + governance (50s)
1. Go to **Portfolio Impact**:
   > “Across the book: **85% of New-to-Credit** and **82% of thin-file** applicants become
   > approvable — an **80% inclusion lift** — with default rates flat.”
2. Go to **Governance**:
   > “And it’s deployable by a regulated bank: New-to-Credit parity passes the four-fifths test,
   > the decision layer is geography-blind, and it’s consent-first, human-in-the-loop, and fully
   > auditable — RBI and DPDP aligned.”

## 4:40 — Close (20s)
> “A working prototype today; wire it to IDBI’s sandbox APIs tomorrow. We make the
> credit-invisible bankable — safely. Thank you.”

---

## Q&A quick-fire
- **“Is the model deciding?”** No — decision-support. Human underwriter decides; thin-file → review.
- **“Synthetic data — is it real?”** Prototype uses synthetic data mirroring real structure; swaps
  to consented real feeds on the sandbox with no rework.
- **“Why not just XGBoost end-to-end?”** We do have a PD model — but pair it with an explainable
  rule-based scorecard, because a bank can’t deploy an unexplainable credit decision.
- **“Accuracy?”** We deliberately don’t headline accuracy on an imbalanced book — AUC/KS/Gini +
  calibration + disparate-impact are the honest metrics.
- **“Can it be gamed?”** Cross-source validation + MNRL + confidence gating raise the bar; flagged
  cases go to a human.
