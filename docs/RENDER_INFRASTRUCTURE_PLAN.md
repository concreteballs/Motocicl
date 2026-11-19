# YJ64 — Render infrastructure plan and deployment registry

**Status:** architecture plan; no Render resources created and no production settings changed.  
**Review date:** 2026-11-19  
**Owner:** Motocicl — autonomous cycle runtime and cross-repository orchestration.  
**Purpose:** define the broadest useful Render deployment surface while using free capabilities first, preserving portability, and avoiding duplicate services.

## 1. Executive decision

Render is a possible execution and presentation platform for the YJ64 ecosystem, not the authoritative owner of project state.

- GitHub remains the source of code, version history and CI.
- Supabase remains the existing managed data/API platform where a project already uses it.
- Motocicl owns the autonomous cycle lifecycle, durable orchestration, task scheduling/recovery and cross-repository coordination.
- The YJ-64 application owns its native multi-model Council engine and its API/worker implementation.
- Engineering Core and the specialist modules own domain solvers and discipline-specific evidence, not a second global scheduler.
- Render may host web frontends, public APIs, long-running workers, scheduled jobs, isolated workflow runs and managed data services when the relevant service type and budget are approved.

**Free-tier conclusion:** Render Free is suitable for static frontends and limited demos/tests. It is not a free always-on compute platform. Background Workers, Private Services, Cron Jobs and Workflows do not have free instances. Do not design durable production execution around Free Web Services, Free Postgres or Free Key Value.

## 2. Current repository inventory and ownership

This is a source/documentation inspection, not a claim that every component is deployed or production-ready.

| Repository | Existing responsibility / observed state | Render disposition |
|---|---|---|
| `concreteballs/Motocicl` | Owns autonomous cycle orchestration, durable lifecycle, provider budgets/adapters, checkpoints/recovery, CI event processing and cycle observability. Current status ledger explicitly marks important runtime pieces as incomplete/not yet demonstrated. | Future primary home for cycle API/worker services. Background Worker or Workflow only after runtime acceptance tests; free Web Service may host a non-authoritative status/demo API. |
| `concreteballs/yj64-clean-bial2modFun5` | YJ-64 Android application plus cloud Council API/worker. Contains FastAPI ingress, persistent worker, Supabase/Postgres queue adapters, Dockerfile, Compose stack and deployment guide. Worker concurrency is configurable 1–8 (default 2), with request isolation, heartbeat, lease renewal, progress, cancellation and retry/recovery. The guide says no external worker host has been selected/deployed. | Do not duplicate it. Existing Supabase Edge Function remains the ingress option; deploy the existing container as a Background Worker only when a paid host is approved, or use the documented portable VM path. |
| `concreteballs/YJ64-Engineering-Core` | Owns engineering disciplines, CAD/physics/materials/economics and specialist solvers. Has a Council Gateway client and durable task adapters; README explicitly forbids a second global scheduler/provider runtime. | Do not create one always-on Render service per solver. Invoke bounded domain handlers through Motocicl's task execution. Consider Workflow task runs only when measured isolation/parallelism needs justify cost. |
| `concreteballs/YJ64-Browser-Council` | Separate product in Phase 1 technical reconnaissance. Proposed responsive web UI, FastAPI API, durable PostgreSQL state, independent worker processes, browser sessions and evidence storage. No product implementation yet. | Strong future Render fit: Static Site for frontend; Web Service for API; paid Background Worker or Workflow for research/browser tasks; external durable DB/object storage. Do not deploy before its architecture review and implementation gate. |
| `concreteballs/YJ64-Biological-Engineering` | Independent computational assessment module; architecture/contracts and tests. No wet-lab execution or deployment capability. | No dedicated service initially. Run bounded computational assessments as isolated Motocicl tasks. |
| `concreteballs/YJ64-Molecular-Genetic-Engineering` | Independent computational module with versioned candidates, evidence and review contracts; no autonomous wet-lab execution. | No dedicated service initially. Run bounded computational assessments as isolated Motocicl tasks. |
| `concreteballs/yj64-base` | Android base application and embedded diagnostic agent; development bridge only, no real HTTPS endpoint configured. | Not a Render workload. A future authenticated diagnostic HTTPS receiver could be a Web Service, but only after protocol/security design. |
| `concreteballs/yj64-fault-injection` | Android diagnostic experiment deliberately crashing the target app process to test monitor detection. | Not a Render workload. Keep fault injection local/device-side. |
| `concreteballs/monitor-bridge` | Repository exists in the account; README was not retrievable during this inspection. | No deployment decision until its contents and role are audited. |
| `concreteballs/yj64-virtual-lab.` | README currently resembles the YJ-64 Base Stage 2 diagnostic scaffold; ownership/function is not sufficiently clear. | No deployment decision until repository identity and purpose are clarified. |

