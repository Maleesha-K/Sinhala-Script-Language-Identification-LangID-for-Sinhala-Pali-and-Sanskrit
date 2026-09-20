#!/usr/bin/env bash
# teardown.sh — Stop and clean up the stress-test Docker stack
#
# What this does:
#   1. Stops all stress-test containers
#   2. Removes containers and volumes (fresh state on next setup)
#   3. Optionally removes built images (pass --rmi to force)
#
# Usage:
#   bash scripts/teardown.sh           # Stop + remove containers + volumes
#   bash scripts/teardown.sh --rmi     # Also remove Docker images

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRESS_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$STRESS_DIR/docker-compose.stress.yml"

REMOVE_IMAGES=false
if [[ "${1:-}" == "--rmi" ]]; then
  REMOVE_IMAGES=true
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     LangID Platform — Stress Test Teardown           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

echo "▶  Stopping and removing containers and volumes..."
docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
echo "   ✓  Containers and volumes removed"

if [ "$REMOVE_IMAGES" = true ]; then
  echo ""
  echo "▶  Removing Docker images..."
  docker rmi langid-stress-api:latest langid-stress-worker:latest 2>/dev/null || true
  echo "   ✓  Images removed"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✓  Teardown complete.                               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
