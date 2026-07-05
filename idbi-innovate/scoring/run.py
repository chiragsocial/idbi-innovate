#!/usr/bin/env python3
"""
Score the curated demo profiles (and optionally a CSV sample) and pretty-print
the Health Cards. Run from the repo root:

    python3 -m scoring.run                       # score demo_profiles.json
    python3 -m scoring.run --csv data/output/msme_dataset.csv --sample 5
"""
import argparse
import csv
import json
import os

from .engine import score_entity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "data", "output", "demo_profiles.json")

_RAG_DOT = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}


def show(card, note=None):
    dot = _RAG_DOT.get(card["rag"], "•")
    print("─" * 78)
    head = f"{dot} {card['rag']:5s} · {card['recommendation']:8s} · score {card['unified_score']:5.1f}/100"
    print(head + f"   [{card['segment']}{' · NTC' if card['is_ntc'] else ''}]")
    if note:
        print(f"   « {note} »")
    er = card["estimated_monthly_revenue"]
    print(f"   est. revenue Rs.{er:,}/mo · suggested limit Rs.{card['suggested_limit']:,}"
          if er else "   est. revenue: n/a")
    print(f"   data-confidence {card['data_confidence']}% ({card['confidence_label']}) · "
          f"{card['sources_used']} sources · risk {card['risk_bucket']}")
    print("   pillars:")
    for p in card["pillars"]:
        sub = f"{p['subscore']:5.1f}" if p["subscore"] is not None else "  -- "
        bar = "█" * int((p["subscore"] or 0) / 5)
        print(f"     {p['label']:30s} {sub}  w={p['weight']:.2f}  {bar}")
    ex = card.get("explanation", {})
    if ex.get("summary"):
        print(f"   ▶ {ex['summary']}")
    if ex.get("strengths"):
        print("   strengths:")
        for s in ex["strengths"]:
            print(f"     + {s['text']}")
    if ex.get("concerns"):
        print("   concerns:")
        for c in ex["concerns"]:
            print(f"     - {c['text']}")
    if ex.get("data_quality"):
        print("   data-quality:")
        for q in ex["data_quality"]:
            print(f"     ⚠ {q}")
    if ex.get("improvements"):
        print("   to sharpen:")
        for im in ex["improvements"]:
            print(f"     → {im}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="score a sample of this CSV instead of demos")
    ap.add_argument("--sample", type=int, default=5)
    args = ap.parse_args()

    if args.csv:
        with open(args.csv) as f:
            rows = list(csv.DictReader(f))
        for r in rows[: args.sample]:
            show(score_entity(r))
    else:
        profiles = json.load(open(DEMO))
        for p in profiles:
            show(score_entity(p), note=p.get("_demo_note"))
    print("─" * 78)


if __name__ == "__main__":
    main()
