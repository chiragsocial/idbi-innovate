#!/usr/bin/env python3
"""
scikit-learn / XGBoost trainer — RUN ON YOUR PERSONAL LAPTOP (needs pip installs).

Reuses the SAME featurizer (ml/featurize.py) and honest metrics (ml/metrics.py) as
the pure-Python baseline, so numbers are directly comparable. Trains a gradient-
boosted model (XGBoost if installed, else sklearn HistGradientBoosting) with
class-imbalance handling and isotonic probability calibration, plus a logistic
baseline. Saves a joblib artifact the FastAPI backend loads.

    pip install -r ml/requirements.txt
    python3 -m ml.train_sklearn

Outputs: ml/artifacts/model.joblib + ml/artifacts/metrics_sklearn.json
"""
import json
import os

import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score

from .featurize import Featurizer, load_rows
from . import metrics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "output", "msme_dataset.csv")
ART = os.path.join(ROOT, "ml", "artifacts")


def _make_booster(n_pos, n_neg):
    """XGBoost if available, else sklearn HistGradientBoosting."""
    spw = max(n_neg / max(n_pos, 1), 1.0)
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(
            n_estimators=400, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.8, reg_lambda=1.0,
            scale_pos_weight=spw, eval_metric="auc", n_jobs=-1,
            tree_method="hist",
        ), "xgboost"
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        return HistGradientBoostingClassifier(
            max_depth=4, learning_rate=0.05, max_iter=400,
            l2_regularization=1.0, class_weight="balanced",
        ), "hist_gbm"


def main():
    rows = load_rows(DATA)
    fz = Featurizer().fit(rows)
    X = np.array(fz.transform(rows), dtype=float)
    y = np.array(fz.labels(rows), dtype=int)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    n_pos, n_neg = int(ytr.sum()), int(len(ytr) - ytr.sum())
    print(f"Train {len(Xtr)} / Test {len(Xte)}, {X.shape[1]} features, {n_pos} train defaults")

    results = {}

    # --- gradient boosted (primary) ---------------------------------------
    booster, kind = _make_booster(n_pos, n_neg)
    booster.fit(Xtr, ytr)
    # isotonic calibration for trustworthy probabilities (prefit on a holdout)
    calib = CalibratedClassifierCV(booster, method="isotonic", cv="prefit")
    Xcal, Xte2, ycal, yte2 = train_test_split(Xte, yte, test_size=0.5, stratify=yte, random_state=1)
    calib.fit(Xcal, ycal)
    p_te = calib.predict_proba(Xte2)[:, 1].tolist()
    # pick the operating threshold on the calibration split (not the test split)
    p_cal = calib.predict_proba(Xcal)[:, 1].tolist()
    thr = metrics.best_f1_threshold(ycal.tolist(), p_cal)
    rep = metrics.report(y=yte2.tolist(), p=p_te, threshold=thr)
    calib_curve = metrics.calibration(yte2.tolist(), p_te)
    metrics.print_report(f"TEST ({kind} + isotonic)", rep, calib_curve)
    print(f"  sklearn roc_auc_score cross-check: {roc_auc_score(yte2, p_te):.4f}")
    results[kind] = rep

    # feature importances
    try:
        imp = getattr(booster, "feature_importances_", None)
        if imp is not None:
            top = sorted(zip(fz.feature_names, imp.tolist()), key=lambda kv: -kv[1])[:15]
            print("\n  Top features by importance:")
            for name, v in top:
                print(f"    {name:34s} {v:.4f}")
            results["top_features"] = top
    except Exception:
        pass

    # --- logistic baseline -------------------------------------------------
    lr = LogisticRegression(class_weight="balanced", max_iter=1000)
    lr.fit(Xtr, ytr)
    p_lr = lr.predict_proba(Xte)[:, 1].tolist()
    rep_lr = metrics.report(y=yte.tolist(), p=p_lr)
    metrics.print_report("TEST (logistic baseline)", rep_lr)
    results["logistic"] = rep_lr

    os.makedirs(ART, exist_ok=True)
    joblib.dump({"model": calib, "featurizer": fz, "op_threshold": thr, "kind": kind},
                os.path.join(ART, "model.joblib"))
    with open(os.path.join(ART, "metrics_sklearn.json"), "w") as f:
        json.dump(results, f, indent=2, default=float)
    print(f"\n  Saved -> ml/artifacts/model.joblib + metrics_sklearn.json\n")


if __name__ == "__main__":
    main()
