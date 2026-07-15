"""Cross-encoder reranking of initial hybrid-retrieval candidates."""
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.core.config import settings


@lru_cache
def _get_model() -> CrossEncoder:
    # Loaded once per container and kept warm; model files are baked into the
    # Docker image (see Dockerfile) to avoid a cold-start download on ECS.
    return CrossEncoder(settings.RERANKER_MODEL)


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    candidates: list of {"content": str, ...metadata}
    Returns the top_k candidates sorted by cross-encoder relevance score (descending),
    with a `rerank_score` field added.
    """
    if not candidates:
        return []

    model = _get_model()
    pairs = [(query, c["content"]) for c in candidates]
    scores = model.predict(pairs)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    return candidates[:top_k]
