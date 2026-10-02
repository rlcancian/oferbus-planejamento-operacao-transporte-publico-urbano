#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0
check_cmd() {
  local label="$1"
  local cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "PASS  $label: $(command -v "$cmd")"
  else
    echo "FAIL  $label: $cmd not found"
    fail=1
  fi
}

check_cmd "Node.js" node
check_cmd "npm" npm
check_cmd "curl" curl

if [[ -x .venv/bin/python ]]; then
  echo "PASS  Python venv: $(.venv/bin/python --version 2>&1)"
else
  echo "FAIL  Python venv: .venv/bin/python not found; run make bootstrap"
  fail=1
fi

if [[ -f .env ]]; then
  echo "PASS  environment file: .env"
  set -a
  source .env
  set +a
else
  echo "FAIL  environment file: .env not found"
  fail=1
fi

if [[ -x .venv/bin/python && -f .env ]]; then
  if .venv/bin/python - <<'PY'
from oferbus_db import check_database
status = check_database()
print(f"PASS  PostgreSQL: {status['database']} · server {status['server_version']} · migration {status['migration']}")
if status['migration'] != '0004_planning_inputs':
    raise SystemExit(f"expected migration 0004_planning_inputs, got {status['migration']}")
PY
  then
    :
  else
    echo "FAIL  PostgreSQL readiness/migration check"
    fail=1
  fi
fi

if (( fail != 0 )); then
  echo "OferBus development doctor found problems." >&2
  exit 1
fi

echo "OferBus development environment is ready."
