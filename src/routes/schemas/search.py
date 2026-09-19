from pydantic import BaseModel
class SearchRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    document: str
    score: float
    content: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
