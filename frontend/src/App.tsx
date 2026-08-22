import { useCallback, useEffect, useMemo, useState } from 'react';
import { useBackendStatus } from './hooks/useBackendStatus';
import { useVoiceRecorder } from './hooks/useVoiceRecorder';
import { ApiError, BASE_URL, submitVoiceQuery } from './services/api';
import { classifyResponse, latencyFromResponse, withMinDuration } from './lib/utils';
import { TopNavBar } from './components/layout/TopNavBar';
import { SideNavBar } from './components/layout/SideNavBar';
import { AppFooter } from './components/layout/AppFooter';
import { ReadyState } from './states/ReadyState';
import { RecordingState } from './states/RecordingState';
import { ProcessingState } from './states/ProcessingState';
import { ResultsState } from './states/ResultsState';
import { RefusalState } from './states/RefusalState';
import { ErrorState } from './states/ErrorState';
import { KnowledgeView } from './views/KnowledgeView';
import { GuardrailsView } from './views/GuardrailsView';
import { LatencyView } from './views/LatencyView';
import type { AppState, AppError, SectionKey } from './types';

type Backend = 'checking' | 'connected' | 'disconnected';

function disconnectedError(): AppError {
  return {
    message: `Backend is not reachable at ${BASE_URL}. Start the API server or verify VITE_API_BASE_URL, then retry.`,
    code: 'NETWORK_ERROR',
    retryable: true,
  };
}

