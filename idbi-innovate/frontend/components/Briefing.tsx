"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Sparkles, Loader2 } from "lucide-react";

// Optional LLM narration. The button is clearly labelled: it rephrases only.
export default function Briefing({ entityId, fallback }: { entityId: string; fallback: string }) {
  const [text, setText] = useState(fallback);
  const [source, setSource] = useState("deterministic");
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    try {
      const r = await api.briefing(entityId);
      setText(r.briefing);
      setSource(r.source);
    } catch {
      /* keep fallback */
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-brand-light bg-brand-light/40 p-3">
      <div className="mb-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand-dark">
          <Sparkles size={14} /> Underwriter briefing
        </div>
        <button className="btn text-xs" onClick={run} disabled={loading}>
          {loading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
          {source === "gemini" ? "Regenerate" : "Generate with AI"}
        </button>
      </div>
      <p className="text-sm leading-relaxed text-slate-700">{text}</p>
      <div className="mt-1 text-[11px] text-slate-400">
        {source === "gemini"
          ? "Rephrased by Gemini — decision & numbers are deterministic and unchanged."
          : "Deterministic summary. Set GEMINI_API_KEY on the backend for AI narration (rephrasing only)."}
      </div>
    </div>
  );
}
