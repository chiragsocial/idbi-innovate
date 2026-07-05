"use client";
import { useState } from "react";
import { api, type SimResult } from "@/lib/api";
import { inr } from "@/lib/format";
import { FlaskConical, Loader2, ArrowRight } from "lucide-react";

const ADDABLE = [
  { id: "aa", label: "Request AA consent" },
  { id: "gst", label: "Pull GST returns" },
  { id: "epf", label: "Add EPFO" },
  { id: "electricity", label: "Add electricity" },
];

// What-if: add a consent/source and watch confidence + limit + PD update live.
export default function Simulator({ entityId, onApply }: { entityId: string; onApply: (c: SimResult["after_card"]) => void }) {
  const [sel, setSel] = useState<string[]>([]);
  const [res, setRes] = useState<SimResult | null>(null);
  const [busy, setBusy] = useState(false);

  const toggle = (id: string) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  async function run() {
    if (sel.length === 0) return;
    setBusy(true);
    try {
      const r = await api.simulate(entityId, sel, []);
      setRes(r);
    } catch {
      /* ignore */
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <FlaskConical size={15} /> What-if: add data sources
      </div>
      <div className="flex flex-wrap gap-2">
        {ADDABLE.map((a) => (
          <button
            key={a.id}
            onClick={() => toggle(a.id)}
            className={`btn ${sel.includes(a.id) ? "btn-brand" : ""}`}
          >
            {a.label}
          </button>
        ))}
        <button className="btn btn-brand" onClick={run} disabled={busy || sel.length === 0}>
          {busy ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />} Simulate
        </button>
      </div>

      {res && (
        <div className="mt-3 grid grid-cols-3 gap-2 text-center">
          <Delta label="Score" before={res.before.unified_score} after={res.after.unified_score} d={res.delta.unified_score} />
          <Delta label="Confidence" before={res.before.data_confidence} after={res.after.data_confidence} d={res.delta.data_confidence} suffix="%" />
          <div className="stat">
            <div className="text-[10px] uppercase text-slate-400">Suggested limit</div>
            <div className="flex items-center justify-center gap-1 text-sm font-semibold">
              <span className="text-slate-400">{inr(res.before.suggested_limit as number)}</span>
              <ArrowRight size={12} className="text-slate-400" />
              <span>{inr(res.after.suggested_limit as number)}</span>
            </div>
          </div>
        </div>
      )}
      {res && (
        <button className="btn mt-2 w-full" onClick={() => onApply(res.after_card)}>
          Apply this scenario to the card ↑
        </button>
      )}
    </div>
  );
}

function Delta({ label, before, after, d, suffix = "" }: { label: string; before: any; after: any; d: number; suffix?: string }) {
  const up = d > 0;
  const color = d === 0 ? "text-slate-500" : up ? "text-rag-green" : "text-rag-red";
  return (
    <div className="stat">
      <div className="text-[10px] uppercase text-slate-400">{label}</div>
      <div className="text-sm font-semibold">
        {Number(after).toFixed(0)}{suffix}
      </div>
      <div className={`text-[11px] ${color}`}>{d > 0 ? "+" : ""}{d.toFixed(1)}{suffix}</div>
    </div>
  );
}
