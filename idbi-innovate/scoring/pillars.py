"""
The six scoring pillars. Each function takes the applicant row (+ shared context
like the cross-validated revenue estimate) and returns:

    {"subscore": 0..100 | None, "coverage": 0..1, "drivers": {...}}

`coverage` = how much of the pillar's expected data was actually present. A pillar
with coverage 0 contributes nothing and its weight redistributes to others — this
is how thin-file applicants are scored instead of auto-rejected.
"""
from .normalize import num, avail, clamp, lin, log_norm, wmean

PILLARS = [
    "revenue_scale", "cash_flow", "operational_vitality",
    "stability_formalization", "credit_discipline", "identity_reliability",
]

PILLAR_LABELS = {
    "revenue_scale": "Revenue & Scale",
    "cash_flow": "Cash-Flow Health",
    "operational_vitality": "Operational Vitality",
    "stability_formalization": "Stability & Formalization",
    "credit_discipline": "Credit Discipline & Obligations",
    "identity_reliability": "Identity & Data Reliability",
}


def _cov(present, total):
    return round(present / total, 3) if total else 0.0


# ---------------------------------------------------------------- 1. Revenue & Scale
def revenue_scale(row, ctx):
    est_rev = ctx.get("estimated_revenue")
    trend = num(row, "gst_trend_pct")
    if trend is None:
        trend = num(row, "electricity_trend_pct")

    level = log_norm(est_rev, 40_000, 5_000_000) if est_rev else None
    growth = lin(trend, -25, 30) if trend is not None else None
    sub = wmean([(level, 0.7), (growth, 0.3)])

    present = sum(x is not None for x in (est_rev, trend))
    return {"subscore": sub, "coverage": _cov(present, 2),
            "drivers": {"estimated_monthly_revenue": est_rev, "growth_pct": trend,
                        "level_score": level, "growth_score": growth}}


# ---------------------------------------------------------------- 2. Cash-Flow Health
def cash_flow(row, ctx):
    buffer_days = num(row, "bank_buffer_days")
    inflow = num(row, "bank_inflow_monthly")
    outflow = num(row, "bank_outflow_monthly")
    vol = num(row, "upi_volatility")
    if vol is None:
        vol = num(row, "gst_volatility")

    buffer_s = lin(buffer_days, 5, 75) if buffer_days is not None else None
    surplus_s = None
    surplus_ratio = None
    if inflow and outflow is not None and inflow > 0:
        surplus_ratio = (inflow - outflow) / inflow
        surplus_s = lin(surplus_ratio, -0.05, 0.25)
    vol_s = lin(vol, 0.9, 0.15) if vol is not None else None  # low volatility -> high score

    sub = wmean([(buffer_s, 0.4), (surplus_s, 0.35), (vol_s, 0.25)])
    present = sum(x is not None for x in (buffer_s, surplus_s, vol_s))
    return {"subscore": sub, "coverage": _cov(present, 3),
            "drivers": {"buffer_days": buffer_days, "surplus_ratio": surplus_ratio,
                        "volatility": vol}}


# ---------------------------------------------------- 3. Operational Vitality (physical proxies)
def operational_vitality(row, ctx):
    comps = []
    drivers = {}
    if avail(row, "electricity"):
        et = num(row, "electricity_trend_pct")
        # steady operation baseline (55) nudged by production growth
        comps.append(("elec", clamp(55 + (et or 0) * 1.4, 0, 100)))
        drivers["electricity_trend_pct"] = et
        drivers["electricity_units_monthly"] = num(row, "electricity_units_monthly")
    if avail(row, "fuel"):
        comps.append(("fuel", 60.0))
        drivers["fuel_spend_monthly"] = num(row, "fuel_spend_monthly")
    if avail(row, "fastag"):
        comps.append(("fastag", 60.0))
        drivers["fastag_toll_monthly"] = num(row, "fastag_toll_monthly")

    sub = (sum(v for _, v in comps) / len(comps)) if comps else None
    # 3 possible operational sources; electricity weighted as the key one
    return {"subscore": sub, "coverage": _cov(len(comps), 3), "drivers": drivers}


# ------------------------------------------------ 4. Stability & Formalization
def stability_formalization(row, ctx):
    vintage = num(row, "vintage_months")
    vintage_s = log_norm(vintage, 6, 180) if vintage is not None else None

    emp_s = months_s = None
    if avail(row, "epf"):
        emp_s = log_norm(num(row, "epf_employee_count"), 1, 80)
        months_s = lin(num(row, "epf_months_contributed"), 3, 60)

    udyam_s = 100.0 if str(row.get("has_udyam")) == "1" else 0.0
    filing_s = None
    fr = num(row, "gst_filing_regularity")
    if fr is not None:
        filing_s = fr * 100.0

    sub = wmean([(vintage_s, 0.35), (emp_s, 0.20), (months_s, 0.15),
                 (udyam_s, 0.12), (filing_s, 0.18)])
    present = sum(x is not None for x in (vintage_s, emp_s, months_s, filing_s)) + 1  # udyam always known
    return {"subscore": sub, "coverage": _cov(present, 5),
            "drivers": {"vintage_months": vintage, "epf_employees": num(row, "epf_employee_count"),
                        "has_udyam": str(row.get("has_udyam")) == "1",
                        "gst_filing_regularity": fr}}


# ------------------------------------------------ 5. Credit Discipline & Obligations
def credit_discipline(row, ctx):
    bureau_s = None
    if avail(row, "bureau"):
        bureau_s = lin(num(row, "bureau_score"), 300, 850)

    oblig_s = oblig_ratio = None
    emi = num(row, "existing_emi_monthly")
    est_rev = ctx.get("estimated_revenue")
    if emi is not None and est_rev:
        oblig_ratio = clamp(emi / est_rev, 0, 1)
        oblig_s = lin(oblig_ratio, 0.5, 0.0)  # low obligation -> high score

    bounce_s = None
    bounces = num(row, "bank_bounces_12m")
    if bounces is not None:
        bounce_s = lin(bounces, 6, 0)  # fewer bounces -> higher

    fr = num(row, "gst_filing_regularity")
    filing_s = fr * 100.0 if fr is not None else None

    sub = wmean([(bureau_s, 0.40), (oblig_s, 0.25), (bounce_s, 0.20), (filing_s, 0.15)])
    present = sum(x is not None for x in (bureau_s, oblig_s, bounce_s, filing_s))
    return {"subscore": sub, "coverage": _cov(present, 4),
            "drivers": {"bureau_score": num(row, "bureau_score"), "is_ntc": str(row.get("is_ntc")) == "1",
                        "obligation_ratio": oblig_ratio, "bounces_12m": bounces}}


# ------------------------------------------------ 6. Identity & Data Reliability
def identity_reliability(row, ctx):
    sub = 100.0
    drivers = {}
    if str(row.get("mnrl_flag")) == "1":
        sub -= 45
        drivers["mnrl_flag"] = True
    cv = ctx.get("cv")
    if cv is not None:
        # every 10% of divergence above 20% costs ~15 points
        sub -= max(0.0, cv - 0.20) * 150
        drivers["cross_source_cv"] = cv
    sub = clamp(sub, 0, 100)
    return {"subscore": sub, "coverage": 1.0, "drivers": drivers}


COMPUTE = {
    "revenue_scale": revenue_scale,
    "cash_flow": cash_flow,
    "operational_vitality": operational_vitality,
    "stability_formalization": stability_formalization,
    "credit_discipline": credit_discipline,
    "identity_reliability": identity_reliability,
}
