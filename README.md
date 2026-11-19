# Motocicl

Motocicl owns the YJ64 autonomous Council/cycle orchestration runtime: durable task execution, provider adapters and budgets, checkpoints and recovery, CI event/log processing, bounded repair proposals, persistence and cycle-level observability.

Engineering Core remains the owner of specialist engineering disciplines and solvers. It connects to the Council/cycle through its narrow versioned API adapter. The YJ-64 application remains the owner of its internal multi-model Council engine and Agent Communication Hub.

The Python package is `motocicl` under `src/`; the extracted runtime lives in `motocicl.automation`.

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
