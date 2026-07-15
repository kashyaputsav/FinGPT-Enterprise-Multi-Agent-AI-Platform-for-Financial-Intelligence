"""Thin wrapper around the Qdrant client with hybrid (dense + sparse) collection setup."""
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, SparseVectorParams, VectorParams

from app.core.config import settings

_client: AsyncQdrantClient | None = None

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
DENSE_VECTOR_SIZE = 3072  # text-embedding-3-large dimensionality


def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    return _client


async def ensure_collection() -> None:
    """Idempotently create the hybrid (dense + sparse) collection on startup."""
    client = get_qdrant_client()
    existing = await client.get_collections()
    names = {c.name for c in existing.collections}
    if settings.QDRANT_COLLECTION in names:
        return

    await client.create_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config={DENSE_VECTOR_NAME: VectorParams(size=DENSE_VECTOR_SIZE, distance=Distance.COSINE)},
        sparse_vectors_config={SPARSE_VECTOR_NAME: SparseVectorParams()},
    )


async def upsert_points(points: list[PointStruct]) -> None:
    client = get_qdrant_client()
    await client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
