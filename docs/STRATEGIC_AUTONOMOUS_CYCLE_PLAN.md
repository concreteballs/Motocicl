# Motocicl — Strategic Autonomous Cycle Plan

**Ownership:** Motocicl owns the autonomous cycle runtime and its execution lifecycle. Engineering Core owns engineering disciplines and specialist solvers; it does not own or operate a second autonomous cycle.

**Programme relationship:** this document extracts the cycle-specific stage from the former shared YJ64 strategic plan. The remaining engineering stages and discipline delivery plan stay in [YJ64 Engineering Core](https://github.com/concreteballs/YJ64-Engineering-Core/blob/main/docs/STRATEGIC_MASTER_PLAN.md).

## 1. Finish the shared Autonomous Engineering Cycle
**Goal:** one cloud-based operating cycle that can continue work when the user's phone is offline.

<details>
<summary>Open implementation steps and acceptance criteria</summary>

### Implementation
1. Establish a fresh CI/build history for Motocicl and define authenticated event delivery for this repository; do not migrate old workflow-run history.
2. Verify actual PostgreSQL persistence in Supabase: event record, durable task, deduplication and queue state.
3. Verify atomic task claims, leases, bounded retries, completion/blocked states and recovery after worker restart.
4. Deploy a separate cloud worker that can claim tasks without relying on the phone, browser, or an open ChatGPT conversation. The worker must comply with the [Session Independence Protocol](SESSION_INDEPENDENCE_PROTOCOL.md): durable task state is authoritative; model calls are replaceable, bounded sessions; context rollover is automatic and recoverable.
5. Connect a server-side model provider using a separately configured API key; do not assume a ChatGPT subscription is an API credential.
6. Implement [MODEL_PROVIDER_LIMITS_AND_CHUNKED_INGESTION.md](MODEL_PROVIDER_LIMITS_AND_CHUNKED_INGESTION.md): detect provider RPM/TPM/context/concurrency/quota limits and structured errors; schedule Retry-After/reset-aware retries; adaptively chunk oversized inputs; verify ordered chunk hashes and explicit FINALIZE before model work. Stateless calls must be assembled by the orchestrator, not assumed to accumulate.
7. Make the worker read Motocicl's strategic cycle plan, detailed cycle roadmap and cycle implementation ledger; select only the next unblocked task.
8. Require exact-commit CI validation before a task is marked complete or the next dependent task is started.
9. Add bounded repair attempts, task/time/token/cost budgets, pause/resume/cancel, kill switch and safe blocked states.
10. Add external notifications and a status view for active task, queue, last commit, CI result, next task, budget and stop reason.
6. Make the worker read this strategic plan, the detailed roadmap and implementation ledger; select only the next unblocked task.
7. Require exact-commit CI validation before a task is marked complete or the next dependent task is started.
8. Add bounded repair attempts, task/time/token/cost budgets, pause/resume/cancel, kill switch and safe blocked states.
9. Add external notifications and a status view for active task, queue, last commit, CI result, next task, budget and stop reason.

### Acceptance
- A task is durably queued.
- The cloud worker claims it while the phone is offline.
- It makes a small authorized change in the authorized target repository and on its authorized branch.
- CI runs for the exact resulting commit.
- Completion event is authenticated, persisted and deduplicated.
- The worker records the evidence and advances, or stops with a clear reason.
- Restart does not lose or duplicate work.
- Context-window exhaustion triggers a persisted checkpoint and a fresh model request automatically, without a user pressing “New chat”.
- A new worker process can resume from durable state without access to the previous model conversation.
- Replayed or uncertain in-flight operations are handled idempotently and do not duplicate external side effects.
- Pause/kill switch and budget limits are demonstrated.

**Exit gate:** do not call the cycle autonomous until the full acceptance sequence passes. Do not start broad automated module development before this gate.

</details>

## Cross-repository execution rule

The cycle may coordinate engineering tasks in Engineering Core only through its authorized, versioned integration contract. A task result is not complete merely because the originating discipline accepts it: cross-disciplinary review, evidence provenance, applicable physical models and unresolved uncertainty must be checked by the cycle. The cycle may request additional discipline review; it may not silently change the engineering module's domain acceptance criteria or repository permissions.
