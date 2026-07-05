# ML — default-prediction model

Predicts probability of default (PD) from the alternate-data features. This PD is the
sharp risk **ranking**; it sits alongside the explainable pillar score from `scoring/`.

## Two trainers, one pipeline
Both share `featurize.py` (identical features) and `metrics.py` (identical honest metrics).

| Trainer | Runs where | Model | Purpose |
|---|---|---|---|
| `train_logreg.py` | **anywhere** (pure stdlib) | logistic regression | validate the pipeline; baseline |
| `train_sklearn.py` | **personal laptop** (needs pip) | XGBoost + isotonic calibration | the real model |

## Run

Baseline (no installs):
```bash
python3 -m ml.train_logreg          # from repo root
```

Real model (personal laptop):
```bash
pip install -r ml/requirements.txt
python3 -m ml.train_sklearn
```

## Metrics we report (and why NOT accuracy)
Defaults are ~10% of the book, so a model that predicts "never defaults" is ~90%
"accurate" and useless. We lead with:
- **AUC-ROC** / **Gini** (= 2·AUC−1) — ranking power
- **KS statistic** — max separation of good vs bad distributions (classic scorecard metric)
- **Precision / Recall / F1** at a chosen operating threshold
- **Calibration** by decile — are predicted probabilities trustworthy
Accuracy is printed only, explicitly flagged as not-a-headline.

## Artifacts (`ml/artifacts/`, gitignored)
- `logreg_model.json` — portable baseline (weights + scaler + categories)
- `model.joblib` — calibrated XGBoost + fitted featurizer (loaded by the backend)
- `metrics_*.json` — full metric reports for the deck

## Leakage guard
`entity_id`, the `default` label, and all `_gt_*` ground-truth columns are excluded
from features by the featurizer.
