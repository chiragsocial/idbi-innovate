"use client";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { Pillar } from "@/lib/api";

const SHORT: Record<string, string> = {
  revenue_scale: "Revenue",
  cash_flow: "Cash-Flow",
  operational_vitality: "Operations",
  stability_formalization: "Stability",
  credit_discipline: "Discipline",
  identity_reliability: "Reliability",
};

export default function PillarRadar({ pillars }: { pillars: Pillar[] }) {
  const data = pillars.map((p) => ({
    pillar: SHORT[p.key] || p.label,
    score: p.subscore ?? 0,
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis dataKey="pillar" tick={{ fontSize: 11, fill: "#475569" }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "#94a3b8" }} angle={90} />
        <Radar dataKey="score" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.28} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
