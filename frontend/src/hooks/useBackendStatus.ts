import { useCallback, useEffect, useRef, useState } from 'react';
import type { BackendStatus, HealthStatus, LatencyTelemetry } from '../types';
import { checkHealth, getLatencyTelemetry } from '../services/api';

const POLL_MS = 15_000;

export function useBackendStatus(pollIntervalMs = POLL_MS) {
  const [status, setStatus] = useState<BackendStatus>('checking');
  const [healthDetail, setHealthDetail] = useState<HealthStatus | null>(null);
  const [telemetry, setTelemetry] = useState<LatencyTelemetry | null>(null);

  const controllerRef = useRef<AbortController | null>(null);

  const fetchTelemetry = useCallback(async () => {
    if (controllerRef.current) controllerRef.current.abort();
    controllerRef.current = new AbortController();
    const hc = await checkHealth();
    setStatus(hc.status === 'healthy' ? 'connected' : 'disconnected');
    setHealthDetail(hc.data);

    if (hc.status === 'healthy') {
      const t = await getLatencyTelemetry();
      setTelemetry(t);
    }
  }, []);

  const check = useCallback(() => {
    void fetchTelemetry();
  }, [fetchTelemetry]);

  useEffect(() => {
    check();
    const id = setInterval(check, pollIntervalMs);
    return () => clearInterval(id);
  }, [check, pollIntervalMs]);

  return { status, healthDetail, telemetry, recheck: check };
}
