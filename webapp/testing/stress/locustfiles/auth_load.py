"""
Auth Load Test
--------------
Tests the authentication endpoints under concurrent load.

Endpoints covered:
  POST /api/v1/auth/signup    - User registration
  POST /api/v1/auth/login     - Credential authentication
  POST /api/v1/auth/refresh   - Token refresh

RUP coverage:
  - Performance Profiling : baseline response times for auth endpoints
  - Load Testing          : concurrent login storm (spike test)
  - Security Testing      : ensures 401 is returned quickly under load

Run:
  locust -f auth_load.py --host=http://localhost:8000
"""
import uuid
from locust import HttpUser, task, between


class AuthUser(HttpUser):
    """Simulates a user authenticating against the API."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Each virtual user signs up and logs in before running tasks."""
        self.email = f"loadtest_{uuid.uuid4().hex[:10]}@stress.com"
        self.password = "LoadTest123!"
        self.access_token: str = ""
        self.refresh_token: str = ""

        # Sign up
        signup_resp = self.client.post(
            "/api/v1/auth/signup",
            json={
                "email": self.email,
                "password": self.password,
                "display_name": "Load Test User",
            },
            name="/auth/signup [setup]",
        )
        if signup_resp.status_code != 201:
            signup_resp.failure(f"Signup failed: {signup_resp.status_code} {signup_resp.text[:200]}")
            return

        # Login to obtain tokens
        self._do_login()

    def _do_login(self) -> bool:
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/auth/login",
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self.access_token = data.get("access_token", "")
            self.refresh_token = data.get("refresh_token", "")
            return True
        return False

    # ── Tasks ──────────────────────────────────────────────────────────────────

    @task(5)
    def login(self) -> None:
        """Simulate repeated logins — most frequent auth operation."""
        self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/auth/login",
        )

    @task(2)
    def refresh_token_task(self) -> None:
        """Simulate token refresh — periodic, less frequent than login."""
        if not self.refresh_token:
            return
        resp = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token},
            name="/auth/refresh",
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self.access_token = data.get("access_token", self.access_token)
            self.refresh_token = data.get("refresh_token", self.refresh_token)

    @task(1)
    def invalid_login_attempt(self) -> None:
        """
        Simulates credential probing with wrong password.
        The API must return 401 quickly — not hang or 500.
        Marked as 'success' when 401 is received correctly.
        """
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": "notexist@stress.com", "password": "WrongPassword!"},
            name="/auth/login [invalid — expect 401]",
            catch_response=True,
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401 for invalid creds, got {response.status_code}")
