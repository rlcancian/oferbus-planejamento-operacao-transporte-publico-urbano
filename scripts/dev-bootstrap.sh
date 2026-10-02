#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3.13}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN is required (Python 3.13). Set PYTHON_BIN if installed under another name." >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: Node.js >=22 and npm >=10 are required." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Review local credentials before production use."
fi

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  -e './packages/oferbus-db[dev]' \
  -e './packages/oferbus-jobs[dev]' \
  -e './packages/oferbus-ai[dev]' \
  -e './apps/api[dev]' \
  -e './apps/worker[dev]' \
  -e './reference-core' \
  'ruff>=0.11,<1'

npm install

echo
echo "OferBus bootstrap complete."
echo "Next: make postgres-up   # or start your native PostgreSQL"
echo "      make migrate"
echo "      make seed"
echo "      make dev"
