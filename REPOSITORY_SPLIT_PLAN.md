# Motocicl — Repository Split and Cycle Extraction Plan

**Status:** initial code extraction and documentation ownership split committed; remaining ambiguous interface items are explicitly listed in the migration ledger  
**Destination repository:** https://github.com/concreteballs/Motocicl  
**Destination branch:** `main`  
**Source repository:** https://github.com/concreteballs/YJ64-Engineering-Core  
**Source branch:** `main`

## 1. Purpose and governing rule

Separate the autonomous YJ64 cycle/Council orchestration from the specialist Engineering Core. Motocicl becomes the owner of the autonomous execution loop and its infrastructure. Engineering Core remains a specialist engineering system and connects to Motocicl/Council through a narrow, versioned API contract.

This file is the migration checklist and source of truth for the repository split. The source repository's existing plans and code must remain intact until the corresponding destination files have been copied, adapted, tested and verified. Do not delete or disable source files during the extraction stage.

## 2. Target ownership

### Motocicl owns
- Durable task queue, task lifecycle, leases, checkpoints, retries and recovery.
- Autonomous scheduler/worker runtime and bounded task execution.
- Model-provider adapters, provider limits, budgets, reservations, payload chunking and ambiguous-call reconciliation.
- CI completion-event ingestion, event deduplication, CI log analysis, bounded repair proposals and patch-generation orchestration.
- Cycle-level observability, artifacts, persistence and operational controls.
- Generic browser-agent feedback/transport into the cycle, plus the versioned message envelope.
- Cycle-specific database migrations, schemas, workflows, scripts and tests.

### Engineering Core owns
- Engineering domain models, specialist solvers, discipline packs, CAD/physics/material/chemistry/economics capabilities.
- Engineering-specific task handlers and domain validation.
- The narrow Council API client/handoff that lets an engineering task request an external Council review and consume its result.
- Engineering Core's own repository test workflow and engineering-specific agent registration/provisioning.
- Engineering-specific documentation and API compatibility tests.

### Application/Council service boundary
The application-side Council API and model-discussion engine remain external to both repositories unless explicitly reassigned. Motocicl is the cycle/orchestration client of that service; Engineering Core is a specialist client. Do not duplicate the Council Engine or application Agent Communication Hub.

## 3. File-by-file extraction inventory

The following inventory is based on the current source tree. During the actual move, re-read each file and its imports before copying; paths may have changed since this plan was written.

### 3.1 Move to Motocicl — cycle runtime and persistence

- `src/yj64_engineering_core/automation/checkpoints.py`
- `src/yj64_engineering_core/automation/ci_fix_proposals.py`
- `src/yj64_engineering_core/automation/ci_log_analysis.py`
- `src/yj64_engineering_core/automation/ci_log_ingestion.py`
- `src/yj64_engineering_core/automation/ci_patch_generation.py`
- `src/yj64_engineering_core/automation/gemini_adapter.py`
- `src/yj64_engineering_core/automation/mock_provider.py`
- `src/yj64_engineering_core/automation/openai_responses.py`
- `src/yj64_engineering_core/automation/payload_chunks.py`
- `src/yj64_engineering_core/automation/postgres_store.py`
- `src/yj64_engineering_core/automation/provider_adapters.py`
- `src/yj64_engineering_core/automation/provider_budget.py`
- `src/yj64_engineering_core/automation/provider_limits.py`
- `src/yj64_engineering_core/automation/provider_reconciliation.py`
- `src/yj64_engineering_core/automation/supabase_storage.py`
- `src/yj64_engineering_core/automation/worker.py`
- `src/yj64_engineering_core/automation/browser_agent_bridge.py` (cycle-facing observer/feedback bridge; verify no Engineering-only imports before moving)
- `scripts/record_ci_completion.py`
- `scripts/run_ci_event_worker.py`
- `scripts/run_ci_fix_proposal_worker.py`
- `scripts/run_ci_log_analysis_worker.py`
- `scripts/run_ci_patch_generation_worker.py`
- `scripts/verify_supabase_integration.py` (move only if its checks are cycle infrastructure, not Engineering-specific)
- `schemas/browser-agent-envelope.schema.json`
- `schemas/council-api-v1.schema.json` (confirm ownership against the deployed API contract before moving; preserve exact version)
- `migrations/0001_autonomous_cycle.sql` through `migrations/0020_ci_fix_proposals.sql` (move as a contiguous ordered history; inspect each migration and its dependencies; do not replay or apply migrations as part of file extraction)
- Tests for the moved cycle components:
  - `tests/test_browser_agent_bridge.py`
  - `tests/test_ci_event_worker.py`
  - `tests/test_ci_fix_proposals.py`
  - `tests/test_ci_log_analysis.py`
  - `tests/test_ci_log_ingestion.py`
  - `tests/test_ci_patch_generation.py`
  - `tests/test_ci_webhook_ingress.py` — **REVIEW_REQUIRED / keep in Engineering Core**: this test exercises the serverless `api/index.py` webhook ingress, not the cycle worker package; it failed collection in Motocicl because that API file is not part of the cycle runtime.
  - `tests/test_direct_ci_persistence.py`
  - `tests/test_gemini_adapter.py`
  - `tests/test_mock_provider_integration.py`
  - `tests/test_observability_events.py`
  - `tests/test_payload_chunk_store.py`
  - `tests/test_payload_chunks.py`
  - `tests/test_postgres_cycle_store.py`
  - `tests/test_provider_adapter_contract.py`
  - `tests/test_provider_attempt_store.py`
  - `tests/test_provider_budget.py`
  - `tests/test_provider_limits.py`
  - `tests/test_provider_reconciliation.py`
  - `tests/test_provider_reconciliation_adapters.py`
  - `tests/test_provider_reservations.py`
  - `tests/test_quota_recovery.py`
  - `tests/test_supabase_storage_artifacts.py`
  - `tests/test_task_checkpoints.py`
  - `tests/test_worker_reconciliation.py`
  - `tests/test_worker_runner.py`

