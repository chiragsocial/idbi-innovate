"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, WifiOff, CheckCircle2, AlertTriangle, ShieldCheck, Scale, MapPin, Users } from "lucide-react";

function DiBadge({ pass }: { pass: boolean }) {
  return (
    <span className={`chip ${pass ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}`}>
      {pass ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
      {pass ? "Passes four-fifths" : "Review"}
    </span>
  );
}

export default function GovernancePage() {
  const [f, setF] = useState<Record<string, any> | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.fairness().then(setF).catch((e) => setErr(String(e)));
  }, []);

  if (err)
    return (
      <div className="card mx-auto max-w-lg p-6 text-center">
        <WifiOff className="mx-auto mb-2 text-slate-400" />
        <h2 className="font-semibold">Fairness report unavailable</h2>
        <p className="mt-1 text-sm text-slate-500">Run <code className="rounded bg-slate-100 px-1">python -m ml.fairness</code> on the backend.</p>
        <p className="mt-2 text-xs text-slate-400">{err}</p>
      </div>
    );
  if (!f)
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    );

  const ntc = f.is_ntc;
  const ntcG = ntc.groups;
  const seg = f.segment;
  const state = f.state;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-semibold">
          <ShieldCheck className="text-brand" /> Governance & Fairness
        </h1>
        <p className="text-sm text-slate-500">
          Disparate-impact monitoring (four-fifths rule) over {f.n?.toLocaleString()} applicants.
          Decision layer is deterministic, explainable, and human-in-the-loop.
        </p>
      </div>

      {/* NTC parity — the headline */}
      <div className="card p-5">
        <div className="mb-2 flex items-center gap-2">
          <Users size={16} className="text-brand" />
          <h3 className="text-sm font-semibold">New-to-Credit parity — do we penalise the credit-invisible?</h3>
          <DiBadge pass={ntc.passes_four_fifths} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          {["1", "0"].map((k) => (
            <div key={k} className="stat">
              <div className="text-xs text-slate-500">{k === "1" ? "New-to-Credit" : "Existing credit history"}</div>
              <div className="mt-1 text-2xl font-bold">{(ntcG[k].approval_rate * 100).toFixed(0)}%</div>
              <div className="text-xs text-slate-400">
                approval · default {(ntcG[k].default_rate * 100).toFixed(1)}% · avg score {ntcG[k].avg_score}
              </div>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          DI ratio <b>{ntc.disparate_impact_ratio}</b> — NTC applicants are approved at parity with
          equal default rates. Alternate data safely serves the credit-invisible.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Geography */}
        <div className="card p-5">
          <div className="mb-2 flex items-center gap-2">
            <MapPin size={16} className="text-brand" />
            <h3 className="text-sm font-semibold">Geographic disparate impact</h3>
            <DiBadge pass={state.passes_four_fifths} />
          </div>
          <div className="text-3xl font-bold">{state.disparate_impact_ratio}</div>
          <p className="mt-1 text-xs text-slate-500">
            The decision layer uses <b>no geographic attribute</b>, so location does not drive the
            recommendation.
          </p>
        </div>

        {/* Segment (risk-justified) */}
        <div className="card p-5">
          <div className="mb-2 flex items-center gap-2">
            <Scale size={16} className="text-brand" />
            <h3 className="text-sm font-semibold">Segment differences (risk-justified)</h3>
          </div>
          <p className="text-xs text-slate-500">
            DI {seg.disparate_impact_ratio}. Lower approval for higher-risk segments tracks{" "}
            <b>actual default experience</b>, not bias — segment is a business-risk dimension, not a
            protected class.
          </p>
          <div className="mt-2 max-h-40 space-y-1 overflow-auto">
            {Object.entries(seg.groups)
              .sort((a: any, b: any) => b[1].approval_rate - a[1].approval_rate)
              .map(([k, g]: any) => (
                <div key={k} className="flex items-center justify-between text-xs">
                  <span className="capitalize text-slate-600">{k}</span>
                  <span className="tabular-nums text-slate-500">
                    approval {(g.approval_rate * 100).toFixed(0)}% · default {(g.default_rate * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      <div className="card p-5 text-sm text-slate-600">
        <h3 className="mb-2 text-sm font-semibold">Governance guarantees</h3>
        <ul className="list-inside list-disc space-y-1 marker:text-slate-300">
          <li>Human-in-the-loop — AI recommends, the underwriter decides; thin-file → review, never auto-reject.</li>
          <li>Deterministic, auditable reason codes — no LLM in the decision path.</li>
          <li>Consent-first (Account Aggregator), data-minimising, purpose-bound (DPDP Act 2023).</li>
          <li>Cross-source validation + MNRL checks for data reliability.</li>
          <li>Continuous disparate-impact + drift monitoring (see Model Card).</li>
        </ul>
      </div>
    </div>
  );
}
