#!/usr/bin/env python3
"""
Fairness / disparate-impact analysis (pure stdlib, runs anywhere).

Credit models must be checked for disparate impact — this is a hard requirement for
any bank deploying an AI scorecard (RBI fair-lending expectations + reputational risk).
We report, per group:
  * approval rate (APPROVE or REVIEW — i.e. not auto-declined)
  * actual default rate
  * average score
and the four-fifths (80%) disparate-impact ratio = min_group_rate / max_group_rate.

Two questions we specifically answer:
  1. Do we PENALISE New-to-Credit applicants?  (should be ~parity — the thesis)
  2. Does geography create disparate impact?    (we use state features — must monitor)

    python3 -m ml.fairness
Writes ml/artifacts/fairness.json.
"""
import csv
import json
import os
from collections import defaultdict

from scoring import score_entity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "output", "msme_dataset.csv")
ART = os.path.join(ROOT, "ml", "artifacts")

APPROVABLE = {"APPROVE", "REVIEW"}


def _groups(rows, key):
    agg = defaultdict(lambda: {"n": 0, "approvable": 0, "defaults": 0, "score": 0.0})
    for r, card in rows:
        g = str(r.get(key))
        a = agg[g]
        a["n"] += 1
        a["approvable"] += int(card["recommendation"] in APPROVABLE)
        a["defaults"] += int(r["default"])
        a["score"] += card["unified_score"]
    out = {}
    for g, a in agg.items():
        out[g] = {
            "n": a["n"],
            "approval_rate": round(a["approvable"] / a["n"], 3),
            "default_rate": round(a["defaults"] / a["n"], 3),
            "avg_score": round(a["score"] / a["n"], 1),
        }
    return out


def _disparate_impact(groups, min_n=30):
    rates = [g["approval_rate"] for g in groups.values() if g["n"] >= min_n]
    if len(rates) < 2 or max(rates) == 0:
        return None
    return round(min(rates) / max(rates), 3)


def main():
    with open(DATA) as f:
        raw = list(csv.DictReader(f))
    scored = [(r, score_entity(r)) for r in raw]

    report = {"n": len(raw)}
    for dim in ["is_ntc", "segment", "state", "city_tier"]:
        groups = _groups(scored, dim)
        di = _disparate_impact(groups)
        report[dim] = {"groups": groups, "disparate_impact_ratio": di,
                       "passes_four_fifths": (di is None or di >= 0.8)}

    os.makedirs(ART, exist_ok=True)
    with open(os.path.join(ART, "fairness.json"), "w") as f:
        json.dump(report, f, indent=2)

    # ---- console summary ----
    print(f"\nFairness analysis over {report['n']} applicants\n")

    ntc = report["is_ntc"]["groups"]
    print("1) New-to-Credit parity (do we penalise NTC?)")
    for k in sorted(ntc):
        label = "NTC" if k == "1" else "non-NTC"
        g = ntc[k]
        print(f"   {label:8s}  approval {g['approval_rate']:.1%}  default {g['default_rate']:.1%}  avg score {g['avg_score']}")
    print(f"   -> disparate-impact ratio {report['is_ntc']['disparate_impact_ratio']} "
          f"({'PASS' if report['is_ntc']['passes_four_fifths'] else 'REVIEW'} four-fifths)\n")

    print("2) Segment approval rates")
    for k, g in sorted(report["segment"]["groups"].items(), key=lambda kv: -kv[1]["approval_rate"]):
        print(f"   {k:13s} n={g['n']:4d}  approval {g['approval_rate']:.1%}  default {g['default_rate']:.1%}")
    print(f"   -> DI ratio {report['segment']['disparate_impact_ratio']} "
          f"({'PASS' if report['segment']['passes_four_fifths'] else 'REVIEW'})\n")

    di_state = report["state"]["disparate_impact_ratio"]
    print(f"3) Geographic disparate impact: DI ratio {di_state} "
          f"({'PASS' if report['state']['passes_four_fifths'] else 'REVIEW — monitor/mitigate geographic features'})")
    worst = sorted(report["state"]["groups"].items(), key=lambda kv: kv[1]["approval_rate"])[:3]
    best = sorted(report["state"]["groups"].items(), key=lambda kv: -kv[1]["approval_rate"])[:3]
    print("   lowest approval:", ", ".join(f"{k} {v['approval_rate']:.0%}" for k, v in worst))
    print("   highest approval:", ", ".join(f"{k} {v['approval_rate']:.0%}" for k, v in best))
    print(f"\n  Saved -> ml/artifacts/fairness.json\n")


if __name__ == "__main__":
    main()
