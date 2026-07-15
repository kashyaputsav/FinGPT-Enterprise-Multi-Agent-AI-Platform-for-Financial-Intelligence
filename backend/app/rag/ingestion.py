"""
Ingestion pipeline: raw document bytes -> chunks -> embeddings -> Qdrant + Postgres.

Supports financial reports, contracts, KYC documents, and bank statements.
Uses LlamaIndex's sentence-aware splitter to keep clause/paragraph boundaries intact,
which matters for financial/legal text where mid-sentence splits break meaning.
"""
import uuid

from llama_index.core.node_parser import SentenceSplitter
from qdrant_client.models import PointStruct

from app.core.logging import get_logger
from app.rag.embeddings import embed_dense
from app.rag.qdrant_client import DENSE_VECTOR_NAME, upsert_points

logger = get_logger(__name__)

splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)


async def ingest_document(document_id: uuid.UUID, filename: str, raw_text: str) -> list[dict]:
    """
    Chunk `raw_text`, embed each chunk, and upsert into Qdrant.
    Returns the list of chunk records to be persisted in Postgres (DocumentChunk rows).
    """
    chunks = splitter.split_text(raw_text)
    if not chunks:
        logger.warning("empty_document_after_split", document_id=str(document_id), filename=filename)
        return []

    vectors = await embed_dense(chunks)

    points: list[PointStruct] = []
    chunk_records: list[dict] = []

    for idx, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector={DENSE_VECTOR_NAME: vector},
                payload={
                    "document_id": str(document_id),
                    "filename": filename,
                    "chunk_index": idx,
                    "content": chunk_text,
                },
            )
        )
        chunk_records.append(
            {"chunk_index": idx, "content": chunk_text, "qdrant_point_id": point_id}
        )

    await upsert_points(points)
    logger.info("document_ingested", document_id=str(document_id), num_chunks=len(chunks))
    return chunk_records
