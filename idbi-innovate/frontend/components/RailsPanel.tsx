"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Network, Loader2 } from "lucide-react";

const RAILS: { kind: "aa" | "ocen" | "uli"; label: string }[] = [
  { kind: "aa", label: "Account Aggregator" },
  { kind: "ocen", label: "OCEN" },
  { kind: "uli", label: "ULI" },
];

export default function RailsPanel({ entityId }: { entityId: string }) {
  const [out, setOut] = useState<Record<string, any> | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function call(kind: "aa" | "ocen" | "uli") {
    setBusy(kind);
    try {
      setOut(await api.rail(kind, entityId));
    } catch {
      setOut({ error: "Backend unreachable" });
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <Network size={15} /> Ecosystem rails (mocked)
      </div>
      <div className="flex flex-wrap gap-2">
        {RAILS.map((r) => (
          <button key={r.kind} className="btn" onClick={() => call(r.kind)} disabled={busy !== null}>
            {busy === r.kind ? <Loader2 size={14} className="animate-spin" /> : null}
            {r.label}
          </button>
        ))}
      </div>
      {out && (
        <pre className="mt-2 max-h-52 overflow-auto rounded-lg bg-slate-900 p-3 text-[11px] leading-relaxed text-slate-100">
          {JSON.stringify(out, null, 2)}
        </pre>
      )}
    </div>
  );
}
