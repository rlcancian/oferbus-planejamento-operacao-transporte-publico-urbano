SHELL := /bin/bash

.PHONY: bootstrap postgres-up postgres-down migrate seed doctor dev test-python lint-python web-typecheck web-build smoke

bootstrap:
	bash scripts/dev-bootstrap.sh

postgres-up:
	docker compose --env-file .env -f infra/dev/compose.yml up -d postgres

postgres-down:
	docker compose --env-file .env -f infra/dev/compose.yml down

migrate:
	set -a; source .env; set +a; source .venv/bin/activate; python -m alembic upgrade head

seed:
	set -a; source .env; set +a; source .venv/bin/activate; python scripts/dev_seed.py

doctor:
	bash scripts/dev-doctor.sh

dev:
	bash scripts/dev-run.sh

test-python:
	source .venv/bin/activate; pytest -q packages/oferbus-db/tests packages/oferbus-jobs/tests packages/oferbus-ai/tests apps/api/tests apps/worker/tests reference-core/tests

lint-python:
	source .venv/bin/activate; ruff check --select E9,F63,F7,F82 apps packages reference-core scripts

web-typecheck:
	npm run web:typecheck

web-build:
	npm run web:build

smoke:
	set -a; source .env; set +a; source .venv/bin/activate; python scripts/integration_smoke.py --api-url "$${OFERBUS_API_URL:-http://127.0.0.1:8010}"
