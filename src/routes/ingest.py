import os
import logging

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse

from routes.schemas.ingest import IngestResponse
from helpers.config import get_settings

logger = logging.getLogger(__name__)

ingest_router = APIRouter(tags=["Ingest"])


@ingest_router.post("/ingest/", response_model=IngestResponse)
async def ingest(
    request: Request,
    input: list[UploadFile] = File(None),
):
    settings = get_settings()
    files_to_process: list[tuple[str, bytes]] = []
    if input and isinstance(input, list) and len(input) > 0:
        first = input[0]
        if first.filename:
            for upload_file in input:
                filename = upload_file.filename or "unknown"
                if not filename.lower().endswith(".pdf"):
                    logger.warning(f"Rejected non-PDF file: {filename}")
                    continue

                file_bytes = await upload_file.read()
                files_to_process.append((filename, file_bytes))

            if not files_to_process:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Only PDF files are accepted."},
                )
        else:
            return await __handle_directory_input(
                first, request.app.state.ingestion_worker, settings
            )
    else:
        form = await request.form()
        input_value = form.get("input")

        if input_value and isinstance(input_value, str):
            dir_path = input_value.strip()
            return await __process_directory(
                dir_path, request.app.state.ingestion_worker, settings
            )

        return JSONResponse(
            status_code=400,
            content={"error": "No input provided. Send PDF file(s) or a directory path."},
        )

    for filename, file_bytes in files_to_process:
        await request.app.state.ingestion_worker.submit(filename, file_bytes)
    return IngestResponse(
        message=f"Successfully queued {len(files_to_process)} PDF document(s) for ingestion.",
        files=[filename for filename, _ in files_to_process],
    )


async def __handle_directory_input(upload_file, ingestion_worker, settings):
    try:
        content = await upload_file.read()
        dir_path = content.decode("utf-8").strip()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid directory path."},
        )

    return await __process_directory(dir_path, ingestion_worker, settings)


async def __process_directory(
    dir_path: str,
    ingestion_worker,
    settings,
):
    allowed_base = settings.ALLOWED_DIRECTORY
    real_path = os.path.realpath(dir_path)
    real_base = os.path.realpath(allowed_base)

    if not real_path.startswith(real_base):
        return JSONResponse(
            status_code=400,
            content={"error": f"Directory must be within {allowed_base}."},
        )

    if not os.path.isdir(real_path):
        return JSONResponse(
            status_code=400,
            content={"error": f"Directory not found: {dir_path}"},
        )

    files_to_process = []
    for filename in sorted(os.listdir(real_path)):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(real_path, filename)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                files_to_process.append((filename, file_bytes))

    if not files_to_process:
        return JSONResponse(
            status_code=400,
            content={"error": "No PDF files found in the specified directory."},
        )

    for filename, file_bytes in files_to_process:
        await ingestion_worker.submit(filename, file_bytes)
    return IngestResponse(
        message=f"Successfully queued {len(files_to_process)} PDF document(s) for ingestion.",
        files=[filename for filename, _ in files_to_process],
    )