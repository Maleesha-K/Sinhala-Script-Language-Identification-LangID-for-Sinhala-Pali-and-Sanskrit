#!/usr/bin/env bash
# run_mixed.sh — Run the mixed workload stress test headlessly and save reports
#
# Runs the StepLoadShape defined in mixed_workload.py (15 minutes total):
#   Phase 1: Warm-up    10 users @ 2/s  (0–2 min)
#   Phase 2: Normal     50 users @ 5/s  (2–5 min)
#   Phase 3: Peak      100 users @10/s  (5–10 min)
#   Phase 4: Spike     200 users @20/s  (10–12 min)
#   Phase 5: Cool-down  20 users @ 5/s  (12–15 min)
#
# Output: reports/mixed_YYYYMMDD_HHMMSS.html and CSV files
#
# Usage:
#   bash scripts/run_mixed.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRESS_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$STRESS_DIR/.venv"
REPORT_DIR="$STRESS_DIR/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$REPORT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     LangID — Mixed Workload Stress Test              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Duration  : 15 minutes (5 phases)"
echo "  Max users : 200"
echo "  Report    : $REPORT_DIR/mixed_$TIMESTAMP.html"
echo ""

# Verify Locust is installed
if [ ! -f "$VENV_DIR/bin/locust" ]; then
  echo "✗  Locust not found. Run 'bash scripts/setup.sh' first."
  exit 1
fi

# Verify API is up
if ! curl -sf http://localhost:8000/health > /dev/null; then
  echo "✗  API is not running on http://localhost:8000."
  echo "   Run 'bash scripts/setup.sh' to start the stack."
  exit 1
fi

echo "▶  Starting Locust..."
echo ""

"$VENV_DIR/bin/locust" \
  -f "$STRESS_DIR/locustfiles/mixed_workload.py" \
  --host=http://localhost:8000 \
  --headless \
  --run-time=15m \
  --csv="$REPORT_DIR/mixed_$TIMESTAMP" \
  --html="$REPORT_DIR/mixed_$TIMESTAMP.html" \
  --logfile="$REPORT_DIR/mixed_$TIMESTAMP.log"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✓  Test complete!                                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  HTML Report : $REPORT_DIR/mixed_$TIMESTAMP.html"
echo "  Stats CSV   : $REPORT_DIR/mixed_${TIMESTAMP}_stats.csv"
echo "  History CSV : $REPORT_DIR/mixed_${TIMESTAMP}_stats_history.csv"
echo "  Failures CSV: $REPORT_DIR/mixed_${TIMESTAMP}_failures.csv"
echo ""
echo "  Open report : xdg-open $REPORT_DIR/mixed_$TIMESTAMP.html"
echo ""
