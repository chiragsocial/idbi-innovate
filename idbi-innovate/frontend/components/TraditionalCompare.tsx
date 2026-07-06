"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RagBadge, RecoBadge } from "./badges";
import { inr } from "@/lib/format";
import { Eye, EyeOff, Ban, CheckCircle2 } from "lucide-react";

const ALT_SOURCES = ["upi", "aa", "epf", "electricity", "fuel", "fastag"];

export default function TraditionalCompare({
  entityId,
  current,
}: {
  entityId: string;
  current: any;
}) {
  const hasGst = current?.cross_validation?.estimates?.gst != null;
  const hasBureau = current?.is_ntc === false;
  const canAssess = hasGst || hasBureau;
  const [tradConf, setTradConf] = useState<number | null>(null);

  useEffect(() => {
    if (!canAssess) return;
    let alive = true;
    api
      .simulate(entityId, [], ALT_SOURCES)
      .then((r) => alive && setTradConf(r.after.data_confidence ?? null))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [entityId, canAssess]);

  const fullConf = current.data_confidence;

  return (
    <div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <EyeOff size={14} /> Traditional lens (bureau + GST only)
          </div>
          {!canAssess ? (
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
          ) : (
            <>
              <span className="chip bg-slate-200 text-slate-700">
                <CheckCircle2 size={12} /> Assessable
              </span>
              <div className="mt-2 text-3xl font-bold text-slate-700">
                {tradConf !== null ? `${tradConf.toFixed(0)}%` : "—"}
                <span className="ml-1 text-sm font-medium text-slate-400">data-confidence</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Bureau/GST alone is thin evidence — and it rejects the ~40% who have neither.
              </p>
            </>
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
            <b>{inr(current.suggested_limit)}</b> ·{" "}
            <b className="tabular-nums">{fullConf.toFixed(0)}%</b> confidence
          </div>
          <p className="mt-2 text-xs text-brand-dark">
            Assesses <b>every</b> borrower — including the credit-invisible — at higher confidence,
            with explainable, reliability-checked signals.
          </p>
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Our edge is <b>reach &amp; confidence</b>: we bring credit-invisible MSMEs into assessment
        and decide on richer evidence — not a higher score for the already-documented.
      </p>
    </div>
  );
}