Other similarly named historical YJ64 repositories are not assumed to be active deployment targets. Before assigning any additional repository a service, inspect its current main branch and ownership document.

## 3. Render service-type registry

### 3.1 Static Sites — FREE; use broadly

Good candidates:
- Browser Council React/PWA frontend once implemented.
- Public documentation and read-only project pages.
- Non-sensitive status dashboards or static reports.
- Static documentation for Engineering Core and specialist modules.

Constraints:
- Static assets only; no server-side secrets or private provider keys.
- Bandwidth and build-pipeline usage still count against workspace allowances.
- A static site cannot execute Python workers or protect secrets.

**Priority:** first Render resource to consider, once a real frontend repository and deployment requirements are identified.

### 3.2 Web Services — FREE for prototypes; paid for dependable always-on APIs

Good candidates:
- Temporary/demo API for Browser Council.
- Non-authoritative health/status endpoint.
- Public HTTPS ingress for a module, if it does not duplicate an existing API.
- Later production API gateway, with an approved paid compute plan.

Free-plan constraints:
- 512 MB RAM; 750 free instance-hours per workspace per calendar month.
- Spins down after 15 minutes without inbound traffic; waking takes about one minute.
- Ephemeral filesystem; no persistent disk, SSH/shell access or scaling beyond one instance.
- May restart at any time.
- Cannot receive private-network traffic.
- External-service traffic may trigger Render's free-service traffic threshold.
- Not appropriate for the live autonomous cycle's dependable ingress or always-on orchestration.

### 3.3 Background Workers — PAID; core execution target

Potential workloads:
- Motocicl autonomous cycle worker/scheduler.
- Existing YJ-64 Council worker from `yj64-clean-bial2modFun5`.
- Browser Council research/browser workers.
- Bounded specialist engineering task consumers.
- File conversion, report generation and evidence processing.

Architecture rules:
- Workers claim durable tasks from the authoritative database/queue.
- Every task has stable task/session/request identity, idempotency, bounded retries, timeout, cancellation and persisted output.
- No worker-local filesystem is authoritative.
- Keep provider credentials in Render secret environment variables, never in Git, APKs or logs.
- Start with one worker instance and explicit concurrency limits; scale horizontally only after load and cost tests.
- Do not run multiple competing schedulers for the same queue.

### 3.4 Private Services — PAID; internal-only components

Possible later uses:
- Internal-only API adapters.
- Private search/indexing or analytics services.
- Internal artifact processing endpoints.
- Supporting services that must not have a public URL.

Do not create these until a real internal-network dependency exists. Avoid exposing internal APIs publicly just to make service-to-service calls work.

### 3.5 Cron Jobs — PAID; scheduled maintenance only

Possible uses:
- Periodic reconciliation and cleanup.
- Scheduled report generation.
- Retention/expiry checks.
- Periodic health probes or data quality checks.

Do not use a Cron Job as the autonomous cycle's durable scheduler. A cron run is bounded and may be delayed by a previous run; the cycle scheduler must persist task state and recover after restarts.

### 3.6 Workflows — PAID; optional distributed execution layer

Potential uses:
- Independent parallel engineering assessments.
- Browser research pipelines.
- Evidence ingestion, parsing and summarization.
- Multi-stage report or artifact production.
- On-demand specialist jobs with retries and observable task results.

Constraints and integration rules:
- Render Workflows is currently documented as public beta.
- Python and TypeScript task SDKs are supported.
- Individual task runs can run for up to 24 hours.
- Render manages the run queue and task provisioning; compute and retained run state are billable.
- Native scheduling is not yet supported; a Cron Job or external scheduler must trigger scheduled runs.
- It must not replace Motocicl's authoritative task ledger, acceptance gates, cross-repository permissions or durable checkpoints.
- Integrate only through a versioned adapter so tasks remain portable to ordinary OCI workers.

### 3.7 Postgres — FREE only for disposable tests; PAID for durable Render-hosted DB

