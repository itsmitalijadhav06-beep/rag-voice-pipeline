"""
Sentence-aware chunking strategy.
"""

import re
from typing import List
from app.schemas import DocumentRecord, ChunkRecord
from app.retrieval import BaseChunker

# Pattern to split text into sentences (supports standard punctuation: . ! ? | and Devanagari full stop ।)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?|\u0964])\s+|\n+")


class SentenceChunker(BaseChunker):
    """
    Sentence-aware chunker that preserves sentence boundaries.
    Accumulates sentences until target max_chunk_size is reached.
    """

    def __init__(self, max_chunk_size: int = 1000, sentence_overlap_count: int = 1):
        """
        :param max_chunk_size: Maximum character limit for a chunk.
        :param sentence_overlap_count: Number of sentences to overlap into the next chunk.
        """
        self.max_chunk_size = max_chunk_size
        self.sentence_overlap_count = max(0, sentence_overlap_count)

    def _split_into_sentences(self, text: str) -> List[tuple[str, int, int]]:
        """
        Splits text into (sentence_str, start_pos, end_pos) tuples.
        """
        sentences = []
        raw_parts = SENTENCE_SPLIT_PATTERN.split(text)
        current_offset = 0

        for part in raw_parts:
            part_clean = part.strip()
            if not part_clean:
                continue

            # Find actual start in text from current_offset
            start = text.find(part_clean, current_offset)
            if start == -1:
                start = current_offset
            end = start + len(part_clean)
            sentences.append((part_clean, start, end))
            current_offset = end

        if not sentences and text.strip():
            sentences.append((text.strip(), 0, len(text)))

        return sentences

    def chunk(self, document: DocumentRecord) -> List[ChunkRecord]:
        """Splits document into sentence-aware chunks."""
        text = document.text.strip() if document.text else ""
        if not text:
            return []

        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks: List[ChunkRecord] = []
        chunk_idx = 0

        i = 0
        n_sentences = len(sentences)

        while i < n_sentences:
            current_sentences = []
            chunk_char_count = 0
            start_pos = sentences[i][1]
            end_pos = sentences[i][2]

            j = i
            while j < n_sentences:
                s_text, s_start, s_end = sentences[j]
                added_len = len(s_text) + (1 if current_sentences else 0)

                if current_sentences and (chunk_char_count + added_len > self.max_chunk_size):
                    break

                current_sentences.append(s_text)
                chunk_char_count += added_len
                end_pos = s_end
                j += 1

            chunk_text = " ".join(current_sentences)
            chunk_id = f"{document.document_id}_sent_{chunk_idx}"

            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    text=chunk_text,
                    strategy="sentence",
                    start_position=start_pos,
                    end_position=end_pos,
                    metadata=dict(document.metadata),
                )
            )
            chunk_idx += 1

            if j == n_sentences:
                break

            # Advance by number of sentences added minus sentence overlap count
            advanced = max(1, (j - i) - self.sentence_overlap_count)
            i += advanced

        return chunks
