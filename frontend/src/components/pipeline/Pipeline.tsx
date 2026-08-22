import { Icon } from '../ui/Icon';

export type PipelineMode = 'idle' | 'processing' | 'results';

interface StageDef {
  key: string;
  label: string;
  icon: string;
  state: 'idle' | 'done' | 'active' | 'pending' | 'halt' | 'error';
  sub?: string;
  meta?: string;
}

const neutralStages: StageDef[] = [
  { key: 'voice', label: 'VOICE', icon: 'record_voice_over', state: 'idle' },
  { key: 'stt', label: 'STT', icon: 'subtitles', state: 'idle' },
  { key: 'retrieval', label: 'RETRIEVAL', icon: 'database', state: 'idle' },
  { key: 'generation', label: 'GENERATION', icon: 'memory', state: 'idle' },
  { key: 'guardrails', label: 'GUARDRAILS', icon: 'shield_lock', state: 'idle' },
  { key: 'answer', label: 'ANSWER', icon: 'forum', state: 'idle' },
];

export interface PipelineProps {
  mode?: PipelineMode;
  stages?: StageDef[];
  sttLatencyMs?: number | null;
  elapsedMs?: number;
}

export function Pipeline({ mode = 'idle', stages, sttLatencyMs, elapsedMs }: PipelineProps) {
  switch (mode) {
    case 'processing':
      return <PipelineProcessing stages={stages} sttLatencyMs={sttLatencyMs} elapsedMs={elapsedMs} />;
    case 'results':
      return <PipelineResults stages={stages} />;
    case 'idle':
    default:
      return <PipelineIdle stages={stages ?? neutralStages} />;
  }
}

function PipelineIdle({ stages }: { stages: StageDef[] }) {
  return (
    <div className="w-full mt-xl pt-lg border-t border-white/5">
      <div className="flex items-center justify-between w-full">
        {stages.map((s, idx) => (
          <div key={s.key}>
            <div className="pipeline-node flex flex-col items-center gap-xs text-outline">
              <div className="w-10 h-10 rounded-[4px] border border-white/5 bg-[rgba(30,41,59,0.3)] flex items-center justify-center backdrop-blur">
                <Icon name={s.icon} size="md" className="text-outline" />
              </div>
              <span className="font-mono-label text-mono-label text-outline">{s.label}</span>
            </div>
            {idx < stages.length - 1 && <div className="pipeline-line" />}
          </div>
        ))}
      </div>
    </div>
  );
}

const circleBase = 'w-8 h-8 rounded-full flex items-center justify-center border';

function PipelineResults({ stages }: { stages?: StageDef[] }) {
  const list = stages ?? neutralStages;
  return (
    <div className="w-full flex items-center justify-between relative py-sm px-md">
      <div className="absolute top-1/2 left-md right-md h-[1px] bg-white/5 -z-10 -translate-y-1/2" />
      <div className="absolute top-1/2 left-md right-md h-[1px] bg-tertiary/50 -z-10 -translate-y-1/2 shadow-[0_0_8px_rgba(76,215,246,0.5)]" />
      {list.map((s) => {
        const active = s.state === 'done' || s.state === 'active';
        const isAnswer = s.key === 'answer';
        const ring = active
          ? isAnswer
            ? 'shadow-[0_0_10px_rgba(173,198,255,0.6)] border-primary'
            : 'shadow-[0_0_10px_rgba(76,215,246,0.4)] border-tertiary'
          : 'border-white/5';
        const fill = active ? (isAnswer ? 'bg-primary/20' : 'bg-tertiary/20') : 'bg-[#05070A]';
        const iconColor = active ? (isAnswer ? 'text-primary' : 'text-tertiary') : 'text-on-surface-variant';
        const labelColor = active ? (isAnswer ? 'text-primary' : 'text-tertiary') : 'text-on-surface-variant';
        return (
          <div key={s.key} className="flex flex-col items-center gap-xs z-10">
            <div className={`${circleBase} ${ring} ${fill}`}>
              <Icon name={s.icon} size="xs" className={iconColor} />
            </div>
            <span className={`font-mono-label text-mono-label ${labelColor}`}>{s.label}</span>
          </div>
        );
      })}
    </div>
  );
}

