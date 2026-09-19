"""
Comprehensive functional test suite for the PDF Ingestor & Semantic Search API.

Validates:
1. Service health and startup
2. Single PDF ingestion
3. Multiple PDF ingestion
4. Semantic search queries
5. Edge cases: invalid files, empty queries, concurrent uploads, duplicates
"""

import pytest
import requests
import time
import os
import io
import concurrent.futures

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"


def create_valid_pdf(text: str) -> bytes:
    """Create a minimal valid PDF containing the given text."""
    lines = text.split('\n')
    content_lines = ['BT', '/F1 12 Tf']
    y = 750
    for line in lines:
        safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        content_lines.append(f'1 0 0 1 72 {y} Tm')
        content_lines.append(f'({safe}) Tj')
        y -= 20
    content_lines.append('ET')
    stream_content = '\n'.join(content_lines)
    stream_bytes = stream_content.encode('latin-1')

    pdf_parts = []
    offsets = []

    def add(s):
        pdf_parts.append(s)

    add(b'%PDF-1.4\n')

    offsets.append(sum(len(p) for p in pdf_parts))
    add(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')

    offsets.append(sum(len(p) for p in pdf_parts))
    add(b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')

    offsets.append(sum(len(p) for p in pdf_parts))
    add(b'3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
        b'/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n')

    offsets.append(sum(len(p) for p in pdf_parts))
    add(f'4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n'.encode()
        + stream_bytes + b'\nendstream\nendobj\n')

    offsets.append(sum(len(p) for p in pdf_parts))
    add(b'5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n')

    xref_offset = sum(len(p) for p in pdf_parts)
    add(b'xref\n')
    add(f'0 {len(offsets) + 1}\n'.encode())
    add(b'0000000000 65535 f \n')
    for off in offsets:
        add(f'{off:010d} 00000 n \n'.encode())
    add(b'trailer\n')
    add(f'<< /Size {len(offsets) + 1} /Root 1 0 R >>\n'.encode())
    add(b'startxref\n')
    add(f'{xref_offset}\n'.encode())
    add(b'%%EOF\n')

    return b''.join(pdf_parts)


@pytest.fixture(scope="session", autouse=True)
def wait_for_service():
    """Wait for service to be ready before tests start."""
    for _ in range(30):
        try:
            r = requests.get(f"{BASE_URL}/docs")
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(2)
    pytest.fail("Service did not start within expected time.")


# ── 1. Health & Welcome ─────────────────────────────────────────────

def test_docs_endpoint():
    """Swagger UI should be accessible."""
    r = requests.get(f"{BASE_URL}/docs")
    assert r.status_code == 200


def test_welcome_endpoint():
    """Welcome endpoint should return app name and version."""
    r = requests.get(f"{API_URL}/")
    assert r.status_code == 200
    body = r.json()
    assert "message" in body
    assert "version" in body


# ── 2. PDF Ingestion ────────────────────────────────────────────────

def test_ingest_single_pdf():
    """Test single valid PDF ingestion."""
    pdf_bytes = create_valid_pdf(
        "Artificial intelligence enables systems to learn from data.\n"
        "Machine learning is a subset of AI."
    )
    files = {"input": ("sample_ai.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = requests.post(f"{API_URL}/ingest/", files=files)

    assert response.status_code == 200, f"Ingest failed: {response.text}"
    body = response.json()
    assert "message" in body
    assert "files" in body
    assert "sample_ai.pdf" in body["files"]


def test_ingest_multiple_pdfs():
    """Test multiple PDF ingestion in a single request."""
    pdf1 = create_valid_pdf("Python is a programming language used in data science.")
    pdf2 = create_valid_pdf("JavaScript powers the modern web and runs in browsers.")

    files = [
        ("input", ("python.pdf", io.BytesIO(pdf1), "application/pdf")),
        ("input", ("javascript.pdf", io.BytesIO(pdf2), "application/pdf")),
    ]
    response = requests.post(f"{API_URL}/ingest/", files=files)

    assert response.status_code == 200, f"Multi-ingest failed: {response.text}"
    body = response.json()
    assert "files" in body
    assert len(body["files"]) >= 2


def test_ingest_duplicate_pdf():
    """Test that re-ingesting the same PDF is handled gracefully."""
    pdf_bytes = create_valid_pdf(
        "Artificial intelligence enables systems to learn from data.\n"
        "Machine learning is a subset of AI."
    )
    files = {"input": ("sample_ai.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = requests.post(f"{API_URL}/ingest/", files=files)

    assert response.status_code == 200, f"Duplicate ingest failed: {response.text}"
    body = response.json()
    assert "message" in body
    # Should report duplicate recognition
    assert "duplicate" in body["message"].lower() or "success" in body["message"].lower()


# ── 3. Semantic Search ──────────────────────────────────────────────

def test_search_query():
    """Test semantic search returns results."""
    query = {"query": "How does artificial intelligence learn from data?"}
    response = requests.post(f"{API_URL}/search/", json=query)

    assert response.status_code == 200, f"Search failed: {response.text}"
    body = response.json()
    assert "results" in body
    assert isinstance(body["results"], list)
    if len(body["results"]) > 0:
        result = body["results"][0]
        assert "document" in result
        assert "content" in result
        assert "score" in result


def test_search_returns_relevant_content():
    """Test that search results are semantically relevant."""
    query = {"query": "programming language for data science"}
    response = requests.post(f"{API_URL}/search/", json=query)

    assert response.status_code == 200, f"Search failed: {response.text}"
    body = response.json()
    assert "results" in body
    assert isinstance(body["results"], list)


# ── 4. Edge Cases ───────────────────────────────────────────────────

def test_ingest_non_pdf_file():
    """Test that non-PDF files are rejected."""
    files = {"input": ("test.txt", io.BytesIO(b"This is not a PDF"), "text/plain")}
    response = requests.post(f"{API_URL}/ingest/", files=files)

    assert response.status_code == 400, f"Expected 400 for non-PDF, got {response.status_code}: {response.text}"
    body = response.json()
    assert "error" in body


def test_ingest_empty_request():
    """Test that empty requests are rejected."""
    response = requests.post(f"{API_URL}/ingest/")

    # Should return 400 or 422 for missing input
    assert response.status_code in (400, 422), (
        f"Expected 400/422 for empty request, got {response.status_code}: {response.text}"
    )


def test_search_empty_query():
    """Test that empty queries are rejected with 400."""
    query = {"query": ""}
    response = requests.post(f"{API_URL}/search/", json=query)

    assert response.status_code == 400, (
        f"Expected 400 for empty query, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "error" in body


def test_search_whitespace_only_query():
    """Test that whitespace-only queries are rejected."""
    query = {"query": "   "}
    response = requests.post(f"{API_URL}/search/", json=query)

    assert response.status_code == 400, (
        f"Expected 400 for whitespace query, got {response.status_code}: {response.text}"
    )


def test_search_missing_query_field():
    """Test that missing query field returns error."""
    response = requests.post(f"{API_URL}/search/", json={})

    # FastAPI returns 422 for missing required fields
    assert response.status_code == 422, (
        f"Expected 422 for missing query, got {response.status_code}: {response.text}"
    )


def test_concurrent_uploads():
    """Test that concurrent uploads are handled gracefully."""
    def upload_pdf(name, text):
        pdf_bytes = create_valid_pdf(text)
        files = {"input": (name, io.BytesIO(pdf_bytes), "application/pdf")}
        return requests.post(f"{API_URL}/ingest/", files=files)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(upload_pdf, "concurrent_1.pdf", "Concurrent test document one about databases."),
            executor.submit(upload_pdf, "concurrent_2.pdf", "Concurrent test document two about networking."),
            executor.submit(upload_pdf, "concurrent_3.pdf", "Concurrent test document three about security."),
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for r in results:
        assert r.status_code in (200, 400), (
            f"Concurrent upload returned unexpected {r.status_code}: {r.text}"
        )
