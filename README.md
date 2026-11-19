# Motocicl

Motocicl owns the YJ64 autonomous Council/cycle orchestration runtime: durable task execution, provider adapters and budgets, checkpoints and recovery, CI event/log processing, bounded repair proposals, persistence and cycle-level observability.

Engineering Core remains the owner of specialist engineering disciplines and solvers. It connects to the Council/cycle through its narrow versioned API adapter. The YJ-64 application remains the owner of its internal multi-model Council engine and Agent Communication Hub.

The Python package is `motocicl` under `src/`; the extracted runtime lives in `motocicl.automation`.

## Documentation

- [Repository ownership boundaries](docs/REPOSITORY_BOUNDARIES.md)
- [Strategic autonomous-cycle plan](docs/STRATEGIC_AUTONOMOUS_CYCLE_PLAN.md)
- [Detailed autonomous-cycle roadmap](docs/AUTONOMOUS_ENGINEERING_CYCLE_AND_MASTER_ROADMAP.md)
- [Cycle implementation status and historical evidence](docs/CYCLE_IMPLEMENTATION_STATUS.md)
- [Engineering Core ↔ Council Gateway contract](docs/ENGINEERING_CORE_COUNCIL_GATEWAY_INTEGRATION_RU.md)
- [Repository split and migration ledger](REPOSITORY_SPLIT_PLAN.md)
- [Council API v1 canonical schema](schemas/council-api-v1.schema.json)
- [Resolved extraction reviews](docs/EXTRACTION_REVIEW_RESOLUTIONS.md)

## Safety and maturity

- Extracted files are a migration baseline, not proof of a live autonomous deployment.
- Database migrations are stored as source files only; they have not been applied.
- Provider and database credentials must be configured as environment/repository secrets. Never commit secret values.
- Legacy Engineering Core workflow YAML and workflow-run history are intentionally not migrated. Motocicl starts a fresh build/CI history; any future automation should be designed for this repository from current requirements, permissions and secrets.
- See [REPOSITORY_SPLIT_PLAN.md](REPOSITORY_SPLIT_PLAN.md) for ownership, migration ledger and remaining review items.

## Development

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```
