import { Icon } from '../ui/Icon';
import { fmtMs } from '../../lib/utils';
import { Surface } from '../ui/Surface';
import type { QueryResponse, PipelineLatencyBreakdown } from '../../types';

export interface TelemetryGridProps {
  response: QueryResponse;
}

interface RowDef {
  key: string;
  icon: string;
  label: string;
  color: string;
}

const rows: RowDef[] = [
  { key: 'stt', icon: 'mic', label: 'STT', color: 'text-tertiary' },
  { key: 'retrieval', icon: 'database', label: 'RETRIEVAL', color: 'text-tertiary' },
  { key: 'generation', icon: 'psychology', label: 'GENERATION', color: 'text-tertiary' },
  { key: 'guardrails', icon: 'shield_lock', label: 'GUARDRAILS', color: 'text-tertiary' },
  { key: 'total', icon: 'speed', label: 'TOTAL', color: 'text-primary' },
];

export function TelemetryGrid({ response }: TelemetryGridProps) {
  const lat = response.latency;
  return (
    <Surface className="p-md rounded flex flex-col gap-sm border border-white/5">
      <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Telemetry</span>
      <div className="grid grid-cols-2 gap-xs font-mono-data text-mono-data text-on-surface-variant">
        {rows.map((r) => {
          const value = valueForKey(r.key, lat);
          const present = value != null && Number.isFinite(value);
          return (
            <div key={r.key} className="flex items-center justify-between gap-sm py-xs">
              <div className="flex items-center gap-xs">
                <Icon name={r.icon} size="xs" className={`text-outline ${r.color}`} />
                <span className={r.color}>{r.label}</span>
              </div>
              <span className={`text-right font-mono-data ${present ? r.color : 'text-outline opacity-50'}`}>
                {present ? fmtMs(value) : '—'}
              </span>
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-xs pt-sm border-t border-white/5 font-mono-data text-mono-data">
        <Icon name="timer" size="xs" className="text-outline" />
        <span className="text-outline">RAG Pipeline: {fmtMs(lat?.rag_pipeline_ms)} • Total: {fmtMs(lat?.total_ms)} end-to-end</span>
      </div>
    </Surface>
  );
}

function valueForKey(key: string, lat: PipelineLatencyBreakdown | undefined): number | undefined {
  if (!lat) return undefined;
  if (key === 'stt') return lat.stt_ms ?? undefined;
  if (key === 'retrieval') return lat.retrieval_ms ?? undefined;
  if (key === 'generation') return lat.generation_ms ?? undefined;
  if (key === 'guardrails') return lat.guardrail_ms ?? undefined;
  if (key === 'total') return lat.total_ms ?? undefined;
  return undefined;
}
