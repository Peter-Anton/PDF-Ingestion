# PDF Ingestion & Semantic Search API

A containerised microservice that ingests PDF documents, generates vector embeddings with FastEmbed, stores them in PostgreSQL with [pgvector](https://github.com/pgvector/pgvector), and exposes a semantic search endpoint.

---

## Architecture

```
┌──────────┐  PDF upload   ┌──────────────┐  embeddings   ┌─────────┐
│  Client  │ ────────────► │  FastAPI App  │ ────────────► │ FastEmbed│
└──────────┘               │  (uvicorn)   │               │  (LLM)  │
                           └──────┬───────┘               └─────────┘
                                  │
                           store chunks + vectors
                                  │
                           ┌──────▼───────┐
                           │  PostgreSQL   │
                           │  + pgvector   │
                           └──────────────┘
```

| Component  | Purpose                                          |
|------------|--------------------------------------------------|
| **FastAPI** | REST API — ingest PDFs, semantic search          |
| **FastEmbed** | In-process `BAAI/bge-small-en-v1.5` model (384-dim) |
| **PostgreSQL + pgvector** | Document & chunk storage with cosine similarity search |
| **Alembic** | Database schema migrations                       |

---

## Project Structure

```
brightskies/
├── orchestrate.sh             # Start / terminate the full stack
├── init-db.sh                 # PostgreSQL init script (pgvector + pgcrypto)
├── swagger.yaml               # OpenAPI 3.0 specification
├── readme.md                  # This file
├── docker/
│   ├── Docker-compose.yml     # Service definitions (app, postgres)
│   ├── Dockerfile             # App container build
│   ├── .env                   # Environment variables
│   ├── requirements.txt       # Python dependencies
│   └── data/                  # Mounted volume for directory-based ingestion
├── src/
│   ├── main.py                # FastAPI app entry point & lifespan
│   ├── database.py            # Async DB session dependency
│   ├── exceptions.py          # Custom exception classes
│   ├── helpers/
│   │   └── config.py          # Pydantic Settings (env-driven config)
│   ├── routes/
│   │   ├── base.py            # GET /api/v1/ — health / welcome
│   │   ├── ingest.py          # POST /api/v1/ingest/ — PDF ingestion
│   │   ├── search.py          # POST /api/v1/search/ — semantic search
│   │   └── schemas/           # Pydantic request/response models
│   ├── controllers/
│   │   ├── ingest_controller.py   # Ingestion orchestration logic
│   │   └── search_controller.py   # Search orchestration logic
│   ├── services/
│   │   ├── pdf_extractor.py       # PDF text extraction (PyMuPDF)
│   │   ├── chunker.py             # Text chunking (langchain splitters)
│   │   ├── hashing.py             # SHA-256 deduplication
│   │   ├── vector_search.py       # pgvector similarity search
│   │   └── embedding/             # Embedding provider abstraction
│   │       ├── EmbeddingInterface.py
│   │       ├── EmbeddingProviderFactory.py
│   │       └── providers/
│   │           └── local_provider.py  # FastEmbed-backed embeddings
│   ├── repositories/
│   │   ├── document_repository.py  # Document CRUD
│   │   └── chunk_repository.py     # Chunk CRUD + vector search
│   └── models/
│       └── db_scheme/pgvector/
│           ├── schemes/            # SQLAlchemy ORM models
│           │   ├── documents.py
│           │   └── chunk.py
│           ├── alembic.ini
│           └── alembic/            # Migration scripts
└── test/
    └── suite.py               # Pytest functional test suite
```

---

## Quick Start

### Prerequisites

- **Docker** ≥ 20.x and **Docker Compose** ≥ 2.x
- Ports `8000` and `5432` available

### 1. Start the Stack

```bash
chmod +x orchestrate.sh
./orchestrate.sh --action start
```

This will:
1. Start **PostgreSQL** (pgvector) and the **FastAPI app**.
2. Download and cache the `BAAI/bge-small-en-v1.5` embedding model on first startup.
3. Run Alembic migrations to create the database schema.
4. Start the API server on `http://localhost:8000`.

The script polls `http://localhost:8000/docs` and exits once the service is ready (or times out after 2 minutes).

### 2. Ingest a PDF

```bash
# Single file
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -F "input=@/path/to/document.pdf"

# The reviewer-friendly root alias is also supported:
curl -X POST http://localhost:8000/ingest/ \
  -F "input=@/path/to/document.pdf"

# Multiple files
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -F "input=@doc1.pdf" \
  -F "input=@doc2.pdf"

# Directory (must be under /data inside the container)
# Place PDFs in docker/data/ then:
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -F "input=/data"
```

### 3. Search

```bash
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How does machine learning work?"}'

# Root alias:
curl -X POST http://localhost:8000/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How does machine learning work?"}'
```

### 4. Stop the Stack

```bash
./orchestrate.sh --action terminate
```

This stops the containers while preserving indexed data and the downloaded
embedding model. To remove stored data explicitly, run:

```bash
docker compose -f docker/Docker-compose.yml down -v
```

---

## API Reference

| Method | Endpoint              | Description                      |
|--------|-----------------------|----------------------------------|
| GET    | `/api/v1/`            | Health check / welcome           |
| POST   | `/api/v1/ingest/`     | Ingest PDF file(s) or directory  |
| POST   | `/api/v1/search/`     | Semantic search over ingested docs |
| GET    | `/docs`               | Swagger UI (auto-generated)      |

Full OpenAPI spec: [`swagger.yaml`](swagger.yaml)

### Ingest Response

```json
{
  "message": "Successfully ingested 2 PDF document(s).",
  "files": ["doc1.pdf", "doc2.pdf"]
}
```

### Search Response

```json
{
  "results": [
    {
      "document": "doc1.pdf",
      "score": 0.89,
      "content": "Vector embeddings represent text in a numerical space..."
    }
  ]
}
```

---

## Edge Case Handling

| Scenario               | Behaviour                                            |
|------------------------|------------------------------------------------------|
| Non-PDF file uploaded  | `400` — "Only PDF files are accepted."               |
| Empty / whitespace query | `400` — "Query cannot be empty."                   |
| Duplicate PDF          | Detected by SHA-256 hash; returns success with note  |
| Image-only PDF         | `400` — "Could not extract any text from the file."  |
| Invalid directory path | `400` — path traversal protection enforced           |
| Embedding failure      | `500` — logged; partial results for multi-file batch |
| Concurrent uploads     | Handled with asyncio semaphore (max 3 parallel)      |

---

## Configuration

All settings are driven by environment variables (see [`docker/.env`](docker/.env)):

| Variable             | Default       | Description                          |
|----------------------|---------------|--------------------------------------|
| `EMBEDDING_MODEL_ID` | `BAAI/bge-small-en-v1.5` | FastEmbed model for embeddings |
| `EMBEDDING_MODEL_SIZE` | `384`       | Embedding vector dimensions          |
| `CHUNK_SIZE`         | `1000`        | Max characters per text chunk        |
| `CHUNK_OVERLAP`      | `100`         | Overlap between adjacent chunks      |
| `TOP_K`              | `5`           | Number of search results to return   |
| `ALLOWED_DIRECTORY`  | `/data`       | Base directory for directory ingestion |

---

## Testing

```bash
# Install test dependencies
pip install pytest requests

# Run the full test suite (service must be running)
pytest test/suite.py -v
```

The test suite covers:
- Service health checks
- Single and multiple PDF ingestion
- Semantic search queries
- Edge cases (invalid files, empty queries, concurrent uploads, duplicates)

---

## Design Decisions

- **Layered architecture** — Routes → Controllers → Services → Repositories, for separation of concerns and testability.
- **pgvector over standalone vector DB** — Keeps the stack simple with a single database for both relational and vector data.
- **FastEmbed for local embeddings** — No external API keys or model server required; runs entirely inside the app container.
- **SHA-256 deduplication** — Prevents re-processing identical documents.
- **Alembic migrations** — Schema changes are version-controlled and reproducible.
- **Async throughout** — FastAPI + asyncpg + SQLAlchemy async for high concurrency.

---

## License

See [LICENSE](LICENSE) for details.
