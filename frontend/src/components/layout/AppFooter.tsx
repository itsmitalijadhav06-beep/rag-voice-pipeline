import { fmtTelemetryValue, formatPercent } from '../../lib/utils';
import type { LatencyTelemetry } from '../../types';

export interface AppFooterProps {
  backend: 'checking' | 'connected' | 'disconnected';
  telemetry: LatencyTelemetry | null;
  slaTargetMs?: number | null;
}

export function AppFooter({ backend, telemetry, slaTargetMs }: AppFooterProps) {
  const connected = backend === 'connected';
  const p50 = fmtTelemetryValue(telemetry?.p50_ms);
  const p70 = fmtTelemetryValue(telemetry?.p70_ms);
  const p100 = fmtTelemetryValue(telemetry?.p100_ms);
  const samples = telemetry?.sample_count ?? 0;
  const compliance = formatPercent(telemetry?.sla_compliance_rate ?? 0);
  const sla = slaTargetMs != null ? `${Math.round(slaTargetMs)}ms` : '--';

  return (
    <footer className="fixed bottom-0 w-full h-10 flex justify-between items-center px-gutter z-50 bg-surface-container-lowest border-t border-white/10">
      <span className="font-mono-data text-mono-data text-outline">
        LATENCY: P50 {p50} | P70 {p70} | P100 {p100} | SAMPLES {samples}
      </span>
      <div className="flex gap-md font-mono-data text-mono-data text-outline">
        <span className={`${connected ? 'text-outline hover:text-tertiary' : 'text-error'} transition-colors cursor-default`}>SLA: {sla}</span>
        <span className={`${connected ? 'text-outline hover:text-tertiary' : 'text-error'} transition-colors cursor-default`}>COMPLIANCE: {compliance}</span>
        <span className="text-outline hover:text-tertiary transition-colors cursor-default">ENCRYPTION: AES-256</span>
      </div>
    </footer>
  );
}
