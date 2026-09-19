from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_scheme.pgvector.schemes.documents import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hash(self, file_hash: str) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.file_hash == file_hash)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        filename: str,
        file_hash: str,
        file_size: int,
        status: str,
    ) -> Document:
        document = Document(
            filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            status=status,
        )
        self.session.add(document)
        return document

    async def update_status(
        self,
        document_id: UUID,
        status: str,
        error_message: str | None = None,
        chunk_count: int | None = None,
    ) -> None:
        values = {"status": status, "error_message": error_message}
        if chunk_count is not None:
            values["chunk_count"] = chunk_count
        await self.session.execute(
            update(Document).where(Document.id == document_id).values(**values)
        )
