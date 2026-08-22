import type { ComponentProps } from 'react';

export type StatusPillVariant = 'cyan' | 'magenta' | 'amber' | 'red' | 'outline';

const variants: Record<StatusPillVariant, string> = {
  cyan: 'text-on-tertiary bg-tertiary shadow-[0_0_10px_-2px_rgba(76,215,246,0.4)]',
  magenta: 'text-on-secondary bg-secondary shadow-[0_0_10px_-2px_rgba(208,188,255,0.4)]',
  amber: 'text-on-background bg-orange-400/60 shadow-[0_0_10px_-2px_rgba(251,146,60,0.4)]',
  red: 'text-on-error bg-error shadow-[0_0_10px_-2px_rgba(255,180,171,0.4)]',
  outline: 'text-outline border border-white/10',
};

const dotVariants: Record<StatusPillVariant, string> = {
  cyan: 'bg-tertiary',
  magenta: 'bg-secondary',
  amber: 'bg-orange-400',
  red: 'bg-error',
  outline: 'bg-outline',
};

export interface StatusPillProps extends ComponentProps<'span'> {
  label: string;
  variant?: StatusPillVariant;
  dot?: boolean;
  animate?: boolean;
}

export function StatusPill({ label, variant = 'outline', dot = true, animate = false, className, ...rest }: StatusPillProps) {
  return (
    <span
      className={`inline-flex items-center gap-xs px-md py-[3px] rounded-full font-mono-label text-mono-label uppercase tracking-widest ${variants[variant]} ${className ?? ''}`}
      {...rest}
    >
      {dot && (
        <span
          className={`block w-2 h-2 rounded-full ${dotVariants[variant]} ${animate ? 'animate-ping' : ''}`}
          aria-hidden="true"
        />
      )}
      {label}
    </span>
  );
}
