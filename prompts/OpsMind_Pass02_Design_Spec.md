# OpsMind — Pass 02 Design Specification
## Incident & Investigation Control Plane

**Status:** Front A approved design for Implementation Pass 02  
**Date:** 2026-09-03  
**Repository:** `F:\PycharmProjects\Random\RandomML\2026\OpsMind`  
**WSL path:** `/mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind`  
**Baseline commit:** `41954c9a6248f31f66eef431d564c827332ef864`

---

## 1. Objective

Pass 02 turns the Pass 01 repository foundation into a usable incident control plane.

The goal is to support creation and inspection of incidents and registration/inspection of investigation runs through a clean API and service layer.

This pass does **not** execute an investigation. It only creates the durable state that a future worker/agent will consume.

---

## 2. Scope

Implement:

- incident creation;
- incident retrieval;
- incident listing with pagination/filtering;
- investigation-run registration;
- investigation-run retrieval;
- service-layer business rules;
- consistent application error responses;
- tests for happy paths and invalid cases;
- explicit lifecycle guardrails needed by these endpoints.

Do not implement:

- LangGraph;
- an agent worker;
- runtime LLM/provider integration;
- Milvus;
- embeddings;
- telemetry;
- OpenTelemetry Demo;
- background queues;
- frontend;
- remediation;
- incident memory;
- Kubernetes.

---

## 3. API endpoints

### 3.1 Create incident

`POST /api/v1/incidents`

Request:

```json
{
  "title": "Checkout failures detected",
  "description": "Elevated checkout failures in the demo environment.",
  "environment": "development",
  "severity": "high",
  "external_ref": "alert-123",
  "service_hint": "checkout",
  "detected_at": "2026-09-03T08:30:00Z",
  "trigger_payload": {}
}
```

Rules:

- `title` is required and must not be blank.
- `description` defaults to `""`.
- `environment` defaults to `development`.
- `severity` defaults to `medium`.
- `external_ref` is optional.
- `service_hint` is optional.
- `detected_at` defaults to current UTC time if omitted.
- `trigger_payload` defaults to `{}`.
- Client **must not set incident status** in this endpoint.
- New incidents always start at `DETECTED`.

Response: HTTP `201 Created`.

Do not silently deduplicate by `external_ref`.

### 3.2 Get incident

`GET /api/v1/incidents/{incident_id}`

Response includes:

```text
id
external_ref
title
description
environment
severity
status
service_hint
detected_at
investigation_start
resolved_at
trigger_payload
created_at
updated_at
investigation_run_count
```

Unknown UUID -> `404 INCIDENT_NOT_FOUND`.

Malformed UUID -> standard/request-validation `422`.

### 3.3 List incidents

`GET /api/v1/incidents`

Query parameters:

```text
limit        integer, default 20, min 1, max 100
offset       integer, default 0, min 0
status       optional IncidentStatus
environment  optional Environment
severity     optional Severity
```

Sorting:

```text
detected_at DESC
id DESC
```

The second key provides stable ordering when timestamps are equal.

Response:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

`total` is the count after filters but before pagination.

Do not add fuzzy search, arbitrary sort expressions, or cursor pagination in this pass.

### 3.4 Register investigation run

`POST /api/v1/incidents/{incident_id}/investigations`

This endpoint does **not** run the future agent. It registers a durable request for investigation.

No runtime-model configuration is accepted from the client in Pass 02.

Request body: none.

The server creates:

```text
InvestigationRun.status = PENDING
runtime_model_provider = null
runtime_model_name = null
prompt_context_version = null
retrieval_config = {}
budget_config = {}
started_at = null
finished_at = null
```

Response: HTTP `201 Created`.

#### Incident eligibility

An investigation may be registered when the incident is:

```text
DETECTED
TRIAGING
INVESTIGATING
INCONCLUSIVE
INVESTIGATION_FAILED
```

Registration must be rejected for:

```text
ROOT_CAUSE_PROPOSED
REMEDIATION_PROPOSED
RESOLVED
POSTMORTEM_COMPLETE
CANCELLED
```

with HTTP `409` and code `INCIDENT_NOT_INVESTIGATABLE`.

