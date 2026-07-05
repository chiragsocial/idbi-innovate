#!/usr/bin/env python3
"""
Synthetic MSME data engine  ·  IDBI Innovate 2026 — MSME Financial Health Card
------------------------------------------------------------------------------
Generates a realistic, dependency-free (pure stdlib) dataset of MSME / individual
credit applicants for training the default model and demoing the Health Card.

Design goals (see docs/DESIGN.md):
  * Correlated signals — a real business's electricity, GST, UPI and bank flows
    all move with its true (latent) revenue and health, not independently.
  * Persona-driven data availability — manufacturers have electricity, transporters
    have fuel/FASTag, gig workers have UPI-but-no-GST. This drives the thin-file
    and adaptive-weighting story.
  * Thin-file / New-to-Credit cases that must NOT be auto-rejected.
  * Injected data-inconsistency cases (wrong-account / false data) so the
    cross-validation reliability engine has something real to detect.
  * A plausible latent-risk model producing the `default` label — importantly,
    being New-to-Credit is NOT itself made risky (that's the whole thesis).

Usage:
    python3 generate.py                 # 5,000 rows -> output/
    python3 generate.py --n 20000       # bigger
    python3 generate.py --seed 7        # different draw

Outputs:
    output/msme_dataset.csv     flat table (features + `default` label + _gt_* truth)
    output/demo_profiles.json   ~8 curated hero archetypes with 12-month series
"""
import argparse
import csv
import json
import math
import os
import random

from personas import PERSONAS, SEGMENT_WEIGHTS, STATES, SOURCES

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# Latent-risk model intercept — tuned so overall default rate ≈ 10%.
DEFAULT_INTERCEPT = -2.20


# ----------------------------------------------------------------------------- helpers
def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def sigmoid(x):
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def lognoise(rng, sigma):
    """Multiplicative lognormal noise centred on 1.0."""
    return math.exp(rng.gauss(0.0, sigma))


def weighted_choice(rng, weights: dict):
    r = rng.random() * sum(weights.values())
    upto = 0.0
    for key, w in weights.items():
        upto += w
        if r <= upto:
            return key
    return next(iter(weights))


def rint(x):
    return int(round(x))


