import type { QueryResponse } from '../types';

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function fmtMs(ms?: number | null): string {
  if (ms == null || !Number.isFinite(ms)) return '--';
  return `${Math.round(ms)}ms`;
}

export function fmtTelemetryValue(v: number | undefined | null): string {
  if (v == null || !Number.isFinite(v)) return '--';
  return `${Math.round(v)}ms`;
}

export function formatPercent(v: number): string {
  if (!Number.isFinite(v)) return '--';
  return `${v.toFixed(1)}%`;
}

export function classifyResponse(res: QueryResponse): 'results' | 'refused' | 'unsafe' | 'error' {
  const status = (res.status || '').toUpperCase();
  const grounded = res.grounded ?? false;

  if (status === 'UNSAFE') return 'unsafe';
  if (status === 'GENERATION_ERROR') return 'error';
  if (!grounded || ['UNGROUNDED', 'INSUFFICIENT_CONTEXT', 'OFF_TOPIC', 'REFUSED'].includes(status)) return 'refused';
  return 'results';
}

export function safeText(value: unknown, fallback = ''): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  return fallback;
}

export function latencyFromResponse(res: QueryResponse | null): {
  stt: number | null;
  retrieval: number | null;
  generation: number | null;
  total: number | null;
} {
  if (!res) return { stt: null, retrieval: null, generation: null, total: null };
  const lat = res.latency;
  return {
    stt: lat?.stt_ms ?? null,
    retrieval: lat?.retrieval_ms ?? null,
    generation: lat?.generation_ms ?? null,
    total: lat?.total_ms ?? null,
  };
}

export async function withMinDuration<T>(p: Promise<T>, minMs: number): Promise<T> {
  const start = Date.now();
  let result: T | undefined;
  let errored: unknown;
  try {
    result = await p;
  } catch (e) {
    errored = e;
  }
  const elapsed = Date.now() - start;
  if (elapsed < minMs) {
    await new Promise((r) => setTimeout(r, minMs - elapsed));
  }
  if (errored !== undefined) throw errored;
  return result as T;
}
