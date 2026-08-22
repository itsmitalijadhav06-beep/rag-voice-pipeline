import { Icon } from '../ui/Icon';
import { Waveform } from './Waveform';

export interface MicButtonProps {
  phase: 'idle' | 'recording';
  samples?: number[];
  onClick: () => void;
  disabled?: boolean;
  label?: string;
}

export function MicButton({ phase, samples, onClick, disabled, label }: MicButtonProps) {
  const labelText = label ?? (phase === 'recording' ? 'Listening…' : 'Ask with your voice');

  return (
    <div className="flex flex-col items-center gap-6">
      <button
        type="button"
        aria-label={phase === 'recording' ? 'Stop recording' : labelText}
        onClick={onClick}
        disabled={disabled}
        className="mic-btn-wrapper relative group outline-none focus:outline-none"
      >
        {phase === 'idle' && (
          <div
            className="absolute inset-[-4px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-0"
            aria-hidden="true"
          >
            <div className="w-full h-full rounded-full animate-rotateGlow bg-[conic-gradient(from_0deg,_transparent_0%,_rgba(76,215,246,0.3)_25%,_transparent_50%,_rgba(173,198,255,0.3)_75%,_transparent_100%)]" />
          </div>
        )}
        <div
          className={
            phase === 'idle'
              ? 'relative w-32 h-32 rounded-full bg-gradient-to-b from-primary-container to-background flex items-center justify-center border border-white/10 shadow-[0_0_40px_rgba(76,215,246,0.1)] group-hover:shadow-[0_0_60px_rgba(76,215,246,0.2)] transition-all duration-500 z-10'
              : 'relative w-32 h-32 rounded-full border border-tertiary/50 bg-surface-container/80 backdrop-blur-xl flex items-center justify-center transition-all duration-500 z-10'
          }
        >
          {phase === 'idle' && (
            <div className="w-24 h-24 rounded-full bg-surface-container-low flex items-center justify-center border border-white/5">
              <Icon
                name="mic"
                size="xxxl"
                filled
                className="text-[48px] text-tertiary transition-transform duration-300 group-hover:scale-110"
              />
            </div>
          )}
          {phase === 'recording' && (
            <>
              <span className="absolute" style={{ fontSize: '48px' }} aria-hidden="true">
                <Icon name="mic" size="xxxl" filled className="text-[48px] text-tertiary/20" />
              </span>
              <div className="flex items-center justify-center z-10">
                <Waveform samples={samples} maxBars={10} />
              </div>
            </>
          )}
        </div>
      </button>
      <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">
        {phase === 'recording' ? 'Listening…' : labelText}
      </span>
    </div>
  );
}
