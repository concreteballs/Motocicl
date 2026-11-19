# Motocicl — Render deployment readiness audit

**Review date:** 2026-11-19  
**Repository / branch:** `concreteballs/Motocicl` / `main`  
**Scope:** read-only source and deployment-definition inspection. No database, secrets, queue, Render settings or production resources were changed.

## Executive result

**Deployment readiness: BLOCKED — do not create a Render service yet.**

The repository contains substantial durable orchestration primitives, but the inspected main branch does not yet provide a verified always-on worker process that Render can start safely. The existing worker class is deliberately single-step and requires an externally constructed handler registry. The repository's documented session-independence and live provider orchestration requirements are not yet fully implemented or demonstrated.

This is a source audit, not a claim about live Supabase state or any running service.

## Verified implementation

- `src/motocicl/automation/worker.py` defines `WorkerRunner` and `run_once()`. Its module documentation explicitly says it does not start a background loop or select a provider; deployment must construct the runner and call `run_once()`.
- The runner supports bounded task claiming, recovery maintenance, leases, checkpoints, task handlers, controlled outcomes, optional evidence-backed provider reconciliation and Council suspend/resume.
- `src/motocicl/automation/postgres_store.py` contains PostgreSQL-backed queue, lease, checkpoint, recovery, provider reservation and Council resume persistence operations. The store does not create tables implicitly; schema is managed by ordered SQL migrations.
- `src/motocicl/automation/checkpoints.py`, provider budgeting/limits, payload chunking, provider contracts and browser-agent envelope validation are present.
- A Gemini `generateContent` adapter exists and persists successful responses through an artifact-store interface. The OpenAI adapter inspected is for retrieval/reconciliation of an existing Responses object, not a generation dispatcher.
- `pyproject.toml` defines a Python 3.11+ package with `psycopg[binary]` as its runtime dependency and pytest as the test extra.
- `.github/workflows/tests.yml` currently runs package installation and unit tests only.

## Deployment blockers

### 1. No verified long-running process entrypoint

- `WorkerRunner.run_once()` handles at most one task and returns.
- The checked paths did not contain `scripts/run_cycle_worker.py`, `scripts/run_worker.py`, `Dockerfile`, `render.yaml` or `Procfile`.
- The runner needs a concrete store, a stable worker identity and a mapping of task types to production handlers. No verified deployment composition root was found in the inspected paths.
- Therefore there is no evidence-backed Render Start Command yet. Do not substitute a loop around `run_once()` without defining graceful shutdown, lease renewal during long handlers, polling/backoff, signal handling and concurrency semantics.

### 2. Session independence is not complete

The cycle status ledger explicitly marks checkpoint persistence as an initial primitive, while automatic context-budget monitoring/rollover, worker restart recovery and model-call idempotency/reconciliation end-to-end acceptance remain unimplemented or undemonstrated. The session-independence protocol itself is labelled an approved requirement with runtime implementation planned.

### 3. Provider execution is not production-wired

The repository has useful provider contracts and individual adapter code, but the inspected source does not establish a complete production dispatcher that:
- loads verified provider profiles and global/task budgets;
- reserves capacity before every call;
- selects a concrete adapter and performs a bounded request;
- persists full response artifacts;
- reconciles ambiguous outcomes; and
- resumes the task from durable evidence.

The cycle status ledger reports zero provider profiles and zero global budget rows in its referenced Supabase project at the time of that status snapshot. It says the admission path fails closed until explicit global daily/monthly limits are configured. Treat that as a repository-recorded status, not a fresh live database check.

### 4. Council Gateway contract is not ready for a live connection

The Motocicl Gateway document is a requirements/ownership contract and explicitly says it is not evidence of a completed live application API. The expected `schemas/council-api-v1.schema.json` was not present at the checked path. Engineering Core owns the client/result adapter; Motocicl owns orchestration. Before E2E, reconcile the exact schema, authentication, request/session/parent-task identities, result artifact format, retry and resume semantics across both repositories and the application API.

### 5. CI does not yet prove deployment readiness

The current Motocicl workflow only installs the package and runs pytest. It does not build a container, validate a Render start command, run a PostgreSQL service integration test, or exercise a long-running worker's restart/shutdown behaviour. The migration ledger reports an earlier passing unit-test run (227 tests), but that is not a live runtime acceptance test.

## Render service decision

| Render type | Decision for Motocicl now | Reason |
|---|---|---|
| Static Site | Not selected | No verified frontend target identified in this audit |
| Free Web Service | Not selected | Sleeping/ephemeral demo service does not solve durable orchestration |
| Background Worker | **Blocked** | No verified long-running entrypoint or production handler composition |
| Private Service | Defer | No verified internal service boundary requiring it |
| Cron Job | Defer | Must not become a substitute for the durable cycle scheduler |
| Workflow | Defer | No accepted task adapter or integration tests yet |
| Postgres / Key Value | Do not provision | Existing PostgreSQL/Supabase ownership must be reconciled first; free data services are not authoritative stores |
| Sandbox Group | Defer | Beta and isolation policy not yet designed |

## Required work before a Render deployment proposal

1. Inspect the complete current source tree and identify every registered task type, task handler, script and migration dependency.
2. Implement a Motocicl-owned runtime composition module: validated environment configuration, database connection, durable store, explicit handler registry, worker identity and a controlled long-running process loop.
3. Define graceful shutdown and lease behaviour for long-running tasks; test process termination, lease expiry, restart recovery, duplicate delivery, cancellation and concurrent workers against real PostgreSQL.
4. Complete the provider dispatch/admission path and configure verified provider profiles and explicit budgets only in an approved non-production/staging environment.
5. Reconcile the Council Gateway schema and run contract tests across Motocicl, Engineering Core and the application API.
6. Add a reproducible container build and CI checks for the exact production start command. Keep secrets out of source and image layers.
7. Only after the above acceptance tests pass, prepare a Render Background Worker Blueprint and a cost estimate. Provisioning remains a separate approval.

## Change-control boundary

No migrations were applied, no Supabase rows were changed, no secrets were created or edited, no queue jobs were submitted or requeued, and no Render service or paid resource was created.
