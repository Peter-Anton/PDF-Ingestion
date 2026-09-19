import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from controllers.search_controller import search
from schemas.search import SearchRequest, SearchResponse, SearchResult
from exceptions import EmptyQueryError

logger = logging.getLogger(__name__)

search_router = APIRouter(
    prefix="/api/v1",
    tags=["Search"])


@search_router.post("/search/", response_model=SearchResponse)
async def search_endpoint(
    request: Request,
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    embedding_provider = request.app.state.embedding_client

    results = await search(
        query=body.query,
        session=db,
        embedding_provider=embedding_provider,
    )

    return SearchResponse(
        results=[
            SearchResult(
                document=r["document"],
                score=r["score"],
                content=r["content"],
            )
            for r in results
        ]
    )
