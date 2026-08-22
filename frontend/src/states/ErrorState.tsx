import { Icon } from '../components/ui/Icon';
import { Surface } from '../components/ui/Surface';
import type { AppError } from '../types';

export interface ErrorStateProps {
  error: AppError;
  backend: 'checking' | 'connected' | 'disconnected';
  onRetry: () => void;
  onReset: () => void;
}

interface Config {
  icon: string;
  title: string;
  color: 'tertiary' | 'error' | 'outline' | 'amber';
  glowBorder: string;
  iconBg: string;
}

const configs: Record<string, Config> = {
  ENDPOINT_NOT_IMPLEMENTED: {
    icon: 'warning',
    title: 'Endpoint Unavailable',
    color: 'amber',
    glowBorder: 'border-amber-300/40',
    iconBg: 'bg-orange-400/10 border-amber-300/30',
  },
  NETWORK_ERROR: {
    icon: 'cloud_off',
    title: 'Backend Disconnected',
    color: 'error',
    glowBorder: 'border-error-container/30',
    iconBg: 'bg-error-container/5 border-error-container/20',
  },
  SERVER_ERROR: {
    icon: 'error',
    title: 'Server Error',
    color: 'error',
    glowBorder: 'border-error-container/30',
    iconBg: 'bg-error-container/5 border-error-container/20',
  },
  MICROPHONE_ERROR: {
    icon: 'mic_off',
    title: 'Microphone Unavailable',
    color: 'amber',
    glowBorder: 'border-amber-300/40',
    iconBg: 'bg-orange-400/10 border-amber-300/30',
  },
};

export function ErrorState({ error, backend, onRetry, onReset }: ErrorStateProps) {
  const cfg = configs[error.code ?? ''] ?? {
    icon: 'report',
    title: 'Something Went Wrong',
    color: 'outline' as const,
    glowBorder: 'border-white/5',
    iconBg: 'bg-surface-container-low/50 border-white/10',
  };
  const colorMap = { tertiary: 'text-tertiary', error: 'text-error', amber: 'text-orange-400', outline: 'text-outline' };
  const iconColor = colorMap[cfg.color];
  const showRetry = error.retryable !== false;

  return (
    <div className="flex-1 flex flex-col items-center justify-center pt-16 pb-10 px-gutter w-full max-w-[1200px] mx-auto relative z-10">
      <div className="max-w-2xl w-full">
        <Surface className={`border ${cfg.glowBorder} rounded flex flex-col items-center text-center p-lg gap-md`}>
          <div className={`w-16 h-16 rounded flex items-center justify-center border ${cfg.iconBg}`}>
            <Icon name={cfg.icon} size="xxxl" className={iconColor} />
          </div>
          <h2 className={`font-headline-md text-headline-md ${iconColor}`}>{cfg.title}</h2>
          <p className="font-body-md text-body-md text-on-surface-variant text-balance">{error.message}</p>
          <div className="flex items-center gap-md pt-sm">
            {showRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="flex items-center gap-2 px-6 py-3 rounded border border-tertiary/30 bg-tertiary/10 hover:bg-tertiary/20 font-mono-label text-mono-label text-tertiary transition-colors"
                aria-label="Retry"
              >
                <Icon name="refresh" size="sm" className="text-tertiary" />
                Retry
              </button>
            )}
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
          <div className="font-mono-data text-mono-data text-outline-variant text-[11px] pt-sm border-t border-white/5 w-full">
            Backend: {backend === 'connected' ? 'ONLINE' : backend === 'checking' ? 'CHECKING' : 'OFFLINE'}
          </div>
        </Surface>
      </div>
    </div>
  );
}
