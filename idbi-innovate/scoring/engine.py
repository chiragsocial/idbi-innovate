"""
Scoring engine orchestrator.

score_entity(row) -> full Health Card dict:
  unified_score, RAG band, risk bucket, recommendation (APPROVE/REVIEW/DECLINE),
  suggested credit limit, data-confidence, per-pillar breakdown, cross-validation,
  and reliability flags.

Key rule (from the AMA): this is a RECOMMENDATION for a human underwriter, never an
auto-decision — and thin-file / New-to-Credit applicants are routed to REVIEW,
never auto-rejected for missing data.
"""
from . import crossval
from .normalize import clamp
from .pillars import COMPUTE, PILLARS, PILLAR_LABELS
from .reasons import generate_reasons
from .weighting import effective_weights, base_weights

# RAG thresholds on the 0..100 unified score.
GREEN_MIN = 72
AMBER_MIN = 50


def _rag(score):
    if score >= GREEN_MIN:
        return "GREEN", "Low"
    if score >= AMBER_MIN:
        return "AMBER", "Medium"
    return "RED", "High"


def _confidence(sources_used, scale_reliability, mnrl):
    base = clamp(sources_used / 6.0, 0, 1) * 100.0
    conf = base * (0.5 + 0.5 * scale_reliability)
    if mnrl:
        conf *= 0.7
    conf = round(clamp(conf, 0, 100), 1)
    label = "High" if conf >= 70 else ("Medium" if conf >= 45 else "Low")
    return conf, label


def _suggested_limit(recommendation, score, est_rev, confidence):
    if recommendation == "DECLINE" or not est_rev:
        return 0
    multiple = clamp((score - 45) / 18.0, 0, 3)          # score 45->0x, 63->1x, 99->3x
    multiple *= clamp(confidence / 100.0 + 0.2, 0.4, 1.0)  # low confidence -> smaller limit
    limit = est_rev * multiple
    return int(round(limit / 10_000.0)) * 10_000          # round to nearest Rs.10k


def _source_count(row):
    srcs = ["gst", "upi", "aa", "epf", "electricity", "fuel", "fastag", "bureau"]
    return sum(str(row.get(f"{s}_available")) == "1" for s in srcs)


def score_entity(row):
    segment = row.get("segment", "trader")

    # 1) cross-validate sources -> revenue estimate + reliability
    xv = crossval.assess(row)
    ctx = {"estimated_revenue": xv["estimated_revenue"], "cv": xv["cv"]}

    # 2) compute the six pillar sub-scores
    pillar_results = {p: COMPUTE[p](row, ctx) for p in PILLARS}

    # 3) adaptive weights
    weights = effective_weights(segment, pillar_results, xv["scale_reliability"])

    # 4) unified score
    unified = 0.0
    for p in PILLARS:
        sub = pillar_results[p]["subscore"]
        if sub is not None:
            unified += weights[p] * sub
    unified = round(clamp(unified, 0, 100), 1)

    # 5) RAG + confidence
    rag, risk_bucket = _rag(unified)
    sources_used = _source_count(row)
    mnrl = str(row.get("mnrl_flag")) == "1"
    confidence, conf_label = _confidence(sources_used, xv["scale_reliability"], mnrl)

    # 6) recommendation (NEVER auto-reject thin files; low trust -> REVIEW)
    flags = list(xv["flags"])
    thin = sources_used <= 2
    low_trust = (confidence < 45) or (xv["consistent"] is False) or mnrl
    if thin:
        flags.append("Thin file — few data sources; routed for review, not rejected.")

    if low_trust or thin:
        recommendation = "REVIEW"
    elif rag == "GREEN":
        recommendation = "APPROVE"
    elif rag == "AMBER":
        recommendation = "REVIEW"
    else:
        recommendation = "DECLINE"

    limit = _suggested_limit(recommendation, unified, xv["estimated_revenue"], confidence)

    # 7) assemble per-pillar breakdown for the UI / explainability layer
    pillars_out = []
    for p in PILLARS:
        res = pillar_results[p]
        pillars_out.append({
            "key": p,
            "label": PILLAR_LABELS[p],
            "subscore": round(res["subscore"], 1) if res["subscore"] is not None else None,
            "coverage": res["coverage"],
            "weight": round(weights[p], 3),
            "contribution": round(weights[p] * res["subscore"], 1) if res["subscore"] is not None else 0.0,
            "drivers": res["drivers"],
        })

    card = {
        "entity_id": row.get("entity_id"),
        "segment": segment,
        "is_ntc": str(row.get("is_ntc")) == "1",
        "is_ntb": str(row.get("is_ntb")) == "1",
        "unified_score": unified,
        "rag": rag,
        "risk_bucket": risk_bucket,
        "recommendation": recommendation,
        "suggested_limit": limit,
        "estimated_monthly_revenue": xv["estimated_revenue"],
        "data_confidence": confidence,
        "confidence_label": conf_label,
        "sources_used": sources_used,
        "cross_validation": {
            "estimates": xv["estimates"],
            "cv": xv["cv"],
            "consistent": xv["consistent"],
            "scale_reliability": xv["scale_reliability"],
        },
        "flags": flags,
        "pillars": pillars_out,
        "note": "Recommendation for underwriter review. Final credit decision rests with the human underwriter.",
    }

    card["explanation"] = generate_reasons(card)
    return card
