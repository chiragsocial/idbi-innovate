import type { Explanation } from "@/lib/api";
import { CheckCircle2, AlertTriangle, ShieldAlert, ArrowUpCircle } from "lucide-react";

export default function ReasonPanel({ ex }: { ex: Explanation }) {
  return (
    <div className="space-y-4">
      {ex.strengths.length > 0 && (
        <Section title="Strengths" icon={<CheckCircle2 size={15} className="text-rag-green" />}>
          {ex.strengths.map((s, i) => (
            <li key={i} className="text-slate-700">{s.text}</li>
          ))}
        </Section>
      )}
      {ex.concerns.length > 0 && (
        <Section title="Concerns" icon={<AlertTriangle size={15} className="text-rag-red" />}>
          {ex.concerns.map((c, i) => (
            <li key={i} className="text-slate-700">{c.text}</li>
          ))}
        </Section>
      )}
      {ex.data_quality.length > 0 && (
        <Section title="Data quality" icon={<ShieldAlert size={15} className="text-amber-600" />}>
          {ex.data_quality.map((q, i) => (
            <li key={i} className="text-slate-700">{q}</li>
          ))}
        </Section>
      )}
      {ex.improvements.length > 0 && (
        <Section title="To sharpen the score" icon={<ArrowUpCircle size={15} className="text-brand" />}>
          {ex.improvements.map((im, i) => (
            <li key={i} className="text-slate-700">{im}</li>
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {icon} {title}
      </div>
      <ul className="ml-1 list-inside list-disc space-y-1 text-sm marker:text-slate-300">{children}</ul>
    </div>
  );
}
