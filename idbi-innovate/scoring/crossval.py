"""
Cross-validation / data-reliability engine.

The AMA mentors stressed: don't trust a single source — data can be wrong
(wrong account number -> false data). So we independently ESTIMATE the business's
monthly revenue from several unrelated sources (GST, UPI, bank inflows) and check
whether they AGREE. Tight agreement -> high confidence. Divergence -> we flag it,
lower reliability, and route to manual review instead of trusting a bad number.
"""
import statistics

from .normalize import num, clamp

# Gross-up factors: fraction of true revenue each source typically captures.
# Dividing the observed value by this recovers an independent revenue estimate.
_CAPTURE = {
    "gst": 0.85,   # GST turnover ~ most of revenue for formal firms
    "upi": 0.65,   # UPI captures a portion of sales
    "bank": 1.00,  # bank inflows ~ total revenue (+ some non-revenue)
}


def revenue_estimates(row):
    """Independent monthly-revenue estimates keyed by source."""
    est = {}
    g = num(row, "gst_turnover_monthly")
    if g:
        est["gst"] = g / _CAPTURE["gst"]
    u = num(row, "upi_inflow_monthly")
    if u:
        est["upi"] = u / _CAPTURE["upi"]
    b = num(row, "bank_inflow_monthly")
    if b:
        est["bank"] = b / _CAPTURE["bank"]
    return est


def assess(row):
    """
    Returns dict:
      estimates        {source: monthly_rev}
      estimated_revenue robust (median) estimate, or None
      cv               coefficient of variation across estimates (or None if <2)
      consistent       bool | None
      scale_reliability 0..1 multiplier applied to scale-derived pillars
      flags            list of human-readable reliability flags
    """
    est = revenue_estimates(row)
    vals = list(est.values())
    flags = []

    estimated_revenue = statistics.median(vals) if vals else None

    if len(vals) >= 2:
        mean = statistics.mean(vals)
        sd = statistics.pstdev(vals)
        cv = (sd / mean) if mean else 0.0
        consistent = cv < 0.35
        # cv 0.20 -> full trust; grows to 0.35 reliability floor as divergence rises
        scale_reliability = clamp(1.0 - max(0.0, cv - 0.20) / 0.80, 0.35, 1.0)
        if not consistent:
            hi = max(est, key=est.get)
            lo = min(est, key=est.get)
            flags.append(
                f"Sources disagree on business size: {hi.upper()} implies "
                f"~Rs.{int(est[hi]):,}/mo but {lo.upper()} implies ~Rs.{int(est[lo]):,}/mo "
                f"(CV {cv:.0%}) — verify data before relying on the score."
            )
    else:
        cv = None
        consistent = None
        # Can't cross-check with <2 sources -> mild discount, not a penalty.
        scale_reliability = 0.85

    if str(row.get("mnrl_flag")) == "1":
        flags.append("Contact mobile on MNRL (revocation list) — identity/data unverifiable.")

    return {
        "estimates": {k: int(v) for k, v in est.items()},
        "estimated_revenue": int(estimated_revenue) if estimated_revenue else None,
        "cv": round(cv, 3) if cv is not None else None,
        "consistent": consistent,
        "scale_reliability": round(scale_reliability, 3),
        "flags": flags,
    }
