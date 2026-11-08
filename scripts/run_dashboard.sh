#!/usr/bin/env bash
# Run the BEN Engine dashboard (simulation mode, no hardware needed).
# Usage: scripts/run_dashboard.sh [port]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-${BEN_PORT:-8080}}"
export PYTHONPATH="$HERE/software${PYTHONPATH:+:$PYTHONPATH}"
echo "BEN Engine dashboard -> http://0.0.0.0:${PORT}/  (API docs at /docs)"
exec python -m uvicorn ben_engine.api:app --host 0.0.0.0 --port "$PORT" "${UVICORN_ARGS:-}"
