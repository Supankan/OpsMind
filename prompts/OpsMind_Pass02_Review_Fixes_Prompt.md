# Antigravity — OpsMind Pass 02 Review Fixes

Work only in the existing OpsMind repository:

```text
F:\PycharmProjects\Random\RandomML\2026\OpsMind
```

WSL path:

```bash
/mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind
```

This is a small corrective pass after Front A review of Pass 02. Do **not** start Pass 03.

## Fix 1 — Make active-investigation registration race-safe

Pass 02 correctly rejects a second active (`PENDING` / `RUNNING`) investigation in ordinary sequential requests, but the implementation must also be safe when two requests attempt to register a run for the same incident concurrently.

The current architecture deliberately avoided adding a new uniqueness constraint in Pass 02. Preserve that decision.

### Preferred implementation

Inside the same database transaction used to register a run:

1. Load and lock the parent incident row using PostgreSQL row-level locking (`SELECT ... FOR UPDATE` / SQLAlchemy equivalent).
2. Re-check incident eligibility while holding the lock.
3. Query for an existing active run (`PENDING` or `RUNNING`) while the lock is held.
4. If one exists, raise `ACTIVE_INVESTIGATION_EXISTS`.
5. Otherwise insert the new `PENDING` run and commit.

The lock must be acquired before the active-run check so two concurrent registrations for the same incident serialize correctly.

Do not add advisory locks, Redis/distributed locks, or a new DB uniqueness constraint in this corrective pass.

### Required concurrency test

Add a PostgreSQL-backed concurrency integration test using two independent database sessions or requests that attempt to register an investigation for the same incident at the same time.

Acceptance condition:

```text
exactly one registration succeeds
exactly one registration is rejected with ACTIVE_INVESTIGATION_EXISTS
exactly one active investigation row exists afterward
```

Avoid a test that only performs requests sequentially.

## Fix 2 — Remove global Ruff B008 suppression

Pass 02 added a project-wide Ruff ignore for `B008` because FastAPI commonly uses calls such as `Depends(...)` or `Query(...)` in parameter declarations.

Do not globally disable `B008`, because that weakens linting for unrelated code.

Prefer modern FastAPI `typing.Annotated` declarations, conceptually:

```python
db: Annotated[Session, Depends(get_db_session)]
limit: Annotated[int, Query(ge=1, le=100)] = 20
```

Refactor the affected route declarations so `B008` can remain enabled globally.

Then remove the project-wide `B008` ignore from `pyproject.toml`.

If there is a specific isolated case where `Annotated` is not appropriate, use the narrowest possible suppression and explain it in the report.

## Documentation / traceability

Update `docs/handoffs/PASS_02_SUMMARY.md` so that:

- it does not describe the old sequential active-run guard as full concurrency protection;
- it documents the row-lock behavior and concurrency test;
- it includes the final corrective commit hash(es);
- reported test counts/results are updated.

## Verification

Run:

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run mypy opsmind apps tests
make check
uv run alembic current
uv run alembic check
```

Also confirm the normal live API smoke test still succeeds.

## Scope restrictions

Do not implement:

- Pass 03;
- LangGraph;
- runtime LLM/provider integration;
- Milvus;
- telemetry;
- OpenTelemetry Demo;
- background workers/queues;
- frontend;
- remediation;
- incident memory;
- Kubernetes.

No schema migration should be required for the preferred row-lock solution.

## Git

Commit the corrective implementation separately after checks pass.

Suggested commit message:

```text
fix: harden investigation registration concurrency
```

If the documentation update is a second commit, report both hashes.

## Final report

Return:

1. Files changed
2. Previous race condition
3. Exact locking implementation
4. Concurrent test design and result
5. B008 cleanup performed
6. Full verification results
7. Migration status
8. Live smoke-test result
9. Git commit hash(es) and working-tree status
10. Architecture deviation requests (`None` if none)

Stop after this corrective pass.
