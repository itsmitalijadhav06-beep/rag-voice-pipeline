import type { HealthStatus, SectionKey } from '../../types';
import { Icon } from '../ui/Icon';

export interface SideNavBarProps {
  health: HealthStatus | null;
  active: SectionKey;
  onNavigate: (key: SectionKey) => void;
}

interface NavItem {
  key: SectionKey;
  label: string;
  icon: string;
  base: string;
  activeClass: string;
}

const items: NavItem[] = [
  {
    key: 'hub',
    label: 'Neural Hub',
    icon: 'graphic_eq',
    base: 'flex items-center gap-sm px-gutter py-sm text-on-surface-variant font-mono-label text-mono-label hover:bg-white/5 transition-colors cursor-pointer border-0 bg-transparent w-full text-left',
    activeClass: 'flex items-center gap-sm px-gutter py-sm text-primary border-r-2 border-primary bg-primary/5 font-mono-label text-mono-label cursor-pointer border-0 bg-transparent w-full text-left',
  },
  {
    key: 'knowledge',
    label: 'Knowledge',
    icon: 'database',
    base: 'flex items-center gap-sm px-gutter py-sm text-on-surface-variant font-mono-label text-mono-label hover:bg-white/5 transition-colors cursor-pointer border-0 bg-transparent w-full text-left',
    activeClass: 'flex items-center gap-sm px-gutter py-sm text-primary border-r-2 border-primary bg-primary/5 font-mono-label text-mono-label cursor-pointer border-0 bg-transparent w-full text-left',
  },
  {
    key: 'guardrails',
    label: 'Guardrails',
    icon: 'shield_lock',
    base: 'flex items-center gap-sm px-gutter py-sm text-on-surface-variant font-mono-label text-mono-label hover:bg-white/5 transition-colors cursor-pointer border-0 bg-transparent w-full text-left',
    activeClass: 'flex items-center gap-sm px-gutter py-sm text-primary border-r-2 border-primary bg-primary/5 font-mono-label text-mono-label cursor-pointer border-0 bg-transparent w-full text-left',
  },
  {
    key: 'latency',
    label: 'Latency',
    icon: 'query_stats',
    base: 'flex items-center gap-sm px-gutter py-sm text-on-surface-variant font-mono-label text-mono-label hover:bg-white/5 transition-colors cursor-pointer border-0 bg-transparent w-full text-left',
    activeClass: 'flex items-center gap-sm px-gutter py-sm text-primary border-r-2 border-primary bg-primary/5 font-mono-label text-mono-label cursor-pointer border-0 bg-transparent w-full text-left',
  },
];

export function SideNavBar({ health, active, onNavigate }: SideNavBarProps) {
  const providerLine = health ? `STT: ${health.stt_provider} | LLM: ${health.llm_provider}` : '—';
  return (
    <aside className="fixed left-0 top-16 h-[calc(100vh-64px)] z-40 hidden md:flex flex-col bg-surface-container-low/50 backdrop-blur-xl border-r border-white/5 w-64 transition-all duration-200">
      <div className="p-gutter border-b border-white/5 flex flex-col gap-sm">
        <div className="w-10 h-10 rounded bg-surface-container-high border border-white/10 flex items-center justify-center">
          <Icon name="terminal" size="md" className="text-outline" />
        </div>
        <div>
          <div className="font-headline-sm text-headline-sm text-primary">Core Engine</div>
          <div className="font-mono-data text-mono-data text-on-surface-variant text-[10px] break-all" aria-label="Configured STT and LLM providers">
            {providerLine}
          </div>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-sm">
        {items.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => onNavigate(item.key)}
            className={item.key === active ? item.activeClass : item.base}
          >
            <Icon name={item.icon} size="lg" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="p-gutter border-t border-white/5">
        <button
          type="button"
          className="w-full py-sm px-md border border-primary text-primary font-mono-label text-mono-label hover:bg-primary/10 transition-colors uppercase tracking-widest text-center"
          aria-label="Reset current session"
        >
          RESET SESSION
        </button>
      </div>
    </aside>
  );
}