Free constraints:
- One active free database per workspace.
- 1 GB storage.
- Expires 30 days after creation; 14-day upgrade grace period, then deletion.
- No backups or managed connection pooling.
- Maintenance/restarts may cause temporary unavailability.

Decision:
- Do not move Council or Motocicl authoritative state into free Render Postgres.
- Keep existing Supabase-backed data where already deployed.
- If a future paid Render Postgres is selected, treat it as a deliberate database migration with backup/restore, security, retention and rollback plans.
- A temporary free database may be used only for disposable integration tests with no unique data.

### 3.8 Key Value (Redis-compatible Valkey) — FREE only for disposable cache tests; PAID for persistent queue/cache

Free constraints:
- One active free instance per workspace.
- 25 MB and 50 connections (per current Render pricing documentation).
- In-memory only; all data is lost on restart, maintenance, suspension or upgrade.

Decision:
- Never use free Key Value as the authoritative task queue, lock store, checkpoint store, session store or audit log.
- It may be used for disposable cache/rate-limit experiments only.
- Paid Key Value can be considered for ephemeral cache/pub-sub, but PostgreSQL remains the durable source of truth.

### 3.9 Sandbox Groups — BETA / NOT IN BASELINE

Potential future use:
- Isolated, ephemeral execution of untrusted or model-generated code.
- Disposable browser/automation environments.
- Reproducible test environments.

Decision:
- Do not rely on availability, pricing or production guarantees until Render's current beta documentation and account eligibility are verified.
- Any code execution must have network, CPU, memory, time, filesystem and secret-access boundaries. No access to production credentials or authoritative databases by default.

## 4. Cross-cutting Render capabilities to reserve in the design

- **Blueprints / Infrastructure as Code:** eventually describe approved services and environment groups as versioned configuration. No Blueprint is created in this phase.
- **Environment Groups:** share non-secret configuration across related services; secrets remain restricted and separately managed.
- **Private Networking:** use for paid internal services in the same region; do not assume free Web Services can receive private traffic.
- **Logs and Observability:** centralize service logs, health endpoints, worker heartbeats, restart counts, task latency and error rates. Never log prompts, API keys, bearer tokens or sensitive evidence.
- **Webhooks and Notifications:** later send deploy/failure/health events to the authorized monitoring path; authenticate and deduplicate events.
- **Custom Domains and TLS:** use managed TLS for public Web Services and Static Sites; do not publish internal worker endpoints.
- **Persistent Disks:** paid-only for service filesystem persistence; prefer external object storage for large artifacts and PostgreSQL for authoritative state.
- **Render API / CLI:** future automation adapter only after scoped credentials and least-privilege access are agreed.

## 5. Recommended deployment topology

### Phase A — zero-cost / no-production-risk

1. Keep the current Supabase Council ingress and data path unchanged.
2. Do not create a Render Postgres or Key Value instance.
3. Do not deploy a free Web Service as a substitute for a permanent worker.
4. Once a suitable frontend exists, use a free Static Site for public documentation or a non-sensitive UI.
5. Use a free Web Service only for a temporary demo or non-critical API, with its sleep/restart limitations explicitly accepted.
6. Continue CI builds and tests in GitHub Actions.

### Phase B — first dependable execution host

1. Select one host for Motocicl's durable cycle worker and one clearly owned queue/database.
2. Prefer the existing portable OCI/container model and standard PostgreSQL contract.
3. Keep API ingress, worker and database on one consistent queue backend. Never connect a Supabase Edge Function to a PostgreSQL-backed worker or a standalone PostgreSQL API to a Supabase-backed worker.
4. Verify heartbeat, leases, restart recovery, idempotency, cancellation, provider budgets, checkpoints and context rollover before autonomous claims.
5. Candidate Render option: paid Background Worker plus an explicitly approved durable database. Candidate non-Render option: the free-VM portability route already documented in the Council deployment assessment, subject to fresh eligibility/capacity and operational review.
6. Do not provision or spend until the user explicitly approves the exact resources and expected monthly cost.

### Phase C — optional distributed execution

1. Add Render Workflows only for tasks that benefit from isolated on-demand execution.
2. Keep Motocicl as the system-level coordinator and source of task acceptance decisions.
3. Add private services only for actual internal API boundaries.
4. Add Cron Jobs only for bounded maintenance/reporting schedules.
5. Add paid Key Value only after measuring a real cache/pub-sub need; do not move durable state out of PostgreSQL.
6. Deploy Browser Council separately after its own product and security gates.

