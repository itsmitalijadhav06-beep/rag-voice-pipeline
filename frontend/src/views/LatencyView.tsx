import { fmtTelemetryValue, formatPercent, fmtMs } from '../lib/utils';
import type { LatencyTelemetry, QueryResponse } from '../types';

interface LatencyViewProps {
  telemetry: LatencyTelemetry | null;
  slaTargetMs?: number | null;
  response?: QueryResponse | null;
}

interface MetricCardProps {
  label: string;
  value: string;
  unit?: string;
}

function MetricCard({ label, value, unit }: MetricCardProps) {
  return (
    <div className="panel-level-1 p-md rounded border border-white/5 flex flex-col gap-xs">
      <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">{label}</span>
      <span className="font-headline-sm text-headline-sm text-on-surface">{value}</span>
      {unit && <span className="font-mono-data text-mono-data text-outline">{unit}</span>}
    </div>
  );
}

function BreakdownRow({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="flex items-center justify-between gap-sm py-xs">
      <div className="flex items-center gap-xs">
        <span className="text-outline">{icon}</span>
        <span className="font-mono-data text-mono-data text-outline">{label}</span>
      </div>
      <span className="font-mono-data text-mono-data text-on-surface">{value}</span>
    </div>
  );
}

export function LatencyView({ telemetry, slaTargetMs, response }: LatencyViewProps) {
  const p50 = fmtTelemetryValue(telemetry?.p50_ms);
  const p70 = fmtTelemetryValue(telemetry?.p70_ms);
  const p100 = fmtTelemetryValue(telemetry?.p100_ms);
  const samples = telemetry?.sample_count ?? 0;
  const compliance = formatPercent(telemetry?.sla_compliance_rate ?? 0);
  const sla = slaTargetMs != null ? `${Math.round(slaTargetMs)}ms` : '--';

  const breakdown = response?.latency;
  const stt = breakdown ? fmtMs(breakdown.stt_ms) : '--';
  const retrieval = breakdown ? fmtMs(breakdown.retrieval_ms) : '--';
  const generation = breakdown ? fmtMs(breakdown.generation_ms) : '--';
  const guardrails = breakdown ? fmtMs(breakdown.guardrail_ms) : '--';
  const total = breakdown ? fmtMs(breakdown.total_ms) : '--';
  const ragPipeline = breakdown ? fmtMs(breakdown.rag_pipeline_ms) : '--';
  const embedding = breakdown ? fmtMs(breakdown.embedding_ms) : '--';

  return (
    <div className="flex-1 flex flex-col pt-16 pb-10 md:pl-64 w-full">
      <div className="max-w-[1200px] mx-auto p-gutter lg:p-lg grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        <div className="xl:col-span-8 flex flex-col gap-gutter">
          <div className="flex items-center justify-between">
            <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Latency Telemetry</span>
            <span className="font-mono-data text-mono-data text-outline">SLA: {sla}</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-md">
            <MetricCard label="P50" value={p50} />
            <MetricCard label="P70" value={p70} />
            <MetricCard label="P100" value={p100} />
            <MetricCard label="Samples" value={String(samples)} />
          </div>
          <div className="panel-level-1 p-md rounded flex flex-col gap-sm border border-white/5">
            <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Pipeline Breakdown</span>
            <BreakdownRow label="STT" value={stt} icon="mic" />
            <BreakdownRow label="Embedding" value={embedding} icon="linear_scale" />
            <BreakdownRow label="Retrieval" value={retrieval} icon="database" />
            <BreakdownRow label="Generation" value={generation} icon="psychology" />
            <BreakdownRow label="Guardrails" value={guardrails} icon="shield_lock" />
            <div className="border-t border-white/5 pt-xs mt-xs">
              <BreakdownRow label="RAG Pipeline" value={ragPipeline} icon="memory" />
              <BreakdownRow label="Total" value={total} icon="speed" />
            </div>
          </div>
          <div className="flex items-center gap-sm font-mono-data text-mono-data">
            <span className="text-outline">COMPLIANCE: {compliance}</span>
            <span className="text-outline">|</span>
            <span className="text-outline">TARGET: {sla}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
