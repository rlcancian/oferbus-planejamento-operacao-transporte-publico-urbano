# OferBus — Rematerialization Architecture v0.1

**Status:** arquitetura alvo inicial para o OferBus renascido em 2026.  
**Data:** 2026-10-02.  
**Escopo:** arquitetura de aplicação, fronteiras, stack e plano de materialização.  
**Base:** arqueologia consolidada, reference core executável, matriz de paridade e modelo PostgreSQL v0.1.

## 1. Objetivo do produto

Rematerializar o OferBus como uma plataforma web moderna de planejamento operacional de transporte público urbano para prefeituras, autoridades de transporte, consultorias e empresas operadoras.

A plataforma deve preservar o patrimônio funcional recuperado do OferBus histórico e, ao mesmo tempo, permitir evolução científica e operacional. O novo produto deve tratar o planejamento como uma cadeia integrada:

```text
dados observados
→ modelos temporais
→ especificações de serviço
→ oferta necessária
→ quadro de horários
→ viagens e deslocamentos operacionais
→ vínculos
→ blocos de veículos
→ frota
→ ocupação / nível de serviço
→ indicadores / custos
→ comparação de cenários
→ intervenção do planejador
```

Escala de tripulação, multilinha e otimização fazem parte da trajetória do produto e entram em fases posteriores, sem serem excluídos pela arquitetura inicial.

## 2. Princípios arquiteturais

### 2.1 Núcleo computacional independente da web

Os modelos de demanda, previsão, tempo de viagem, IR, quadro mínimo, retornos, vínculos, frota, ocupação, indicadores e custos não pertencem ao frontend nem à camada HTTP.

Eles formam uma biblioteca Python determinística e versionada, testável sem banco de dados, navegador ou servidor web.

### 2.2 Três famílias computacionais coexistentes

O motor mantém explicitamente:

- `legacy-exact`: comportamento histórico quando reproduzível;
- `normalized`: semântica recuperada com defeitos conhecidos corrigidos;
- `modern`: novos modelos e algoritmos.

Nenhuma modernização deve destruir a possibilidade de comparar resultados com o comportamento histórico.

### 2.3 Modular monolith primeiro

A arquitetura inicial será um **monólito modular**, não um conjunto de microserviços.

Haverá processos separados para web, API e workers, mas o backend é organizado por módulos de domínio e compartilha o mesmo motor computacional e modelo de persistência.

Microserviços somente serão considerados se métricas de escala, isolamento operacional ou organização de equipes justificarem a complexidade.

### 2.4 PostgreSQL como fonte de verdade

PostgreSQL é a persistência transacional do domínio. Arquivos legados não são armazenamento primário.

Dados históricos, relatórios ou exports podem existir como objetos auxiliares, mas o estado operacional autoritativo permanece no banco.

### 2.5 Revisões imutáveis e proveniência

O sistema preserva a linhagem:

```text
Scenario
→ ScenarioRevision
→ ComputationRun
→ PlanRevision
→ ResultSnapshot
```

Recálculo não sobrescreve silenciosamente decisões anteriores.

### 2.6 Edição humana como parte do domínio

O gráfico de marcha é um editor operacional. Toda alteração relevante é um comando de domínio com autoria, timestamp, revisão de origem, validações e efeitos derivados.

## 3. Arquitetura lógica

```text
┌─────────────────────────────────────────────────────────────┐
│                       Browser / PWA                         │
│ Next.js + React + TypeScript                               │
│ dashboards · dados · cenários · gráfico de marcha         │
│ programação de veículos · comparação · relatórios         │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / REST / SSE
┌──────────────────────────────▼──────────────────────────────┐
│                      OferBus API                            │
│ FastAPI                                                     │
│ auth boundary · use cases · validation · authorization     │
│ scenario commands · queries · orchestration                │
└───────────────┬────────────────────────┬────────────────────┘
                │                        │ enqueue
                │                        ▼
                │              ┌──────────────────────┐
                │              │ OferBus Workers      │
                │              │ Celery                │
                │              │ long computations    │
                │              │ optimizer / reports  │
                │              └──────────┬───────────┘
                │                         │
                ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                OferBus Computational Core                  │
│ Python package — deterministic / versioned                 │
│ legacy-exact · normalized · modern                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ PostgreSQL                                                  │
│ domain state · revisions · plans · metrics · audit         │
└─────────────────────────────────────────────────────────────┘

Auxiliary: Redis for job coordination/cache; S3-compatible object storage only
for generated artifacts/import staging when needed.
```