# ----------------------------------------------------------------------------- core
def generate_entity(rng, idx, segment=None, force=None):
    """
    Build one applicant. `force` (dict) lets the demo builder pin specific traits:
      segment, cw, true_rev, ntc, inconsistent(bool), avail_on(set), avail_off(set)
    """
    force = force or {}
    seg = force.get("segment") or segment or weighted_choice(rng, SEGMENT_WEIGHTS)
    P = PERSONAS[seg]

    # --- latent truth -------------------------------------------------------
    k = 6.0
    m = P["cw_mean"]
    cw = force.get("cw", clamp(rng.betavariate(m * k, (1 - m) * k), 0.02, 0.98))

    lo, hi = P["scale"]
    true_rev = force.get(
        "true_rev", math.exp(rng.uniform(math.log(lo), math.log(hi)))
    )

    v_lo, v_hi = P["vintage"]
    vintage = rint(clamp(rng.uniform(v_lo, v_hi) * (0.7 + 0.6 * cw), v_lo, v_hi))

    # growth & volatility track creditworthiness
    growth_pct = force.get("growth_pct",
                           clamp(rng.gauss((cw - 0.5) * 40, 14), -35, 60))
    volatility = clamp(0.45 - 0.35 * cw + rng.gauss(0, 0.07), 0.05, 0.90)

    is_ntc = force.get("ntc", rng.random() < P["ntc_prob"])
    is_ntb = rng.random() < P["ntb_prob"]
    has_udyam = rng.random() < P["udyam_prob"]

    state, geo_risk = rng.choice(STATES)
    city_tier = rng.choice([1, 1, 2, 2, 2, 3])

    # --- which sources are present -----------------------------------------
    avail = {}
    for s in SOURCES:
        p = P["avail"][s]
        present = rng.random() < p
        avail[s] = present
    for s in force.get("avail_on", set()):
        avail[s] = True
    for s in force.get("avail_off", set()):
        avail[s] = False
    # salaried individuals don't file GST as a business
    if seg == "salaried":
        avail["gst"] = False

    row = {
        "entity_id": f"MSME{idx:06d}",
        "segment": seg,
        "state": state,
        "city_tier": city_tier,
        "vintage_months": vintage,
        "is_ntc": int(is_ntc),
        "is_ntb": int(is_ntb),
        "has_udyam": int(has_udyam),
    }

    # --- GST ----------------------------------------------------------------
    if avail["gst"]:
        row["gst_available"] = 1
        row["gst_turnover_monthly"] = rint(true_rev * rng.uniform(0.70, 1.00) * lognoise(rng, 0.08))
        row["gst_trend_pct"] = round(growth_pct + rng.gauss(0, 4), 1)
        row["gst_volatility"] = round(clamp(volatility + rng.gauss(0, 0.05), 0.03, 0.95), 3)
        row["gst_filing_regularity"] = round(clamp(0.45 + 0.55 * cw + rng.gauss(0, 0.08), 0, 1), 3)
        row["gst_months_filed"] = min(vintage, rint(vintage * rng.uniform(0.6, 1.0)))
    else:
        _blank(row, ["gst_turnover_monthly", "gst_trend_pct", "gst_volatility",
                     "gst_filing_regularity", "gst_months_filed"], available=0, flag="gst_available")

    # --- UPI / POS ----------------------------------------------------------
    if avail["upi"]:
        inflow = true_rev * rng.uniform(0.40, 0.90) * lognoise(rng, 0.10)
        avg_ticket = rng.uniform(150, 2200)
        row["upi_available"] = 1
        row["upi_inflow_monthly"] = rint(inflow)
        row["upi_txn_count"] = rint(inflow / avg_ticket)
        row["upi_volatility"] = round(clamp(volatility + rng.gauss(0, 0.05), 0.03, 0.95), 3)
    else:
        _blank(row, ["upi_inflow_monthly", "upi_txn_count", "upi_volatility"],
               available=0, flag="upi_available")

    # --- Account Aggregator (bank statements) -------------------------------
    if avail["aa"]:
        inflow = true_rev * rng.uniform(0.85, 1.25) * lognoise(rng, 0.08)
        outflow = inflow * rng.uniform(0.70, 0.98)
        balance = true_rev * rng.uniform(0.05, 0.55) * (0.5 + cw)
        bounces = max(0, rint((1 - cw) * 4 + rng.gauss(0, 1.0)))
        emi = 0 if is_ntc and rng.random() < 0.7 else rint(true_rev * rng.uniform(0.0, 0.30))
        row["aa_available"] = 1
        row["bank_inflow_monthly"] = rint(inflow)
        row["bank_outflow_monthly"] = rint(outflow)
        row["bank_avg_balance"] = rint(balance)
        row["bank_buffer_days"] = round(clamp(balance / max(outflow / 30.0, 1), 0, 400), 1)
        row["bank_bounces_12m"] = bounces
        row["existing_emi_monthly"] = emi
    else:
        _blank(row, ["bank_inflow_monthly", "bank_outflow_monthly", "bank_avg_balance",
                     "bank_buffer_days", "bank_bounces_12m", "existing_emi_monthly"],
               available=0, flag="aa_available")

    # --- EPFO ---------------------------------------------------------------
    if avail["epf"]:
        if seg == "salaried":
            emp = 1
        else:
            emp = max(1, rint(true_rev / rng.uniform(90_000, 220_000)))
        row["epf_available"] = 1
        row["epf_employee_count"] = emp
        row["epf_months_contributed"] = min(vintage, rint(vintage * rng.uniform(0.5, 1.0)))
    else:
        _blank(row, ["epf_employee_count", "epf_months_contributed"], available=0, flag="epf_available")

    # --- Electricity (production proxy) ------------------------------------
    if avail["electricity"]:
        factor = {"manufacturer": 1.6, "transport": 0.5, "gig": 0.25,
                  "salaried": 0.4, "retail": 0.6}.get(seg, 1.0)
        units = (true_rev / rng.uniform(90, 200)) * factor * lognoise(rng, 0.10)
        row["electricity_available"] = 1
        row["electricity_units_monthly"] = rint(units)
        # production growth tracks revenue growth (strong for manufacturers)
        tie = 0.85 if seg == "manufacturer" else 0.5
        row["electricity_trend_pct"] = round(growth_pct * tie + rng.gauss(0, 5), 1)
    else:
        _blank(row, ["electricity_units_monthly", "electricity_trend_pct"],
               available=0, flag="electricity_available")

    # --- Fuel ---------------------------------------------------------------
    if avail["fuel"]:
        share = rng.uniform(0.15, 0.35) if seg == "transport" else rng.uniform(0.02, 0.10)
        row["fuel_available"] = 1
        row["fuel_spend_monthly"] = rint(true_rev * share * lognoise(rng, 0.12))
    else:
        _blank(row, ["fuel_spend_monthly"], available=0, flag="fuel_available")

    # --- FASTag -------------------------------------------------------------
    if avail["fastag"]:
        share = rng.uniform(0.03, 0.08) if seg == "transport" else rng.uniform(0.002, 0.02)
        row["fastag_available"] = 1
        row["fastag_toll_monthly"] = rint(true_rev * share * lognoise(rng, 0.12))
    else:
        _blank(row, ["fastag_toll_monthly"], available=0, flag="fastag_available")

    # --- Credit bureau ------------------------------------------------------
    if not is_ntc:
        row["bureau_available"] = 1
        row["bureau_score"] = rint(clamp(300 + 550 * cw + rng.gauss(0, 40), 300, 900))
    else:
        row["bureau_available"] = 0
        row["bureau_score"] = ""

    # --- MNRL (mobile validity) — data-reliability flag ---------------------
    row["mnrl_flag"] = int(rng.random() < 0.03)  # 1 = mobile on revocation list

    # --- inject data inconsistency (wrong-account / false data) -------------
    inconsistent = force.get("inconsistent", rng.random() < 0.08)
    if inconsistent:
        candidates = [c for c in ("gst_turnover_monthly", "upi_inflow_monthly",
                                  "electricity_units_monthly", "bank_inflow_monthly")
                      if row.get(c) not in (None, "", 0)]
        if candidates:
            col = rng.choice(candidates)
            row[col] = rint(row[col] * rng.choice([0.25, 0.30, 3.0, 3.5]))
    row["_gt_inconsistent"] = int(inconsistent)

    # --- latent-risk model -> default label --------------------------------
    obligation_ratio = 0.0
    if row.get("existing_emi_monthly") not in (None, ""):
        obligation_ratio = clamp(row["existing_emi_monthly"] / max(true_rev, 1), 0, 0.8)
    bounce_rate = 0.0
    if row.get("bank_bounces_12m") not in (None, ""):
        bounce_rate = row["bank_bounces_12m"] / 12.0

    propensity = (
        DEFAULT_INTERCEPT
        - 3.0 * (cw - 0.5)
        - 0.35 * (math.log10(max(true_rev, 1)) - math.log10(50_000))
        + 1.6 * obligation_ratio
        + 1.0 * volatility
        + 1.2 * bounce_rate
        - 0.6 * min(vintage / 60.0, 1.0)
        + 4.0 * geo_risk
        + rng.gauss(0, 0.45)
    )
    p_default = sigmoid(propensity)
    row["default"] = int(rng.random() < p_default)

    # --- ground-truth (for evaluation/plots only; NOT model inputs) ---------
    row["_gt_creditworthiness"] = round(cw, 4)
    row["_gt_true_revenue"] = rint(true_rev)
    row["_gt_growth_pct"] = round(growth_pct, 1)
    row["_gt_default_prob"] = round(p_default, 4)

    return row


