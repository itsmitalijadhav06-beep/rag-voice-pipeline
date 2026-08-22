import { Icon } from '../components/ui/Icon';
import { Surface } from '../components/ui/Surface';
import type { QueryResponse } from '../types';

export type RefusalKind = 'refused' | 'unsafe';

export interface RefusalStateProps {
  response: QueryResponse;
  kind: RefusalKind;
  onReset: () => void;
  onNewQuery: () => void;
}

export function RefusalState({ response, kind, onReset, onNewQuery }: RefusalStateProps) {
  const status = (response.status || '').toUpperCase();
  const title = status === 'UNSAFE' ? 'Blocked' : 'Refused';
  const message = response.answer || (status === 'UNSAFE' ? 'Request blocked by safety guardrails.' : 'Insufficient evidence to provide a grounded answer.');
  const iconName = status === 'UNSAFE' ? 'block' : 'search_off';

  return (
    <div className="flex-1 flex flex-col pt-16 pb-20 px-gutter bg-grid max-w-[1440px] mx-auto w-full min-h-screen">
      <header className="mb-lg">
        <div className="font-mono-label text-mono-label text-outline-variant mb-base uppercase">Intercepted Query</div>
        <h1 className="font-headline-md text-headline-md text-on-surface max-w-3xl border-l-2 border-surface-variant pl-sm">
          {`"${response.transcript || ''}"`}
        </h1>
      </header>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-lg relative z-10">
        <section
          className={`border ${kind === 'unsafe' ? 'border-error-container/30 bg-error-container/5' : 'border-white/5 bg-surface-container-low/50'} backdrop-blur-xl rounded flex flex-col relative overflow-hidden`}
        >
          <div
            className={kind === 'unsafe' ? 'absolute inset-0 glow-red pointer-events-none' : 'absolute inset-0 glow-amber pointer-events-none'}
            aria-hidden="true"
          />
          <div
            className={`p-md border-b ${kind === 'unsafe' ? 'border-error-container/20 bg-error-container/5' : 'border-white/5 bg-surface-container/30'} flex justify-between items-center`}
          >
            <div className="flex items-center gap-sm">
              <span className={`w-2 h-2 rounded-full ${kind === 'unsafe' ? 'bg-error animate-pulse' : 'bg-outline'}`} aria-hidden="true" />
              <span className={`font-mono-label text-mono-label ${kind === 'unsafe' ? 'text-error' : 'text-outline'} tracking-widest uppercase`}>Response State</span>
            </div>
            <div
              className={`px-sm py-base flex items-center gap-xs border ${kind === 'unsafe' ? 'bg-error-container/20 border-error/20 text-error' : 'bg-surface border-white/10 text-outline'}`}
            >
              <Icon name={kind === 'unsafe' ? 'gavel' : 'info'} size="sm" className={kind === 'unsafe' ? 'text-error' : 'text-outline'} />
              <span className="font-mono-label text-mono-label uppercase tracking-wider">{title}</span>
            </div>
          </div>
          <div className="p-md flex-1 flex flex-col justify-center items-center text-center min-h-[200px]">
            <Icon name={iconName} size="xxxl" className={kind === 'unsafe' ? 'text-error/70' : 'text-outline-variant'} />
            <h2 className={`font-headline-sm text-headline-sm uppercase tracking-widest mt-sm ${kind === 'unsafe' ? 'text-error' : 'text-on-surface'}`}>
              {title}
            </h2>
            <p className={`font-mono-data text-mono-data max-w-sm mt-xs ${kind === 'unsafe' ? 'text-error/80' : 'text-on-surface-variant'}`}>{message}</p>
          </div>
          <div className="p-md border-t border-white/5 bg-surface-container-lowest/50">
            <span className="font-mono-label text-mono-label text-outline-variant uppercase mb-sm">Pipeline Trace</span>
            <div className="flex items-center justify-between gap-2 text-center font-mono-data text-mono-data text-[10px]">
              <div className="flex flex-col items-center gap-1 opacity-50">
                <Icon name="graphic_eq" size="xs" />
                <span>STT</span>
              </div>
              <div className="flex-1 h-px bg-white/5" />
              <div className="flex flex-col items-center gap-1 opacity-50">
                <Icon name="database" size="xs" />
                <span>RAG</span>
              </div>
              <div className={`flex-1 h-px ${kind === 'unsafe' ? 'bg-error/20' : 'bg-white/5'}`} />
              <div className={`flex flex-col items-center gap-1 px-2 py-1 border ${kind === 'unsafe' ? 'text-error bg-error-container/20 border-error/30' : 'text-on-surface bg-surface border-white/10'}`}>
                <Icon name={kind === 'unsafe' ? 'shield_lock' : 'search_off'} size="xs" className={kind === 'unsafe' ? 'text-error' : 'text-outline'} />
                <span className={kind === 'unsafe' ? 'text-error' : 'text-outline'}>{kind === 'unsafe' ? 'GUARDRAILS' : 'HALT'}</span>
              </div>
            </div>
          </div>
        </section>
        <Surface className="rounded flex flex-col gap-gutter p-md border border-white/5">
          <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Retrieved Evidence</span>
          <div className="font-body-md text-body-md text-on-surface-variant opacity-70">
            {response.retrieved_chunks && response.retrieved_chunks.length > 0
              ? `${response.retrieved_chunks.length} chunk(s) retrieved but could not support a grounded response.`
              : 'No sufficient context retrieved to support an answer.'}
          </div>
          <div className="flex items-center gap-md">
            <button
              type="button"
              onClick={onNewQuery}
              className="flex items-center gap-2 px-6 py-3 rounded border border-tertiary/30 bg-tertiary/10 hover:bg-tertiary/20 font-mono-label text-mono-label text-tertiary transition-colors"
              aria-label="Ask a new question"
            >
              <Icon name="mic" filled size="sm" className="text-tertiary" />
              New query
            </button>
            <button
              type="button"
              onClick={onReset}
              className="flex items-center gap-2 px-6 py-3 rounded border border-white/10 bg-surface-container-low/30 hover:bg-surface-container-low font-mono-label text-mono-label text-on-surface-variant transition-colors"
              aria-label="Reset session"
            >
              <Icon name="restart_alt" size="sm" className="text-outline" />
              Reset
            </button>
          </div>
        </Surface>
      </div>
    </div>
  );
}
