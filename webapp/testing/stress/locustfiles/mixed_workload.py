"""
Mixed Workload Stress Test
---------------------------
Primary stress test for the LangID Platform. Combines all user types at
realistic weights to simulate actual production traffic patterns.

Virtual user distribution (by weight):
  ReadHeavyUser      (weight=5) — ~50% of traffic: browse, list, health-check
  ClassificationUser (weight=3) — ~30% of traffic: submit texts, poll jobs
  UploaderUser       (weight=2) — ~20% of traffic: upload PDFs, list documents

Load ramp (StepLoadShape):
  Phase 1 (0–2 min)   : Warm-up      —  10 users
  Phase 2 (2–5 min)   : Normal load  —  50 users
  Phase 3 (5–10 min)  : Peak load    — 100 users
  Phase 4 (10–12 min) : Stress spike — 200 users
  Phase 5 (12–15 min) : Cool-down    —  20 users

RUP coverage:
  - Load Testing          : average and peak workload simulation
  - Performance Profiling : full-system bottleneck detection
  - Failover Testing      : system behaviour when a service is unavailable

Run (automated with step shape):
  locust -f mixed_workload.py --host=http://localhost:8000 --headless --run-time=15m

Run (interactive web UI):
  locust -f mixed_workload.py --host=http://localhost:8000
"""
import io
import os
import random
import time
import uuid

from locust import HttpUser, LoadTestShape, between, task

# ── Fixtures ───────────────────────────────────────────────────────────────────

_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_sinhala.txt")
with open(_FIXTURE_PATH, encoding="utf-8") as _f:
    SAMPLE_TEXTS = [line.strip() for line in _f if line.strip()]

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


# ── Auth helper ────────────────────────────────────────────────────────────────

def _authenticate(user: HttpUser, prefix: str) -> None:
    """Create a unique test user and log them in. Stores headers on the user."""
    user.email = f"{prefix}_{uuid.uuid4().hex[:10]}@stress.com"  # type: ignore[attr-defined]
    user.password = "Stress123!"  # type: ignore[attr-defined]
    user.headers = {}  # type: ignore[attr-defined]

    user.client.post(
        "/api/v1/auth/signup",
        json={
            "email": user.email,
            "password": user.password,
            "display_name": f"Stress {prefix}",
        },
        name="/auth/signup [setup]",
    )
    resp = user.client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": user.password},
        name="/auth/login [setup]",
    )
    if resp.status_code == 200:
        token = resp.json()["data"]["access_token"]
        user.headers = {"Authorization": f"Bearer {token}"}  # type: ignore[attr-defined]


# ── User Classes ───────────────────────────────────────────────────────────────

class ReadHeavyUser(HttpUser):
    """
    Browsing user — primarily reads, rarely submits.
    Represents ~50% of production traffic.
    Bottleneck: Postgres read throughput, auth middleware overhead.
    """

    wait_time = between(1, 4)
    weight = 5

    def on_start(self) -> None:
        _authenticate(self, "reader")

    @task(6)
    def health_check(self) -> None:
        self.client.get("/health", name="/health")

    @task(5)
    def list_documents(self) -> None:
        self.client.get("/api/v1/documents", headers=self.headers, name="/documents [list]")

    @task(3)
    def get_user_profile(self) -> None:
        self.client.get("/api/v1/users/me", headers=self.headers, name="/users/me")

    @task(1)
    def poll_nonexistent_job(self) -> None:
        """Poll a random UUID job — tests 404 handling speed under load."""
        fake_id = uuid.uuid4()
        with self.client.get(
            f"/api/v1/classification/jobs/{fake_id}",
            headers=self.headers,
            name="/classification/jobs/{id} [404]",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Expected 404, got {response.status_code}")


class ClassificationUser(HttpUser):
    """
    Power user submitting texts for language identification.
    Represents ~30% of production traffic.
    Bottleneck: Celery worker CPU (ML inference), Redis queue depth.
    """

    wait_time = between(3, 8)
    weight = 3

    def on_start(self) -> None:
        _authenticate(self, "classifier")
        self.job_ids: list = []

    @task(4)
    def submit_classification(self) -> None:
        text = random.choice(SAMPLE_TEXTS)
        resp = self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": text, "segmentation_strategy": "sentence"},
            headers=self.headers,
            name="/classification/jobs [submit]",
        )
        if resp.status_code == 201:
            self.job_ids.append(resp.json()["data"]["id"])

    @task(5)
    def poll_job(self) -> None:
        if not self.job_ids:
            return
        job_id = random.choice(self.job_ids)
        self.client.get(
            f"/api/v1/classification/jobs/{job_id}",
            headers=self.headers,
            name="/classification/jobs/{id} [poll]",
        )

    @task(1)
    def submit_multi_language_text(self) -> None:
        """Submit a deliberately long mixed-language text."""
        text = " ".join(random.choices(SAMPLE_TEXTS, k=4))
        self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": text, "segmentation_strategy": "auto"},
            headers=self.headers,
            name="/classification/jobs [multi-lang]",
        )


class UploaderUser(HttpUser):
    """
    Document uploader — uploads PDFs and checks status.
    Represents ~20% of production traffic.
    Bottleneck: MinIO write throughput, OCR Celery queue.
    """

    wait_time = between(5, 15)
    weight = 2

    def on_start(self) -> None:
        _authenticate(self, "uploader")
        self.doc_ids: list = []

    @task(2)
    def upload_document(self) -> None:
        filename = f"stress_{uuid.uuid4().hex[:6]}.pdf"
        resp = self.client.post(
            "/api/v1/documents/upload",
            headers=self.headers,
            files={"file": (filename, io.BytesIO(MINIMAL_PDF), "application/pdf")},
            name="/documents/upload",
        )
        if resp.status_code == 201:
            self.doc_ids.append(resp.json()["data"]["id"])

    @task(4)
    def list_documents(self) -> None:
        self.client.get("/api/v1/documents", headers=self.headers, name="/documents [list]")

    @task(1)
    def get_document(self) -> None:
        if not self.doc_ids:
            return
        doc_id = random.choice(self.doc_ids)
        self.client.get(
            f"/api/v1/documents/{doc_id}",
            headers=self.headers,
            name="/documents/{id} [get]",
        )


# ── Load Shape ─────────────────────────────────────────────────────────────────

class StepLoadShape(LoadTestShape):
    """
    Five-phase load ramp that mirrors a real traffic spike:

    Phase 1  (0– 2 min):  Warm-up        10 users  @ 2/s
    Phase 2  (2– 5 min):  Normal load    50 users  @ 5/s
    Phase 3  (5–10 min):  Peak load     100 users  @10/s
    Phase 4 (10–12 min):  Stress spike  200 users  @20/s
    Phase 5 (12–15 min):  Cool-down      20 users  @ 5/s

    After Phase 5, the test stops automatically.
    """

    stages = [
        {"duration": 120,  "users": 10,  "spawn_rate": 2},
        {"duration": 300,  "users": 50,  "spawn_rate": 5},
        {"duration": 600,  "users": 100, "spawn_rate": 10},
        {"duration": 720,  "users": 200, "spawn_rate": 20},
        {"duration": 900,  "users": 20,  "spawn_rate": 5},
    ]

    def tick(self) -> tuple | None:
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None  # All stages done — stop the test
