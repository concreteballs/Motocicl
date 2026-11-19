# Repository boundaries — Motocicl

## Motocicl owns

- Autonomous cycle orchestration and lifecycle: durable queue, scheduler/worker, leases, checkpoints, retries, recovery, pause/resume and bounded execution.
- Model-provider adapters, provider limits/budgets/reservations/reconciliation and payload chunking.
- CI event/log ingestion, diagnosis, repair proposals and patch-candidate generation as cycle capabilities.
- Cycle-level observability, evidence audit, roadmap auditor, session independence and browser-agent feedback transport.
- The versioned cross-repository contract used to coordinate engineering tasks.

## YJ64-Engineering-Core owns

- Engineering domain modules, physics/CAD/materials/chemistry/economics and specialist solvers.
- Engineering task handlers, domain validation, calculations, artifact production and discipline-specific acceptance criteria.
- A narrow Council Gateway client/result adapter and parent-task integration; no second autonomous scheduler or provider runtime.

## Application ownership

The YJ-64 application owns its internal Council engine, model routing, participants, dialogue/session state, Consensus/Critique lifecycle and private voting/rating data. Neither Motocicl nor Engineering Core duplicates that engine.

## Shared contracts

Motocicl owns the canonical, versioned cross-repository Council API contract in `schemas/council-api-v1.schema.json`. Engineering Core retains a compatibility snapshot for its narrow Gateway adapter; update the canonical schema first and synchronize the snapshot in the same coordinated change. The YJ-64 application owns and must implement the Council API service and internal Council engine; schema ownership does not transfer service ownership.

Cross-disciplinary evidence, provenance, identity, task handoff and decision-integrity rules are shared interfaces. Motocicl enforces orchestration-level gates; Engineering Core must provide domain evidence and report limitations. A discipline passing its own checks is not by itself proof of whole-system acceptability.

## Documentation source of truth

- Cycle execution and lifecycle documents: this repository.
- Engineering programme, discipline roadmaps and implementation status: Engineering Core.
- Council Gateway API contract: versioned shared interface; Engineering Core documents its client, Motocicl documents its caller/orchestration behaviour.
- Shared observability and evidence schemas: coordinated contract; each repository documents its own producer/consumer implementation.

## Migration policy

The initial extraction intentionally does not copy legacy operational workflows or old CI history. Motocicl starts a fresh build/CI history. Legacy code and documentation remain in Engineering Core's Git history for traceability; cycle work must not continue there.
