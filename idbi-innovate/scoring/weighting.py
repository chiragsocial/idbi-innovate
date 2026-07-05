"""
Adaptive pillar weighting.

    effective_weight(p) = base_weight(segment, p) x coverage(p) x reliability(p)

then renormalized to sum to 1. This delivers three things we promised:
  * segment-awareness  — a manufacturer leans on Operational Vitality, a salaried
                         applicant on Cash-Flow/Stability (base weights differ).
  * thin-file handling — a missing source drops that pillar's coverage, so its
                         weight flows to the pillars we DO have (no auto-reject).
  * reliability-awareness — cross-source divergence lowers the weight of the
                         scale-derived pillars (we lean on what we can trust).
"""
from .pillars import PILLARS

# Generic base weights (sum ~1).
_BASE = {
    "revenue_scale": 0.22, "cash_flow": 0.24, "operational_vitality": 0.14,
    "stability_formalization": 0.16, "credit_discipline": 0.16, "identity_reliability": 0.08,
}

# Per-segment overrides (only the pillars that differ from _BASE).
_SEGMENT = {
    "manufacturer": {"operational_vitality": 0.22, "revenue_scale": 0.22, "cash_flow": 0.18,
                     "stability_formalization": 0.16, "credit_discipline": 0.14},
    "transport":    {"operational_vitality": 0.24, "cash_flow": 0.22, "revenue_scale": 0.16,
                     "stability_formalization": 0.14, "credit_discipline": 0.16},
    "gig":          {"cash_flow": 0.34, "credit_discipline": 0.22, "revenue_scale": 0.14,
                     "operational_vitality": 0.06, "stability_formalization": 0.16},
    "salaried":     {"cash_flow": 0.28, "stability_formalization": 0.24, "credit_discipline": 0.22,
                     "revenue_scale": 0.10, "operational_vitality": 0.08, "identity_reliability": 0.08},
    "retail":       {"cash_flow": 0.28, "revenue_scale": 0.20, "operational_vitality": 0.12,
                     "credit_discipline": 0.16, "stability_formalization": 0.16},
    "agri":         {"operational_vitality": 0.20, "cash_flow": 0.22, "revenue_scale": 0.18,
                     "stability_formalization": 0.16, "credit_discipline": 0.16},
}

# Which pillars are "scale-derived" and thus subject to cross-validation reliability.
_SCALE_PILLARS = {"revenue_scale", "cash_flow", "operational_vitality"}

# Identity & Data Reliability is NOT a positive credit signal — it feeds
# data-confidence, reliability multipliers and flags instead. Excluding it from the
# score composition avoids a ~100-point floor that would compress every applicant
# upward. It is still computed and displayed as an informational indicator.
_SCORE_EXCLUDE = {"identity_reliability"}


def base_weights(segment):
    w = dict(_BASE)
    w.update(_SEGMENT.get(segment, {}))
    return w


def effective_weights(segment, pillar_results, scale_reliability):
    """
    pillar_results: {pillar: {"subscore":..., "coverage":...}}
    Returns {pillar: effective_weight} renormalized over pillars that scored.
    """
    base = base_weights(segment)
    raw = {}
    for p in PILLARS:
        res = pillar_results[p]
        if p in _SCORE_EXCLUDE or res["subscore"] is None or res["coverage"] <= 0:
            raw[p] = 0.0
            continue
        rel = scale_reliability if p in _SCALE_PILLARS else 1.0
        raw[p] = base[p] * res["coverage"] * rel

    total = sum(raw.values())
    if total <= 0:
        return {p: 0.0 for p in PILLARS}
    return {p: raw[p] / total for p in PILLARS}
