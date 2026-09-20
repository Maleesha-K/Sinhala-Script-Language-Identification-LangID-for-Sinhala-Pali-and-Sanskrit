#!/usr/bin/env bash
# setup.sh — Bootstrap the LangID stress-test environment
#
# What this does:
#   1. Builds Docker images for the API and Worker
#   2. Starts all containers (Postgres, Redis, MinIO, API, Worker)
#   3. Waits for all services to become healthy
#   4. Runs Alembic migrations inside the API container
#   5. Creates and activates the Python venv with Locust
#
# Usage:
#   cd webapp/testing/stress
#   bash scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRESS_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$STRESS_DIR/docker-compose.stress.yml"
VENV_DIR="$STRESS_DIR/.venv"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     LangID Platform — Stress Test Setup              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. Check prerequisites ────────────────────────────────────────────────────
echo "▶  Checking prerequisites..."

if ! command -v docker &>/dev/null; then
  echo "✗  Docker is not installed. Please install Docker and try again."
  exit 1
fi

if ! docker info &>/dev/null; then
  echo "✗  Docker daemon is not running. Start Docker and try again."
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "✗  Python 3 is not installed."
  exit 1
fi

echo "✓  All prerequisites met."

# ── 2. Build and start Docker stack ──────────────────────────────────────────
echo ""
echo "▶  Building Docker images and starting containers..."
echo "   (This may take a few minutes on the first run)"
echo ""

docker compose -f "$COMPOSE_FILE" up --build -d

# ── 3. Wait for all services to be healthy ────────────────────────────────────
echo ""
echo "▶  Waiting for all services to be healthy..."

wait_healthy() {
  local name="$1"
  local max_attempts=30
  local attempt=0

  while [ $attempt -lt $max_attempts ]; do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null || echo "not_found")
    if [ "$status" = "healthy" ]; then
      echo "   ✓  $name is healthy"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 3
  done

  echo "   ✗  $name did not become healthy within 90 seconds"
  docker logs "$name" --tail 20
  exit 1
}

wait_healthy "stress_postgres"
wait_healthy "stress_redis"
wait_healthy "stress_minio"
wait_healthy "stress_api"

# ── 4. Run database migrations ────────────────────────────────────────────────
echo ""
echo "▶  Running Alembic migrations..."
docker exec stress_api sh -c "uv run alembic upgrade head"
echo "   ✓  Migrations complete"

# ── 5. Set up Locust virtualenv ───────────────────────────────────────────────
echo ""
echo "▶  Setting up Locust virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
  echo "   ✓  Created venv at $VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$STRESS_DIR/requirements.txt"
echo "   ✓  Locust installed"

# ── 6. Create reports directory ───────────────────────────────────────────────
mkdir -p "$STRESS_DIR/reports"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✓  Setup complete! The stack is ready.              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  API is running at:   http://localhost:8000"
echo "  API health check:    http://localhost:8000/health"
echo "  Locust Web UI:       http://localhost:8089"
echo ""
echo "  To start a test (Web UI):"
echo "    source $VENV_DIR/bin/activate"
echo "    locust -f $STRESS_DIR/locustfiles/mixed_workload.py --host=http://localhost:8000"
echo ""
echo "  To run headless (automated):"
echo "    bash $SCRIPT_DIR/run_mixed.sh"
echo ""
echo "  To stop and clean up:"
echo "    bash $SCRIPT_DIR/teardown.sh"
echo ""
