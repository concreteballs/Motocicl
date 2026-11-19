# Resolution of the two pending extraction reviews

Date: 2026-11-19

## 1. Council API v1 schema ownership — resolved

The canonical, versioned `yj64.council-api.v1` JSON Schema is owned by **Motocicl** as the cross-repository orchestration contract. Motocicl owns the caller-side lifecycle and the versioned boundary used by the autonomous cycle.

This does **not** transfer ownership of the Council service or its internal engine: the YJ-64 application remains the sole owner and implementer of its native Council engine, API service, model routing, participants, sessions, consensus/critique lifecycle and private voting state. Engineering Core remains a client through its narrow Gateway adapter.

Canonical schema:
- `schemas/council-api-v1.schema.json` in this repository.
- Protocol version: `yj64.council-api.v1`.

The existing Engineering Core schema file is retained as a compatibility snapshot to avoid deleting source material during the extraction. Its `$comment` points to the canonical Motocicl schema. Any protocol change must update the canonical schema first and synchronize the Core snapshot in the same coordinated change. Do not treat either client implementation or the schema proposal as proof that the application API is deployed.

## 2. Supabase integration smoke script — cycle-owned and copied

Read-only source review established that `scripts/verify_supabase_integration.py` checks the autonomous-cycle persistence layer, not Engineering Core domain functionality. Its required tables cover cycle CI events, durable task queue/checkpoints, model request attempts, provider limits/reservations, cycle usage budgets and chunked payload manifests/acknowledgements. Its storage round-trip uses the cycle's immutable private artifact store.

The script has therefore been copied to:
- `scripts/verify_supabase_integration.py` in Motocicl.

The Motocicl copy imports `motocicl.automation.supabase_storage.SupabaseStorageArtifactStore` and identifies Motocicl in its deterministic smoke payload. The Engineering Core source copy is intentionally preserved for traceability and is no longer the execution target for cycle work.

**Execution was not performed.** This is a live integration smoke test: it requires `YJ64_DATABASE_URL`, `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`, reads the configured database and writes then reads a deterministic private-storage artifact. No secrets were inspected or changed, no database or storage requests were made, and no migrations were applied.

## 3. Boundary and safety

- Motocicl owns the canonical cross-repository Council API contract and autonomous-cycle infrastructure.
- Engineering Core owns engineering disciplines and its narrow Council Gateway client/result adapter.
- The YJ-64 application owns the Council service and internal engine.
- No legacy workflows, secrets, live database changes, migrations, queue mutations or deployments were transferred or executed.
- The Engineering Core source copies remain intact pending any separately authorized source cleanup.
