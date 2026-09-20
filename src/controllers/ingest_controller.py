import asyncio
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services.hashing import compute_sha256
from services.pdf_extractor import extract_text
from services.chunker import chunk_text
from services.embedding.EmbeddingInterface import EmbeddingInterface
from repositories.document_repository import DocumentRepository
from repositories.chunk_repository import ChunkRepository
from exceptions import PDFExtractionError, EmbeddingError
from helpers.config import get_settings

logger = logging.getLogger(__name__)


async def ingest_single_file(
    filename: str,
    file_bytes: bytes,
    session: AsyncSession,
    embedding_provider: EmbeddingInterface,
) -> dict:
    settings = get_settings()
    doc_repo = DocumentRepository(session)
    chunk_repo = ChunkRepository(session)
    try:
        file_hash = compute_sha256(file_bytes)
        file_size = len(file_bytes)
        existing = await doc_repo.get_by_hash(file_hash)
        if existing and existing.status == "completed":
            logger.info(f"Duplicate detected: {filename} (hash={file_hash[:12]}...)")
            return {
                "success": True,
                "filename": filename,
                "error": None,
                "duplicate": True,
            }
        try:
            doc = await doc_repo.create(
                filename=filename,
                file_hash=file_hash,
                file_size=file_size,
                status="processing",
            )
            await session.flush()
        except IntegrityError:
            await session.rollback()
            logger.info(f"Race condition duplicate: {filename} (hash={file_hash[:12]}...)")
            return {
                "success": True,
                "filename": filename,
                "error": None,
                "duplicate": True,
            }
        try:
            text = extract_text(file_bytes)
        except PDFExtractionError as e:
            await doc_repo.update_status(doc.id, "failed", error_message=str(e))
            await session.commit()
            logger.error(f"Text extraction failed for {filename}: {e}")
            return {
                "success": False,
                "filename": filename,
                "error": str(e),
                "duplicate": False,
            }
        chunks = chunk_text(
            text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        if not chunks:
            await doc_repo.update_status(doc.id, "failed", error_message="No text chunks produced.")
            await session.commit()
            return {
                "success": False,
                "filename": filename,
                "error": "No text chunks produced.",
                "duplicate": False,
            }
        try:
            embeddings = await asyncio.to_thread(
                embedding_provider.embed_texts,
                chunks,
                "document",
            )
        except Exception as e:
            await doc_repo.update_status(doc.id, "failed", error_message=f"Embedding failed: {e}")
            await session.commit()
            logger.error(f"Embedding failed for {filename}: {e}")
            return {
                "success": False,
                "filename": filename,
                "error": f"Embedding failed: {e}",
                "duplicate": False,
            }
        chunk_data = [
            {
                "content": chunks[i],
                "chunk_index": i,
                "embedding": embeddings[i],
            }
            for i in range(len(chunks))
        ]
        num_chunks = await chunk_repo.bulk_create(doc.id, chunk_data)
        await doc_repo.update_status(doc.id, "completed", chunk_count=num_chunks)
        await session.commit()

        logger.info(f"Successfully ingested {filename}: {num_chunks} chunks")
        return {
            "success": True,
            "filename": filename,
            "error": None,
            "duplicate": False,
        }

    except Exception as e:
        logger.exception(f"Unexpected error ingesting {filename}: {e}")
        await session.rollback()
        return {
            "success": False,
            "filename": filename,
            "error": str(e),
            "duplicate": False,
        }


async def ingest_files(
    files: list[tuple[str, bytes]],
    session: AsyncSession,
    embedding_provider: EmbeddingInterface,
) -> dict:
    results = []
    for filename, file_bytes in files:
        result = await ingest_single_file(filename, file_bytes, session, embedding_provider)
        results.append(result)
    successful_files = [r["filename"] for r in results if r["success"]]
    failed_files = [r for r in results if not r["success"]]

    if not successful_files and failed_files:
        error_msgs = "; ".join(
            f"{r['filename']}: {r['error']}" for r in failed_files
        )
        return {
            "success": False,
            "message": f"All files failed processing: {error_msgs}",
            "files": [],
        }

    new_count = sum(1 for r in results if r["success"] and not r["duplicate"])
    dup_count = sum(1 for r in results if r["success"] and r["duplicate"])

    parts = []
    if new_count:
        parts.append(f"Successfully ingested {new_count} PDF document(s)")
    if dup_count:
        parts.append(f"{dup_count} duplicate(s) recognized")
    if failed_files:
        parts.append(f"{len(failed_files)} file(s) failed")

    message = ". ".join(parts) + "."

    return {
        "success": True,
        "message": message,
        "files": successful_files,
    }
