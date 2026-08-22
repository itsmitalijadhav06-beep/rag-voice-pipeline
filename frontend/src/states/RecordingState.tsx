import { MicButton } from '../components/voice/MicButton';
import type { VoiceRecorderHandle } from '../hooks/useVoiceRecorder';

export interface RecordingStateProps {
  recorder: VoiceRecorderHandle;
  onCancel: () => void;
}

export function RecordingState({ recorder, onCancel }: RecordingStateProps) {
  const { isRecording, durationMs, amplitudeSamples, latestAmplitude } = recorder;
  return (
    <div className="flex-grow flex flex-col items-center justify-center pt-16 pb-10 px-gutter w-full max-w-[1200px] mx-auto relative z-10">
      <div className="flex flex-col items-center justify-center space-y-8 w-full max-w-3xl">
        <div className="text-center space-y-2">
          <h1 className="font-display-lg text-display-lg text-on-surface">Listening</h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-md mx-auto">
            Speak clearly. Press done when finished, or let the recorder stop automatically.
          </p>
        </div>
        <MicButton phase="recording" onClick={recorder.stop} disabled={!isRecording} samples={amplitudeSamples} />
        <div className="flex flex-col items-center gap-2 text-tertiary font-mono-data text-mono-data">
          <div className="flex items-center gap-xs">
            <span className="w-2 h-2 rounded-full bg-error animate-pulse" aria-hidden="true" />
            <span>{formatDuration(durationMs)}</span>
          </div>
          <div className="flex items-center gap-xs">
            <span className="w-2 h-2 rounded-full bg-tertiary" style={{ opacity: Math.max(0.3, latestAmplitude) }} aria-hidden="true" />
            <span>{`Amplitude ${Math.round(latestAmplitude * 100)}%`}</span>
          </div>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="flex items-center gap-2 px-6 py-3 rounded border border-white/10 bg-surface-container-low/30 hover:bg-surface-container-low hover:border-outline transition-colors font-mono-label text-mono-label text-on-surface-variant"
          aria-label="Cancel recording"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function formatDuration(ms: number): string {
  const total = Math.floor(ms / 1000);
  const s = (total % 60).toString().padStart(2, '0');
  const m = Math.floor(total / 60)
    .toString()
    .padStart(2, '0');
  return `${m}:${s}`;
}