# ADR-0002 — OferBus application architecture and stack

- **Status:** Accepted for initial materialization
- **Date:** 2026-10-02
- **Refined:** 2026-10-02 after architecture review

## Context

The rematerialized OferBus is an independent B2B web product for municipalities, transit authorities, consultancies and urban public-transport operators. It contains a deterministic/scientific planning core, long-running optimization workloads, a highly interactive March Diagram, future multiline and crew scheduling, multi-user concurrency, multi-tenant isolation and immutable scenario/result provenance.

The product must also be AI-native from inception: a planner can converse with an OferBus Copilot that interprets intent and invokes validated domain tools. The LLM is never the numerical planning authority and never writes SQL directly.

The visual language must be substantially renewed. Precise engineering editors remain 2D where precision matters, while analytical/immersive views may use 3D.

## Decision

The accepted OferBus 2026 architecture is:

- **Web:** Next.js 16.3 Active LTS + React 19.3 + TypeScript 5.x;
- **API/application backend:** Python + FastAPI;
- **computational engine:** independent, deterministic, versioned Python package;
- **database:** PostgreSQL 18.x, with current supported patch releases;
- **database access/migrations:** SQLAlchemy 2.1 + Alembic + psycopg 3;
- **API contract:** OpenAPI with generated TypeScript client/types;
- **2D scientific/operational graphics:** SVG + D3 utilities initially;
- **3D analytical graphics:** Three.js via React Three Fiber where 3D adds analytical value;
- **UI motion:** restrained application-level motion, with a React animation library selected during UI bootstrap;
- **AI:** first-class OferBus Copilot/Planning Agent using provider adapters and structured domain tools;
- **testing:** pytest, frontend unit/component tests and Playwright for critical end-to-end workflows;
- **CI:** GitHub Actions;
- **deployment unit:** containers;
- **architecture style:** modular monolith with separate web/API/worker processes, not microservices.

PostgreSQL is the authoritative domain store. The frontend does not own the database schema. The Python backend is the single application/domain persistence boundary.

The computational engine supports three semantic families:

- `legacy-exact`;
- `normalized`;
- `modern`.

## AI command boundary

The agent architecture is:

```text
User natural language
→ LLM / planning agent
→ structured OferBus tools
→ domain commands / validation
→ OferBus Core and application services
→ PostgreSQL / computation runs
```

The following pattern is explicitly rejected:

```text
LLM → arbitrary SQL → PostgreSQL
```

Mutating AI actions must use the same validated command layer used by the graphical interface and must be auditable. Depending on risk, commands may require explicit user confirmation before execution.

The LLM/provider is deliberately replaceable. OpenAI, Anthropic or future providers can be adapters behind a stable OferBus AI interface.

## 2D and 3D visualization boundary

The March Diagram remains primarily a precise 2D engineering editor. Three-dimensional rendering is intended for analytical views where the extra axis communicates useful information, for example time × route position × occupancy, animated fleet flows or multidimensional scenario comparison.

3D is therefore part of the product vision but must not make core engineering interaction less precise or less accessible.

## Asynchronous jobs

The requirement is accepted: expensive planning, optimization, reporting and future crew-scheduling computations run outside HTTP request lifetimes in Python workers.

The concrete queue/broker implementation is **deferred**. Candidates include:

- Celery + Redis;
- a PostgreSQL-backed Python worker/job mechanism;
- another mature Python-compatible job system demonstrated to fit the operational constraints.

The choice must consider reliability, retries, observability, operational burden on the initial VPS and ability to scale workers independently. PostgreSQL remains authoritative regardless of the selected queue.

## Rationale

Python preserves continuity with the reconstructed executable core and is the natural environment for scientific computation, optimization and AI tooling. FastAPI is kept thin around application use cases rather than embedding planning algorithms in HTTP handlers.

Next.js/React/TypeScript matches the modern web experience required by a rich operational workspace and is also compatible with experience already accumulated in the user's other web systems. The OferBus remains technically independent and is not constrained to copy their backend architecture.

SQLAlchemy is preferred over introducing Prisma into the OferBus backend because the authoritative application backend is Python. Using two independent ORMs against the same production schema would create unnecessary schema ownership and migration ambiguity.

PostgreSQL matches the accepted persistence model and provides strong transactionality, relational integrity and mechanisms for multi-tenant isolation.

A modular monolith minimizes distributed-systems complexity while preserving clear module boundaries. Splitting modules into services is a future scaling decision, not a starting assumption.

## Deferred decisions

This ADR does not yet select:

- final OpenID Connect identity provider;
- exact worker/queue implementation;
- AI provider/model and commercial routing policy;
- cloud/vendor;
- Kubernetes;
- PostGIS activation;
- final PDF/reporting engine;
- exact animation library;
- billing/payment stack;
- future realtime collaborative-editing transport.

## Consequences

Phase A begins with a minimal monorepo skeleton and explicit boundaries. It must not prematurely implement database migrations, auth, AI provider code or a queue before the corresponding subphase is designed and validated.
