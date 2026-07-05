# Backend — FastAPI scoring API

Wraps the `scoring/` engine + `ml/` model in a REST API for the cockpit, and mocks
the AA / OCEN / ULI rails.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + which model is loaded |
| GET | `/applicants` | list demos + sample with summary verdicts |
| GET | `/applicants/{id}` | full Health Card (score, pillars, reasons, PD, chart series) |
| POST | `/score` | score an arbitrary applicant JSON |
| POST | `/simulate` | what-if: add/remove data sources → re-score + delta |
| GET | `/portfolio` | inclusion-impact stats for the dashboard |
| POST | `/rails/aa/{id}` · `/rails/ocen/{id}` · `/rails/uli/{id}` | mocked rails |
| POST | `/briefing/{id}` | optional Gemini narration (deterministic fallback) |

## Run locally (personal laptop)
```bash
pip install -r backend/requirements.txt
python data/generate.py            # ensure data/output/ exists
python -m ml.train_logreg          # portable PD model (or train_sklearn for XGBoost)
uvicorn backend.app.main:app --reload --port 8000
# open http://localhost:8000/docs  (interactive Swagger UI)
```

## Deploy — Hugging Face Spaces (free, Docker SDK)
1. Create a new **Space** → SDK: **Docker**.
2. Push this repo (the `backend/Dockerfile` builds data + model automatically).
   - In Space settings, point the Dockerfile path to `backend/Dockerfile`, or move it to repo root.
3. It serves on port **7860** (HF default). The public URL becomes the frontend's `API_BASE`.

## Optional LLM briefing
Set `GEMINI_API_KEY` (from Google AI Studio, free tier) in Space secrets to enable
the `/briefing` narration. Without it, `/briefing` returns the deterministic summary.
The LLM only rephrases — it never touches the credit decision.

## Notes
- The predictor auto-selects `model.joblib` (XGBoost) if present + sklearn installed,
  else the portable `logreg_model.json`. So PD works even on the minimal deploy.
- `FRONTEND_ORIGIN` env var locks CORS to your Vercel URL in production (defaults to `*`).
