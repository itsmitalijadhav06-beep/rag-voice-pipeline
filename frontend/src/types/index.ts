export type BackendStatus = 'checking' | 'connected' | 'disconnected';

export type AppError = {
  message: string;
  code?: string;
  retryable: boolean;
};

export type AppState =
  | { phase: 'ready' }
  | { phase: 'recording'; startedAt: number; durationMs: number }
  | { phase: 'processing'; startedAt: number }
  | { phase: 'results'; response: QueryResponse }
  | { phase: 'refused'; response: QueryResponse }
  | { phase: 'unsafe'; response: QueryResponse }
  | { phase: 'error'; error: AppError }
  | { phase: 'disconnected' };

export type QueryEndpointState = 'checking' | 'available' | 'unavailable';

export type SectionKey = 'hub' | 'knowledge' | 'guardrails' | 'latency';

export interface HealthStatus {
  status: string;
  environment: string;
  stt_provider: string;
  llm_provider: string;
  vector_db_type: string;
  sla_target_ms: number;
}

export interface LatencyTelemetry {
  sample_count: number;
  p50_ms: number;
  p70_ms: number;
  p100_ms: number;
  sla_compliance_rate: number;
}

export interface ContextChunk {
  chunk_id: string;
  text: string;
  score: number;
  strategy_used: string;
  metadata: Record<string, unknown>;
}

export interface GuardrailCheckResult {
  passed: boolean;
  reason?: string | null;
  off_topic: boolean;
  unsafe: boolean;
  grounded: boolean;
  refusal_triggered: boolean;
}

export interface QueryResponse {
  query: string;
  answer: string;
  grounded: boolean;
  retrieved_chunks: ContextChunk[];
  guardrail_status: GuardrailCheckResult;
  stt_latency_ms?: number | null;
  rag_pipeline_latency_ms: number;
  total_latency_ms: number;
  latency_breakdown_ms: Record<string, number>;
  sla_met: boolean;
}
