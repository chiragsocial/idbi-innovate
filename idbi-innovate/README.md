# IDBI Innovate 2026 — MSME Financial Health Card

Alternate-data credit scoring for New-to-Credit / New-to-Bank MSMEs.
**Track 03 — Financial Inclusion / Digital Lending / Credit Decisioning.**

> Decision-**support** for underwriters (not auto-approve): ingest alternate data
> (GST, UPI, Account Aggregator, EPFO, electricity, fuel, FASTag, Udyam…),
> compute a multi-pillar financial-health score, and present a **RAG (Red/Amber/Green)
> recommendation with plain-language reasons**. The human underwriter decides.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full design (data catalog, scoring
pillars, adaptive-weighting formula, architecture, compliance story).

## Results at a glance
- **84.9%** of New-to-Credit and **82%** of thin-file applicants become approvable
- **80.3% inclusion lift** — credit-invisible borrowers a bureau+GST-only model can't even assess
- **Fairness:** NTC disparate-impact **0.912** (passes four-fifths), decision layer **geography-blind** (0.939)
- **Model:** AUC-ROC 0.685 baseline (XGBoost higher), Gini 0.37, KS 0.27 — honest metrics, never raw accuracy
- **Rule-based score validated:** default rate 4% / 9% / 18% across GREEN / AMBER / RED

## For evaluators — where to look
| Want to see… | Open |
|---|---|
| The pitch | [`docs/deck/index.html`](docs/deck/index.html) (open in a browser; ← → to navigate) |
| Live demo path | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |
| Design & data model | [`docs/DESIGN.md`](docs/DESIGN.md) |
| Model governance | [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) · [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) |
| Scoring IP | [`scoring/`](scoring/) — pillars, adaptive weighting, cross-validation, reason codes |
| Run it yourself | [`docs/SETUP.md`](docs/SETUP.md) |

> Everything runs on **synthetic data with zero paid services**. The pure-Python data engine,
> scoring engine, baseline model, and fairness analysis run with **no dependencies**; the
> FastAPI backend and Next.js cockpit need only free, standard tooling.

## Repo layout
```
idbi-innovate/
├── docs/         # design doc, deck notes, compliance/governance writeups
├── data/         # synthetic MSME data engine (pure Python stdlib — no installs)
│   └── output/   # generated datasets (gitignored)
├── ml/           # model training (XGBoost/sklearn) + metrics   [later]
├── backend/      # FastAPI scoring API + mocked AA/OCEN/ULI      [later]
└── frontend/     # Next.js underwriter cockpit                   [later]
```

## Tech stack (all free)
- **Frontend:** Next.js → Vercel (free Hobby)
- **Backend:** FastAPI + model → Hugging Face Spaces (free Docker)
- **LLM (optional, narration/OCR only — never in the credit decision):** Gemini via Google AI Studio (free tier)
- **Data:** synthetic, generated locally

## Quick start

### 1. Generate synthetic data (works anywhere, no dependencies)
```bash
cd data
python3 generate.py            # writes output/msme_dataset.csv + output/demo_profiles.json
python3 generate.py --n 20000  # bigger dataset
```

### 2. Backend / frontend
See `backend/README.md` and `frontend/README.md` (added in later phases).

## Build phases
1. ✅ Foundations + **synthetic data engine**  ← current
2. Scoring engine (pillars + adaptive weighting)
3. ML default model (AUC-ROC / KS / Gini — never raw accuracy)
4. Explainability + reason codes (SHAP + templates)
5. FastAPI backend + mocked AA/OCEN/ULI
6. Next.js underwriter cockpit
7. Fairness / governance / compliance differentiators
8. Deploy + deck + backup demo video
