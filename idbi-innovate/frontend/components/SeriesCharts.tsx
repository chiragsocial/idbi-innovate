"use client";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const META: Record<string, { label: string; color: string }> = {
  gst_turnover: { label: "GST turnover", color: "#4f46e5" },
  upi_inflow: { label: "UPI inflow", color: "#0891b2" },
  electricity_units: { label: "Electricity (units)", color: "#d97706" },
};

export default function SeriesCharts({ series }: { series: Record<string, number[]> }) {
  const entries = Object.entries(series).filter(([, v]) => v && v.length > 0);
  if (entries.length === 0) return null;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {entries.map(([key, values]) => {
        const meta = META[key] || { label: key, color: "#64748b" };
        const data = values.map((v, i) => ({ m: `M${i + 1}`, v }));
        return (
          <div key={key} className="stat">
            <div className="mb-1 text-xs font-medium text-slate-600">{meta.label} · 12 mo</div>
            <ResponsiveContainer width="100%" height={90}>
              <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                <XAxis dataKey="m" hide />
                <YAxis hide domain={["dataMin", "dataMax"]} />
                <Tooltip
                  formatter={(v: number) => v.toLocaleString("en-IN")}
                  labelClassName="text-xs"
                  contentStyle={{ fontSize: 11, borderRadius: 8 }}
                />
                <Line type="monotone" dataKey="v" stroke={meta.color} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
}
