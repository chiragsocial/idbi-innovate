"use client";
import { useEffect, useState } from "react";
import { api, type ApplicantList as List, type Card } from "@/lib/api";
import ApplicantList from "@/components/ApplicantList";
import HealthCard from "@/components/HealthCard";
import { Loader2, WifiOff } from "lucide-react";

export default function Cockpit() {
  const [list, setList] = useState<List | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [card, setCard] = useState<Card | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loadingCard, setLoadingCard] = useState(false);

  useEffect(() => {
    api
      .applicants()
      .then((l) => {
        setList(l);
        if (l.demos[0]) setActiveId(l.demos[0].entity_id);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (!activeId) return;
    setLoadingCard(true);
    api
      .card(activeId)
      .then(setCard)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoadingCard(false));
  }, [activeId]);

  if (err) {
    return (
      <div className="card mx-auto max-w-lg p-6 text-center">
        <WifiOff className="mx-auto mb-2 text-slate-400" />
        <h2 className="font-semibold">Cannot reach the backend</h2>
        <p className="mt-1 text-sm text-slate-500">
          Start it with <code className="rounded bg-slate-100 px-1">uvicorn backend.app.main:app --port 8000</code>{" "}
          and set <code className="rounded bg-slate-100 px-1">NEXT_PUBLIC_API_BASE</code> in <code>.env.local</code>.
        </p>
        <p className="mt-2 text-xs text-slate-400">{err}</p>
      </div>
    );
  }

  if (!list) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <Loader2 className="animate-spin" /> <span className="ml-2">Loading applicants…</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[300px_1fr]">
      <aside className="lg:sticky lg:top-20 lg:self-start">
        <ApplicantList demos={list.demos} sample={list.sample} activeId={activeId} onSelect={setActiveId} />
      </aside>
      <section>
        {loadingCard && !card ? (
          <div className="flex h-64 items-center justify-center text-slate-400">
            <Loader2 className="animate-spin" />
          </div>
        ) : card ? (
          <HealthCard key={card.entity_id} initial={card} />
        ) : null}
      </section>
    </div>
  );
}
