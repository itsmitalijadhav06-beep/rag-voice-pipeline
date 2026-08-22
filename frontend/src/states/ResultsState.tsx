import { QueryTranscript } from '../components/results/QueryTranscript';
import { AnswerCard } from '../components/results/AnswerCard';
import { EvidenceList } from '../components/results/EvidenceList';
import { TelemetryGrid } from '../components/results/TelemetryGrid';
import { Pipeline } from '../components/pipeline/Pipeline';
import { Icon } from '../components/ui/Icon';
import type { QueryResponse } from '../types';

interface StageDef {
  key: string;
  label: string;
  icon: string;
  state: 'idle' | 'done' | 'active' | 'pending' | 'halt' | 'error';
}

export interface ResultsStateProps {
  response: QueryResponse;
  sttLatencyMs: number | null;
  retrievalLatencyMs: number | null;
  onReset: () => void;
  onNewQuery: () => void;
}

export function ResultsState({ response, sttLatencyMs, retrievalLatencyMs, onReset, onNewQuery }: ResultsStateProps) {
  const resultStages: StageDef[] = [
    { key: 'voice', label: 'VOICE', icon: 'mic', state: 'done' },
    { key: 'stt', label: 'STT', icon: 'notes', state: 'done' },
    { key: 'retrieval', label: 'RETRIEVAL', icon: 'search', state: 'done' },
    { key: 'answer', label: 'ANSWER', icon: 'forum', state: 'active' },
  ];
  return (
    <div className="flex-1 flex flex-col pt-16 pb-10 md:pl-64 w-full">
      <div className="max-w-[1200px] mx-auto p-gutter lg:p-lg grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        <div className="xl:col-span-8 flex flex-col gap-gutter">
          <QueryTranscript transcript={response.transcript || ''} sttLatencyMs={sttLatencyMs} />
          <AnswerCard response={response} variant={response.grounded ? 'grounded' : 'not-grounded'} />
          <div className="panel-level-1 p-md rounded flex flex-col gap-md border border-white/5">
            <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Processing Pipeline</span>
            <Pipeline mode="results" stages={resultStages} />
          </div>
          <TelemetryGrid response={response} />
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
        </div>
        <div className="xl:col-span-4">
          <EvidenceList response={response} retrievalLatencyMs={retrievalLatencyMs} />
        </div>
      </div>
    </div>
  );
}
