"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RagBadge, RecoBadge } from "./badges";
import { inr } from "@/lib/format";
import { Eye, EyeOff, Loader2, Ban } from "lucide-react";

const ALT_SOURCES = ["upi", "aa", "epf", "electricity", "fuel", "fastag"];

export default function TraditionalCompare({
  entityId,
  current,
}: {
  entityId: string;
  current: any;
}) {
  const [trad, setTrad] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const hasGst = current?.cross_validation?.estimates?.gst != null;
  const hasBureau = current?.is_ntc === false;
  const canAssess = hasGst || hasBureau;

  useEffect(() => {
    if (!canAssess) {
      setLoading(false);
      return;
    }
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
  }, [entityId, canAssess]);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <EyeOff size={14} /> Traditional lens (bureau + GST only)
        </div>
        {loading ? (
          <Loader2 className="animate-spin text-slate-400" size={18} />
        ) : !canAssess ? (
          <>
            <div className="flex items-center gap-2">
              <span className="chip bg-red-100 text-red-800">
                <Ban size={12} /> Cannot assess
              </span>
              <RecoBadge reco="DECLINE" />
            </div>
            <div className="mt-2 text-3xl font-bold text-rag-red">Rejected</div>
            <p className="mt-2 text-xs text-slate-500">
              No bureau score and no financial statements — a legacy model has nothing to
              assess, so this borrower is declined outright.
            </p>
          </>
        ) : trad ? (
          <>
            <div className="flex items-center gap-2">
              <RagBadge rag={trad.rag} />
              <RecoBadge reco={trad.recommendation} />
            </div>
            <div className="mt-2 text-sm text-slate-600">
              Score <b className="tabular-nums">{trad.unified_score?.toFixed(0)}</b> · limit{" "}
              <b>{inr(trad.suggested_limit)}</b> · confidence <b>{trad.data_confidence?.toFixed(0)}%</b>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              What a legacy bureau/GST-only model sees — often too thin to lend on.
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