## 4. Technology baseline

Technologies are selected for the 2026 implementation baseline and must be pinned to tested versions when the repository is bootstrapped.

### 4.1 Web frontend

- **Next.js 16** using App Router.
- **React 19.2**.
- **TypeScript 5.x**.
- CSS variables + project-owned CSS/CSS Modules for the product visual language.
- **lucide-react** for iconography.
- Accessible component primitives may use **Radix UI** where useful, without imposing a generic visual identity.
- **TanStack Query** for client-side server-state synchronization where interactive workflows require it.
- **Zustand** is a candidate for transient state of editors such as the gráfico de marcha; domain state remains server-side.
- Forms: React Hook Form + Zod where client validation materially improves UX.

Next.js Server Components are useful for application shell, navigation and read-oriented pages. The highly interactive planning editors remain client components.

### 4.2 Graphs and the March Diagram

The March Diagram is not delegated to a generic chart component.

Initial renderer:

- **SVG** for semantic/vector rendering;
- **D3** utilities for scales, axes, zoom/pan and geometric calculations;
- React owns UI composition and commands;
- a renderer abstraction must allow Canvas/WebGL only if benchmarks with real datasets prove SVG insufficient.

The domain command layer is independent of screen coordinates.

### 4.3 API and application backend

- **Python** as backend/application language.
- **FastAPI** as HTTP API framework.
- **Pydantic** for API contracts and validation.
- OpenAPI is the canonical machine-readable API contract.
- TypeScript API types/client should be generated from OpenAPI rather than manually duplicated.

FastAPI must orchestrate use cases; it must not contain the scientific algorithms themselves.

### 4.4 Computational engine

The existing `reference-core` evolves into a production-quality package tentatively named `oferbus-core`.

Responsibilities:

- deterministic computational models;
- explicit units and validated input structures;
- semantic layer selection;
- model release/version metadata;
- no HTTP dependency;
- no UI dependency;
- no hidden global state;
- database-independent core calculations where feasible.

`reference-core` remains characterization evidence until modules are deliberately promoted.

### 4.5 Persistence

- **PostgreSQL 18** baseline.
- **SQLAlchemy 2.1** for relational mapping/query composition.
- **Alembic** for versioned migrations.
- **psycopg 3** PostgreSQL driver.
- UUID identifiers; PostgreSQL 18 `uuidv7()` may be used after migration/design validation.
- tenant-aware constraints and PostgreSQL Row-Level Security are recommended as defense in depth for organization isolation.

The existing PostgreSQL logical model v0.1 is input to the physical schema; it is not copied blindly into ORM models.

### 4.6 Asynchronous computation

Long-running operations must not occupy HTTP request lifetimes.

Initial stack:

- **Celery 5.x stable** workers;
- **Redis** as broker / short-lived coordination and cache;
- PostgreSQL remains the source of truth for run state and durable results.

Candidate workloads:

- full scenario recomputation;
- enumerative legacy optimizer;
- future modern optimization;
- multilinha planning;
- crew scheduling;
- heavy report generation;
- historical import/migration.

Progress updates to the browser should initially use **Server-Sent Events (SSE)**. WebSockets are reserved for genuinely bidirectional realtime use cases such as future collaborative editing.

### 4.7 Authentication and authorization

The architecture requires OpenID Connect / OAuth 2 compatible authentication and organization-scoped authorization, but the identity provider is not frozen in v0.1.

Reason: municipality/operator deployments may require different SSO, self-hosted or managed identity arrangements.

The application model must support:

- multiple organizations;
- membership and roles;
- project/scenario permissions;
- administrative roles;
- audit trail.

### 4.8 Artifacts and file storage

PostgreSQL persists domain data.

