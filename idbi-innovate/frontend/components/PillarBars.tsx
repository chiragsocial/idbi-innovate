"use client";
import type { Pillar } from "@/lib/api";
import { RAG_COLOR } from "@/lib/format";

function barColor(score: number | null): string {
  if (score === null) return "#cbd5e1";
  if (score >= 72) return RAG_COLOR.GREEN;
  if (score >= 50) return RAG_COLOR.AMBER;
  return RAG_COLOR.RED;
}

// Shows each pillar's sub-score AND its adaptive weight — the "hybrid" story made visible.
export default function PillarBars({ pillars }: { pillars: Pillar[] }) {
  return (
    <div className="space-y-2.5">
      {pillars.map((p) => {
        const excluded = p.key === "identity_reliability";
        return (
          <div key={p.key}>
            <div className="flex items-baseline justify-between text-xs">
              <span className="font-medium text-slate-700">
                {p.label}
                {excluded && (
                  <span className="ml-1 text-slate-400" title="Informational — feeds data-confidence, not the credit score">
                    (info)
                  </span>
                )}
              </span>
              <span className="tabular-nums text-slate-500">
                {p.subscore === null ? (
                  <span className="italic text-slate-400">no data</span>
                ) : (
                  <>
                    {p.subscore.toFixed(0)}
                    <span className="ml-2 text-slate-400">w {(p.weight * 100).toFixed(0)}%</span>
                  </>
                )}
              </span>
            </div>
            <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${p.subscore ?? 0}%`, backgroundColor: barColor(p.subscore) }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
