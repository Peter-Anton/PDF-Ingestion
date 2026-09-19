import logging
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.chunk_repository import ChunkRepository
logger = logging.getLogger(__name__)
async def search_similar(
    session: AsyncSession,
    query: str,
    query_embedding: list[float],
    top_k: int = 5,
    rrf_k: int = 60,
    min_relevance_score: float = 0.55,
) -> list[dict]:
    chunk_repo = ChunkRepository(session)
    results = await chunk_repo.hybrid_search(
        query,
        query_embedding,
        top_k,
        rrf_k,
        min_relevance_score,
    )
    logger.info(f"Hybrid search returned {len(results)} results")
    return results
