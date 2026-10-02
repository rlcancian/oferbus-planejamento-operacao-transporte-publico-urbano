# OferBus worker

This directory is the process boundary for long-running Python computations.

The worker technology is intentionally **not selected in Phase A.1**. The accepted requirement is that planning, optimization, reporting and future crew-scheduling workloads execute outside HTTP request lifetimes while PostgreSQL remains the authoritative source of run state and durable results.

Candidates to evaluate in Phase A.4 include Celery + Redis and a PostgreSQL-backed Python job mechanism.

No business logic belongs in the worker bootstrap. Workers must invoke the same versioned OferBus Core used by synchronous tests and application services.
