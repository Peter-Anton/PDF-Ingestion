from sqlalchemy import select
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
