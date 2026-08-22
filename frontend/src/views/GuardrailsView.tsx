import { Surface } from '../components/ui/Surface';
import { Icon } from '../components/ui/Icon';
import type { HealthStatus } from '../types';

interface GuardrailsViewProps {
  health: HealthStatus | null;
}

interface CheckItem {
  label: string;
  icon: string;
  description: string;
}

const checks: CheckItem[] = [
  { label: 'Grounded', icon: 'verified', description: 'Answer supported by retrieved context' },
  { label: 'Unsafe', icon: 'shield', description: 'Block harmful or sensitive requests' },
  { label: 'Off-topic', icon: 'filter_alt', description: 'Detect queries outside knowledge domain' },
  { label: 'Refusal', icon: 'search_off', description: 'Refuse when evidence is insufficient' },
];

export function GuardrailsView({ health }: GuardrailsViewProps) {
  return (
    <div className="flex-1 flex flex-col pt-16 pb-10 md:pl-64 w-full">
      <div className="max-w-[1200px] mx-auto p-gutter lg:p-lg grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        <div className="xl:col-span-8 flex flex-col gap-gutter">
          <div className="flex items-center justify-between">
            <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Guardrails</span>
            <span className="font-mono-data text-mono-data text-outline">
              {health ? 'Configured' : '—'}
            </span>
          </div>
          <Surface className="p-lg rounded flex flex-col items-center justify-center text-center gap-md border border-white/5 min-h-[200px]">
            <div className="w-12 h-12 rounded border border-white/10 bg-surface-container-high flex items-center justify-center">
              <Icon name="shield_lock" size="lg" className="text-outline" />
            </div>
            <div className="flex flex-col gap-sm">
              <span className="font-headline-sm text-headline-sm text-on-surface">Awaiting Query</span>
              <span className="font-body-md text-body-md text-on-surface-variant max-w-sm">
                Execute a voice query to evaluate groundedness, safety, and relevance guardrails.
              </span>
            </div>
          </Surface>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
            {checks.map((c) => (
              <Surface key={c.label} className="p-md rounded flex items-start gap-sm border border-white/5">
                <div className="mt-0.5">
                  <Icon name={c.icon} size="sm" className="text-outline" />
                </div>
                <div className="flex flex-col gap-xs">
                  <span className="font-mono-label text-mono-label text-on-surface uppercase tracking-wider">{c.label}</span>
                  <span className="font-body-md text-body-md text-on-surface-variant">{c.description}</span>
                </div>
              </Surface>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
