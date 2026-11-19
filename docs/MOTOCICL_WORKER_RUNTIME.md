# Motocicl Worker Runtime

**Status:** bounded runtime and container build implemented; production deployment not approved.

## What this runtime does

`scripts/run_motocicl_worker.py` starts a long-running process around the existing single-step `WorkerRunner`. Each loop iteration runs recovery maintenance and claims at most one task. PostgreSQL leases coordinate multiple replicas. Idle polling is bounded, and SIGTERM/SIGINT request a clean stop between task iterations.

The default handler registry contains only:

- `prepare_ci_fix` — creates a review-only repair proposal from an already persisted CI diagnosis. It does not edit repositories or apply patches.

The optional `generate_ci_patch` handler is disabled unless `MOTOCICL_ENABLE_ZERO_COST_PATCH_WORKER=true`. Enabling it requires `GEMINI_API_KEY`, a verified provider profile, and explicit daily/monthly cost budgets equal to zero. This handler creates review-only patch candidates; it does not apply or commit them.

The runtime deliberately does **not** register `process_ci_event`, `analyze_ci_logs`, `submit_council_request`, `poll_council_request` or `council_result_ready`. Those require separately verified handlers and Gateway contracts. Unknown task types are not claimed by this worker.

## Required environment

- `YJ64_DATABASE_URL` — PostgreSQL connection string for the existing Motocicl queue.
- `SUPABASE_URL` — Supabase project URL for private artifact storage.
- `SUPABASE_SERVICE_ROLE_KEY` — service-role credential, supplied only through the host's secret manager.

Optional:

- `MOTOCICL_WORKER_ID` — stable unique worker identifier. If omitted, hostname and process ID are used.
- `MOTOCICL_LEASE_SECONDS` — integer from 30 to 3600; default 600.
- `MOTOCICL_POLL_SECONDS` — number from 1 to 300; default 5.
- `MOTOCICL_ENABLE_ZERO_COST_PATCH_WORKER` — set to `true` only after explicit approval and verification of zero-cost provider budgets.
- `GEMINI_API_KEY` — required only when the optional patch handler is enabled.

No credentials belong in the image, source code, GitHub repository variables, or build arguments. Inject them at runtime through the deployment provider's secret manager.

## Container

The root `Dockerfile` builds a Python 3.11 image, installs the package, runs as a non-root user and starts:

```sh
python scripts/run_motocicl_worker.py
```

CI builds the image after unit tests. CI does not push it to a registry or deploy it.

## Render implications

- The correct Render service type for this process is **Background Worker**, not Web Service.
- Render Background Workers are not available on the free instance tier. Do not create this service under a free-only constraint.
- The worker exposes no HTTP port; do not add a fake web health endpoint or use a free Web Service as a substitute.
- Do not provision Render Postgres or Key Value for authoritative task state. The runtime uses the existing PostgreSQL store and Supabase private artifact bucket.
- No Render Blueprint, service, environment variable, secret, paid resource or database migration has been created by this change.

## Remaining acceptance work

Before production deployment:
1. Verify the exact Motocicl schema migrations and permissions in a dedicated staging database.
2. Exercise the container against staging PostgreSQL and Supabase Storage.
3. Test two or more worker processes claiming independent tasks, duplicate delivery, SIGTERM during idle and during task execution, lease expiry and restart recovery.
4. Implement and contract-test the missing main-cycle task handlers and Council Gateway integration.
5. Add operational heartbeat/health reporting and alerting.
6. Approve the paid Background Worker instance and resource budget separately.

This runtime is a deployable foundation for the currently implemented CI-proposal worker tasks. It is **not** evidence that the complete autonomous engineering cycle is operational.

## Recovery and lease audit — 2026-11-19

The current PostgreSQL claim path has durable recovery behavior at the SQL level:

- Claims are serialized with `FOR UPDATE SKIP LOCKED`; a new worker can reclaim an expired `running` task while its attempt budget remains.
- The claim returns the latest checkpoint and verifies its integrity before the handler receives the task.
- Expired tasks with provider reservations in `sending` or `accepted` are quarantined as `unknown` and blocked for reconciliation rather than blindly replayed.
- Expired tasks at their final attempt become terminal failures.
- Checkpoint writes and lease renewal require the current owner and a lease that has not already expired.

Important remaining gaps:

- The runner now starts a background lease heartbeat for ordinary task handlers, renewing at one third of the configured lease interval. The heartbeat is stopped and joined before the runner performs the final task transition.
- If renewal returns false or raises an error, the runner reports `lease_lost` and does not complete, fail, or block the task under stale ownership.
- Unit tests cover repeated automatic renewal during ordinary and reconciliation handlers, plus lease-loss paths. GitHub Actions runs 35–38 passed before reconciliation heartbeat was added; the new reconciliation tests are pending CI verification.
- Lease-loss detection does not forcibly interrupt a synchronous handler. That handler may continue until it returns, so handlers must still use bounded provider timeouts and idempotent side effects. Reconciliation evidence lookup and its handler are also wrapped by the heartbeat; renewal is stopped and joined before reservation decisions are applied, because resolving the final reservation may release the lease and requeue the original task. The reservation-resolution/finalization phase itself is intentionally not heartbeated.
- Existing tests still use fake stores; they do not execute a real PostgreSQL kill/restart or concurrent-claim scenario.
- The runtime loop stops between task iterations. A SIGTERM received during a handler sets the stop flag but does not interrupt that handler or persist an explicit shutdown checkpoint.

Acceptance status: automatic lease renewal is implemented and unit-tested for ordinary handlers. Database-backed restart recovery, real concurrent claims, and heartbeat coverage for reconciliation handlers remain **unverified**. Do not treat the worker as fully restart-safe for arbitrary-duration or side-effecting handlers.
