# Voice-Enabled RAG Pipeline — Hacker House Goa 2026

Shortlisting Task 2: High-Performance Voice-Enabled Retrieval-Augmented Generation (RAG) System.

## Pipeline Architecture Overview
```
Voice Input -> Speech-to-Text -> Chunking/Retrieval (Vector DB) -> Answer Generation
                                              │                         │
                                     Guardrails Engine        Reliability Harness
                                              │                         │
                                      Latency Analytics Dashboard & Telemetry
```

## Features & Requirements Compliance
- **Speech-to-Text**: Plug-and-play abstraction for Sarvam AI and ElevenLabs.
- **Vast Chunking Strategy**: Multi-tier chunking (Fixed-size overlap, Semantic splitting, Metadata-aware chunking).
- **Sub-200ms Target**: Performance-tuned vector retrieval + lightweight inference path.
- **P50 / P70 / P100 Telemetry**: Built-in latency analytics suite for benchmark runs.
- **Reliability Harness**: Retry policy with exponential backoff, structured output parsing, error recovery.
- **Guardrails**: Query safety filter, groundedness evaluation, hallucination detection, explicit refusal mechanism.

## Project Structure
```
rag-voice-pipeline/
├── app/
│   ├── api/          # FastAPI routes & endpoints
│   ├── stt/          # Sarvam & ElevenLabs speech-to-text engines
│   ├── retrieval/    # Chunking strategies & Vector DB indexers
│   ├── generation/   # LLM synthesis & grounded answer generation
│   ├── guardrails/   # Safety & hallucination guardrail checks
│   ├── analytics/    # Latency tracking (P50/P70/P100)
│   ├── core/         # Config, structured logging, custom exceptions
│   └── schemas/      # Pydantic data models
├── data/             # Raw, processed, and vector index storage
├── scripts/          # Benchmark and dataset preprocessing scripts
├── tests/            # Test suite
└── run.py            # Uvicorn app runner
```

## Quickstart

1. Copy `.env.example` to `.env` and fill in credentials:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   python run.py
   ```

## STT Integration (Phase 2)

### Provider Selection
**Sarvam AI** was selected as the primary Speech-to-Text provider for Phase 2. Sarvam AI specializes in Indian English and Indic language acoustics with code-mixing capabilities (`saaras:v3` model), making it optimal for the target domain.

### API & Interface Choice
Rather than relying on volatile third-party SDK versions, the STT layer utilizes `httpx.AsyncClient` to directly interface with Sarvam's official REST API endpoint (`POST https://api.sarvam.ai/speech-to-text`). This ensures zero extra dependencies, async non-blocking HTTP execution, precise timeout management, and strict exception mapping.

### Configuration
Configure `.env` with:
```env
STT_PROVIDER=sarvam
SARVAM_API_KEY=your_sarvam_api_key_here
```

### Supported Input Assumptions
- **Input Types**: File path (`str`/`Path`), raw audio `bytes`, or binary file-like objects (`IO[bytes]`).
- **Formats**: WAV, MP3, M4A, AAC, FLAC, OGG, OPUS, AIFF, AMR, WMA, WebM, PCM.
- **Payload Limit**: Maximum 25 MB synchronous payload limit per request.

### Failure Handling & Validation
The client performs pre-flight validation for empty inputs, missing files, unsupported formats, and binary header mismatches. Errors are caught and mapped into application-level `STTProcessingError` exceptions:
- Missing or placeholder API key
- Authentication failures (HTTP 401/403)
- Network connectivity failures (`httpx.NetworkError`)
- Request timeouts (`httpx.TimeoutException`)
- Provider API error status codes (HTTP 400/422/500/502/503)
- Empty transcriptions (returns `TranscriptionResult(status="error", ...)` or raises exception)
- Malformed provider JSON payloads

### Latency Measurement
STT latency (`latency_ms`) is measured strictly around the external provider API HTTP call using `time.perf_counter()` monotonic timers. It is recorded cleanly in the returned `TranscriptionResult` object.

### Testing Locally
- **Automated Tests**:
  ```bash
  pytest tests/test_stt.py
  ```
  *(All unit tests use mocking and do not call real external APIs by default)*
- **Manual Test Script**:
  ```bash
  python scripts/test_stt.py [path/to/audio.wav]
  ```

## Retrieval Implementation (Phases 3A – 3D)

### Primary Dataset (Phase 3A)
- **Dataset**: `ai4bharat/MSMARCO-XI` (MS MARCO translated into 14 Indic languages).
- **Controlled Subset Ingestion**: Supports streaming and local parquet subset loading via `--language` (e.g. `mr`, `hi`, `en`), `--split` (`train`, `validation`), and `--limit`.
- **Normalization Layer**: Converts nested raw records (queries, answers, passage arrays, `is_selected` flags, query types) into normalized `DocumentRecord` structures (`document_id`, `text`, `metadata`).

### Vast Chunking Strategies (Phase 3B)
The pipeline implements four distinct chunking strategies to satisfy vast chunking requirements:
1. **FixedSizeChunker**: Token/word windowing (default: 512 tokens, 50 token overlap). Validates `overlap < chunk_size`.
2. **SentenceAwareChunker**: Sentence-boundary preserving chunker grouping complete sentences up to a target character budget without splitting mid-sentence. Supports Indic punctuation (`।`).
3. **SemanticChunker**: Sentence segmentation + embedding similarity thresholding over adjacent sentence pairs to detect semantic topic shifts.
4. **MetadataAwareChunker**: Metadata wrapper enriching chunks with document provenance and chunk positions.

### Embeddings & FAISS Vector Indexing (Phase 3C)
- **Embedding Model**: Configurable `sentence-transformers/all-MiniLM-L6-v2` (384-dim) with offline fallback.
- **FAISS Storage**: Flat inner-product vector store (`IndexFlatIP`) persisted under strategy-specific directories:
  ```
  data/index/
  ├── fixed/       (index.faiss, chunks.pkl, meta.json)
  ├── sentence/    (index.faiss, chunks.pkl, meta.json)
  └── semantic/    (index.faiss, chunks.pkl, meta.json)
  ```

### Stable Retrieval Contract & Benchmark (Phase 3D)
- **Stable Entry Point**:
  ```python
  retrieve(query: str, top_k: int = 5, strategy: str = "fixed") -> list[RetrievedChunk]
  ```
- **Runtime Path**: Searches pre-built strategy indexes lazily without runtime index rebuilding.
- **Measured Retrieval Benchmark**:
  - **Total Test Queries**: 20
  - **P50 (Median) Latency**: 5.85 ms
  - **P70 Latency**: 6.07 ms
  - **P100 (Max) Latency**: 12.75 ms
  - **Average Top-K Similarity Score**: 0.6476