def _blank(row, cols, available, flag):
    row[flag] = available
    for c in cols:
        row[c] = ""


# ----------------------------------------------------------------------------- schema
def column_order():
    cols = ["entity_id", "segment", "state", "city_tier", "vintage_months",
            "is_ntc", "is_ntb", "has_udyam",
            "gst_available", "gst_turnover_monthly", "gst_trend_pct", "gst_volatility",
            "gst_filing_regularity", "gst_months_filed",
            "upi_available", "upi_inflow_monthly", "upi_txn_count", "upi_volatility",
            "aa_available", "bank_inflow_monthly", "bank_outflow_monthly",
            "bank_avg_balance", "bank_buffer_days", "bank_bounces_12m", "existing_emi_monthly",
            "epf_available", "epf_employee_count", "epf_months_contributed",
            "electricity_available", "electricity_units_monthly", "electricity_trend_pct",
            "fuel_available", "fuel_spend_monthly",
            "fastag_available", "fastag_toll_monthly",
            "bureau_available", "bureau_score",
            "mnrl_flag",
            "default",
            "_gt_inconsistent", "_gt_creditworthiness", "_gt_true_revenue",
            "_gt_growth_pct", "_gt_default_prob"]
    return cols


# ----------------------------------------------------------------------------- demo profiles
def month_series(rng, level, trend_pct, vol, n=12):
    if level in (None, "", 0):
        return []
    out = []
    for i in range(n):
        g = (1 + trend_pct / 100.0) ** (i / 12.0)
        s = level * g * (1 + rng.gauss(0, vol * 0.25))
        out.append(rint(max(s, 0)))
    return out


