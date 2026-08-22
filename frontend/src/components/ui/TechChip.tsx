import type { ComponentProps } from 'react';
import { Icon } from './Icon';

export type ChipVariant = 'neutral' | 'cyan' | 'magenta' | 'amber' | 'red';

const variants: Record<ChipVariant, string> = {
  neutral: 'text-outline-variant border-white/10 bg-surface-container',
  cyan: 'text-tertiary border-tertiary/30 bg-tertiary/10',
  magenta: 'text-secondary border-secondary/30 bg-secondary/10',
  amber: 'text-orange-400 border-orange-400/30 bg-orange-400/10',
  red: 'text-error border-error/30 bg-error-container/30',
};

export interface TechChipProps extends ComponentProps<'span'> {
  label: string;
  variant?: ChipVariant;
  active?: boolean;
  icon?: string;
}

export function TechChip({ label, variant = 'neutral', active = false, icon, className, ...rest }: TechChipProps) {
  const flicker = active ? 'after:animate-pulse after:opacity-60' : '';
  return (
    <span
      className={`inline-flex items-center gap-xs px-xs py-[3px] rounded-none font-mono-label text-mono-label text-[11px] border ${variants[variant]} ${flicker} ${className ?? ''}`}
      {...rest}
    >
      <span
        className={`w-1.5 h-1.5 rounded-none bg-current ${active ? 'animate-pulse' : ''}`}
        aria-hidden="true"
      />
      {icon && <Icon name={icon} filled size="xs" />}
      {label}
    </span>
  );
}