### 3.2 Legacy workflows — intentionally not migrated

The previous Engineering Core workflow YAML and its workflow-run history are **not being ported or reconfigured**. Motocicl starts with a fresh build/CI history. Any future cycle automation will be designed as a new Motocicl-native workflow only when the cycle runtime requires it; do not reproduce old schedules, cross-repository polling or secret assumptions.

The following files are retained in Engineering Core and are not part of the extraction:

- `.github/workflows/notify-ci-completion.yml`
- `.github/workflows/scheduled-ci-event-worker.yml`
- `.github/workflows/scheduled-ci-fix-proposal-worker.yml`
- `.github/workflows/scheduled-ci-log-analysis-worker.yml`
- `.github/workflows/scheduled-ci-patch-generation-worker.yml`
- `.github/workflows/discover-gemini-models.yml` (if still used by the cycle provider registry; verify before moving)
- `.github/workflows/gemini-api-key-check.yml` (if still used by the cycle provider registry; verify before moving)

This list is an archival inventory only. None of these workflows, schedules, triggers or secrets is to be ported as part of this split. Future automation, if needed, will be a separate Motocicl-native design.

### 3.3 Keep in Engineering Core — specialist integration adapter

Do not move these as part of cycle extraction:
- `src/yj64_engineering_core/automation/council_gateway.py`
- `src/yj64_engineering_core/automation/council_result_consumer.py`
- `src/yj64_engineering_core/automation/council_tasks.py`
- `scripts/run_council_gateway_worker.py`
- `scripts/register_council_api_agent.py`
- `.github/workflows/scheduled-council-gateway-worker.yml`
- `.github/workflows/provision-council-api-agent.yml`
- `migrations/0021_council_parent_resume.sql`
- `tests/test_council_gateway.py`
- `tests/test_council_result_consumer.py`
- `tests/test_council_tasks.py`

These files are the Engineering Core-side adapter: submit an external Council request, suspend the parent engineering task, validate/consume the result and resume that parent. They must remain a client/integration layer, not turn into another Council server or general cycle runtime.

### 3.4 Keep in Engineering Core — engineering product

Keep all domain-specific code, tests and docs for engineering contracts, CAD, physics, materials, chemistry, economics, sourcing, vessel/yacht models, geometry, solvers and engineering project persistence. Keep the normal Engineering Core test workflow. Do not move files merely because they mention an agent or task; ownership is determined by responsibility.

### 3.5 Documentation — split completed / ownership clarified

