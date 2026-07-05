"""
In-memory applicant store for the backend.

Loads the curated demo profiles + a sample of the synthetic dataset, scores each
via the scoring engine (attaching the ML probability-of-default), indexes by
entity_id, and precomputes portfolio-level impact stats for the dashboard.
"""
import csv
import json
import os

from scoring import score_entity
from scoring import crossval
from ml.predict import load_predictor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEMO = os.path.join(ROOT, "data", "output", "demo_profiles.json")
CSV = os.path.join(ROOT, "data", "output", "msme_dataset.csv")

PORTFOLIO_SAMPLE = 1500   # rows scored for the impact dashboard


class Store:
    def __init__(self):
        self.predictor = load_predictor()
        self.raw = {}       # entity_id -> raw row
        self.demo_ids = []
        self.sample_ids = []
        self.portfolio = {}
        self._load()

    # ---------------------------------------------------------------- loading
    def _load(self):
        with open(DEMO) as f:
            demos = json.load(f)
        for d in demos:
            self.raw[d["entity_id"]] = d
            self.demo_ids.append(d["entity_id"])

        rows = []
        if os.path.exists(CSV):
            with open(CSV) as f:
                rows = list(csv.DictReader(f))
        for r in rows[:200]:
            self.raw[r["entity_id"]] = r
            self.sample_ids.append(r["entity_id"])

        self._compute_portfolio(rows[:PORTFOLIO_SAMPLE] or [self.raw[i] for i in self.demo_ids])

    # ---------------------------------------------------------------- scoring
    def score(self, row):
        card = score_entity(row)
        if self.predictor is not None:
            try:
                pd = self.predictor.predict_proba(row)
                card["ml_pd"] = round(pd, 4)
                card["ml_model"] = self.predictor.kind
            except Exception:
                card["ml_pd"] = None
        else:
            card["ml_pd"] = None
        return card

    def get_card(self, entity_id):
        row = self.raw.get(entity_id)
        if row is None:
            return None
        card = self.score(row)
        # attach demo metadata + chart series if present
        if "_demo_name" in row:
            card["demo_name"] = row["_demo_name"]
            card["demo_note"] = row["_demo_note"]
        if "series" in row:
            card["series"] = row["series"]
        return card

    def summary(self, entity_id):
        card = self.get_card(entity_id)
        return {
            "entity_id": entity_id,
            "segment": card["segment"],
            "is_ntc": card["is_ntc"],
            "rag": card["rag"],
            "unified_score": card["unified_score"],
            "recommendation": card["recommendation"],
            "suggested_limit": card["suggested_limit"],
            "data_confidence": card["data_confidence"],
            "ml_pd": card.get("ml_pd"),
            "demo_name": card.get("demo_name"),
            "demo_note": card.get("demo_note"),
        }

    def list_applicants(self):
        return {
            "demos": [self.summary(i) for i in self.demo_ids],
            "sample": [self.summary(i) for i in self.sample_ids],
        }

    def est_revenue(self, row):
        return crossval.assess(row)["estimated_revenue"]

    # ---------------------------------------------------------------- portfolio
    def _compute_portfolio(self, rows):
        from collections import Counter
        rag = Counter()
        rec = Counter()
        ntc_total = ntc_approvable = 0
        thinfile_total = thinfile_approvable = 0
        traditional_rejected = alt_recovered = 0
        n = 0
        for r in rows:
            card = score_entity(r)
            n += 1
            rag[card["rag"]] += 1
            rec[card["recommendation"]] += 1
            is_ntc = str(r.get("is_ntc")) == "1"
            has_bureau = str(r.get("bureau_available")) == "1"
            has_gst = str(r.get("gst_available")) == "1"
            approvable = card["recommendation"] in ("APPROVE", "REVIEW")
            if is_ntc:
                ntc_total += 1
                ntc_approvable += approvable
            srcs = sum(str(r.get(f"{s}_available")) == "1"
                       for s in ["gst", "upi", "aa", "epf", "electricity", "fuel", "fastag", "bureau"])
            if srcs <= 3:
                thinfile_total += 1
                thinfile_approvable += approvable
            # "traditional" = would a bureau+GST-only model even assess them?
            if not has_bureau and not has_gst:
                traditional_rejected += 1
                if approvable:
                    alt_recovered += 1
        self.portfolio = {
            "scored": n,
            "rag_distribution": dict(rag),
            "recommendation_distribution": dict(rec),
            "ntc": {"total": ntc_total, "approvable": ntc_approvable,
                    "rate": round(ntc_approvable / ntc_total, 3) if ntc_total else 0},
            "thin_file": {"total": thinfile_total, "approvable": thinfile_approvable,
                          "rate": round(thinfile_approvable / thinfile_total, 3) if thinfile_total else 0},
            "inclusion_lift": {
                "traditionally_invisible": traditional_rejected,
                "recovered_by_alt_data": alt_recovered,
                "rate": round(alt_recovered / traditional_rejected, 3) if traditional_rejected else 0,
            },
        }
