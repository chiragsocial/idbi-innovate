// API client + shared types for the MSME Health Card backend.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface Pillar {
  key: string;
  label: string;
  subscore: number | null;
  coverage: number;
  weight: number;
  contribution: number;
  drivers: Record<string, unknown>;
}

export interface Reason {
  pillar: string;
  impact: number;
  text: string;
}

export interface Explanation {
  summary: string;
  strengths: Reason[];
  concerns: Reason[];
  data_quality: string[];
  improvements: string[];
}

export interface CrossValidation {
  estimates: Record<string, number>;
  cv: number | null;
  consistent: boolean | null;
  scale_reliability: number;
}

export type Rag = "GREEN" | "AMBER" | "RED";
export type Recommendation = "APPROVE" | "REVIEW" | "DECLINE";

export interface Card {
  entity_id: string;
  segment: string;
  is_ntc: boolean;
  is_ntb: boolean;
  unified_score: number;
  rag: Rag;
  risk_bucket: string;
  recommendation: Recommendation;
  suggested_limit: number;
  estimated_monthly_revenue: number | null;
  data_confidence: number;
  confidence_label: string;
  sources_used: number;
  cross_validation: CrossValidation;
  flags: string[];
  pillars: Pillar[];
  explanation: Explanation;
  ml_pd: number | null;
  ml_model?: string;
  demo_name?: string;
  demo_note?: string;
  series?: Record<string, number[]>;
  note: string;
}

export interface Summary {
  entity_id: string;
  segment: string;
  is_ntc: boolean;
  rag: Rag;
  unified_score: number;
  recommendation: Recommendation;
  suggested_limit: number;
  data_confidence: number;
  ml_pd: number | null;
  demo_name?: string;
  demo_note?: string;
}

export interface ApplicantList {
  demos: Summary[];
  sample: Summary[];
}

export interface SimResult {
  before: Partial<Card>;
  after: Partial<Card>;
  delta: { unified_score: number; data_confidence: number; suggested_limit: number };
  after_card: Card;
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}
async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export const api = {
  applicants: () => get<ApplicantList>("/applicants"),
  card: (id: string) => get<Card>(`/applicants/${id}`),
  portfolio: () => get<Record<string, any>>("/portfolio"),
  fairness: () => get<Record<string, any>>("/fairness"),
  simulate: (entity_id: string, add_sources: string[], remove_sources: string[]) =>
    post<SimResult>("/simulate", { entity_id, add_sources, remove_sources }),
  rail: (kind: "aa" | "ocen" | "uli", id: string) =>
    post<Record<string, any>>(`/rails/${kind}/${id}`),
  briefing: (id: string) => post<{ briefing: string; source: string }>(`/briefing/${id}`),
  health: () => get<Record<string, any>>("/health"),
};
