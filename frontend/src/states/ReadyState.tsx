import { Icon } from '../components/ui/Icon';
import { MicButton } from '../components/voice/MicButton';
import { Pipeline } from '../components/pipeline/Pipeline';
import type { HealthStatus } from '../types';

export interface ReadyStateProps {
  onMicPress: () => void;
  onUpload: () => void;
  backend: 'checking' | 'connected' | 'disconnected';
  health: HealthStatus | null;
}

export function ReadyState({ onMicPress, onUpload, backend }: ReadyStateProps) {
  const disabled = backend !== 'connected';
  return (
    <div className="flex-grow flex flex-col items-center justify-center pt-16 pb-10 px-gutter w-full max-w-[1200px] mx-auto relative z-10">
      <div className="flex flex-col items-center justify-center space-y-10 w-full max-w-3xl">
        <div className="text-center space-y-4">
          <h1 className="font-display-lg text-display-lg text-on-surface">Ask with your voice</h1>
          <p className="font-body-lg text-body-lg text-outline max-w-md mx-auto">
            Speak naturally and the pipeline will retrieve the most relevant context.
          </p>
        </div>
        <MicButton phase="idle" onClick={onMicPress} disabled={disabled} />
        <button
          type="button"
          onClick={onUpload}
          disabled={backend !== 'connected'}
          className="flex items-center gap-2 px-6 py-3 rounded border border-white/5 bg-surface-container-low/50 hover:bg-surface-container-low hover:border-tertiary/30 transition-all duration-300 group disabled:opacity-40"
          aria-label="Upload an audio file"
        >
          <Icon name="upload_file" size="sm" className="text-outline group-hover:text-tertiary transition-colors" />
          <span className="font-mono-label text-mono-label text-outline group-hover:text-on-surface transition-colors">Upload audio</span>
        </button>
        <Pipeline mode="idle" />
      </div>
    </div>
  );
}