interface PipelineProcessingProps {
  stages?: StageDef[];
  sttLatencyMs?: number | null;
  elapsedMs?: number;
}

function PipelineProcessing({ stages, sttLatencyMs }: PipelineProcessingProps) {
  const blocks = stages ?? [
    { key: 'stt', label: '01_STT', icon: 'check_circle', state: 'done', sub: 'Whisper-v3', meta: sttLatencyMs != null ? `Lat: ${Math.round(sttLatencyMs)}ms | Conf: 98%` : undefined },
    { key: 'retrieval', label: '02_RETRIEVAL', icon: 'sync', state: 'active', sub: 'Searching Vector DB', meta: 'Top-K: 5 | Dist: Cosine' },
    { key: 'synthesis', label: '03_SYNTHESIS', icon: 'pending', state: 'pending', sub: 'Awaiting Context', meta: 'Model: GPT-4-Turbo' },
  ];

  return (
    <div className="w-full flex gap-xs bg-surface-container-lowest/50 p-xs border border-white/5 rounded flex-col gap-md">
      <div className="flex gap-xs w-full">
        {blocks.map((b) => {
          const isActive = b.state === 'active';
          const isPending = b.state === 'pending';
          const isDone = b.state === 'done';
          const cls = isPending
            ? 'flex-1 bg-surface-container-low p-sm border border-white/5 opacity-60'
            : isDone
              ? 'flex-1 bg-surface-container p-sm border border-tertiary/30 relative overflow-hidden'
              : 'flex-1 bg-surface border border-tertiary relative overflow-hidden';
          const iconCls = isPending ? 'text-on-surface-variant' : isDone ? 'text-tertiary' : 'text-tertiary animate-spin';
          const labelCls = isPending ? 'text-on-surface-variant' : 'text-tertiary font-bold';
          const subCls = isPending ? 'text-on-surface-variant' : 'text-on-surface';
          const metaCls = 'text-tertiary';
          return (
            <div key={b.key} className={cls}>
              {isActive && <div className="absolute top-0 left-0 w-full h-[2px] bg-tertiary/50 animate-scanlineFast" />}
              {isDone && <div className="absolute inset-0 bg-tertiary/5 opacity-50" />}
              <div className={`flex justify-between items-start mb-sm ${isDone ? 'relative z-10' : ''}`}>
                <span className={`font-mono-label text-mono-label ${labelCls}`}>{b.label}</span>
                <Icon name={b.icon} size="sm" className={iconCls} />
              </div>
              <div className={`flex items-center gap-1 font-mono-data text-mono-data ${isDone ? 'relative z-10' : ''}`}>
                {isActive && <span className="w-1 h-3 bg-tertiary animate-pulse" />}
                <span className={subCls}>{b.sub}</span>
              </div>
              {b.meta && (
                <div className={`font-mono-data text-mono-data ${metaCls} text-[10px] ${isDone ? 'relative z-10' : ''}`}>{b.meta}</div>
              )}
            </div>
          );
        })}
      </div>
      <div className="w-full border border-white/5 bg-surface-container-lowest/80 backdrop-blur p-sm h-32 overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-surface-container-lowest z-10 pointer-events-none" />
        <div className="font-mono-data text-mono-data text-on-surface-variant/50 text-[11px] leading-relaxed break-all relative z-20">
          <span className="text-tertiary/70">&gt; processing pipeline: VOICE -&gt; STT -&gt; RETRIEVAL -&gt; GENERATION -&gt; GUARDRAILS -&gt; ANSWER</span>
          <br />
          <span className="text-tertiary/70">&gt; awaiting backend response (POST /query)</span>
          <br />
          <span className="text-tertiary/70">&gt; payload encoded | codec: opus</span>
          <br />
          <span className="text-tertiary/70">&gt; vector search queued</span>
        </div>
      </div>
    </div>
  );
}
