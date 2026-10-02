#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Run make bootstrap first." >&2
  exit 1
fi
if [[ ! -d .venv ]]; then
  echo "ERROR: .venv not found. Run make bootstrap first." >&2
  exit 1
fi

NEXT_CLI="$ROOT/node_modules/next/dist/bin/next"
if [[ ! -f "$NEXT_CLI" ]]; then
  echo "ERROR: Next.js CLI not found at $NEXT_CLI. Run make bootstrap first." >&2
  exit 1
fi

set -a
source .env
set +a
source .venv/bin/activate

API_PORT="${API_PORT:-8010}"
WEB_PORT="${WEB_PORT:-3010}"

cleanup() {
  trap - INT TERM EXIT
  for pid in ${API_PID:-} ${WORKER_PID:-} ${WEB_PID:-}; do
    if [[ -n "$pid" ]]; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

python -m uvicorn oferbus_api.main:app --host 127.0.0.1 --port "$API_PORT" --reload &
API_PID=$!

oferbus-worker &
WORKER_PID=$!

(
  cd "$ROOT/apps/web"
  exec node "$NEXT_CLI" dev -H 0.0.0.0 -p "$WEB_PORT"
) &
WEB_PID=$!

echo "OferBus development services started:"
echo "  Web: http://127.0.0.1:${WEB_PORT}"
echo "  API: http://127.0.0.1:${API_PORT}"
echo "  API docs: http://127.0.0.1:${API_PORT}/docs"
echo "Press Ctrl+C to stop web, API and worker."

wait -n "$API_PID" "$WORKER_PID" "$WEB_PID"
echo "One OferBus development process exited; stopping the remaining processes." >&2
exit 1
