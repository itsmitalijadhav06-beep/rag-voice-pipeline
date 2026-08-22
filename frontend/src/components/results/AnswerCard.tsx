import { Icon } from '../ui/Icon';
import { fmtMs } from '../../lib/utils';
import type { QueryResponse } from '../../types';

export interface AnswerCardProps {
  response: QueryResponse;
  variant?: 'grounded' | 'not-grounded' | 'refused' | 'unsafe';
}

const variantConfig: Record<NonNullable<AnswerCardProps['variant']>, { badge: string; badgeColor: string; icon: string; iconColor: string }> =
  {
    grounded: { badge: 'Grounded', badgeColor: 'text-tertiary', icon: 'verified', iconColor: 'text-tertiary' },
    'not-grounded': { badge: 'Not Grounded', badgeColor: 'text-amber-300', icon: 'warning', iconColor: 'text-amber-300' },
    refused: { badge: 'Refused', badgeColor: 'text-amber-300', icon: 'search_off', iconColor: 'text-amber-300' },
    unsafe: { badge: 'Blocked', badgeColor: 'text-error', icon: 'block', iconColor: 'text-error' },
  };

export function AnswerCard({ response, variant = 'grounded' }: AnswerCardProps) {
  const cfg = variantConfig[variant];
  const genMs = fmtMs(response.latency_breakdown_ms?.generation ?? response.rag_pipeline_latency_ms);
  const totalMs = fmtMs(response.total_latency_ms);
  const supportNote = variant === 'grounded' ? 'Answer supported by retrieved context' : reasonNote(response, variant);

  return (
    <div className="ai-response-glow active-glow panel-level-1 p-lg rounded flex flex-col gap-md border border-white/5">
      <div className="flex items-center justify-between border-b border-white/5 pb-sm">
        <div className="flex items-center gap-sm">
          <Icon name="auto_awesome" filled size="md" className="text-primary" />
          <span className="font-mono-label text-mono-label text-primary uppercase tracking-wider">Synthesized Answer</span>
        </div>
        <div className="inline-flex items-center gap-xs bg-tertiary/10 border border-tertiary/30 px-sm py-base rounded-none">
          <Icon name={cfg.icon} filled size="sm" className={cfg.iconColor} />
          <span className={`font-mono-label text-mono-label ${cfg.badgeColor} uppercase tracking-wider`}>{cfg.badge}</span>
          {supportNote && (
            <span className="font-mono-data text-mono-data text-outline -ml-xs hidden sm:inline">- {supportNote}</span>
          )}
        </div>
      </div>
      <div className={`font-body-lg text-body-lg text-on-surface leading-relaxed ${variant !== 'grounded' ? 'italic opacity-80' : ''}`}>
        {response.answer || <span className="opacity-50">—</span>}
      </div>
      <div className="flex items-center gap-gutter pt-sm mt-auto border-t border-white/5 font-mono-data text-mono-data text-outline">
        <div className="flex items-center gap-xs">
          <Icon name="psychology" size="sm" className="text-outline" />
          <span>GEN: {genMs}</span>
        </div>
        <div className="flex items-center gap-xs">
          <Icon name="speed" size="sm" className="text-outline" />
          <span>TOTAL: {totalMs}</span>
        </div>
      </div>
    </div>
  );
}

function reasonNote(response: QueryResponse, variant: NonNullable<AnswerCardProps['variant']>): string {
  const reason = response.guardrail_status?.reason;
  if (reason) return reason;
  switch (variant) {
    case 'not-grounded':
      return 'Answer not supported by retrieved context';
    case 'refused':
      return 'Insufficient evidence to provide a grounded answer';
    case 'unsafe':
      return 'Request blocked by safety guardrails';
    default:
      return '';
  }
}
