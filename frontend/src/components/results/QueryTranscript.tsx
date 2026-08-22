import { Icon } from '../ui/Icon';

export interface QueryTranscriptProps {
  transcript: string;
  sttLatencyMs?: number | null;
}

export function QueryTranscript({ transcript, sttLatencyMs }: QueryTranscriptProps) {
  const latency = sttLatencyMs != null && Number.isFinite(sttLatencyMs) ? `${Math.round(sttLatencyMs)}ms` : '--';
  return (
    <div className="bg-[rgba(30,41,59,0.5)] backdrop-blur-xl border border-white/5 p-md rounded flex flex-col gap-sm">
      <div className="flex items-center justify-between">
        <span className="font-mono-label text-mono-label text-outline uppercase tracking-wider">Query / Transcript</span>
        <div className="flex items-center gap-base">
          <Icon name="mic" size="sm" className="text-outline" />
          <span className="font-mono-data text-mono-data text-outline">STT: {latency}</span>
        </div>
      </div>
      {transcript ? (
        <p className="font-headline-md text-headline-md text-on-surface italic opacity-90 border-l-2 border-tertiary/50 pl-md py-xs">
          {`"${transcript}"`}
        </p>
      ) : (
        <span className="font-body-md text-on-surface-variant opacity-60">No transcript available</span>
      )}
    </div>
  );
}
