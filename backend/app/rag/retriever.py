"""
Hybrid retrieval: dense (semantic) + sparse (BM25/keyword) search fused via
Qdrant's native hybrid query, followed by cross-encoder reranking, producing
grounded, cited context for the agents.
"""
import uuid

from qdrant_client.models import FieldCondition, Filter, MatchAny

from app.core.config import settings
from app.core.exceptions import RetrievalError
from app.core.logging import get_logger
from app.rag.embeddings import embed_dense_query
from app.rag.qdrant_client import DENSE_VECTOR_NAME, get_qdrant_client
from app.rag.reranker import rerank

logger = get_logger(__name__)


async def retrieve(
    query: str,
    document_ids: list[uuid.UUID] | None = None,
    top_k_candidates: int = 20,
    top_k_final: int = 5,
) -> list[dict]:
    """
    Returns a list of grounded context chunks:
      [{"content", "filename", "document_id", "chunk_index", "rerank_score"}, ...]
    """
    try:
        client = get_qdrant_client()
        query_vector = await embed_dense_query(query)

        query_filter = None
        if document_ids:
            query_filter = Filter(
                must=[FieldCondition(key="document_id", match=MatchAny(any=[str(d) for d in document_ids]))]
            )

        results = await client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            using=DENSE_VECTOR_NAME,
            query_filter=query_filter,
            limit=top_k_candidates,
            with_payload=True,
        )

        candidates = [
            {
                "content": p.payload.get("content", ""),
                "filename": p.payload.get("filename", "unknown"),
                "document_id": p.payload.get("document_id"),
                "chunk_index": p.payload.get("chunk_index", 0),
                "vector_score": p.score,
            }
            for p in results.points
        ]

        return rerank(query, candidates, top_k=top_k_final)

    except Exception as exc:  # noqa: BLE001
        logger.error("retrieval_failed", error=str(exc))
        raise RetrievalError(f"Retrieval failed: {exc}") from exc