export function App() {
  const { status, healthDetail, telemetry, recheck } = useBackendStatus();
  const recorder = useVoiceRecorder();

  const backend: Backend = status;
  const mockMode = false;

  const [phase, setPhase] = useState<AppState>({ phase: 'ready' });
  const [section, setSection] = useState<SectionKey>('hub');

  const activeSection: SectionKey = useMemo(() => {
    if (phase.phase !== 'ready') {
      switch (phase.phase) {
        case 'results':
          return 'knowledge';
        case 'refused':
        case 'unsafe':
          return 'guardrails';
        default:
          return section;
      }
    }
    return section;
  }, [phase.phase, section]);

  const response =
    phase.phase === 'results' || phase.phase === 'refused' || phase.phase === 'unsafe'
      ? phase.response
      : null;

  const handleQueryFile = useCallback(async (file: File) => {
    setPhase({ phase: 'processing', startedAt: Date.now() });
    try {
      const res = await withMinDuration(submitVoiceQuery(file, { strategy: 'fixed', top_k: 5 }), 700);
      const cls = classifyResponse(res);
      if (cls === 'unsafe') setPhase({ phase: 'unsafe', response: res });
      else if (cls === 'error') setPhase({ phase: 'error', error: { message: res.answer || 'Generation failed.', code: 'GENERATION_ERROR', retryable: true } });
      else if (cls === 'refused') setPhase({ phase: 'refused', response: res });
      else setPhase({ phase: 'results', response: res });
    } catch (e) {
      const apiErr = e instanceof ApiError ? e : new ApiError((e as Error)?.message || 'Query failed.', 0, 'QUERY_FAILED');
      setPhase({ phase: 'error', error: { message: apiErr.message, code: apiErr.code, retryable: true } });
    }
  }, []);

  const startQueryFromBlob = useCallback(
    async (blob: Blob) => {
      const ext = blob.type.split(';')[0].replace('audio/', '');
      const file = new File([blob], `recording.${ext || 'blob'}`, { type: blob.type });
      await handleQueryFile(file);
    },
    [handleQueryFile],
  );

  const toggleMic = useCallback(() => {
    if (phase.phase === 'recording') {
      recorder.stop();
      return;
    }
    if (backend !== 'connected') return;
    if (phase.phase !== 'ready') {
      recorder.reset();
      setPhase({ phase: 'ready' });
    }
    setPhase({ phase: 'recording', startedAt: Date.now(), durationMs: 0 });
    void recorder.start();
  }, [phase.phase, recorder, backend]);

  const onUpload = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'audio/*';
    input.onchange = () => {
      const file = input.files?.[0];
      if (file) {
        recorder.reset();
        void handleQueryFile(file);
      }
    };
    input.click();
  }, [recorder, handleQueryFile]);

  // recording -> processing when a blob is ready
  useEffect(() => {
    if (phase.phase === 'recording' && recorder.state === 'stopped' && recorder.blob) {
      void startQueryFromBlob(recorder.blob);
    }
  }, [phase.phase, recorder.state, recorder.blob, startQueryFromBlob]);

  // surface mic errors
  useEffect(() => {
    if (phase.phase === 'recording' && recorder.error && recorder.state !== 'recording') {
      setPhase({ phase: 'error', error: { message: recorder.error, code: 'MICROPHONE_ERROR', retryable: true } });
    }
  }, [phase.phase, recorder.error, recorder.state]);

  // disconnected override (only when not mid-flight)
  useEffect(() => {
    if (backend === 'disconnected') {
      if (phase.phase !== 'processing' && phase.phase !== 'recording') {
        setPhase({ phase: 'disconnected' });
      }
    } else if (backend === 'connected' && phase.phase === 'disconnected') {
      setPhase({ phase: 'ready' });
    }
  }, [backend, phase.phase]);

  const onReset = useCallback(() => {
    recorder.reset();
    setPhase({ phase: 'ready' });
  }, [recorder]);

  const onRetry = useCallback(() => {
    void recheck();
    setPhase({ phase: 'ready' });
  }, [recheck]);

  const onNavigate = useCallback((key: SectionKey) => {
    setSection(key);
    if (phase.phase !== 'ready') {
      recorder.reset();
      setPhase({ phase: 'ready' });
    }
  }, [phase.phase, recorder]);

  const navVariant =
    phase.phase === 'results' ? 'results' : phase.phase === 'refused' || phase.phase === 'unsafe' ? 'refusal' : phase.phase === 'processing' ? 'processing' : 'idle';

  const ambientClass =
    phase.phase === 'processing'
      ? 'ambient-cyan'
      : phase.phase === 'results'
        ? 'ambient-blue'
        : phase.phase === 'refused' || phase.phase === 'unsafe'
          ? 'ambient-grid'
          : '';

  const lt = latencyFromResponse(response);

  const renderContent = () => {
    if (phase.phase === 'ready') {
      switch (section) {
        case 'hub':
          return (
            <ReadyState backend={backend} health={healthDetail} onMicPress={toggleMic} onUpload={onUpload} />
          );
        case 'knowledge':
          return <KnowledgeView health={healthDetail} />;
        case 'guardrails':
          return <GuardrailsView health={healthDetail} />;
        case 'latency':
          return <LatencyView telemetry={telemetry} slaTargetMs={healthDetail?.sla_target_ms ?? null} response={response} />;
      }
    }

    switch (phase.phase) {
      case 'recording':
        return <RecordingState recorder={recorder} onCancel={onReset} />;
      case 'processing':
        return (
          <ProcessingState startedAt={phase.startedAt} recordedSamples={recorder.amplitudeSamples} sttLatencyMs={lt.stt} onCancel={onReset} />
        );
      case 'results':
        return <ResultsState response={phase.response} sttLatencyMs={lt.stt} retrievalLatencyMs={lt.retrieval} onReset={onReset} onNewQuery={toggleMic} />;
      case 'refused':
        return <RefusalState response={phase.response} kind="refused" onReset={onReset} onNewQuery={toggleMic} />;
      case 'unsafe':
        return <RefusalState response={phase.response} kind="unsafe" onReset={onReset} onNewQuery={toggleMic} />;
      case 'error':
        return <ErrorState error={phase.error} backend={backend} onRetry={onRetry} onReset={onReset} />;
      case 'disconnected':
        return <ErrorState error={disconnectedError()} backend={backend} onRetry={onRetry} onReset={onReset} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen text-on-surface font-body-md">
      <div aria-hidden="true" className={`fixed inset-0 -z-10 ${ambientClass}`}>
        {phase.phase === 'processing' && <div className="absolute inset-0 scan-overlay" />}
      </div>
      <TopNavBar variant={navVariant} backend={backend} mockMode={mockMode} health={healthDetail} onRecordToggle={toggleMic} recording={phase.phase === 'recording'} />
      <SideNavBar health={healthDetail} active={activeSection} onNavigate={onNavigate} />
      <main className="flex-1 flex flex-col md:pl-64 w-full relative z-10">{renderContent()}</main>
      <AppFooter backend={backend} telemetry={telemetry} slaTargetMs={healthDetail?.sla_target_ms ?? null} />
    </div>
  );
}

export default App;
