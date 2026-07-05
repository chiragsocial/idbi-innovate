"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import PortfolioDashboard from "@/components/PortfolioDashboard";
import { Loader2, WifiOff } from "lucide-react";

export default function PortfolioPage() {
  const [p, setP] = useState<Record<string, any> | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.portfolio().then(setP).catch((e) => setErr(String(e)));
  }, []);

  if (err)
    return (
      <div className="card mx-auto max-w-lg p-6 text-center">
        <WifiOff className="mx-auto mb-2 text-slate-400" />
        <h2 className="font-semibold">Cannot reach the backend</h2>
        <p className="mt-2 text-xs text-slate-400">{err}</p>
      </div>
    );

  if (!p)
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    );

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-semibold">Portfolio impact</h1>
        <p className="text-sm text-slate-500">
          Financial-inclusion lift and risk distribution across the scored book.
        </p>
      </div>
      <PortfolioDashboard p={p} />
    </div>
  );
}
