import type { QueryResponse, HealthStatus, LatencyTelemetry } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export { BASE_URL };

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export type HealthCheck = {
  status: 'healthy' | 'unhealthy';
  data: HealthStatus | null;
};

export async function checkHealth(): Promise<HealthCheck> {
  try {
    const res = await fetch(`${BASE_URL}/health`, { method: 'GET', signal: AbortSignal.timeout(5000) });
    if (!res.ok) return { status: 'unhealthy', data: null };
    const data = (await res.json()) as HealthStatus;
    return { status: 'healthy', data };
  } catch {
    return { status: 'unhealthy', data: null };
  }
}

export async function getLatencyTelemetry(): Promise<LatencyTelemetry | null> {
  try {
    const res = await fetch(`${BASE_URL}/analytics/latency`, { method: 'GET', signal: AbortSignal.timeout(5000) });
    if (!res.ok) return null;
    return (await res.json()) as LatencyTelemetry;
  } catch {
    return null;
  }
}

export async function checkQueryEndpoint(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/query`, { method: 'GET', signal: AbortSignal.timeout(4000) });
    return res.status === 405 || res.status === 200 || res.status === 403;
  } catch {
    return false;
  }
}

export async function submitVoiceQuery(
  audioFile: File,
  options?: { language?: string; strategy?: string; top_k?: number },
): Promise<QueryResponse> {
  const form = new FormData();
  form.append('audio', audioFile);
  if (options?.language) {
    form.append('language', options.language);
  }
  form.append('strategy', options?.strategy ?? 'fixed');
  form.append('top_k', String(options?.top_k ?? 5));

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/query`, {
      method: 'POST',
      body: form,
      signal: AbortSignal.timeout(60_000),
    });
  } catch (err) {
    const timedOut = err instanceof Error && err.name === 'AbortError';
    throw new ApiError(
      timedOut ? 'Request timed out.' : 'Unable to reach the backend query endpoint.',
      timedOut ? 408 : 0,
      'NETWORK_ERROR',
    );
  }

  const text = await res.text();
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const json = JSON.parse(text);
      detail = json?.detail ?? json?.error;
    } catch {
      /* plain text body */
    }
    const message = detail || text || `Request failed (${res.status})`;
    let code = 'QUERY_FAILED';
    if (res.status === 404 || res.status === 405) {
      code = 'ENDPOINT_NOT_IMPLEMENTED';
    } else if (res.status >= 500) {
      code = 'SERVER_ERROR';
    }
    throw new ApiError(message, res.status, code);
  }

  return JSON.parse(text) as QueryResponse;
}
