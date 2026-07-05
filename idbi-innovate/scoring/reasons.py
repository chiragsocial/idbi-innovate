"""
Deterministic reason-code generator.

Turns the pillar drivers into plain-language, auditable "why" statements for the
underwriter. NO LLM sits in this path — every sentence is a template filled from
explicit numbers, so the explanation is reproducible and defensible to a regulator
(the optional Gemini "briefing" only rephrases THIS output for readability).

Produces: strengths, concerns, data-quality flags, and "what would sharpen the
score" (which consents/sources to add) — the last is how a thin-file applicant is
guided forward instead of rejected.
"""

# high-value sources whose absence we suggest adding
_SOURCE_SUGGEST = {
    "aa": "Account Aggregator consent (bank-statement analysis)",
    "gst": "GST returns (verified turnover & filing history)",
    "bureau": "credit-bureau pull (if any prior credit exists)",
    "epf": "EPFO data (payroll size & continuity)",
    "electricity": "electricity-board consumption (production proxy)",
}


def _inr(x):
    if x is None:
        return "n/a"
    x = float(x)
    if x >= 1e7:
        return f"₹{x/1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x/1e5:.1f} L"
    return f"₹{x:,.0f}"


def _years(months):
    if months is None:
        return None
    m = float(months)
    return f"{m/12:.1f} yrs" if m >= 12 else f"{int(m)} mo"


def _pillar_text(key, d, positive):
    """One plain-language phrase for a pillar, oriented strength vs concern."""
    if key == "revenue_scale":
        rev = _inr(d.get("estimated_monthly_revenue"))
        g = d.get("growth_pct")
        if positive:
            gt = f", growing {g:.0f}%/yr" if g and g > 3 else ""
            return f"Healthy turnover (~{rev}/mo{gt})."
        gt = f", declining {abs(g):.0f}%/yr" if g and g < -3 else ""
        return f"Modest/soft turnover (~{rev}/mo{gt})."

    if key == "cash_flow":
        bd = d.get("buffer_days")
        sr = d.get("surplus_ratio")
        vol = d.get("volatility")
        if positive:
            bits = []
            if bd is not None:
                bits.append(f"{bd:.0f}-day liquidity buffer")
            if sr is not None and sr > 0.05:
                bits.append("positive operating surplus")
            if vol is not None and vol < 0.35:
                bits.append("stable cash flows")
            return "Sound cash flow: " + ", ".join(bits) + "." if bits else "Sound cash flow."
        bits = []
        if bd is not None and bd < 15:
            bits.append(f"thin {bd:.0f}-day buffer")
        if sr is not None and sr < 0:
            bits.append("spends more than it earns")
        if vol is not None and vol > 0.5:
            bits.append("volatile inflows")
        return "Cash-flow pressure: " + ", ".join(bits) + "." if bits else "Weak cash flow."

    if key == "operational_vitality":
        et = d.get("electricity_trend_pct")
        if et is not None and positive and et > 3:
            return f"Rising electricity use (+{et:.0f}%) signals growing production."
        if et is not None and not positive and et < -3:
            return f"Falling electricity use ({et:.0f}%) suggests slowing operations."
        if "fuel_spend_monthly" in d or "fastag_toll_monthly" in d:
            return "Active fuel/toll spend confirms ongoing operations."
        return "Steady physical operations." if positive else "Limited operational signal."

    if key == "stability_formalization":
        yrs = _years(d.get("vintage_months"))
        bits = []
        if yrs:
            bits.append(f"{yrs} in operation")
        if d.get("epf_employees"):
            bits.append(f"payroll for {int(d['epf_employees'])} staff (EPF)")
        if d.get("has_udyam"):
            bits.append("Udyam-registered")
        fr = d.get("gst_filing_regularity")
        if fr is not None:
            bits.append(("regular" if fr >= 0.7 else "irregular") + f" GST filing ({fr*100:.0f}%)")
        core = ", ".join(bits) if bits else "limited history"
        return ("Established & formal: " if positive else "Formalization gaps: ") + core + "."

    if key == "credit_discipline":
        if d.get("is_ntc"):
            base = "New-to-Credit — no bureau history; assessed on alternate data"
        elif d.get("bureau_score"):
            base = f"bureau score {int(d['bureau_score'])}"
        else:
            base = "limited credit history"
        bits = [base]
        obl = d.get("obligation_ratio")
        if obl is not None:
            bits.append(("low" if obl < 0.2 else "high") + f" existing EMI burden ({obl*100:.0f}% of income)")
        b = d.get("bounces_12m")
        if b is not None:
            bits.append("no payment bounces" if b == 0 else f"{int(b)} bounce(s)/12mo")
        return ("Disciplined: " if positive else "Discipline concerns: ") + ", ".join(bits) + "."

    return ""


def generate_reasons(card):
    strengths, concerns = [], []
    for p in card["pillars"]:
        key, sub, w = p["key"], p["subscore"], p["weight"]
        if key == "identity_reliability" or sub is None or w <= 0:
            continue
        impact = round((sub - 50) * w, 2)
        if sub >= 60:
            strengths.append({"pillar": p["label"], "impact": impact,
                              "text": _pillar_text(key, p["drivers"], True)})
        elif sub <= 48:
            concerns.append({"pillar": p["label"], "impact": impact,
                             "text": _pillar_text(key, p["drivers"], False)})
    strengths.sort(key=lambda x: -x["impact"])
    concerns.sort(key=lambda x: x["impact"])

    # data-quality concerns come straight from the reliability flags
    quality = list(card.get("flags", []))

    # what would sharpen the score: high-value sources not present
    improvements = []
    cov = {p["key"]: p["coverage"] for p in card["pillars"]}
    if cov.get("credit_discipline", 0) < 0.5 and card["is_ntc"]:
        improvements.append("This is a New-to-Credit case — score rests on alternate data by design; "
                            "no action needed to avoid rejecting a credit-invisible borrower.")
    if card["cross_validation"]["estimates"].get("gst") is None:
        improvements.append(f"Add {_SOURCE_SUGGEST['gst']} to corroborate turnover.")
    if card["data_confidence"] < 60:
        improvements.append(f"Request {_SOURCE_SUGGEST['aa']} to raise data confidence "
                            f"(currently {card['data_confidence']:.0f}%).")

    summary = _summary(card, strengths, concerns)
    return {"summary": summary, "strengths": strengths[:4], "concerns": concerns[:4],
            "data_quality": quality, "improvements": improvements[:3]}


def _summary(card, strengths, concerns):
    """One deterministic sentence — the headline the underwriter reads first."""
    seg = card["segment"]
    ntc = " New-to-Credit" if card["is_ntc"] else ""
    verb = {"APPROVE": "Recommend approval", "REVIEW": "Route for review",
            "DECLINE": "Recommend decline"}[card["recommendation"]]
    lead = strengths[0]["text"].rstrip(".") if strengths else "limited positive signal"
    risk = concerns[0]["text"].rstrip(".") if concerns else "no major red flags"
    lim = _inr(card["suggested_limit"]) if card["suggested_limit"] else "—"
    return (f"{verb} for this{ntc} {seg} ({card['rag']}, score {card['unified_score']:.0f}/100, "
            f"suggested limit {lim}). Key strength: {lead}. Key watch-point: {risk}. "
            f"Data confidence {card['data_confidence']:.0f}% ({card['confidence_label']}). "
            f"Final decision rests with the underwriter.")