S3-compatible object storage is permitted for non-authoritative binary artifacts such as:

- uploaded legacy packages during migration;
- generated PDF reports;
- exported datasets;
- support bundles;
- large externally sourced attachments.

Local development may use MinIO if this capability becomes necessary.

### 4.9 Quality and testing

Python:

- pytest;
- characterization/golden-master fixtures;
- property/invariant tests where useful;
- deterministic numeric tolerances.

Frontend:

- Vitest;
- React Testing Library;
- Playwright for critical end-to-end flows.

Cross-layer:

- OpenAPI contract checks;
- migration tests;
- end-to-end planning fixtures;
- regression fixtures for `legacy-exact` versus `normalized`.

CI: **GitHub Actions**.

### 4.10 Observability

Baseline:

- structured logs;
- correlation/run IDs;
- computation timing and model-version metadata;
- OpenTelemetry instrumentation;
- error tracking;
- metrics suitable for Prometheus/Grafana-compatible backends.

Specific hosted products are deployment choices, not hard dependencies of the domain.

## 5. Backend module boundaries

Initial modules:

1. `identity` — organizations, users, memberships, authorization boundary;
2. `network` — municipalities, operators, lines, directions, terminals, garages;
3. `fleet` — vehicle types and physical vehicles;
4. `datasets` — observations, monthly demand, imports, provenance;
5. `scenarios` — projects, scenarios, immutable revisions, parameter sets;
6. `models` — model-release catalog and semantic layers;
7. `planning` — orchestration of the computational core;
8. `operations` — trips, movement connections, vehicle blocks;
9. `results` — curves, metrics, costs, snapshots;
10. `editor` — manual plan revisions and domain commands;
11. `optimization` — legacy enumerative search and future algorithms;
12. `reporting` — reports and exports;
13. `audit` — provenance and immutable audit records;
14. `crew` — future module for policies, personnel and scheduling;
15. `multiline` — future orchestration crossing multiple lines.

These are logical modules inside the modular monolith, not independently deployed services.

## 6. Critical user workflows

### 6.1 Create a planning study

```text
Organization
→ Project
→ select/add line(s)
→ bind datasets
→ define scenario revision
→ choose planning/model parameters
→ compute
→ inspect results
```

### 6.2 Inspect and edit the plan

```text
PlanRevision
→ March Diagram
→ select trip/block
→ execute domain command
→ validate consequences
→ create derived PlanRevision
→ recalculate metrics
```

The old behavior of silently mutating the current plan is not reproduced.

### 6.3 Compare alternatives

```text
Scenario A / Revision n
vs
Scenario B / Revision m
→ compare provenance
→ timetable/fleet/service/cost metrics
→ visual overlays and differences
```

### 6.4 Long computation

```text
POST computation run
→ persist queued run
→ enqueue worker
→ worker loads immutable inputs
→ execute exact model releases
→ persist plan/result snapshot
→ stream progress/status to UI
```

## 7. March Diagram command model

The editor should use explicit commands such as:

- `CreateTrip`;
- `DeleteTrip`;
- `MoveTrip`;
- `MoveTripGroup`;
- `ChangeTripKind`;
- `ConnectTrips`;
- `ConnectToStorage`;
- `ConnectToGarage`;
- `DisconnectMovement`;
- `ReassignVehicleBlock`.

Every accepted command records:

- user;
- source plan revision;
- parameters;
- timestamp;
- validation result;
- derived plan revision;
- impacted metrics/blocks where applicable.

Undo/redo is therefore implemented as revision/command semantics rather than mutable browser history only.

## 8. Security and multitenancy

Minimum controls:

- organization boundary on every tenant-owned aggregate;
- tenant-aware database constraints;
- Row-Level Security evaluated for production schema;
- least-privilege service accounts;
- no secrets in repository;
- audit of privileged operations;
- encrypted transport;
- encrypted backups;
- rate limits for expensive computations;
- input size/format validation;
- sandboxed legacy import path;
- LGPD-aware treatment of future crew/personnel information.

## 9. Repository target structure

Proposed monorepo layout:

