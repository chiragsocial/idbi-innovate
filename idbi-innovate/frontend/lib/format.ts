export function inr(x: number | null | undefined): string {
  if (x === null || x === undefined) return "—";
  const n = Number(x);
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(1)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
}

export function pct(x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined) return "—";
  return `${(x * 100).toFixed(digits)}%`;
}

export const RAG_COLOR: Record<string, string> = {
  GREEN: "#16a34a",
  AMBER: "#d97706",
  RED: "#dc2626",
};

export const RAG_BG: Record<string, string> = {
  GREEN: "bg-rag-green",
  AMBER: "bg-rag-amber",
  RED: "bg-rag-red",
};

export function titleCase(s: string): string {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