### Phase D — production hardening and portability

- Maintain identical OCI images for Render, another cloud host and user-owned Linux hardware.
- Keep secrets injected at runtime and rotateable.
- Test PostgreSQL backup and restore.
- Use external object storage for durable artifacts and evidence bundles.
- Enforce request/task budgets, rate limits, quotas, concurrency limits and cost alerts.
- Test service restart, host migration, database restore and queue recovery.
- Preserve audit logs and evidence provenance across host changes.

## 6. Service matrix by project

| Project / component | Static Site | Web Service | Private Service | Background Worker | Cron | Workflow | Render datastore |
|---|---|---|---|---|---|---|---|
| Motocicl cycle runtime | Status UI later | API/status endpoint if needed | Internal adapters later | **Primary candidate** | Maintenance only | Optional task execution | Existing authoritative DB first; paid Postgres only after migration decision |
| YJ-64 Council | Documentation/UI later | Do not duplicate current Edge ingress by default | Not initially | **Existing worker, paid host only** | Not initially | Optional future adapter, not replacement | Existing Supabase queue or matching PostgreSQL backend |
| Engineering Core | Docs/report UI later | Not initially | Not initially | Shared task executor, not per-discipline service | Not initially | Good candidate for isolated solver jobs | No separate DB by default |
| Browser Council | **Frontend candidate** | **API candidate** | Internal browser-control APIs later | **Research/browser worker candidate** | Scheduled research only if needed | Multi-step research pipelines | Durable DB + private object storage; avoid free Render Postgres |
| Biological Engineering | Docs only if needed | None initially | None | Shared bounded task executor | None | Optional isolated analysis | No separate DB by default |
| Molecular & Genetic Engineering | Docs only if needed | None initially | None | Shared bounded task executor | None | Optional isolated analysis | No separate DB by default |
| Android Base / Monitor / Fault Injection | None | Diagnostic HTTPS receiver only if later required | None | None | None | None | No Render datastore required |

## 7. Non-negotiable architecture and safety rules

1. Render is replaceable infrastructure, not a source of truth.
2. One global cycle scheduler: Motocicl. No duplicate schedulers in Engineering Core or individual discipline modules.
3. The YJ-64 application retains ownership of its native Council engine; Motocicl does not reimplement it.
4. Every durable task, session and request has stable identity and isolated state.
5. Every worker has bounded concurrency, leases, idempotency, retry policy, cancellation and graceful shutdown.
6. A module cannot approve its own result as system-level acceptable; cross-disciplinary review remains mandatory.
7. Free ephemeral storage and cache are never authoritative.
8. No secrets in source, images, Android clients, public configuration or logs.
9. No public access to worker ports, databases or internal APIs.
10. No paid resource, production gate, secret, domain, database migration or deployment is changed without explicit approval.
11. All deployment definitions must be version-controlled and portable.
12. Do not claim a component is live merely because source code, CI or a Render service definition exists.

## 8. Immediate next steps

1. Complete a read-only audit of Motocicl's current runtime implementation and deployment readiness; its status document says the extracted runtime must be verified independently.
2. Reconcile Motocicl's actual queue/database contract with the existing Council API/worker. Keep ownership separate and use the versioned Gateway contract.
3. Audit the currently unreadable `monitor-bridge` repository and clarify the purpose of `yj64-virtual-lab.`.
4. Decide which existing frontend, if any, is ready for a free Static Site.
5. Only then prepare a Render Blueprint proposal. Do not create services yet.
6. Separately produce a costed paid-service option for the first always-on worker, with no purchase or deployment action.

## 9. Official Render references

- Free plan and limitations: https://render.com/docs/free
- Service types: https://render.com/docs/service-types
- Pricing: https://render.com/pricing
- Web Services: https://render.com/docs/web-services
- Background Workers: https://render.com/docs/background-workers
- Cron Jobs: https://render.com/docs/cronjobs
- Workflows: https://render.com/docs/workflows
- Workflows pricing/limits: https://render.com/docs/workflows-limits
- Key Value: https://render.com/docs/key-value
- Static Sites: https://render.com/docs/static-sites

Render limits and prices can change; re-check the official documentation and the actual workspace billing screen before any provisioning.