#### Active-run rule

If the incident already has a run in:

```text
PENDING
RUNNING
```

reject a second operational run with HTTP `409` and code:

```text
ACTIVE_INVESTIGATION_EXISTS
```

This is a service-layer guardrail for V0. Do not add a new database uniqueness constraint in this pass.

Future evaluation infrastructure may deliberately create independent experimental runs through a separate internal path rather than weakening the operational API.

#### Incident status

Creating a `PENDING` run does **not** automatically change the incident status.

The future execution worker will change:

```text
Incident -> TRIAGING / INVESTIGATING
InvestigationRun -> RUNNING
```

when execution genuinely starts.

### 3.5 Get investigation run

`GET /api/v1/investigations/{run_id}`

Return:

```text
id
incident_id
status
runtime_model_provider
runtime_model_name
prompt_context_version
retrieval_config
budget_config
code_version
started_at
finished_at
stop_reason
root_cause_summary
failure_reason
created_at
updated_at
```

The runtime-related fields remain nullable/TBD.

Unknown UUID -> `404 INVESTIGATION_NOT_FOUND`.

---

## 4. Idempotency semantics

Pass 02 does not introduce a dedicated idempotency-key persistence subsystem.

Therefore:

- `POST /api/v1/incidents` is explicitly non-idempotent.
- Repeating it creates a new incident even if `external_ref` is identical.
- `POST /api/v1/incidents/{id}/investigations` is protected from accidental duplicate active runs by the active-run rule, but is not a general-purpose idempotency implementation.

Do not infer uniqueness from `external_ref`.

A real idempotency subsystem may be introduced later when alert ingestion/webhooks are implemented.

---

## 5. Error contract

Application/domain errors should use one stable envelope:

```json
{
  "error": {
    "code": "INCIDENT_NOT_FOUND",
    "message": "Incident was not found.",
    "details": {}
  }
}
```

Required codes in Pass 02:

```text
INCIDENT_NOT_FOUND
INVESTIGATION_NOT_FOUND
INCIDENT_NOT_INVESTIGATABLE
ACTIVE_INVESTIGATION_EXISTS
VALIDATION_ERROR
```

HTTP mapping:

```text
INCIDENT_NOT_FOUND              404
INVESTIGATION_NOT_FOUND         404
INCIDENT_NOT_INVESTIGATABLE     409
ACTIVE_INVESTIGATION_EXISTS     409
VALIDATION_ERROR                422
```

Requirements:

- no stack traces in API responses;
- no SQL/database internals in API responses;
- validation errors may include field-level detail in `details`;
- log internal errors with structured logging.

Keep the error system small. Do not build a large generic exception framework.

---

## 6. Service-layer responsibilities

`opsmind/incidents/service.py` owns business operations.

Expected functions/methods, naming may vary slightly:

```text
create_incident(...)
get_incident(...)
list_incidents(...)
create_investigation_run(...)
get_investigation_run(...)
```

The service layer is responsible for:

- persistence;
- filter construction;
- active-run checks;
- incident eligibility checks;
- mapping not-found cases to domain exceptions;
- transaction commit/rollback behavior.

API routers are responsible for:

- HTTP transport;
- request parsing;
- response status codes;
- dependency injection;
- mapping domain exceptions through registered handlers.

Do not place SQLAlchemy queries directly throughout route handlers.

Do not introduce a repository-pattern abstraction merely for ceremony in this pass.

---

## 7. Transaction behavior

For write operations:

```text
validate business conditions
-> create/mutate ORM objects
-> add
-> commit
-> refresh
-> return
```

On a database exception:

```text
rollback
-> log
-> raise appropriate application/database error
```

Read operations must not commit.

Keep the existing synchronous SQLAlchemy stack. Do not convert the project to async SQLAlchemy in Pass 02.

---

## 8. Lifecycle rules

Pass 02 should centralize the lifecycle rules used by this pass, but should **not** expose a generic status-update endpoint yet.

### Incident lifecycle model

Conceptual lifecycle remains:

