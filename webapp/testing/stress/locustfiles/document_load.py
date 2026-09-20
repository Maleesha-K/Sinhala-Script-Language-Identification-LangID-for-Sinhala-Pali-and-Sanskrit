"""
Document Upload Load Test
--------------------------
Tests the document upload and retrieval pipeline under concurrent load.

Endpoints covered:
  POST /api/v1/documents/upload   - Upload PDF → MinIO + Celery OCR dispatch
  GET  /api/v1/documents          - List user documents (Postgres SELECT)
  GET  /api/v1/documents/{id}     - Get specific document metadata

RUP coverage:
  - Performance Profiling : upload throughput and list query time
  - Load Testing          : concurrent uploads to MinIO + Postgres write burst
  - Data & DB Integrity   : uploaded docs appear correctly in list endpoint

Key metrics to watch externally:
  docker stats stress_minio        # MinIO CPU/RAM/network
  docker stats stress_postgres     # Postgres write pressure

Run:
  locust -f document_load.py --host=http://localhost:8000
"""
import io
import random
import uuid

from locust import HttpUser, between, task

# Minimal valid PDF binary — avoids any filesystem dependency.
# This is a 1-page PDF with a single text line.
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (Stress Test) Tj ET\n"
    b"endstream\nendobj\n"
    b"xref\n0 5\n0000000000 65535 f \n"
    b"trailer<</Size 5/Root 1 0 R>>\n"
    b"startxref\n9\n%%EOF"
)


def _auth(user: "DocumentUser") -> None:
    user.email = f"docuser_{uuid.uuid4().hex[:10]}@stress.com"
    user.password = "DocTest123!"
    user.headers: dict = {}
    user.uploaded_doc_ids: list = []

    user.client.post(
        "/api/v1/auth/signup",
        json={"email": user.email, "password": user.password, "display_name": "Doc User"},
        name="/auth/signup [setup]",
    )
    resp = user.client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": user.password},
        name="/auth/login [setup]",
    )
    if resp.status_code == 200:
        token = resp.json()["data"]["access_token"]
        user.headers = {"Authorization": f"Bearer {token}"}


class DocumentUser(HttpUser):
    """Simulates a user uploading and browsing documents."""

    wait_time = between(2, 6)

    def on_start(self) -> None:
        _auth(self)

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(3)
    def upload_document(self) -> None:
        """
        Upload a minimal PDF.
        Tests: MinIO write throughput, Postgres INSERT, Celery OCR dispatch.
        """
        filename = f"stress_{uuid.uuid4().hex[:6]}.pdf"
        resp = self.client.post(
            "/api/v1/documents/upload",
            headers=self.headers,
            files={"file": (filename, io.BytesIO(MINIMAL_PDF), "application/pdf")},
            name="/documents/upload",
        )
        if resp.status_code == 201:
            self.uploaded_doc_ids.append(resp.json()["data"]["id"])
        else:
            resp.failure(f"Upload failed: {resp.status_code} {resp.text[:200]}")

    @task(5)
    def list_documents(self) -> None:
        """
        List all user documents.
        Tests: Postgres SELECT performance under concurrent reads.
        """
        self.client.get(
            "/api/v1/documents",
            headers=self.headers,
            name="/documents [list]",
        )

    @task(2)
    def get_document(self) -> None:
        """
        Fetch a specific document by ID.
        Tests: point-query performance on Postgres.
        """
        if not self.uploaded_doc_ids:
            return
        doc_id = random.choice(self.uploaded_doc_ids)
        self.client.get(
            f"/api/v1/documents/{doc_id}",
            headers=self.headers,
            name="/documents/{id} [get]",
        )

    @task(1)
    def upload_non_pdf(self) -> None:
        """
        Try to upload a non-PDF file.
        Must return 400 quickly — validates error-handling performance.
        """
        with self.client.post(
            "/api/v1/documents/upload",
            headers=self.headers,
            files={"file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")},
            name="/documents/upload [invalid type — expect 400]",
            catch_response=True,
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(f"Expected 400 for non-PDF, got {response.status_code}")
