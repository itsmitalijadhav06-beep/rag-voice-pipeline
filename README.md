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

> [!NOTE]
> The full RAG pipeline (retrieval, vector DB embeddings, LLM generation, and guardrails) is not implemented yet. Phase 2 delivers an isolated, provider-neutral STT module.

## Dataset & Chunking Foundation (Phase 3A)

### Dataset
The official benchmark dataset for Task #2 is `ai4bharat/MSMARCO-XI`. It provides multilingual MSMARCO passages translated across Indic languages (Hindi, Bengali, Tamil, Telugu, etc.).

### Observed Dataset Schema
Inspection of `ai4bharat/MSMARCO-XI` (`validation/hinval.parquet`) revealed the following column structure:
* `query_id` (`int64`): Unique query identifier.
* `query_type` (`str`): Type classification (e.g., `DESCRIPTION`, `NUMERIC`, `LOCATION`, `ENTITY`).
* `source_lang` (`str`): Source language code (e.g., `eng_Latn`).
* `target_lang` (`str`): Target language code (e.g., `hin_Deva`).
* `Eng_Query` (`str`): Original English query text.
* `query` (`str`): Translated target language query text.
* `Eng_Answer` (`str`): Ground truth English answer.
* `Answer` (`str`): Ground truth target language answer.
* `meta` (`dict`): Generation/translation metadata dictionary.
* `passages` (`dict`): Nested dictionary containing arrays:
  - `passages['English_passages']` (`ndarray`): Array of candidate background passage texts in English.
  - `passages['Translated_passages']` (`ndarray`): Array of candidate passage texts translated to target language.
  - `passages['is_selected']` (`ndarray`): Ground truth relevance label array (`0` or `1`).

### Implemented Chunking Strategies
1. **Fixed-Size Overlap (`fixed_overlap`)**:
   - Target chunk size ~1000 characters (~250 tokens) with configurable ~150 character overlap.
   - Ideal for uniform chunk boundaries across continuous text blocks.
2. **Sentence-Aware (`sentence`)**:
   - Detects sentence boundaries (using punctuation `.`, `!`, `?`, `|`, and Devanagari full stop `।`).
   - Accumulates full sentences up to `max_chunk_size` without cutting sentences mid-way.
3. **Passage & Metadata-Aware (`passage_metadata`)**:
   - Leverages structural passage boundaries and passage-level metadata present in MSMARCO-XI.
   - Attaches `passage_index`, `is_selected` (relevance ground truth), `query_id`, `query_type`, and language attributes to each chunk.

### Design Decisions
- **Why passage/metadata-aware chunking for MSMARCO-XI**: Since `MSMARCO-XI` explicitly structures data into discrete candidate passages with query relevance ground truth (`is_selected`), arbitrary character slicing across passage boundaries risks destroying relevance context. `PassageMetadataChunker` respects natural passage boundaries and preserves query-passage relevance metadata.
- **Heavyweight Models Avoided**: In accordance with task guidelines, heavy embedding-based semantic splitters were omitted in Phase 3A to avoid premature optimization and keep offline ingestion fast and deterministic.

### Offline Preprocessing
Dataset ingestion and chunk generation take place **offline** via `scripts/build_chunks.py` rather than on every query request:
```bash
python scripts/build_chunks.py --strategy fixed_overlap --limit 200
```
This produces intermediate local artifacts:
* `data/processed/chunks.jsonl`: Formatted JSON lines conforming to `ChunkRecord`.
* `data/processed/chunk_stats.json`: Batch processing summary metrics.

> [!NOTE]
> Vector DB embeddings and FAISS index construction are deliberately omitted from Phase 3A and will be implemented in Phase 3B.


