import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from controllers.search_controller import search
from routes.schemas.search import SearchRequest, SearchResponse, SearchResult
from exceptions import EmptyQueryError, EmbeddingError

logger = logging.getLogger(__name__)

search_router = APIRouter(tags=["Search"])


@search_router.post("/search/", response_model=SearchResponse)
async def search_endpoint(
    request: Request,
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    embedding_provider = request.app.state.embedding_client

    try:
        results = await search(
            query=body.query,
            session=db,
            embedding_provider=embedding_provider,
        )
    except EmptyQueryError:
        return JSONResponse(
            status_code=400,
            content={"error": "Query cannot be empty."},
        )
    except EmbeddingError as e:
        logger.error(f"Embedding error during search: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Search processing failed."},
        )
    except Exception as e:
        logger.exception(f"Unexpected error during search: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Search processing failed."},
        )

    return SearchResponse(
        results=[
            SearchResult(
                document=str(r["document"]),
                score=r["score"],
                content=r["content"],
            )
            for r in results
        ]
    )
