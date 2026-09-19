from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_scheme.pgvector.schemes.chunk import Chunk


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
            select(Chunk, distance.label("score"))
            .order_by(distance)
            .limit(top_k)
        )
        return [
            {
                "document": chunk.document_id,
                "score": score,
                "content": chunk.chunk_text,
            }
            for chunk, score in result.all()
        ]
