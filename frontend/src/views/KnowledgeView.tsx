import { Surface } from '../components/ui/Surface';
import { Icon } from '../components/ui/Icon';
import type { HealthStatus, ContextChunk } from '../types';

interface KnowledgeViewProps {
  health: HealthStatus | null;
  chunks?: ContextChunk[];
}

export function KnowledgeView({ health, chunks }: KnowledgeViewProps) {
  return (
    <div className="flex-1 flex flex-col pt-16 pb-10 md:pl-64 w-full">
      <div className="max-w-[1200px] mx-auto p-gutter lg:p-lg grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        <div className="xl:col-span-8 flex flex-col gap-gutter">
          <div className="flex items-center justify-between">
            <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Knowledge Base</span>
            <span className="font-mono-data text-mono-data text-outline">
              {health?.vector_db_type || '—'}
            </span>
          </div>
          {!chunks || chunks.length === 0 ? (
            <Surface className="p-lg rounded flex flex-col items-center justify-center text-center gap-md border border-white/5 min-h-[240px]">
              <div className="w-12 h-12 rounded border border-white/10 bg-surface-container-high flex items-center justify-center">
                <Icon name="database" size="lg" className="text-outline" />
              </div>
              <div className="flex flex-col gap-sm">
                <span className="font-headline-sm text-headline-sm text-on-surface">No Retrieved Context</span>
                <span className="font-body-md text-body-md text-on-surface-variant max-w-sm">
                  Execute a voice query to retrieve relevant context chunks from the vector store.
                </span>
              </div>
            </Surface>
          ) : (
            <div className="flex flex-col gap-md">
              {chunks.map((c) => (
                <Surface key={c.chunk_id} className="p-md rounded flex flex-col gap-sm border border-white/10 hover:border-tertiary/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-xs">
                      <Icon name="description" size="xs" className="text-outline" />
                      <span className="font-mono-data text-mono-data text-outline">{c.chunk_id}</span>
                    </div>
                    <div className="px-xs py-[2px] border border-tertiary/30 bg-tertiary/10 font-mono-data text-mono-data text-tertiary">
                      {Number.isFinite(c.score) ? `RELEVANCE: ${c.score.toFixed(2)}` : 'RELEVANCE: —'}
                    </div>
                  </div>
                  <div className="font-body-md text-body-md text-on-surface-variant line-clamp-3">{c.text}</div>
                  <div className="flex items-center gap-md font-mono-data text-mono-data text-outline text-[11px]">
                    {c.strategy_used && <span>STRATEGY: {c.strategy_used}</span>}
                  </div>
                </Surface>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
