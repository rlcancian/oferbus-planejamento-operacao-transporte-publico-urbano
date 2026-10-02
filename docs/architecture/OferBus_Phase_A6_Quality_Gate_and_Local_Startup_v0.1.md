# OferBus — Phase A.6 Quality Gate and Local Startup v0.1

**Status:** operational runbook  
**Date:** 2026-10-02

## Purpose

Close Phase A with a reproducible development baseline that can be pulled on an Ubuntu workstation and started as a real browser-visible OferBus platform.

Phase A.6 does **not** claim planning-domain completeness. The browser surface at this milestone proves the platform foundation: web, API, PostgreSQL, tenancy boundary, asynchronous worker and AI/tool boundary.

## Required local toolchain

- Git;
- Python 3.13 with `venv` support;
- Node.js 22 or newer;
- npm 10 or newer;
- GNU Make;
- PostgreSQL 18, either:
  - through Docker + Docker Compose; or
  - installed natively on the workstation.

## 1. Pull and bootstrap

From the repository root:

```bash
git switch main
git pull
make bootstrap
```

`make bootstrap`:

1. copies `.env.example` to `.env` only when `.env` does not exist;
2. creates `.venv` using Python 3.13;
3. installs the local Python packages in editable mode;
4. installs the web dependencies with npm;
5. installs the lightweight Python lint gate used by CI.

Real credentials must never be committed. `.env` is ignored by Git.

## 2A. PostgreSQL through Docker Compose

This is the shortest isolated development path:

```bash
make postgres-up
make migrate
make seed
make doctor
```

The Compose service is defined in `infra/dev/compose.yml`. It uses the values in `.env` and persists data in a named Docker volume.

To stop only the PostgreSQL development stack:

```bash
make postgres-down
```

## 2B. Native PostgreSQL alternative

Docker is not required. With a local PostgreSQL server, create a development role and database matching your `.env`. Example for a fresh workstation:

```bash
sudo -u postgres psql
```

Then, inside `psql`, adapt the password to the value stored locally in `.env`:

```sql
CREATE ROLE oferbus LOGIN PASSWORD 'CHANGE_ME_LOCAL_ONLY';
CREATE DATABASE oferbus OWNER oferbus;
\q
```

Then:

```bash
make migrate
make seed
make doctor
```

If the role/database already exist, do not recreate them; only make `DATABASE_URL` in `.env` match the real local configuration.

## 3. What migrations and seed create

`make migrate` applies the Alembic chain through:

```text
0001_foundation
0002_identity_tenancy
0003_async_computation
```

`make seed` creates an idempotent development context with deterministic UUIDs:

- organization `OferBus Development`;
- local development user with subject `dev:rafael`;
- owner membership;
- Phase A development project;
- infrastructure-only scenario;
- scenario revision used by the smoke computation.

It may be run repeatedly without intentionally creating duplicate fixtures.

## 4. Start OferBus

```bash
make dev
```

This starts three processes together:

- FastAPI at `http://127.0.0.1:8010`;
- Python computation worker;
- Next.js at `http://127.0.0.1:3010`.

Useful URLs:

- OferBus web: `http://127.0.0.1:3010`
- FastAPI health: `http://127.0.0.1:8010/health`
- FastAPI readiness: `http://127.0.0.1:8010/ready`
- API documentation: `http://127.0.0.1:8010/docs`
- Copilot boundary status: `http://127.0.0.1:8010/ai/status`

`Ctrl+C` stops web, API and worker. PostgreSQL remains running when using the Docker Compose path until `make postgres-down` is invoked.

## 5. Integrated smoke

With `make dev` running, open a second terminal in the repository and run:

```bash
make smoke
```

The smoke test verifies, through public HTTP boundaries:

1. API health;
2. PostgreSQL readiness and migration state;
3. development identity + organization resolution;
4. AI boundary readiness with direct SQL disabled;
5. allow-listed Copilot tool catalog;
6. confirmed invocation of `computations.submit_platform_smoke`;
7. durable `ComputationRun` creation;
8. worker claim and execution;
9. terminal status `succeeded` with 100% progress.

The smoke computation is infrastructure-only. It is **not** a transport-planning algorithm.

## 6. Quality commands

```bash
make test-python
make lint-python
make web-typecheck
make web-build
```

CI performs the same categories of checks and also runs an integrated PostgreSQL/API/worker/AI-tool smoke against a fresh PostgreSQL 18 service.

## 7. CI quality gates

`.github/workflows/ci.yml` defines three independent jobs:

### Python quality and tests

- package installation consistency;
- `compileall` syntax validation;
- Ruff fatal-error lint rules;
- persistence/jobs/AI/API/worker/reference-core tests;
- Python dependency vulnerability audit.

### Web typecheck and build

- npm installation;
- TypeScript `tsc --noEmit`;
- production `next build`;
- runtime dependency audit at high severity.

### Integrated smoke

- clean PostgreSQL 18 service;
- all Alembic migrations;
- deterministic development seed;
- real FastAPI process;
- real worker process;
- HTTP invocation through the AI tool boundary;
- queue completion verification.

## 8. Exit criteria for Phase A

Phase A is closed when all of the following are true:

- A.1 through A.5 are materialized;
- migrations apply to a real PostgreSQL 18 instance;
- deterministic seed is idempotent;
- API and worker share the same durable run state;
- AI tool boundary can invoke a confirmed computation without direct SQL;
- Python quality/tests pass;
- web typecheck/build pass;
- integrated CI smoke passes;
- the local runbook can be executed on the development workstation and the Next.js OferBus shell opens in a browser.

The final workstation/browser validation is intentionally repeated by the developer even after CI passes, because it validates the actual local Ubuntu environment rather than only GitHub-hosted runners.