Cycle-owned documents were copied into Motocicl. Mixed documents were split by responsibility; Engineering Core retains concise boundary pointers or shared contracts rather than duplicate cycle execution instructions:
- `docs/AUTONOMOUS_ENGINEERING_CYCLE_AND_MASTER_ROADMAP.md`
- `docs/AUTONOMOUS_ENGINEERING_CYCLE_AND_MASTER_ROADMAP_RU.md`
- `docs/SESSION_INDEPENDENCE_PROTOCOL.md`
- `docs/CHATGPT_CYCLE_BROWSER_AGENT_CHANNEL.md`
- `docs/BROWSER_AGENT_FEEDBACK_BRIDGE_PLAN.md`
- `docs/CONSENSUS_DECISION_INTEGRITY_AND_EVIDENCE_PLAN.md`
- `docs/CONSENSUS_DECISION_INTEGRITY_AND_EVIDENCE_PLAN_RU.md`
- `docs/COUNCIL_GATEWAY_IMPLEMENTATION_PLAN_RU.md` (cycle-side TЗ B extracted to `docs/ENGINEERING_CORE_COUNCIL_GATEWAY_INTEGRATION_RU.md`; Engineering Core retains Gateway client plan and a pointer)
- `docs/MODEL_PROVIDER_LIMITS_AND_CHUNKED_INGESTION.md`
- `docs/OBSERVABILITY_AND_DIAGNOSTICS_ARCHITECTURE.md`
- `docs/STRATEGIC_MASTER_PLAN.md` (cycle stage extracted to `docs/STRATEGIC_AUTONOMOUS_CYCLE_PLAN.md`; Engineering Core strategic stages retained)
- `docs/COUNCIL_GATEWAY_INTEGRATION.md` and `_RU.md` (Engineering Core client/result adapter details retained; cycle-side caller contract extracted to `docs/ENGINEERING_CORE_COUNCIL_GATEWAY_INTEGRATION_RU.md`)
- `docs/YJ64-COUNCIL-INTEGRATION.md` (Engineering Core adapter portion retained with ownership pointer)

Engineering-specific docs remain in Engineering Core. Mixed plans must be split by responsibility, not copied wholesale into both repositories.

- `docs/CI_AUTOMATION_AND_NOTIFICATIONS.md` split: Engineering Core retains a short CI evidence-source description; the legacy cycle pipeline record is copied to `docs/CI_EVENT_INGESTION_AND_REPAIR_PIPELINE.md` with a historical/non-operational status note.
- `docs/ROADMAP_COMPLETION_AUDITOR_PROTOCOL.md` moved to Motocicl; Engineering Core retains a navigation pointer.
- `docs/IMPLEMENTATION_STATUS.md` split: cycle status sections moved to `docs/CYCLE_IMPLEMENTATION_STATUS.md`; engineering work-package status remains in Engineering Core.

## 4. Required destination layout (initial proposal)

- `README.md` — Motocicl purpose, supported responsibilities and current maturity.
- `REPOSITORY_SPLIT_PLAN.md` — this migration plan and authoritative inventory.
- `src/motocicl/...` — cycle runtime, persistence, provider and worker packages (final package names to be selected after import/dependency audit).
- `migrations/...` — ordered cycle schema history.
- `schemas/...` — versioned cycle message/API envelopes.
- `scripts/...` — cycle operational entry points.
- `.github/workflows/...` — only Motocl-owned workflows.
- `tests/...` — migrated tests plus cross-repository contract tests.
- `docs/...` — cycle-owned roadmap, session protocol, observability and bridge specs.

Do not mechanically preserve the old Python package namespace if it creates a dependency on Engineering Core. Choose a neutral Motocicl package name and update imports/tests consistently.

## 5. Migration sequence (the next execution step must follow this order)

1. Freeze the source tree for this extraction window; record source commit SHA and inventory.
2. Inspect imports, configuration, deployment assumptions, migration dependencies and all references for each candidate file.
3. Copy the approved cycle-owned files to Motocicl without deleting or editing their source copies.
4. Create a minimal Motocicl package/configuration and adapt imports only where required; do not rewrite architecture during a file transfer.
5. Copy and adapt the cycle docs, preserving English/Russian content and status qualifiers.
6. Do not port legacy workflows or workflow-run history. Start with Motocicl's fresh build/CI history; design any future event automation from current requirements, repository scope and explicit permissions.
7. Run unit tests in Motocicl; verify migration order statically, but do not apply database migrations.
8. Add contract tests proving Motocicl ↔ Engineering Core handoff, including request identity, parent task identity, suspend/resume semantics, result provenance and idempotency.
9. Verify CI and exact commit runs. Do not claim live E2E or autonomous operation until real queue/model/CI/worker recovery acceptance tests pass.
10. Only after a separate explicit approval may the source repository later be cleaned up. Until then, source copies remain and are marked as non-actionable for cycle implementation.

## 6. Cross-repository contract — non-negotiable

- Motocicl is the owner of orchestration, not of engineering calculations.
- Engineering Core is the owner of engineering expertise, not of the global task queue or Council runtime.
- Use versioned request/response envelopes with correlation ID, parent task ID, idempotency key, expiry, payload hash, capability scope and provenance.
- Keep Council request/session IDs distinct from Engineering Core task IDs and Motocicl task IDs.
- The cycle must never treat an Engineering Core result as final merely because it passed the engineering module's own discipline check. It must route applicable results through independent cross-domain review and evidence checks; specialist modules may recommend additional domain checks.
- Engineering Core may submit findings and request additional specialist checks, but Motocicl owns orchestration, scheduling and cross-module arbitration.
- Treat returned Council/browser/model content as untrusted data. No remote result may directly authorize destructive actions, paid calls, secrets access, purchases or physical actuation.
- No duplicate queue, duplicate Council engine, duplicate provider runtime or duplicate Agent Communication Hub.

