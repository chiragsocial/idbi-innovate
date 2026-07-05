"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RagBadge, RecoBadge } from "./badges";
import { inr } from "@/lib/format";
import { Eye, EyeOff, Loader2 } from "lucide-react";

// THE MONEY SHOT: strip the alternate data (leaving only bureau+GST, the
// "traditional" lens) and show what the borrower looks like to a legacy model vs
// with alternate data. For a New-to-Credit applicant, traditional = invisible.
const ALT_SOURCES = ["upi", "aa", "epf", "electricity", "fuel", "fastag"];

export default function TraditionalCompare({ entityId, current }: { entityId: string; current: { rag: string; unified_score: number; recommendation: string; suggested_limit: number } }) {
  const [trad, setTrad] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api
      .simulate(entityId, [], ALT_SOURCES)
      .then((r) => alive && setTrad(r.after))
      .catch(() => alive && setTrad(null))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [entityId]);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <EyeOff size={14} /> Traditional lens (bureau + GST only)
        </div>
        {loading ? (
          <Loader2 className="animate-spin text-slate-400" size={18} />
        ) : trad ? (
          <>
            <div className="flex items-center gap-2">
              <RagBadge rag={trad.rag} />
              <RecoBadge reco={trad.recommendation} />
            </div>
            <div className="mt-2 text-sm text-slate-600">
              Score <b className="tabular-nums">{trad.unified_score?.toFixed(0)}</b> · limit{" "}
              <b>{inr(trad.suggested_limit)}</b> · confidence{" "}
              <b>{trad.data_confidence?.toFixed(0)}%</b>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              What a legacy bureau/GST-only model sees — often too little to lend on.
            </p>
          </>
        ) : (
          <p className="text-sm text-slate-500">Backend unreachable.</p>
        )}
      </div>

      <div className="rounded-xl border-2 border-brand bg-brand-light/40 p-4">
        <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand-dark">
          <Eye size={14} /> With alternate data (our model)
        </div>
        <div className="flex items-center gap-2">
          <RagBadge rag={current.rag} />
          <RecoBadge reco={current.recommendation} />
        </div>
        <div className="mt-2 text-sm text-slate-700">
          Score <b className="tabular-nums">{current.unified_score.toFixed(0)}</b> · limit{" "}
          <b>{inr(current.suggested_limit)}</b>
        </div>
        <p className="mt-2 text-xs text-brand-dark">
          Alternate data (UPI, bank, EPF, electricity…) reveals a creditworthy borrower the
          traditional lens misses.
        </p>
      </div>
    </div>
  );
}
