from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_scheme.pgvector.schemes.chunk import Chunk
from models.db_scheme.pgvector.schemes.documents import Document


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, document_id, chunk_data: list[dict]) -> int:
        chunks = [
            Chunk(
                document_id=document_id,
                chunk_text=item["content"],
                chunk_index=item["chunk_index"],
                embedding=item["embedding"],
            )
            for item in chunk_data
        ]
        self.session.add_all(chunks)
        return len(chunks)

    async def search_similar(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict]:
        distance = Chunk.embedding.cosine_distance(query_embedding)
        result = await self.session.execute(
            select(Chunk, Document.filename, distance.label("distance"))
            .join(Document, Chunk.document_id == Document.id)
            .order_by(distance)
            .limit(top_k)
        )
        return [
            {
                "document": filename,
                "score": round(1 - dist, 4),
                "content": chunk.chunk_text,
            }
            for chunk, filename, dist in result.all()
        ]

    async def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 5,
        rrf_k: int = 60,
        min_relevance_score: float = 0.55,
    ) -> list[dict]:
        candidate_limit = max(top_k * 4, 20)
        distance = Chunk.embedding.cosine_distance(query_embedding)
        semantic_result = await self.session.execute(
            select(Chunk, Document.filename, distance.label("distance"))
            .join(Document, Chunk.document_id == Document.id)
            .order_by(distance)
            .limit(candidate_limit)
        )

        document_text = func.to_tsvector("english", Chunk.chunk_text)
        query_text = func.websearch_to_tsquery("english", query)
        lexical_rank = func.ts_rank_cd(document_text, query_text)
        lexical_result = await self.session.execute(
            select(Chunk, Document.filename, lexical_rank.label("rank"))
            .join(Document, Chunk.document_id == Document.id)
            .where(document_text.op("@@")(query_text))
            .order_by(lexical_rank.desc())
            .limit(candidate_limit)
        )

        candidates = {}
        for rank, (chunk, filename, dist) in enumerate(semantic_result.all(), start=1):
            candidates[chunk.id] = {
                "document": filename,
                "content": chunk.chunk_text,
                "semantic_score": 1 - dist,
                "hybrid_score": 1 / (rrf_k + rank),
            }

        for rank, (chunk, filename, _) in enumerate(lexical_result.all(), start=1):
            candidate = candidates.setdefault(
                chunk.id,
                {
                    "document": filename,
                    "content": chunk.chunk_text,
                    "semantic_score": 0.0,
                    "hybrid_score": 0.0,
                },
            )
            candidate["hybrid_score"] += 1 / (rrf_k + rank)

        ranked = sorted(
            candidates.values(),
            key=lambda candidate: candidate["hybrid_score"],
            reverse=True,
        )
        ranked = [
            candidate
            for candidate in ranked
            if candidate["semantic_score"] >= min_relevance_score
        ][:top_k]
        return [
            {
                "document": candidate["document"],
                "score": round(candidate["hybrid_score"], 4),
                "content": candidate["content"],
            }
            for candidate in ranked
        ]