```text
DETECTED
-> TRIAGING
-> INVESTIGATING
-> ROOT_CAUSE_PROPOSED
-> REMEDIATION_PROPOSED
-> RESOLVED
-> POSTMORTEM_COMPLETE
```

Alternative terminal/interruption states:

```text
INVESTIGATION_FAILED
INCONCLUSIVE
CANCELLED
```

Pass 02 only needs enough lifecycle policy to determine whether a new operational investigation can be registered.

### Investigation-run lifecycle

Conceptual:

```text
PENDING
-> RUNNING
-> COMPLETED
```

Alternative terminal states:

```text
FAILED
INCONCLUSIVE
CANCELLED
```

Do not implement public status mutation endpoints yet.

---

## 9. Schemas

Use Pydantic v2.

Expected public schemas:

```text
IncidentCreate
IncidentRead
IncidentDetailRead        # if useful to carry run_count
IncidentListResponse
InvestigationRunRead
ErrorResponse
```

Prefer schema inheritance only when it improves clarity.

Validation requirements include:

- trim/reject blank incident title;
- enforce existing enum values;
- pagination bounds;
- timezone-aware timestamp handling.

Do not expose ORM objects directly as ad-hoc dictionaries.

---

## 10. Suggested code organization

A clean option:

```text
apps/api/
  main.py
  routers/
    __init__.py
    incidents.py
    investigations.py
  errors.py

opsmind/incidents/
  models.py
  schemas.py
  service.py
  lifecycle.py     # only if lifecycle logic warrants a separate small module
```

Do not split into more modules without a concrete need.

---

## 11. Database changes

No schema change is required by the current Pass 02 design.

Do not create a migration unless implementation discovers a genuinely necessary DDL change and reports it as an architecture deviation request before proceeding.

In particular, do not:

- make `external_ref` unique;
- add an idempotency table;
- add an active-run partial unique index;
- add runtime-model fields beyond those already present.

---

## 12. Testing requirements

### Unit tests

Add focused tests for:

- incident-create validation;
- blank-title rejection;
- pagination validation;
- lifecycle eligibility policy;
- active-run rule logic where practical.

### Integration/API tests

Against PostgreSQL, test at least:

1. create incident -> `201`;
2. created incident status is `DETECTED`;
3. get incident -> correct data;
4. get missing incident -> `404` + correct error code;
5. list incidents -> pagination metadata;
6. list filters by status;
7. list filters by environment;
8. list filters by severity;
9. stable default ordering;
10. register investigation -> `201 PENDING`;
11. creating a run does not change incident status;
12. second active investigation -> `409 ACTIVE_INVESTIGATION_EXISTS`;
13. run registration on closed/ineligible incident -> `409 INCIDENT_NOT_INVESTIGATABLE`;
14. get investigation -> correct data;
15. missing investigation -> `404`;
16. malformed UUID/request -> `422`;
17. validation error uses the agreed error envelope;
18. `updated_at` regression tests from Pass 01 continue to pass.

Tests must clean up their own data / use reliable fixtures.

---

## 13. Acceptance criteria

Pass 02 is accepted only if:

- all five API operations work;
- response schemas are typed and stable;
- incident status cannot be set by create request;
- incident creation starts at `DETECTED`;
- list pagination/filtering works;
- default sorting is deterministic;
- registering an investigation creates only a `PENDING` record;
- registering a run does not falsely mark investigation as started;
- duplicate active runs are rejected;
- ineligible incidents are rejected;
- domain errors use the stable envelope;
- no runtime model/provider is selected;
- no out-of-scope agent/retrieval/telemetry work appears;
- full regression suite passes;
- lint, formatting, mypy, and `make check` pass;
- Git working tree is clean after the implementation commit.

---

## 14. Front A review points after implementation

Front A will specifically review:

- route/service separation;
- transaction boundaries;
- error handling;
- query construction;
- pagination correctness;
- lifecycle guardrails;
- active-run race assumptions;
- Pydantic validation;
- absence of premature architecture;
- test quality, not merely test count.

---

## 15. Stop condition

After Pass 02 implementation and verification:

**STOP.**

Do not begin Milvus, telemetry, or agent work.

The next pass will be designed only after Front A reviews the implementation.
