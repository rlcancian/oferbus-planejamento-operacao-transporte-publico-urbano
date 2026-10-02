# ADR-0005 — AI provider and structured tool boundary

**Status:** Accepted  
**Date:** 2026-10-02

## Context

OferBus 2026 is intended to be AI-native: a planner should be able to converse with the system, ask for explanations, request alternatives and eventually operate planning workflows through natural language. At the same time, operational transport results must remain deterministic, reproducible, permission-aware and auditable.

Allowing an LLM to generate arbitrary SQL or directly mutate persistence would bypass domain invariants, tenancy, authorization, provenance and reproducibility. Binding the product to one provider would also create unnecessary architectural coupling.

## Decision

### Provider-neutral LLM adapter

The application depends on the `LLMProvider` contract in `packages/oferbus-ai`, not directly on OpenAI, Anthropic or another vendor SDK. Provider-specific adapters will translate between that contract and vendor APIs when selected.

No provider is selected in Phase A.5. `UnconfiguredLLMProvider` is the explicit baseline state.

### Structured tools only

The LLM may interact with OferBus only through tools registered in `ToolRegistry`. Each tool has:

- a stable name;
- a human-readable description;
- a JSON-schema-shaped input contract;
- one required OferBus permission;
- a risk class;
- a confirmation policy;
- one application/domain handler.

There is deliberately no `sql.execute`, generic database tool, shell tool or unrestricted HTTP tool.

### Authorization follows the human principal

The Copilot never receives broader authority than the authenticated user. A tool executes with a `ToolContext` derived from the active `Principal`, including organization, user, role, permissions and correlation id.

Tenant context is explicit. Tool handlers must scope reads and writes to `organization_id` and use the same domain/application services used by non-AI interfaces.

### Initial confirmation policy

Phase A uses a conservative baseline:

- `read`: no confirmation required;
- `compute`: confirmation required;
- `mutate`: confirmation required;
- `admin`: confirmation required.

Later product modes may support bounded delegation or pre-approved plans, but those modes must remain explicit and auditable rather than silently increasing LLM authority.

### Audit

Tool outcomes are recorded through the existing `audit_event` mechanism with user, organization, role, correlation id, tool name, risk, confirmation policy and argument **keys**. Full prompt/tool payloads are not automatically written to audit storage because they may contain sensitive information.

Future domain-mutating commands must ensure the domain change and its authoritative audit/provenance record are transactionally coherent. The Phase A boundary audit is an additional operational trace, not a substitute for domain provenance.

### LLM does not calculate transport results

The LLM interprets intent, selects tools, explains results and orchestrates workflows. Demand curves, timetable generation, vehicle blocks, fleet, occupancy, costs, optimization and crew scheduling are produced by versioned OferBus computational models and workers.

The same principle applies to future RAG (Retrieval-Augmented Generation): retrieved knowledge may guide explanation and planning, but it does not replace deterministic computation or source provenance.

## Phase A.5 tool catalog

Only capabilities already materialized are exposed:

1. `platform.describe_capabilities` — read-only platform description;
2. `computations.get_status` — organization-scoped computation status;
3. `computations.submit_platform_smoke` — confirmed infrastructure smoke computation.

No transport-planning tool is advertised before its corresponding domain command exists.

## Consequences

Positive:

- provider can be changed without redesigning OferBus domain APIs;
- tenancy and RBAC apply equally to UI and AI actions;
- hallucinated tool names cannot dispatch arbitrary operations;
- direct database access by the LLM is structurally excluded;
- future planning tools can reuse deterministic domain commands;
- human and AI actions share audit/provenance infrastructure.

Costs:

- each useful AI capability needs an explicit structured tool/command;
- confirmation introduces an extra interaction for compute/mutation actions;
- provider adapters and a conversational orchestrator still need implementation after provider selection;
- RAG and long-term conversation memory are not part of Phase A.5.

## Rejected alternatives

### LLM-generated SQL

Rejected because it bypasses authorization, domain invariants, tenant isolation and provenance.

### Provider SDK calls spread throughout endpoints

Rejected because it couples application behavior to one vendor and makes testing/tool governance difficult.

### Pretend chat before a provider exists

Rejected. Phase A.5 exposes an honest `unconfigured` provider state instead of simulating an AI response.
