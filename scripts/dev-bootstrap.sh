#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python_supported() {
  "$1" -c 'import sys; raise SystemExit(0 if (3, 12) <= sys.version_info[:2] < (3, 15) else 1)' >/dev/null 2>&1
}

if [[ -n "${PYTHON_BIN:-}" ]]; then
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 || ! python_supported "$PYTHON_BIN"; then
    echo "ERROR: PYTHON_BIN=$PYTHON_BIN is unavailable or outside the supported range Python >=3.12,<3.15." >&2
    exit 1
  fi
else
  PYTHON_BIN=""
  for candidate in python3.13 python3.12 python3.14 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && python_supported "$candidate"; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
  if [[ -z "$PYTHON_BIN" ]]; then
    echo "ERROR: OferBus requires Python >=3.12,<3.15. Install Python 3.12, 3.13 or 3.14, or set PYTHON_BIN explicitly." >&2
    exit 1
  fi
fi

echo "Using Python: $($PYTHON_BIN --version 2>&1) ($PYTHON_BIN)"

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: Node.js >=22 and npm >=10 are required." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Review local credentials before production use."
fi

if [[ ! -d .venv ]]; then
  if ! "$PYTHON_BIN" -m venv .venv; then
    echo "ERROR: could not create .venv with $PYTHON_BIN." >&2
    echo "On Ubuntu, install the matching venv package (for example: sudo apt install python3.12-venv) and run make bootstrap again." >&2
    exit 1
  fi
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  -e './reference-core' \
  -e './packages/oferbus-core[dev]' \
  -e './packages/oferbus-db[dev]' \
  -e './packages/oferbus-jobs[dev]' \
  -e './packages/oferbus-ai[dev]' \
  -e './apps/api[dev]' \
  -e './apps/worker[dev]' \
  'ruff>=0.11,<1'

npm install

echo
echo "OferBus bootstrap complete."
echo "Next: make postgres-up   # or start your native PostgreSQL"
echo "      make migrate"
echo "      make seed"
echo "      make dev"
