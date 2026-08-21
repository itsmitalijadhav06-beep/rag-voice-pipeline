"""
Metadata-aware & structure-aware chunking strategy for MSMARCO-XI and passage-based corpora.
"""

from typing import List, Dict, Any
from app.schemas import DocumentRecord, ChunkRecord
from app.retrieval import BaseChunker


class PassageMetadataChunker(BaseChunker):
    """
    Metadata-aware chunking strategy.
    Preserves structural passage boundaries, section markers, and rich document metadata
    (e.g., passage index, ground truth relevance labels `is_selected`, query_type, language).
    """

    def __init__(self, max_chunk_size: int = 1500):
        self.max_chunk_size = max_chunk_size

    def chunk(self, document: DocumentRecord) -> List[ChunkRecord]:
        text = document.text.strip() if document.text else ""
        if not text:
            return []

        metadata = dict(document.metadata)
        chunks: List[ChunkRecord] = []

        # Case A: Document contains structured passage array in metadata
        raw_passages = metadata.get("passages")
        if raw_passages and isinstance(raw_passages, list) and len(raw_passages) > 0:
            for idx, item in enumerate(raw_passages):
                if isinstance(item, dict):
                    p_text = item.get("text", "").strip()
                    p_is_selected = item.get("is_selected", 0)
                else:
                    p_text = str(item).strip()
                    p_is_selected = 0

                if not p_text:
                    continue

                chunk_id = f"{document.document_id}_meta_{idx}"
                chunk_meta = dict(metadata)
                chunk_meta.pop("passages", None)  # Remove bulky list from chunk metadata
                chunk_meta["passage_index"] = idx
                chunk_meta["is_selected"] = p_is_selected

                # Compute position in text if present
                start_pos = text.find(p_text)
                end_pos = (start_pos + len(p_text)) if start_pos != -1 else len(p_text)

                chunks.append(
                    ChunkRecord(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        text=p_text,
                        strategy="passage_metadata",
                        start_position=start_pos if start_pos != -1 else 0,
                        end_position=end_pos,
                        metadata=chunk_meta,
                    )
                )

            if chunks:
                return chunks

        # Case B: Structural text delimiters (e.g. paragraphs or section headers)
        sections = [sec.strip() for sec in text.split("\n\n") if sec.strip()]
        if not sections:
            sections = [text]

        chunk_idx = 0
        current_offset = 0

        for sec in sections:
            start_pos = text.find(sec, current_offset)
            if start_pos == -1:
                start_pos = current_offset
            end_pos = start_pos + len(sec)
            current_offset = end_pos

            chunk_id = f"{document.document_id}_meta_{chunk_idx}"
            chunk_meta = dict(metadata)
            chunk_meta["section_index"] = chunk_idx

            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    text=sec,
                    strategy="passage_metadata",
                    start_position=start_pos,
                    end_position=end_pos,
                    metadata=chunk_meta,
                )
            )
            chunk_idx += 1

        return chunks
