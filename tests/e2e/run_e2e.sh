#!/usr/bin/env bash
# Runs the BEN Engine dashboard end-to-end test with Playwright (plain `playwright` module).
# Starts its own uvicorn on a free port, writes screenshots to docs/media/screens and the
# guided-tour frames to docs/media/frames. Exits non-zero on any failed check.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
export PYTHONPATH="$ROOT/software${PYTHONPATH:+:$PYTHONPATH}"
export PYTHON="${PYTHON:-python}"
node -e "require('playwright')" 2>/dev/null || { echo "playwright is not importable by node (npm i -g playwright && npx playwright install chromium)"; exit 2; }
"$PYTHON" -c "import fastapi, uvicorn, ben_engine.api" || { echo "python deps missing (pip install fastapi uvicorn websockets)"; exit 2; }
exec node "$HERE/dashboard.spec.mjs" "$@"