def build_demo_profiles(rng):
    """Curated archetypes that make the demo tell the whole story."""
    specs = [
        ("green_manufacturer", "manufacturer",
         {"cw": 0.82, "true_rev": 1_800_000, "ntc": False, "inconsistent": False,
          "growth_pct": 12},
         "Established, formal, all sources agree — a clean GREEN."),
        ("thin_file_ntc_fabrication", "manufacturer",
         {"cw": 0.68, "true_rev": 650_000, "ntc": True, "inconsistent": False,
          "growth_pct": 18, "avail_off": {"gst"}, "avail_on": {"electricity", "epf", "upi"}},
         "THE MONEY SHOT: no loan history, thin GST — but strong rising electricity "
         "and steady EPF prove a stable, growing unit. Traditional model rejects; we approve."),
        ("red_high_risk", "retail",
         {"cw": 0.22, "true_rev": 180_000, "ntc": False, "inconsistent": False,
          "growth_pct": -22},
         "Low health, bounces, high obligations — a defensible RED."),
        ("amber_borderline", "trader",
         {"cw": 0.58, "true_rev": 900_000, "ntc": False, "inconsistent": False,
          "growth_pct": 2},
         "Mixed signals — AMBER with conditions and a moderate limit."),
        ("gig_worker", "gig",
         {"cw": 0.6, "true_rev": 65_000, "ntc": True, "inconsistent": False,
          "growth_pct": 8, "avail_off": {"gst", "epf"}, "avail_on": {"upi", "aa"}},
         "Thin GST, rich UPI — score leans on cash-flow. Inclusion case."),
        ("transporter", "transport",
         {"cw": 0.58, "true_rev": 1_100_000, "ntc": False, "inconsistent": False,
          "growth_pct": 14, "avail_on": {"fuel", "fastag"}},
         "Fuel + FASTag carry the score for a logistics operator."),
        ("inconsistent_data", "trader",
         {"cw": 0.62, "true_rev": 1_000_000, "ntc": False, "inconsistent": True,
          "growth_pct": 8},
         "One source disagrees with the others — cross-validation flags it, "
         "confidence drops, routed for manual review (data-reliability story)."),
        ("salaried_individual", "salaried",
         {"cw": 0.66, "true_rev": 95_000, "ntc": False, "inconsistent": False,
          "growth_pct": 6, "avail_on": {"epf", "aa", "upi"}},
         "Salary credits + EPF + clean bank flows — retail-asset applicant."),
    ]
    profiles = []
    for i, (name, seg, force, note) in enumerate(specs):
        row = generate_entity(rng, 900000 + i, segment=seg, force=force)
        row["_demo_name"] = name
        row["_demo_note"] = note
        row["series"] = {
            "gst_turnover": month_series(rng, row.get("gst_turnover_monthly"),
                                         row.get("gst_trend_pct") or 0, row.get("gst_volatility") or 0.2),
            "upi_inflow": month_series(rng, row.get("upi_inflow_monthly"),
                                       row.get("gst_trend_pct") or 0, row.get("upi_volatility") or 0.2),
            "electricity_units": month_series(rng, row.get("electricity_units_monthly"),
                                              row.get("electricity_trend_pct") or 0, 0.15),
        }
        profiles.append(row)
    return profiles


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Generate synthetic MSME credit dataset.")
    ap.add_argument("--n", type=int, default=5000, help="number of rows (default 5000)")
    ap.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    os.makedirs(OUT_DIR, exist_ok=True)

    rows = [generate_entity(rng, i) for i in range(args.n)]

    cols = column_order()
    csv_path = os.path.join(OUT_DIR, "msme_dataset.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    demo_rng = random.Random(args.seed + 1)
    demos = build_demo_profiles(demo_rng)
    json_path = os.path.join(OUT_DIR, "demo_profiles.json")
    with open(json_path, "w") as f:
        json.dump(demos, f, indent=2)

    _summary(rows, args.n, csv_path, json_path)


def _summary(rows, n, csv_path, json_path):
    defaults = sum(r["default"] for r in rows)
    ntc = sum(r["is_ntc"] for r in rows)
    thin = sum(1 for r in rows if _source_count(r) <= 3)
    incons = sum(r["_gt_inconsistent"] for r in rows)
    print(f"\n  Wrote {n:,} rows -> {csv_path}")
    print(f"  Wrote 8 demo profiles -> {json_path}\n")
    print(f"  Overall default rate : {defaults / n:6.2%}   ({defaults:,} defaults)")
    print(f"  New-to-Credit        : {ntc / n:6.2%}")
    print(f"  Thin-file (<=3 srcs) : {thin / n:6.2%}")
    print(f"  Inconsistent-data    : {incons / n:6.2%}\n")
    print("  Default rate & size by segment:")
    segs = {}
    for r in rows:
        s = r["segment"]
        segs.setdefault(s, [0, 0, 0.0])
        segs[s][0] += 1
        segs[s][1] += r["default"]
        segs[s][2] += r["_gt_true_revenue"]
    for s in sorted(segs, key=lambda x: -segs[x][0]):
        cnt, dfl, rev = segs[s]
        print(f"    {s:13s} n={cnt:5d}  default={dfl / cnt:6.2%}  avg_rev=Rs.{rint(rev / cnt):>10,}")
    print()


def _source_count(r):
    return sum(int(r.get(f"{s}_available", 0) or 0) for s in SOURCES) + int(r.get("bureau_available", 0) or 0)


if __name__ == "__main__":
    main()
