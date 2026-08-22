import { useCallback, useEffect, useRef, useState } from 'react';

export type RecorderState = 'idle' | 'loading' | 'recording' | 'stopped';

export interface VoiceRecorderState {
  state: RecorderState;
  isRecording: boolean;
  durationMs: number;
  amplitudeSamples: number[];
  latestAmplitude: number;
  blob: Blob | null;
  error: string | null;
  permission: 'prompt' | 'granted' | 'denied';
  ready: boolean;
}

export interface VoiceRecorderHandle extends VoiceRecorderState {
  start: () => Promise<void>;
  stop: () => void;
  reset: () => void;
}

const CLAMP_MAX = 16;

export function useVoiceRecorder(): VoiceRecorderHandle {
  const [state, setState] = useState<RecorderState>('idle');
  const [durationMs, setDurationMs] = useState(0);
  const [amplitudeSamples, setAmplitudeSamples] = useState<number[]>([]);
  const [latestAmplitude, setLatestAmplitude] = useState(0);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permission, setPermission] = useState<'prompt' | 'granted' | 'denied'>('prompt');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const samplesRef = useRef<number[]>([]);
  const startTimeRef = useRef<number>(0);
  const durationTimerRef = useRef<number | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);

  const ready = state === 'idle' || state === 'stopped';

  const stopAnalysis = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }
  }, []);

  const analyzeLoop = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser || !rafRef) return;
    if (!dataArrayRef.current) {
      dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
    }
    const data = dataArrayRef.current;
    analyser.getByteFrequencyData(data as unknown as Uint8Array<ArrayBuffer>);
    let sum = 0;
    const len = data.length;
    for (let i = 0; i < len; i++) sum += data[i] * data[i];
    const rms = Math.sqrt(sum / len) / 255; // 0..1
    const normalized = Math.min(1, rms * 3); // boost for visibility

    setLatestAmplitude(normalized);
    samplesRef.current.push(normalized);
    if (samplesRef.current.length > CLAMP_MAX * 3) {
      samplesRef.current = samplesRef.current.slice(samplesRef.current.length - CLAMP_MAX * 3);
    }
    // update visible waveform samples at SAMPLE_RATE
    const downsampled = downsample(samplesRef.current, CLAMP_MAX);
    setAmplitudeSamples(downsampled);

    rafRef.current = requestAnimationFrame(analyzeLoop);
  }, []);

  const start = useCallback(async () => {
    setError(null);
    setBlob(null);
    samplesRef.current = [];
    setAmplitudeSamples([]);
    setLatestAmplitude(0);
    setDurationMs(0);

    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Microphone access is not supported in this browser.');
      setState('idle');
      setPermission('denied');
      return;
    }

    setState('loading');

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      const name = (err as DOMException)?.name;
      setPermission('denied');
      setError(
        name === 'NotAllowedError'
          ? 'Microphone access was denied. Please allow microphone use and try again.'
          : name === 'NotFoundError'
            ? 'No microphone was found. Please connect a microphone and try again.'
            : 'Unable to access the microphone. Check your device permissions.',
      );
      setState('idle');
      return;
    }

    setPermission('granted');
    streamRef.current = stream;

    try {
      const audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.4;
      analyserRef.current = analyser;
      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;
      source.connect(analyser);
      dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount) as Uint8Array;
      rafRef.current = requestAnimationFrame(analyzeLoop);
    } catch {
      // analysis is non-essential; continue without real-time waveform
      analyserRef.current = null;
    }

    const options: MediaRecorderOptions = { mimeType: preferMimeType() };
    const recorder = new MediaRecorder(stream, options);
    mediaRecorderRef.current = recorder;

    const chunks: BlobPart[] = [];
    recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    recorder.onstop = () => {
      const newBlob = new Blob(chunks, { type: options.mimeType || 'audio/webm' });
      setBlob(newBlob);
      setState('stopped');
    };

    startTimeRef.current = Date.now();
    setDurationMs(0);
    durationTimerRef.current = window.setInterval(() => {
      setDurationMs(Date.now() - startTimeRef.current);
    }, 250);

    setState('recording');
    recorder.start();
  }, [analyzeLoop]);

  const stop = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop();
    }
    stopAnalysis();
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    setState('stopped');
  }, [stopAnalysis]);

  const reset = useCallback(() => {
    stopAnalysis();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    streamRef.current = null;
    samplesRef.current = [];
    setAmplitudeSamples([]);
    setLatestAmplitude(0);
    setDurationMs(0);
    setBlob(null);
    setError(null);
    setState('idle');
  }, [stopAnalysis]);

  useEffect(() => {
    return () => {
      stopAnalysis();
      if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
        audioCtxRef.current.close();
      }
    };
  }, [stopAnalysis]);

  return {
    state,
    isRecording: state === 'recording',
    durationMs,
    amplitudeSamples,
    latestAmplitude,
    blob,
    error,
    permission,
    ready,
    start,
    stop,
    reset,
  };
}

function preferMimeType(): string {
  if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) return 'audio/webm;codecs=opus';
  if (MediaRecorder.isTypeSupported('audio/webm')) return 'audio/webm';
  if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) return 'audio/ogg;codecs=opus';
  return '';
}

function downsample(samples: number[], bars: number): number[] {
  if (samples.length === 0) {
    return new Array(bars).fill(0);
  }
  const out: number[] = [];
  const step = samples.length / bars;
  for (let i = 0; i < bars; i++) {
    const start = Math.floor(i * step);
    const end = Math.min(samples.length, Math.floor((i + 1) * step));
    if (start >= end) {
      out.push(0);
      continue;
    }
    let sum = 0;
    for (let j = start; j < end; j++) sum += samples[j];
    out.push(sum / (end - start));
  }
  return out.length ? out : new Array(bars).fill(0);
}

interface BlobEvent {
  data: Blob;
}
