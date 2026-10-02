# OferBus — Phase A Platform Skeleton Plan v0.1

**Status:** active implementation plan  
**Date:** 2026-10-02

## Goal

Establish the minimum production-shaped repository skeleton for OferBus 2026 without prematurely implementing business modules.

## Phase A.1 — skeleton

This subphase creates only:

- root workspace metadata;
- `apps/web` with a minimal Next.js 16 / React 19 shell;
- `apps/api` with a minimal FastAPI application and `/health` endpoint;
- `apps/worker` placeholder documenting the asynchronous execution boundary;
- `packages/oferbus-core` placeholder documenting promotion rules from `reference-core`;
- shared environment placeholders and ignore rules.

It explicitly does **not** yet create:

- PostgreSQL physical migrations;
- SQLAlchemy models;
- authentication or authorization;
- AI provider integration;
- queue/broker implementation;
- March Diagram implementation;
- Three.js views;
- business CRUD or planning endpoints.

## Phase A.2 — persistence baseline

- local PostgreSQL 18 development service;
- SQLAlchemy 2.1 application models derived from the accepted logical model;
- Alembic migration baseline;
- tenant-aware keys and invariant tests;
- database health/readiness checks.

## Phase A.3 — identity and tenancy boundary

- authentication adapter boundary;
- organizations, memberships and roles;
- authorization guards;
- audit identity propagation;
- identity provider remains replaceable.

## Phase A.4 — asynchronous computation boundary

- stable `ComputationRun` lifecycle;
- Python worker interface;
- select queue implementation after comparing operational cost and reliability;
- progress/event transport;
- retry/idempotency rules.

## Phase A.5 — AI and tool boundary skeleton

- provider-neutral LLM adapter;
- structured tool contract;
- command authorization/confirmation policy;
- no direct SQL access from the LLM;
- audit trail for agent actions.

## Phase A.6 — quality gate

- CI for web/API/reference-core;
- lint/type checking/test commands;
- dependency/security checks;
- reproducible local startup documentation.

## Exit criteria for Phase A

Phase A is complete only when web, API and PostgreSQL can run together locally; migrations are reproducible; tenant isolation is testable; a computation job can be submitted through an abstraction; and CI validates the skeleton. No planning-domain completeness is required until Phase B.
