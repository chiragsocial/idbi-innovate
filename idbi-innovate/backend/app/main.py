"""
MSME Financial Health Card — FastAPI backend.

Wraps the scoring engine in a clean API for the Next.js cockpit:
  GET  /health                     liveness
  GET  /applicants                 list (demos + sample) with summary verdicts
  GET  /applicants/{id}            full Health Card (score, pillars, reasons, PD, series)
  POST /score                      score an arbitrary applicant payload
  POST /simulate                   what-if: add/remove data sources -> re-score + delta
  GET  /portfolio                  inclusion-impact stats for the dashboard
  POST /rails/aa|ocen|uli          mocked AA / OCEN / ULI integrations
  POST /briefing/{id}              OPTIONAL Gemini narration (off unless GEMINI_API_KEY set)
"""
import os
import sys

# make the repo root importable (scoring/, ml/) regardless of launch dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from backend.app.data_store import Store  # noqa: E402
from backend.app import rails  # noqa: E402
from backend.app import briefing  # noqa: E402

app = FastAPI(title="MSME Financial Health Card API", version="1.0")

# CORS — allow the Vercel frontend (set FRONTEND_ORIGIN in prod; * for the demo)
origins = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origins] if origins != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = Store()


# ---------------------------------------------------------------- schemas
class ScoreRequest(BaseModel):
    applicant: dict


class SimulateRequest(BaseModel):
    entity_id: str
    add_sources: list[str] = []
    remove_sources: list[str] = []


# ---------------------------------------------------------------- endpoints
@app.get("/health")
def health():
    return {"status": "ok", "model": store.predictor.kind if store.predictor else "pillar-only",
            "applicants": len(store.raw)}


@app.get("/applicants")
def applicants():
    return store.list_applicants()


@app.get("/applicants/{entity_id}")
def applicant(entity_id: str):
    card = store.get_card(entity_id)
    if card is None:
        raise HTTPException(404, f"Unknown applicant {entity_id}")
    return card


@app.post("/score")
def score(req: ScoreRequest):
    return store.score(req.applicant)


@app.post("/simulate")
def simulate(req: SimulateRequest):
    row = store.raw.get(req.entity_id)
    if row is None:
        raise HTTPException(404, f"Unknown applicant {req.entity_id}")
    before = store.score(row)
    est_rev = store.est_revenue(row)

    new_row = dict(row)
    for s in req.remove_sources:
        new_row = rails.remove_source(new_row, s)
    for s in req.add_sources:
        new_row = rails.apply_source(new_row, s, est_rev)

    after = store.score(new_row)
    return {
        "before": {"unified_score": before["unified_score"], "rag": before["rag"],
                   "recommendation": before["recommendation"], "suggested_limit": before["suggested_limit"],
                   "data_confidence": before["data_confidence"], "ml_pd": before.get("ml_pd")},
        "after": {"unified_score": after["unified_score"], "rag": after["rag"],
                  "recommendation": after["recommendation"], "suggested_limit": after["suggested_limit"],
                  "data_confidence": after["data_confidence"], "ml_pd": after.get("ml_pd")},
        "delta": {
            "unified_score": round(after["unified_score"] - before["unified_score"], 1),
            "data_confidence": round(after["data_confidence"] - before["data_confidence"], 1),
            "suggested_limit": after["suggested_limit"] - before["suggested_limit"],
        },
        "after_card": after,
    }


@app.get("/portfolio")
def portfolio():
    return store.portfolio


@app.get("/fairness")
def fairness():
    """Disparate-impact report (four-fifths rule) — from ml/fairness.py output."""
    import json
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "ml", "artifacts", "fairness.json",
    )
    if not os.path.exists(path):
        raise HTTPException(503, "Fairness report not generated. Run: python -m ml.fairness")
    with open(path) as f:
        return json.load(f)


@app.post("/rails/aa/{entity_id}")
def rail_aa(entity_id: str):
    return rails.aa_consent(entity_id)


@app.post("/rails/ocen/{entity_id}")
def rail_ocen(entity_id: str):
    return rails.ocen_application(entity_id)


@app.post("/rails/uli/{entity_id}")
def rail_uli(entity_id: str):
    return rails.uli_pull(entity_id)


@app.post("/briefing/{entity_id}")
def underwriter_briefing(entity_id: str):
    card = store.get_card(entity_id)
    if card is None:
        raise HTTPException(404, f"Unknown applicant {entity_id}")
    return briefing.generate(card)
