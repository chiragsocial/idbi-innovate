import type { CrossValidation as XV } from "@/lib/api";
import { inr } from "@/lib/format";
import { GitCompareArrows, CheckCircle2, AlertTriangle } from "lucide-react";

// Shows the independent revenue estimates per source and whether they agree —
// the data-reliability differentiator the AMA mentors asked for.
export default function CrossValidation({ xv }: { xv: XV }) {
  const entries = Object.entries(xv.estimates);
  const ok = xv.consistent !== false;
  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <GitCompareArrows size={15} /> Cross-source validation
      </div>
      {entries.length === 0 ? (
        <p className="text-sm text-slate-500">No scale sources to cross-check.</p>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2">
            {entries.map(([src, v]) => (
              <div key={src} className="stat text-center">
                <div className="text-[10px] uppercase text-slate-400">{src}</div>
                <div className="text-sm font-semibold tabular-nums">{inr(v)}/mo</div>
              </div>
            ))}
          </div>
          <div
            className={`mt-2 flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs ${
              ok ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
            }`}
          >
            {ok ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
            {xv.cv === null
              ? "Single source — cannot cross-check (mild discount applied)."
              : ok
              ? `Sources agree (variation ${(xv.cv * 100).toFixed(0)}%) · reliability ${(xv.scale_reliability * 100).toFixed(0)}%`
              : `Sources disagree (variation ${(xv.cv * 100).toFixed(0)}%) — flagged for manual verification`}
          </div>
        </>
      )}
    </div>
  );
}
