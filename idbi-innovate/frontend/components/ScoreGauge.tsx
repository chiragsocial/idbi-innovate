"use client";
import { RAG_COLOR } from "@/lib/format";

// Semicircular 0-100 gauge, needle + arc coloured by RAG band.
export default function ScoreGauge({
  score,
  rag,
  size = 200,
}: {
  score: number;
  rag: string;
  size?: number;
}) {
  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;
  const startA = Math.PI; // 180deg
  const endA = 0; // 0deg
  const frac = Math.max(0, Math.min(1, score / 100));
  const angle = startA + (endA - startA) * frac;

  const polar = (a: number, radius = r) => [cx + radius * Math.cos(a), cy - radius * Math.sin(a)];
  const arc = (a0: number, a1: number) => {
    const [x0, y0] = polar(a0);
    const [x1, y1] = polar(a1);
    const large = Math.abs(a1 - a0) > Math.PI ? 1 : 0;
    const sweep = a1 < a0 ? 1 : 0;
    return `M ${x0} ${y0} A ${r} ${r} 0 ${large} ${sweep} ${x1} ${y1}`;
  };

  // band boundaries: RED 0-50, AMBER 50-72, GREEN 72-100
  const a50 = startA + (endA - startA) * 0.5;
  const a72 = startA + (endA - startA) * 0.72;
  const [nx, ny] = polar(angle, r - 6);

  return (
    <svg width={size} height={size / 2 + 24} viewBox={`0 0 ${size} ${size / 2 + 24}`}>
      <path d={arc(startA, a50)} stroke={RAG_COLOR.RED} strokeWidth={12} fill="none" strokeLinecap="round" opacity={0.85} />
      <path d={arc(a50, a72)} stroke={RAG_COLOR.AMBER} strokeWidth={12} fill="none" opacity={0.85} />
      <path d={arc(a72, endA)} stroke={RAG_COLOR.GREEN} strokeWidth={12} fill="none" strokeLinecap="round" opacity={0.85} />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={RAG_COLOR[rag]} strokeWidth={3} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={5} fill={RAG_COLOR[rag]} />
      <text x={cx} y={cy - 18} textAnchor="middle" className="fill-ink" style={{ fontSize: 30, fontWeight: 700 }}>
        {score.toFixed(0)}
      </text>
      <text x={cx} y={cy + 2} textAnchor="middle" className="fill-slate-400" style={{ fontSize: 11 }}>
        / 100
      </text>
    </svg>
  );
}
