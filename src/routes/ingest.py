import os
import logging

from fastapi import APIRouter, Request, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from controllers.ingest_controller import ingest_files
from routes.schemas.ingest import IngestResponse
from helpers.config import get_settings

logger = logging.getLogger(__name__)

ingest_router = APIRouter(tags=["Ingest"])


@ingest_router.post("/ingest/", response_model=IngestResponse)
async def ingest(
    request: Request,
    input: list[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    embedding_provider = request.app.state.embedding_client
    files_to_process: list[tuple[str, bytes]] = []
    if input and isinstance(input, list) and len(input) > 0:
        first = input[0]
        if first.filename and first.size is not None:
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
            return await _handle_directory_input(
                first, db, embedding_provider, settings
            )
    else:
        form = await request.form()
        input_value = form.get("input")

        if input_value and isinstance(input_value, str):
            # Directory path string
            dir_path = input_value.strip()
            return await _process_directory(
                dir_path, db, embedding_provider, settings
            )

        return JSONResponse(
            status_code=400,
            content={"error": "No input provided. Send PDF file(s) or a directory path."},
        )

    # Process files
    result = await ingest_files(files_to_process, db, embedding_provider)

    if not result["success"]:
        return JSONResponse(
            status_code=400,
            content={"error": result["message"]},
        )

    return IngestResponse(
        message=result["message"],
        files=result["files"],
    )


async def _handle_directory_input(upload_file, db, embedding_provider, settings):
    """Handle when the input is a directory path sent as a form string."""
    try:
        content = await upload_file.read()
        dir_path = content.decode("utf-8").strip()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid directory path."},
        )

    return await _process_directory(dir_path, db, embedding_provider, settings)


async def _process_directory(
    dir_path: str,
    db: AsyncSession,
    embedding_provider,
    settings,
):
    """
    Process all PDF files in a directory.
    Validates the path is within the allowed base directory.
    """
    allowed_base = settings.ALLOWED_DIRECTORY

    # Path traversal protection
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

    result = await ingest_files(files_to_process, db, embedding_provider)

    if not result["success"]:
        return JSONResponse(
            status_code=400,
            content={"error": result["message"]},
        )

    return IngestResponse(
        message=result["message"],
        files=result["files"],
    )
