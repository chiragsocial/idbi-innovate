#!/usr/bin/env python3
"""
SHAP explainability for the trained model — RUN ON PERSONAL LAPTOP (needs pip installs).

Two purposes:
  1. Global: which features drive the model overall (bar summary) — for the deck.
  2. Local: per-applicant SHAP attributions, aggregated to the SIX PILLARS so the
     model's "why" lines up with the rule-based reason codes. If the ML attribution
     and the rule-based explanation agree, that's a strong trust signal for judges.

    pip install -r ml/requirements.txt
    python3 -m ml.train_sklearn          # produces model.joblib first
    python3 -m ml.shap_explain

Outputs: ml/artifacts/shap_global.json + ml/artifacts/shap_pillar_map.json
"""
import json
import os

import numpy as np
import joblib
import shap

from .featurize import Featurizer, load_rows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "output", "msme_dataset.csv")
ART = os.path.join(ROOT, "ml", "artifacts")

# Map each raw feature name onto one of the six scoring pillars, so model-based
# attributions can be summed per pillar (same taxonomy as scoring/pillars.py).
_PILLAR_OF = {
    "revenue_scale": ["gst_turnover_monthly", "gst_trend_pct", "upi_inflow_monthly",
                      "upi_txn_count", "d_log_revenue", "electricity_trend_pct"],
    "cash_flow": ["bank_inflow_monthly", "bank_outflow_monthly", "bank_avg_balance",
                  "bank_buffer_days", "upi_volatility", "gst_volatility"],
    "operational_vitality": ["electricity_units_monthly", "fuel_spend_monthly",
                             "fastag_toll_monthly", "electricity_available",
                             "fuel_available", "fastag_available"],
    "stability_formalization": ["vintage_months", "epf_employee_count",
                                "epf_months_contributed", "has_udyam",
                                "gst_filing_regularity", "gst_months_filed", "epf_available"],
    "credit_discipline": ["bureau_score", "existing_emi_monthly", "bank_bounces_12m",
                          "d_obligation_ratio", "d_bounce_rate", "is_ntc", "bureau_available"],
    "identity_reliability": ["mnrl_flag", "is_ntb"],
}


def _pillar_for(feature_name):
    base = feature_name.split("=")[0]  # collapse one-hot "segment=x"
    for pillar, feats in _PILLAR_OF.items():
        if base in feats:
            return pillar
    if base in ("segment", "state"):
        return "context"
    return "context"


def main():
    bundle = joblib.load(os.path.join(ART, "model.joblib"))
    fz, calib = bundle["featurizer"], bundle["model"]
    names = fz.feature_names

    rows = load_rows(DATA)
    X = np.array(fz.transform(rows), dtype=float)

    # calibrated classifier wraps the booster — explain the underlying estimator
    base_est = calib.calibrated_classifiers_[0].estimator
    explainer = shap.TreeExplainer(base_est)
    sample = X[:1000]
    sv = explainer.shap_values(sample)
    if isinstance(sv, list):
        sv = sv[1]

    # global importance = mean |shap|
    mean_abs = np.abs(sv).mean(axis=0)
    global_imp = sorted(zip(names, mean_abs.tolist()), key=lambda kv: -kv[1])
    with open(os.path.join(ART, "shap_global.json"), "w") as f:
        json.dump(global_imp[:25], f, indent=2)

    # aggregate mean|shap| per pillar
    pillar_tot = {}
    for name, v in zip(names, mean_abs.tolist()):
        pillar_tot.setdefault(_pillar_for(name), 0.0)
        pillar_tot[_pillar_for(name)] += v
    with open(os.path.join(ART, "shap_pillar_map.json"), "w") as f:
        json.dump(pillar_tot, f, indent=2)

    print("Global top features (mean |SHAP|):")
    for name, v in global_imp[:15]:
        print(f"  {name:34s} {v:.4f}")
    print("\nAttribution aggregated to pillars:")
    for p, v in sorted(pillar_tot.items(), key=lambda kv: -kv[1]):
        print(f"  {p:26s} {v:.4f}")
    print("\n  Saved -> ml/artifacts/shap_global.json + shap_pillar_map.json")
    print("  (If these pillar rankings track the rule-based reason codes, that's your trust story.)")


if __name__ == "__main__":
    main()
