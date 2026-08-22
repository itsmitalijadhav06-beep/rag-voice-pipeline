import { Icon } from '../ui/Icon';
import { Surface } from '../ui/Surface';
import type { ContextChunk, QueryResponse } from '../../types';

export interface EvidenceListProps {
  response: QueryResponse;
  retrievalLatencyMs?: number | null;
}

export function EvidenceList({ response, retrievalLatencyMs }: EvidenceListProps) {
  const chunks = response.retrieved_chunks ?? [];
  const latency = retrievalLatencyMs != null && Number.isFinite(retrievalLatencyMs) ? `${Math.round(retrievalLatencyMs)}ms` : '--';

  return (
    <Surface className="flex flex-col h-full border border-white/5">
      <div className="p-md border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-sm">
          <Icon name="database" size="sm" className="text-tertiary" />
          <span className="font-mono-label text-mono-label text-on-surface uppercase tracking-wider">
            Retrieved Context
          </span>
        </div>
        <span className="font-mono-data text-mono-data text-outline">RET: {latency}</span>
      </div>
      <div className="p-md flex flex-col gap-md flex-1 overflow-y-auto">
        {chunks.length === 0 ? (
          <span className="font-body-md text-on-surface-variant opacity-60">No retrieved evidence available.</span>
        ) : (
          chunks.map((c) => <EvidenceChunk key={c.chunk_id} chunk={c} />)
        )}
      </div>
    </Surface>
  );
}

export function EvidenceChunk({ chunk }: { chunk: ContextChunk }) {
  const score = Number.isFinite(chunk.score) ? chunk.score : 0;
  const label = chunkLabel(chunk);
  const metaLine = metaLineOf(chunk);
  return (
    <Surface className="border border-white/10 rounded-none bg-[#05070A]/50 p-sm flex flex-col gap-sm hover:border-tertiary/50 transition-colors group">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-xs">
          <Icon name="description" size="xs" className="text-outline" />
          <span className="font-mono-data text-mono-data text-outline">{label}</span>
        </div>
        <div className="px-xs py-[2px] border border-tertiary/30 bg-tertiary/10 font-mono-data text-mono-data text-tertiary">
          RELEVANCE: {score.toFixed(2)}
        </div>
      </div>
      <RelevanceBar score={score} />
      <div className="font-body-md text-body-md text-on-surface-variant line-clamp-3">{chunk.text}</div>
      {metaLine && <div className="font-mono-data text-mono-data text-on-surface-variant text-[10px] opacity-70">{metaLine}</div>}
    </Surface>
  );
}

function RelevanceBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(1, score));
  const color = pct >= 0.7 ? 'bg-tertiary' : pct >= 0.4 ? 'bg-amber-300/70' : 'bg-outline';
  return (
    <div className="w-full h-1 rounded-none bg-white/5 overflow-hidden" aria-label={`Relevance ${Math.round(pct * 100)}%`}>
      <div className={`h-full ${color} transition-all`} style={{ width: `${pct * 100}%` }} />
    </div>
  );
}

function chunkLabel(chunk: ContextChunk): string {
  const m = chunk.metadata || {};
  const source = m.source ?? m.doc_id ?? m.document_id ?? m.chunk_id ?? m.id;
  if (source) return String(source);
  if (chunk.chunk_id) return chunk.chunk_id;
  return 'UNKNOWN';
}

function metaLineOf(chunk: ContextChunk): string {
  const m = chunk.metadata || {};
  const parts: string[] = [];
  if (chunk.strategy_used) parts.push(`STRATEGY: ${chunk.strategy_used}`);
  if (m.page != null) parts.push(`PAGE: ${m.page}`);
  if (m.chunk_idx != null) parts.push(`IDX: ${m.chunk_idx}`);
  if (m.source) parts.push(`SRC: ${m.source}`);
  return parts.join(' | ');
}
