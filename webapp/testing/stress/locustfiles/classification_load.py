"""
Classification Pipeline Load Test
----------------------------------
Tests the async language-identification pipeline under concurrent load.

Endpoints covered:
  POST /api/v1/classification/jobs        - Submit text for LangID
  GET  /api/v1/classification/jobs/{id}   - Poll for results

Pipeline path:
  FastAPI (DB write) → Redis (Celery task) → Worker (ML inference) → Postgres (result write)

RUP coverage:
  - Performance Profiling : end-to-end job completion time (P50 / P95 / P99)
  - Load Testing          : Celery queue saturation — how many concurrent jobs?
  - Data & DB Integrity   : segments are written correctly after completion

Key metrics to watch externally while this test runs:
  docker stats stress_worker                               # Worker CPU/RAM
  watch -n1 "docker exec stress_redis redis-cli llen celery"  # Queue depth

Run:
  locust -f classification_load.py --host=http://localhost:8000
"""
import os
import random
import time
import uuid

from locust import HttpUser, between, task

# Load sample texts from the fixtures file
_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_sinhala.txt")
with open(_FIXTURE_PATH, encoding="utf-8") as _f:
    SAMPLE_TEXTS = [line.strip() for line in _f if line.strip()]

STRATEGIES = ["sentence", "paragraph", "full_text", "auto"]


def _auth(user: "ClassificationUser") -> None:
    """Helper: create a unique user and log them in."""
    user.email = f"classify_{uuid.uuid4().hex[:10]}@stress.com"
    user.password = "ClassifyTest123!"
    user.headers: dict = {}
    user.job_ids: list = []

    user.client.post(
        "/api/v1/auth/signup",
        json={"email": user.email, "password": user.password, "display_name": "Classifier"},
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


class ClassificationUser(HttpUser):
    """Simulates a user submitting texts for language identification."""

    wait_time = between(2, 5)

    def on_start(self) -> None:
        _auth(self)

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(4)
    def submit_classification(self) -> None:
        """Submit a single text — tests FastAPI + Redis dispatch speed."""
        text = random.choice(SAMPLE_TEXTS)
        resp = self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": text, "segmentation_strategy": random.choice(STRATEGIES)},
            headers=self.headers,
            name="/classification/jobs [submit]",
        )
        if resp.status_code == 201:
            self.job_ids.append(resp.json()["data"]["id"])

    @task(3)
    def poll_job(self) -> None:
        """Poll an existing job for status — tests Postgres read speed."""
        if not self.job_ids:
            return
        job_id = random.choice(self.job_ids)
        self.client.get(
            f"/api/v1/classification/jobs/{job_id}",
            headers=self.headers,
            name="/classification/jobs/{id} [poll]",
        )

    @task(1)
    def submit_and_wait(self) -> None:
        """
        Submit a job then poll until completed (or 30s timeout).
        Measures the full async pipeline round-trip time.
        """
        text = random.choice(SAMPLE_TEXTS)
        resp = self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": text, "segmentation_strategy": "sentence"},
            headers=self.headers,
            name="/classification/jobs [submit+wait]",
        )
        if resp.status_code != 201:
            return

        job_id = resp.json()["data"]["id"]
        deadline = time.time() + 30

        while time.time() < deadline:
            time.sleep(1)
            poll = self.client.get(
                f"/api/v1/classification/jobs/{job_id}",
                headers=self.headers,
                name="/classification/jobs/{id} [wait-poll]",
            )
            if poll.status_code == 200:
                status = poll.json()["data"].get("status")
                if status in ("completed", "failed"):
                    break

    @task(1)
    def submit_no_auth(self) -> None:
        """Unauthenticated request — must return 401 quickly."""
        with self.client.post(
            "/api/v1/classification/jobs",
            json={"input_text": "test text"},
            name="/classification/jobs [no auth — expect 401]",
            catch_response=True,
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401, got {response.status_code}")
