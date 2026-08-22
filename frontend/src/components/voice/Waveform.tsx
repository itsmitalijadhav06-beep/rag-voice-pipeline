import { useMemo } from 'react';

export interface WaveformProps {
  samples?: number[];
  idle?: boolean;
  bars?: number;
  maxBars?: number;
}

const delays = ['0s', '0.1s', '0.2s', '0.3s', '0.4s', '0.5s', '0.4s', '0.3s', '0.2s', '0.1s'];

export function Waveform({ samples, idle = false, bars = 10, maxBars = 10 }: WaveformProps) {
  const count = Math.min(bars, maxBars);
  const values = useMemo(() => {
    if (idle) return null;
    const arr: number[] = [];
    if (samples && samples.length > 0) {
      for (let i = 0; i < count; i++) {
        const idx = Math.min(samples.length - 1, Math.floor((i / count) * samples.length));
        arr.push(Math.max(0.05, samples[idx] ?? 0));
      }
    } else {
      for (let i = 0; i < count; i++) arr.push(0.05);
    }
    return arr;
  }, [samples, idle, count]);

  const baseClass = 'w-[4px] bg-tertiary rounded-[2px] transition-all';

  if (idle) {
    return (
      <div className="flex items-center justify-center gap-[3px] h-16">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={`${baseClass} animate-waveform`}
            style={{ animationDelay: delays[i % delays.length] }}
            aria-hidden="true"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-end justify-center gap-[3px] h-16" aria-label="Audio amplitude">
      {values!.map((v, i) => (
        <div
          key={i}
          className={baseClass}
          style={{ height: `${Math.round(v * 100)}%`, opacity: Math.max(0.5, v) }}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}
