"""Dense (OpenAI) + sparse (BM25) embedding generation for hybrid search."""
from langchain_openai import OpenAIEmbeddings
from rank_bm25 import BM25Okapi

from app.core.config import settings

_dense_model = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)


async def embed_dense(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of chunks with the configured dense embedding model."""
    return await _dense_model.aembed_documents(texts)


async def embed_dense_query(text: str) -> list[float]:
    return await _dense_model.aembed_query(text)


def build_sparse_vector(tokenized_corpus: list[list[str]], query_tokens: list[str]) -> dict[int, float]:
    """
    Produce a sparse BM25 vector {token_id: weight} for a query against a corpus.
    In production the corpus statistics (IDF) are precomputed once per collection
    and cached in Redis rather than rebuilt per-request.
    """
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query_tokens)
    return {i: float(s) for i, s in enumerate(scores) if s > 0}