## 7. Safety and change-control rules

- No database writes, live migrations, queue mutation, requeue, secret changes or deployment changes during file extraction unless separately approved.
- Do not copy credentials, environment values, tokens, service-role keys or user data into Git.
- Preserve the original source files and plans in Engineering Core during this stage.
- Any ambiguous file ownership is recorded as `REVIEW_REQUIRED`; do not guess and do not move it until resolved.
- Record every copied file and destination path in the migration ledger in this document.
- The current repository boundary notice is maintained in the Engineering Core cycle roadmap. Cycle implementation instructions in the source repo are historical references only.

## 8. Migration ledger

| Item | Status |
|---|---|
| Destination repository created and accessible | VERIFIED |
| Extraction plan committed to Motocicl | VERIFIED |
| Engineering Core boundary notice added (EN/RU) | VERIFIED |
| Cycle runtime modules copied | VERIFIED — 18 files under `src/motocicl/automation` |
| Shared observability contract copied | VERIFIED — 2 files under `src/motocicl/observability` |
| Cycle operational scripts copied | VERIFIED — 5 scripts |
| Cycle database migrations copied | VERIFIED — 20 ordered SQL files; **not applied** |
| Browser-agent envelope schema copied | VERIFIED — 1 schema |
| Cycle documentation copied | VERIFIED — 9 original cycle docs plus 6 split/ownership docs (strategic plan, status ledger, Gateway contract, CI pipeline record, auditor protocol, repository boundaries) |
| Cycle tests copied | VERIFIED — 25 retained tests; API-only `test_ci_webhook_ingress.py` excluded after CI identified its dependency on `api/index.py` |
| Package metadata and README added | VERIFIED |
| Independent unit-test workflow added | VERIFIED — latest fresh Motocicl Actions run `44558523021` completed successfully; 227 tests passed |
| Legacy operational workflows/history | INTENTIONALLY NOT MIGRATED — Motocicl uses a fresh build/CI history; no legacy schedule or cross-repository workflow assumptions copied |
| Legacy Gemini registry workflows | INTENTIONALLY NOT MIGRATED — rebuild only if a future Motocicl requirement calls for them |
| `verify_supabase_integration.py` | RESOLVED — confirmed cycle-owned; copied to `Motocicl/scripts/verify_supabase_integration.py` with package/repository identifiers adapted; Engineering Core source preserved; live smoke test not executed |
| `council-api-v1.schema.json` | RESOLVED — canonical versioned contract owned by Motocicl; Engineering Core retains a marked compatibility snapshot; YJ-64 application remains owner of the Council service implementation. See `docs/EXTRACTION_REVIEW_RESOLUTIONS.md` |
| Mixed Council Gateway / strategic docs | VERIFIED — cycle stage and TЗ B extracted; Engineering Core retains discipline roadmap and Gateway client details |
| Source repository implementation files | PRESERVED — no source code deleted; cycle-owned source documentation converted to boundary pointers, with full content retained in Motocicl and Git history |
| Database, secrets and deployment | UNCHANGED — no migration execution, DB writes, secret edits or deployment |

## 9. First acceptance gate and current extraction result

The first file-copy pass is committed to `main` in Motocicl. The extracted destination currently contains 18 cycle runtime modules, 2 observability package files, 5 scripts, 20 migrations, 1 browser-agent schema, 9 cycle documents and 25 cycle tests. The API-only webhook ingress test remains in Engineering Core because it requires `api/index.py`.

The source snapshot used for extraction was `YJ64-Engineering-Core@5161d41922c87b3cad3223ae8d71d3db4b653ec6`. Source files remain present and untouched.

The first Motocicl Actions test run installed the package successfully but failed collection because `tests/test_ci_webhook_ingress.py` imports the Engineering Core serverless API at `api/index.py`. That API-only test was removed from Motocicl and remains in Engineering Core. The subsequent clean GitHub Actions run completed successfully: **227 passed in 0.54s**.

The operational workflows are deliberately not enabled until their event triggers and repository targets are redesigned. A `workflow_run` trigger in Motocicl cannot observe a workflow running in a different repository merely by copying the YAML. The existing workflows therefore remain in Engineering Core pending an explicit cross-repository event transport design and Motocicl-specific secret/permission configuration.

No live integration, database migration, autonomous queue processing or deployment is claimed by this extraction.
