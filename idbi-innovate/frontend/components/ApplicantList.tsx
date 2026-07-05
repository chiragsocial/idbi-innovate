"use client";
import type { Summary } from "@/lib/api";
import { RAG_COLOR, inr, titleCase } from "@/lib/format";

function Row({ s, active, onClick }: { s: Summary; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-lg border p-2.5 text-left transition ${
        active ? "border-brand bg-brand-light/50 shadow-sm" : "border-slate-200 bg-white hover:bg-slate-50"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-800">
          {s.demo_name ? titleCase(s.demo_name) : s.entity_id}
        </span>
        <span
          className="h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: RAG_COLOR[s.rag] }}
          title={s.rag}
        />
      </div>
      <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
        <span>{titleCase(s.segment)}</span>
        {s.is_ntc && <span className="chip bg-brand-light px-1.5 py-0 text-[10px] text-brand-dark">NTC</span>}
        <span className="ml-auto tabular-nums">{s.unified_score.toFixed(0)} · {inr(s.suggested_limit)}</span>
      </div>
    </button>
  );
}

export default function ApplicantList({
  demos,
  sample,
  activeId,
  onSelect,
}: {
  demos: Summary[];
  sample: Summary[];
  activeId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Showcase applicants
        </div>
        <div className="space-y-1.5">
          {demos.map((s) => (
            <Row key={s.entity_id} s={s} active={s.entity_id === activeId} onClick={() => onSelect(s.entity_id)} />
          ))}
        </div>
      </div>
      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Portfolio sample ({sample.length})
        </div>
        <div className="max-h-[380px] space-y-1.5 overflow-auto pr-1">
          {sample.map((s) => (
            <Row key={s.entity_id} s={s} active={s.entity_id === activeId} onClick={() => onSelect(s.entity_id)} />
          ))}
        </div>
      </div>
    </div>
  );
}
