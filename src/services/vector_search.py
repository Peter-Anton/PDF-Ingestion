import logging
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.chunk_repository import ChunkRepository
logger = logging.getLogger(__name__)
async def search_similar(
    session: AsyncSession,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict]:
    chunk_repo = ChunkRepository(session)
    results = await chunk_repo.search_similar(query_embedding, top_k)
    logger.info(f"Vector search returned {len(results)} results")
    return results
