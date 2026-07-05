import { RAG_COLOR } from "@/lib/format";

export function RagBadge({ rag }: { rag: string }) {
  return (
    <span
      className="chip text-white"
      style={{ backgroundColor: RAG_COLOR[rag] || "#64748b" }}
    >
      ● {rag}
    </span>
  );
}

export function RecoBadge({ reco }: { reco: string }) {
  const map: Record<string, string> = {
    APPROVE: "bg-green-100 text-green-800",
    REVIEW: "bg-amber-100 text-amber-800",
    DECLINE: "bg-red-100 text-red-800",
  };
  return <span className={`chip ${map[reco] || "bg-slate-100 text-slate-700"}`}>{reco}</span>;
}

export function ConfidenceBadge({ value, label }: { value: number; label: string }) {
  const color =
    label === "High" ? "bg-green-100 text-green-800" : label === "Medium" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800";
  return (
    <span className={`chip ${color}`} title="Data confidence: coverage × cross-source agreement">
      {value.toFixed(0)}% confidence · {label}
    </span>
  );
}

export function NtcBadge() {
  return <span className="chip bg-brand-light text-brand-dark">New-to-Credit</span>;
}
