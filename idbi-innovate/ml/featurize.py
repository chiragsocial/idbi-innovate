"""
Feature engineering for the default-prediction model (pure stdlib).

Shared by both trainers (pure-Python logistic regression AND scikit-learn/XGBoost)
so features are identical regardless of which model is used.

Key choices:
  * Missing-not-at-random: an absent source is itself informative, so we keep the
    `*_available` flags AND median-impute the missing numeric value.
  * Money/count features are log1p-transformed (heavy right skew).
  * `segment` and `state` are one-hot encoded.
  * Leakage guard: entity_id, the `default` label, and ALL `_gt_*` ground-truth
    columns (incl. `_gt_default_prob`) are excluded from features.
"""
import csv
import math

LABEL = "default"

# Raw numeric features.
_MONEY = [  # log1p-transformed (heavy skew)
    "gst_turnover_monthly", "upi_inflow_monthly", "upi_txn_count",
    "bank_inflow_monthly", "bank_outflow_monthly", "bank_avg_balance",
    "existing_emi_monthly", "epf_employee_count", "electricity_units_monthly",
    "fuel_spend_monthly", "fastag_toll_monthly",
]
_LINEAR = [  # used as-is
    "vintage_months", "gst_trend_pct", "gst_volatility", "gst_filing_regularity",
    "gst_months_filed", "upi_volatility", "bank_buffer_days", "bank_bounces_12m",
    "epf_months_contributed", "electricity_trend_pct", "bureau_score", "city_tier",
]
_FLAGS = [
    "is_ntc", "is_ntb", "has_udyam", "mnrl_flag",
    "gst_available", "upi_available", "aa_available", "epf_available",
    "electricity_available", "fuel_available", "fastag_available", "bureau_available",
]
_CATEGORICAL = ["segment", "state"]

_NUMERIC = _MONEY + _LINEAR


def _f(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_rows(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def _derived(row):
    """A few engineered ratios that carry real credit signal."""
    emi = _f(row.get("existing_emi_monthly")) or 0.0
    rev = (_f(row.get("gst_turnover_monthly")) or _f(row.get("bank_inflow_monthly"))
           or _f(row.get("upi_inflow_monthly")) or 0.0)
    oblig = (emi / rev) if rev > 0 else 0.0
    bounces = _f(row.get("bank_bounces_12m")) or 0.0
    return {
        "d_obligation_ratio": min(oblig, 1.0),
        "d_bounce_rate": bounces / 12.0,
        "d_log_revenue": math.log1p(rev),
    }


_DERIVED = ["d_obligation_ratio", "d_bounce_rate", "d_log_revenue"]


class Featurizer:
    """fit() learns imputation medians, standardization stats, and category sets."""

    def __init__(self):
        self.medians = {}
        self.mean = {}
        self.std = {}
        self.categories = {}
        self.feature_names = []

    def fit(self, rows):
        # medians for numeric imputation
        for col in _NUMERIC:
            vals = [_f(r.get(col)) for r in rows]
            vals = sorted(v for v in vals if v is not None)
            self.medians[col] = vals[len(vals) // 2] if vals else 0.0
        # category sets
        for col in _CATEGORICAL:
            self.categories[col] = sorted({r.get(col, "") for r in rows})
        # build raw (pre-standardization) matrix to learn mean/std
        raw = [self._raw_numeric(r) for r in rows]
        cont_cols = _NUMERIC + _DERIVED
        for i, col in enumerate(cont_cols):
            xs = [row[i] for row in raw]
            m = sum(xs) / len(xs)
            var = sum((x - m) ** 2 for x in xs) / max(len(xs) - 1, 1)
            self.mean[col] = m
            self.std[col] = math.sqrt(var) or 1.0
        # final feature name order: standardized numerics + derived + flags + one-hot
        self.feature_names = list(cont_cols) + list(_FLAGS)
        for col in _CATEGORICAL:
            self.feature_names += [f"{col}={c}" for c in self.categories[col]]
        return self

    def _raw_numeric(self, row):
        out = []
        for col in _MONEY:
            v = _f(row.get(col))
            v = self.medians[col] if v is None else v
            out.append(math.log1p(max(v, 0.0)))
        for col in _LINEAR:
            v = _f(row.get(col))
            out.append(self.medians[col] if v is None else v)
        d = _derived(row)
        for col in _DERIVED:
            out.append(d[col])
        return out

    def transform(self, rows):
        cont_cols = _NUMERIC + _DERIVED
        X = []
        for r in rows:
            raw = self._raw_numeric(r)
            vec = [(raw[i] - self.mean[c]) / self.std[c] for i, c in enumerate(cont_cols)]
            vec += [1.0 if str(r.get(c)) == "1" else 0.0 for c in _FLAGS]
            for col in _CATEGORICAL:
                cur = r.get(col, "")
                vec += [1.0 if cur == c else 0.0 for c in self.categories[col]]
            X.append(vec)
        return X

    def labels(self, rows):
        return [int(r[LABEL]) for r in rows]
