import type { HealthStatus } from '../../types';
import { Icon } from '../ui/Icon';

export type NavVariant = 'idle' | 'processing' | 'results' | 'refusal';

export interface TopNavBarProps {
  variant: NavVariant;
  backend: 'checking' | 'connected' | 'disconnected';
  mockMode: boolean;
  health: HealthStatus | null;
  onRecordToggle?: () => void;
  recording?: boolean;
}

const systemLabel: Record<string, string> = {
  checking: 'SYSTEM CHECKING',
  connected: 'SYSTEM ONLINE',
  disconnected: 'SYSTEM OFFLINE',
};

export function TopNavBar({ variant, backend, mockMode, onRecordToggle, recording }: TopNavBarProps) {
  const dotColor =
    backend === 'connected'
      ? 'bg-tertiary animate-pulse'
      : backend === 'checking'
        ? 'bg-outline'
        : 'bg-error animate-pulse';
  const statusColor =
    backend === 'connected' ? 'text-tertiary' : backend === 'checking' ? 'text-outline' : 'text-error';
  const modeColor = mockMode ? 'text-tertiary' : 'text-outline';

  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-gutter h-16 bg-background/50 backdrop-blur-xl border-b border-white/5">
      <div className="font-headline-md text-headline-md font-bold tracking-tighter text-on-surface">VOICE RAG</div>
      <div className="flex items-center gap-xs">
        {variant === 'results' && (
          <>
            <span
              className="inline-flex items-center gap-xs px-md py-[3px] rounded-full font-mono-label text-mono-label uppercase tracking-widest text-on-tertiary bg-tertiary shadow-[0_0_10px_-2px_rgba(76,215,246,0.4)]"
              aria-label="System ready"
            >
              <span className="block w-2 h-2 rounded-full bg-tertiary animate-ping" aria-hidden="true" />
              READY
            </span>
            <button
              type="button"
              aria-label={recording ? 'Stop recording' : 'Start new query'}
              onClick={onRecordToggle}
              className="w-10 h-10 rounded-full bg-surface-container-low/50 border border-white/10 flex items-center justify-center hover:bg-white/5 focus-visible:text-tertiary transition-colors"
            >
              <Icon name="mic" filled size="lg" className={recording ? 'text-tertiary' : 'text-on-surface-variant'} />
            </button>
          </>
        )}
        <span className={`font-mono-data text-mono-data ${statusColor} cursor-default`}>
          <span className={`inline-block w-2 h-2 rounded-full mr-xs ${dotColor}`} aria-hidden="true" />
          {systemLabel[backend]}
        </span>
        <span className={`font-mono-label text-mono-label ${modeColor} hover:text-primary transition-colors cursor-default`} aria-label={mockMode ? 'Mock mode active' : 'Live mode'}>
          {mockMode ? 'MOCK MODE' : 'LIVE'}
        </span>
      </div>
    </nav>
  );
}
