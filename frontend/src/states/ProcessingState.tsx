import { useEffect, useState } from 'react';
import { Waveform } from '../components/voice/Waveform';
import { Pipeline } from '../components/pipeline/Pipeline';
import { Icon } from '../components/ui/Icon';

export interface ProcessingStateProps {
  startedAt: number;
  recordedSamples?: number[];
  onCancel: () => void;
  sttLatencyMs?: number | null;
}

export function ProcessingState({ startedAt, recordedSamples, onCancel, sttLatencyMs }: ProcessingStateProps) {
  const [elapsed, setElapsed] = useState(() => Date.now() - startedAt);
  useEffect(() => {
    const id = setInterval(() => setElapsed(Date.now() - startedAt), 250);
    return () => clearInterval(id);
  }, [startedAt]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center pt-24 pb-20 px-gutter max-w-[1440px] mx-auto w-full">
      <div className="relative z-10 w-full max-w-4xl px-gutter flex flex-col items-center gap-gutter">
        <div className="flex flex-col items-center mb-xl">
          <div className="relative w-32 h-32 rounded-full border border-tertiary/50 bg-surface-container/80 backdrop-blur-xl flex items-center justify-center mb-md active-node">
            <span className="absolute" style={{ fontSize: '48px' }} aria-hidden="true">
              <Icon name="mic" size="xxxl" filled className="text-tertiary/20" />
            </span>
            <div className="flex items-center justify-center z-10">
              <Waveform samples={recordedSamples} maxBars={10} />
            </div>
          </div>
          <div className="flex items-center gap-xs">
            <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" aria-hidden="true" />
            <span className="font-mono-data text-mono-data text-tertiary uppercase tracking-wider">
              Processing… {Math.round(elapsed / 1000)}s
            </span>
          </div>
        </div>
        <div className="w-full">
          <Pipeline mode="processing" sttLatencyMs={sttLatencyMs} elapsedMs={elapsed} />
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="mt-md flex items-center gap-2 px-6 py-3 rounded border border-white/10 bg-surface-container-low/30 hover:bg-surface-container-low hover:border-outline font-mono-label text-mono-label text-on-surface-variant transition-colors"
          aria-label="Cancel and start over"
        >
          <Icon name="close" size="sm" className="text-outline" />
          Cancel
        </button>
      </div>
    </div>
  );
}
