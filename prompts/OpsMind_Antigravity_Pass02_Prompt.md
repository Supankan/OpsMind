# Antigravity Prompt — OpsMind Implementation Pass 02
## Incident & Investigation Control Plane

Work only in the existing repository:

```text
F:\PycharmProjects\Random\RandomML\2026\OpsMind
```

WSL path:

```bash
/mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind
```

Baseline:

```text
41954c9a6248f31f66eef431d564c827332ef864
```

You are the implementation/coding front. The architecture/reasoning/review front is handled separately in ChatGPT with GPT-5.6 Sol High.

The runtime AI model used inside OpsMind is still **TBD**. Gemini 3.8 Flash and GPT-5.6 Sol High are development tools, not runtime dependencies.

Use the accompanying `OpsMind_Pass02_Design_Spec.md` as the authoritative specification for this pass.

---

# Objective

Implement the incident and investigation-run control-plane API and service-layer rules defined in the Pass 02 design.

This pass creates durable incident/run state only. It does not execute an investigation.

---

# Required endpoints

Implement:

```text
POST /api/v1/incidents
GET  /api/v1/incidents/{incident_id}
GET  /api/v1/incidents
POST /api/v1/incidents/{incident_id}/investigations
GET  /api/v1/investigations/{run_id}
```

Follow the exact semantics in the design specification.

Important rules:

- client cannot set incident status on create;
- every new incident starts `DETECTED`;
- investigation registration creates `PENDING` only;
- creating a `PENDING` run does not change incident status;
- reject a second `PENDING`/`RUNNING` run for the same incident;
- reject investigation registration for ineligible/closed incident statuses;
- no runtime-model configuration is accepted from the client.

---

# Required list behavior

`GET /api/v1/incidents`

Support:

```text
limit        default 20, 1..100
offset       default 0, >=0
status       optional
environment  optional
severity     optional
```

Return:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

Default deterministic ordering:

```text
detected_at DESC, id DESC
```

---

# Error contract

Use:

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  }
}
```

Required domain codes:

```text
INCIDENT_NOT_FOUND
INVESTIGATION_NOT_FOUND
INCIDENT_NOT_INVESTIGATABLE
ACTIVE_INVESTIGATION_EXISTS
VALIDATION_ERROR
```

No stack traces, SQL, credentials, or database internals may appear in responses.

---

# Service layer

Implement business logic in `opsmind/incidents/service.py`.

Route handlers should remain transport-focused.

Do not introduce a repository-pattern layer unless a concrete requirement makes it necessary.

Keep the existing synchronous SQLAlchemy architecture. Do not refactor to async SQLAlchemy.

---

# Database / migrations

The approved design requires no schema change.

Do not add:

- unique `external_ref`;
- idempotency table;
- active-run DB index/constraint;
- new runtime-model fields.

Do not create a migration unless an actually necessary DDL change is discovered. If so, stop and report an architecture deviation request before implementing it.

---

# Idempotency

Do not invent silent deduplication.

`POST /api/v1/incidents` is non-idempotent in this pass.

The investigation endpoint prevents duplicate active runs through the service-layer business rule, but this is not a general idempotency subsystem.

---

# Tests

Add comprehensive unit/integration/API coverage.

At minimum verify:

1. incident create -> 201;
2. new incident status -> DETECTED;
3. get incident;
4. missing incident -> 404;
5. incident list pagination;
6. status filter;
7. environment filter;
8. severity filter;
9. stable default ordering;
10. investigation registration -> PENDING;
11. investigation registration does not change incident status;
12. duplicate active run -> 409 ACTIVE_INVESTIGATION_EXISTS;
13. ineligible incident -> 409 INCIDENT_NOT_INVESTIGATABLE;
14. get run;
15. missing run -> 404;
16. malformed/invalid request -> 422;
17. validation errors use the approved error envelope;
18. Pass 01 `updated_at` regression tests still pass.

Run tests against PostgreSQL where persistence behavior is involved.

---

# Verification

Run:

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run mypy opsmind apps tests
make check
```

Also run a small live API smoke test against the local FastAPI app and PostgreSQL.

---

# Explicit non-goals

Do not implement:

- LangGraph;
- agent execution;
- background worker/queue;
- runtime LLM/model/provider integration;
- prompt engineering;
- Milvus;
- embeddings;
- Prometheus;
- OpenSearch;
- Jaeger;
- OpenTelemetry Demo integration;
- frontend;
- incident memory;
- remediation;
- Kubernetes.

Do not install dependencies for these future subsystems.

---

# Git

Commit Pass 02 separately after all checks pass.

Suggested commit message:

```text
feat: add incident and investigation control plane
```

Do not rewrite/amend the Pass 01 history.

---

# Final handoff report

Return exactly these sections:

1. **Files created/changed**
2. **API endpoints implemented**
3. **Business/lifecycle rules implemented**
4. **Error contract implementation**
5. **Database/migration changes**
6. **Tests added**
7. **Full verification results**
8. **Live API smoke-test results**
9. **Known limitations**
10. **Architecture deviation requests** — `None` if none
11. **Git commit hash and Git status**
12. **Exact next recommended step**

Also update/create:

```text
docs/handoffs/PASS_02_SUMMARY.md
```

Do not start Pass 03. Stop and wait for Front A review.
