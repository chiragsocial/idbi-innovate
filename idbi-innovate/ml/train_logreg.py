#!/usr/bin/env python3
"""
Pure-Python logistic-regression trainer — runs anywhere, no dependencies.

This validates the whole pipeline (featurize -> train -> honest metrics -> artifact)
on this laptop. The scikit-learn/XGBoost trainer (train_sklearn.py) reuses the SAME
featurizer and metrics on your personal laptop for stronger numbers.

    python3 -m ml.train_logreg                 # from repo root
    python3 -m ml.train_logreg --epochs 400 --lr 0.15

Handles class imbalance via inverse-frequency class weights (never raw accuracy).
Writes ml/artifacts/logreg_model.json + ml/artifacts/metrics_logreg.json.
"""
import argparse
import json
import math
import os
import random

from .featurize import Featurizer, load_rows
from . import metrics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "output", "msme_dataset.csv")
ART = os.path.join(ROOT, "ml", "artifacts")


def sigmoid(z):
    if z < -60:
        return 0.0
    if z > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def train(X, y, epochs, lr, l2, seed=0):
    n, d = len(X), len(X[0])
    w = [0.0] * d
    b = 0.0
    n_pos = sum(y) or 1
    n_neg = (n - sum(y)) or 1
    wpos = n / (2.0 * n_pos)   # inverse-frequency class weights
    wneg = n / (2.0 * n_neg)

    idx = list(range(n))
    rng = random.Random(seed)
    for ep in range(epochs):
        rng.shuffle(idx)
        gw = [0.0] * d
        gb = 0.0
        for i in idx:
            xi, yi = X[i], y[i]
            z = b + sum(w[j] * xi[j] for j in range(d))
            pred = sigmoid(z)
            cw = wpos if yi == 1 else wneg
            err = cw * (pred - yi)
            for j in range(d):
                gw[j] += err * xi[j]
            gb += err
        for j in range(d):
            w[j] -= lr * (gw[j] / n + l2 * w[j])
        b -= lr * (gb / n)
    return w, b


def predict(X, w, b):
    return [sigmoid(b + sum(w[j] * xi[j] for j in range(len(xi)))) for xi in X]


def split(rows, test_frac=0.2, seed=42):
    idx = list(range(len(rows)))
    random.Random(seed).shuffle(idx)
    cut = int(len(rows) * (1 - test_frac))
    tr = [rows[i] for i in idx[:cut]]
    te = [rows[i] for i in idx[cut:]]
    return tr, te


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--lr", type=float, default=0.2)
    ap.add_argument("--l2", type=float, default=1e-4)
    args = ap.parse_args()

    rows = load_rows(args.data)
    train_rows, test_rows = split(rows)

    fz = Featurizer().fit(train_rows)
    Xtr, ytr = fz.transform(train_rows), fz.labels(train_rows)
    Xte, yte = fz.transform(test_rows), fz.labels(test_rows)

    print(f"Training logistic regression: {len(Xtr)} train / {len(Xte)} test, "
          f"{len(fz.feature_names)} features, {sum(ytr)} train defaults")
    w, b = train(Xtr, ytr, args.epochs, args.lr, args.l2)

    p_tr = predict(Xtr, w, b)
    p_te = predict(Xte, w, b)
    rep_tr = metrics.report(p=p_tr, y=ytr)
    thr = rep_tr["op_threshold"]
    rep_te = metrics.report(p=p_te, y=yte, threshold=thr)
    calib = metrics.calibration(yte, p_te)

    metrics.print_report("TRAIN (logreg)", rep_tr)
    metrics.print_report("TEST (logreg)", rep_te, calib)

    # top coefficients (rough importance for a linear model on standardized features)
    coefs = sorted(zip(fz.feature_names, w), key=lambda kv: -abs(kv[1]))[:12]
    print("\n  Top features by |coefficient|:")
    for name, c in coefs:
        print(f"    {name:34s} {c:+.3f}")

    os.makedirs(ART, exist_ok=True)
    with open(os.path.join(ART, "logreg_model.json"), "w") as f:
        json.dump({"weights": w, "bias": b, "feature_names": fz.feature_names,
                   "medians": fz.medians, "mean": fz.mean, "std": fz.std,
                   "categories": fz.categories, "op_threshold": thr}, f)
    with open(os.path.join(ART, "metrics_logreg.json"), "w") as f:
        json.dump({"train": rep_tr, "test": rep_te, "calibration": calib,
                   "top_features": coefs}, f, indent=2)
    print(f"\n  Saved -> ml/artifacts/logreg_model.json + metrics_logreg.json\n")


if __name__ == "__main__":
    main()