```text
/
├── apps/
│   ├── web/                 # Next.js / React / TypeScript
│   ├── api/                 # FastAPI application
│   └── worker/              # Celery process/bootstrap
├── packages/
│   ├── oferbus-core/        # deterministic Python computational core
│   └── oferbus-db/          # SQLAlchemy models/repositories/migrations helpers
├── reference-core/          # archaeological executable characterization
├── migrations/              # Alembic migrations
├── docs/
│   ├── archaeology/
│   ├── architecture/
│   ├── computational/
│   ├── decisions/
│   ├── domain/
│   └── persistence/
├── infra/                   # local/dev deployment definitions
└── tests/                   # cross-component/e2e fixtures where appropriate
```

Exact names can change during bootstrap; the separation of responsibilities should not.

## 10. What is deliberately not selected yet

The following remain deployment/product decisions rather than architecture prerequisites:

- managed versus self-hosted OIDC provider;
- cloud/vendor;
- Kubernetes versus simpler container hosting;
- PostGIS activation;
- final PDF/report rendering library;
- Canvas/WebGL March Diagram renderer;
- AI provider/model;
- payment/billing provider if OferBus becomes SaaS.

## 11. AI in OferBus

AI is an optional assistance layer, not the planning authority.

Potential later capabilities:

- explain a scenario/result;
- answer questions about metrics and model provenance;
- assist data validation/import;
- compare scenarios in natural language;
- explain why a plan needs additional fleet;
- detect suspicious data or inconsistent configuration;
- RAG over manuals, methodology and project documentation.

AI must never silently change a timetable, model parameter or operational plan. Mutating actions require explicit commands and audit.

## 12. Materialization plan

### Phase A — Platform skeleton

- monorepo/bootstrap;
- Next.js web shell;
- FastAPI health/API skeleton;
- PostgreSQL development environment;
- SQLAlchemy/Alembic physical schema baseline;
- authentication boundary stub;
- CI.

### Phase B — Core planning vertical slice

Implement one complete workflow:

```text
line + observed trips + planning specification
→ scenario revision
→ computation run
→ minimum timetable
→ trips/connections
→ vehicle blocks
→ fleet
→ occupancy/metrics/cost
→ persisted result
→ web result view
```

Initially use characterized `normalized` models plus selectable `legacy-exact` where ready.

### Phase C — Interactive March Diagram

- read-only renderer first;
- trip inspection;
- zoom/pan/filter;
- command-based editing;
- derived plan revisions;
- undo/redo;
- synchronized vehicle-block view.

### Phase D — Data/forecast analysis

- observed data workflows;
- demand/TPV/IR charts;
- monthly demand and forecasting;
- MPTDC/variable-demand comparison;
- quality diagnostics.

### Phase E — Scenario comparison and reporting

- side-by-side scenario comparison;
- result deltas;
- reports/exports;
- reproducibility/provenance UI.

### Phase F — Optimization

- legacy enumerative search;
- modern optimization interface;
- queued execution and comparison of candidate solutions.

### Phase G — Multiline and crew

Only after targeted archaeology closes the remaining semantics:

- shared line resources;
- transfer/deadhead matrix;
- crew policies;
- crew scheduling and restriction validation;
- modern optimization alternatives.

## 13. First product milestone

The first credible OferBus 2026 milestone is **not** a landing page and not merely CRUD.

It is a web application where an authenticated planner can:

1. create a project and line;
2. load/enter observed operational data;
3. create a scenario;
4. execute the planning engine;
5. see the generated timetable;
6. see vehicle blocks/fleet;
7. inspect occupancy, service and costs;
8. open a read-only March Diagram;
9. compare at least two immutable scenario revisions;
10. reproduce the run from its recorded inputs/model versions.

This milestone proves the product architecture before complex graphical editing and crew scheduling are added.

## 14. Current architecture decision

**Recommended architecture:**

> Next.js/React/TypeScript web application + FastAPI Python modular backend + independent Python OferBus computational core + PostgreSQL + Celery/Redis asynchronous workers, packaged as containers in a monorepo.

This combination preserves the reconstructed scientific/operational core, provides a current web platform, supports heavy deterministic computations outside request lifetimes, and avoids premature microservice complexity.
