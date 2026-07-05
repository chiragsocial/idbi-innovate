"use client";
import { useState } from "react";
import type { Card } from "@/lib/api";
import { inr, titleCase } from "@/lib/format";
import { RagBadge, RecoBadge, ConfidenceBadge, NtcBadge } from "./badges";
import ScoreGauge from "./ScoreGauge";
import PillarRadar from "./PillarRadar";
import PillarBars from "./PillarBars";
import SeriesCharts from "./SeriesCharts";
import ReasonPanel from "./ReasonPanel";
import CrossValidation from "./CrossValidation";
import Briefing from "./Briefing";
import RailsPanel from "./RailsPanel";
import Simulator from "./Simulator";
import TraditionalCompare from "./TraditionalCompare";
import { Building2, IndianRupee, Activity } from "lucide-react";

export default function HealthCard({ initial }: { initial: Card }) {
  const [card, setCard] = useState<Card>(initial);

  return (
    <div className="space-y-4">
      {/* header */}
      <div className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Building2 size={18} className="text-slate-400" />
              <h2 className="text-lg font-semibold">
                {card.demo_name ? titleCase(card.demo_name) : card.entity_id}
              </h2>
              {card.is_ntc && <NtcBadge />}
            </div>
            <div className="mt-1 text-sm text-slate-500">
              {titleCase(card.segment)} · est. revenue {inr(card.estimated_monthly_revenue)}/mo ·{" "}
              {card.sources_used} data sources
            </div>
            {card.demo_note && (
              <p className="mt-2 max-w-2xl rounded-lg bg-slate-50 px-3 py-2 text-xs italic text-slate-500">
                {card.demo_note}
              </p>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <RagBadge rag={card.rag} />
              <RecoBadge reco={card.recommendation} />
              <ConfidenceBadge value={card.data_confidence} label={card.confidence_label} />
              {card.ml_pd !== null && (
                <span className="chip bg-slate-100 text-slate-700" title={`Model: ${card.ml_model}`}>
                  <Activity size={12} /> PD {(card.ml_pd * 100).toFixed(1)}%
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-center">
            <ScoreGauge score={card.unified_score} rag={card.rag} />
            <div className="mt-1 flex items-center gap-1 text-sm font-semibold">
              <IndianRupee size={14} className="text-slate-400" />
              Suggested limit {inr(card.suggested_limit)}
            </div>
          </div>
        </div>
      </div>

      {/* money shot */}
      <div className="card p-5">
        <h3 className="mb-3 text-sm font-semibold">Traditional vs alternate-data assessment</h3>
        <TraditionalCompare entityId={card.entity_id} current={card} />
      </div>

      {/* pillars + reasons */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className="mb-3 text-sm font-semibold">Financial-health pillars</h3>
          <PillarRadar pillars={card.pillars} />
          <div className="mt-4">
            <PillarBars pillars={card.pillars} />
          </div>
        </div>
        <div className="card space-y-4 p-5">
          <h3 className="text-sm font-semibold">Why — reason codes</h3>
          <Briefing entityId={card.entity_id} fallback={card.explanation.summary} />
          <ReasonPanel ex={card.explanation} />
        </div>
      </div>

      {/* series */}
      {card.series && (
        <div className="card p-5">
          <h3 className="mb-3 text-sm font-semibold">Trends</h3>
          <SeriesCharts series={card.series} />
        </div>
      )}

      {/* validation + simulator + rails */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card p-5">
          <CrossValidation xv={card.cross_validation} />
        </div>
        <div className="card p-5">
          <Simulator entityId={card.entity_id} onApply={setCard} />
        </div>
        <div className="card p-5">
          <RailsPanel entityId={card.entity_id} />
        </div>
      </div>

      <p className="px-1 text-xs text-slate-400">{card.note}</p>
    </div>
  );
}
