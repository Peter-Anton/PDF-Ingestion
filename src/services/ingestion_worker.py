import asyncio
import logging
from dataclasses import dataclass

from services.embedding.EmbeddingInterface import EmbeddingInterface
from controllers.ingest_controller import ingest_single_file

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionJob:
    filename: str
    file_bytes: bytes


class IngestionWorker:
    def __init__(
        self,
        session_factory,
        embedding_provider: EmbeddingInterface,
        worker_count: int,
        queue_size: int,
    ):
        self._session_factory = session_factory
        self._embedding_provider = embedding_provider
        self._worker_count = max(1, worker_count)
        self._queue: asyncio.Queue[IngestionJob] = asyncio.Queue(maxsize=max(1, queue_size))
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._run(), name=f"ingestion-worker-{index}")
            for index in range(self._worker_count)
        ]
        logger.info(
            "Started %s ingestion worker(s) with queue size %s",
            self._worker_count,
            self._queue.maxsize,
        )

    async def submit(self, filename: str, file_bytes: bytes) -> None:
        await self._queue.put(IngestionJob(filename, file_bytes))

    async def stop(self) -> None:
        await self._queue.join()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Stopped ingestion workers")

    async def _run(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                async with self._session_factory() as session:
                    await ingest_single_file(
                        job.filename,
                        job.file_bytes,
                        session,
                        self._embedding_provider,
                    )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Unhandled ingestion worker error for %s", job.filename)
            finally:
                self._queue.task_done()
