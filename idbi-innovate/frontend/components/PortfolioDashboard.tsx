"use client";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { RAG_COLOR } from "@/lib/format";
import { Users, ShieldCheck, TrendingUp } from "lucide-react";

export default function PortfolioDashboard({ p }: { p: Record<string, any> }) {
  const rag = p.rag_distribution || {};
  const ragData = ["GREEN", "AMBER", "RED"].map((k) => ({ name: k, value: rag[k] || 0 }));

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Kpi
          icon={<Users className="text-brand" />}
          value={`${((p.ntc?.rate ?? 0) * 100).toFixed(0)}%`}
          label="New-to-Credit applicants approvable"
          sub={`${p.ntc?.approvable}/${p.ntc?.total} NTC applicants`}
        />
        <Kpi
          icon={<ShieldCheck className="text-brand" />}
          value={`${((p.thin_file?.rate ?? 0) * 100).toFixed(0)}%`}
          label="Thin-file applicants approvable"
          sub={`${p.thin_file?.approvable}/${p.thin_file?.total} thin-file applicants`}
        />
        <Kpi
          icon={<TrendingUp className="text-brand" />}
          value={`${((p.inclusion_lift?.rate ?? 0) * 100).toFixed(0)}%`}
          label="Inclusion lift"
          sub={`${p.inclusion_lift?.recovered_by_alt_data}/${p.inclusion_lift?.traditionally_invisible} credit-invisible borrowers recovered`}
          highlight
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className="mb-2 text-sm font-semibold">Book by risk band</h3>
          <p className="mb-3 text-xs text-slate-500">{p.scored} applicants scored</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={ragData}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#475569" }} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {ragData.map((d) => (
                  <Cell key={d.name} fill={RAG_COLOR[d.name]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className="mb-2 text-sm font-semibold">Recommendation mix</h3>
          <p className="mb-3 text-xs text-slate-500">
            A large REVIEW share is by design — the tool defers to the human underwriter unless
            confident.
          </p>
          <div className="space-y-3">
            {Object.entries(p.recommendation_distribution || {}).map(([k, v]) => {
              const total = p.scored || 1;
              const pctv = ((v as number) / total) * 100;
              return (
                <div key={k}>
                  <div className="flex justify-between text-xs">
                    <span className="font-medium">{k}</span>
                    <span className="text-slate-500">
                      {v as number} ({pctv.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-brand"
                      style={{ width: `${pctv}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function Kpi({ icon, value, label, sub, highlight }: { icon: React.ReactNode; value: string; label: string; sub: string; highlight?: boolean }) {
  return (
    <div className={`card p-5 ${highlight ? "ring-2 ring-brand" : ""}`}>
      <div className="mb-2">{icon}</div>
      <div className="text-3xl font-bold text-ink">{value}</div>
      <div className="mt-1 text-sm font-medium text-slate-700">{label}</div>
      <div className="mt-1 text-xs text-slate-400">{sub}</div>
    </div>
  );
}
