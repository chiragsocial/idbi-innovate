"""
Model loader / predictor used by the backend.

Prefers the calibrated XGBoost artifact (model.joblib) if it exists AND joblib/sklearn
are importable; otherwise falls back to the portable pure-Python logistic model
(logreg_model.json). Both reuse the SAME featurizer, so predictions are consistent.
This lets the backend return a probability-of-default (PD) even on a minimal
(FastAPI-only) deployment where sklearn isn't installed.
"""
import json
import math
import os

from .featurize import Featurizer

ART = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "artifacts")


def _sigmoid(z):
    if z < -60:
        return 0.0
    if z > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


class LogRegPredictor:
    kind = "logreg"

    def __init__(self, art):
        self.w = art["weights"]
        self.b = art["bias"]
        self.threshold = art.get("op_threshold", 0.5)
        fz = Featurizer()
        fz.medians = art["medians"]
        fz.mean = art["mean"]
        fz.std = art["std"]
        fz.categories = art["categories"]
        fz.feature_names = art["feature_names"]
        self.fz = fz

    def predict_proba(self, row):
        x = self.fz.transform([row])[0]
        z = self.b + sum(wi * xi for wi, xi in zip(self.w, x))
        return _sigmoid(z)


class SklearnPredictor:
    def __init__(self, path):
        import joblib
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.fz = bundle["featurizer"]
        self.threshold = bundle.get("op_threshold", 0.5)
        self.kind = bundle.get("kind", "sklearn")

    def predict_proba(self, row):
        import numpy as np
        x = np.array(self.fz.transform([row]), dtype=float)
        return float(self.model.predict_proba(x)[0, 1])


def load_predictor():
    """Return the best available predictor, or None if no artifact exists."""
    joblib_path = os.path.join(ART, "model.joblib")
    if os.path.exists(joblib_path):
        try:
            return SklearnPredictor(joblib_path)
        except Exception:
            pass  # fall through to portable model
    lr_path = os.path.join(ART, "logreg_model.json")
    if os.path.exists(lr_path):
        with open(lr_path) as f:
            return LogRegPredictor(json.load(f))
    return None
