import logging
from sqlalchemy.ext.asyncio import AsyncSession
from services.embedding.EmbeddingInterface import EmbeddingInterface
from services.vector_search import search_similar
from exceptions import EmptyQueryError, EmbeddingError
from helpers.config import get_settings
logger = logging.getLogger(__name__)
async def search(
    query: str,
    session: AsyncSession,
    embedding_provider: EmbeddingInterface,
) -> list[dict]:
    settings = get_settings()

    # 1-Validate query
    if not query or not query.strip():
        raise EmptyQueryError()

    # 2-Embed query
    try:
        query_embedding = embedding_provider.embed_text(query.strip(), "query")
    except Exception as e:
        logger.error(f"Failed to embed query: {e}")
        raise EmbeddingError(f"Failed to embed query: {e}")

    # 3-Search
    results = await search_similar(
        session=session,
        query_embedding=query_embedding,
        top_k=settings.TOP_K,
    )

    logger.info(f"Search for '{query[:50]}...' returned {len(results)} results")
    return results
