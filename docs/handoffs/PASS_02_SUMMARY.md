# OpsMind — Pass 02 Handoff Summary
## Incident & Investigation Control Plane

**Status:** Completed and verified (includes concurrency and lint hardening)  
**Date:** 2026-09-03  
**Implementation Front:** Antigravity (Gemini 3.8 Flash)  
**Architecture/Review Front:** ChatGPT (GPT-5.6 Sol High)  
**Baseline Commit:** `41954c9a6248f31f66eef431d564c827332ef864`  
**Pass 02 Feature Commit:** `5dcb7a65a2eaafe8ccc0b6ae48f192055284fc84`  

---

## 1. Executive Summary

Pass 02 implements the **Incident and Investigation Control Plane** for OpsMind, building directly on the verified Pass 01 modular-monolith foundation. 

This pass introduces the durable API and service layer for creating, querying, and listing operational incidents, as well as registering and inspecting automated investigation runs. In accordance with non-goals, this pass strictly creates and inspects durable state; it does not execute investigations or integrate runtime AI models.

Following Front A review, the control plane was hardened:
1. **Race-Safe Concurrency**: Replaced optimistic sequential querying with PostgreSQL row-level locking (`SELECT ... FOR UPDATE` via SQLAlchemy's `.with_for_update()`) on the parent incident row within the registration transaction.
2. **Lint Cleanliness**: Completely removed the global Ruff `B008` ignore rule by refactoring all route signatures to standard `typing.Annotated` dependency and query declarations.

All 5 API operations, lifecycle guardrails, race-safe concurrency controls, and standardized error envelopes have been verified through **52 automated unit and integration tests** (100% pass rate) and confirmed via live API smoke testing against the running FastAPI application and PostgreSQL 16 Alpine database.

---

## 2. Files Created & Changed

### Created Files
- [`opsmind/incidents/lifecycle.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/incidents/lifecycle.py): Defines investigatable incident statuses, non-investigatable incident statuses, active run statuses, and helper predicate functions.
- [`apps/api/errors.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/errors.py): Implements application error formatting and global exception handlers for `OpsMindError`, `RequestValidationError` (422), and fallback internal server errors.
- [`apps/api/routers/__init__.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/routers/__init__.py): Router package exports.
- [`apps/api/routers/incidents.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/routers/incidents.py): Route handlers for `POST /api/v1/incidents`, `GET /api/v1/incidents/{id}`, `GET /api/v1/incidents`, and `POST /api/v1/incidents/{id}/investigations` using `typing.Annotated`.
- [`apps/api/routers/investigations.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/routers/investigations.py): Route handler for `GET /api/v1/investigations/{run_id}` using `typing.Annotated`.
- [`tests/unit/test_lifecycle.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/tests/unit/test_lifecycle.py): Unit tests for lifecycle eligibility partition and active run status detection.
- [`tests/unit/test_incident_schemas.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/tests/unit/test_incident_schemas.py): Unit tests for Pydantic validation rules, whitespace trimming, blank title rejection, forbidden extra fields, and error payload structure.
- [`tests/integration/test_incident_control_plane.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/tests/integration/test_incident_control_plane.py): Full integration test suite (19 scenarios) against PostgreSQL, including multi-threaded barrier-synchronized concurrency tests.
- [`docs/handoffs/PASS_02_SUMMARY.md`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/docs/handoffs/PASS_02_SUMMARY.md): This comprehensive handoff document.

### Modified Files
- [`opsmind/common/errors.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/common/errors.py): Added domain error classes: `IncidentNotFoundError` (404), `InvestigationNotFoundError` (404), `IncidentNotInvestigatableError` (409), `ActiveInvestigationExistsError` (409), and `ValidationError` (422).
- [`opsmind/incidents/schemas.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/incidents/schemas.py): Implemented `IncidentCreate`, `IncidentRead`, `IncidentDetailRead`, `IncidentListResponse`, `InvestigationRunRead`, and `ErrorResponse`.
- [`opsmind/incidents/service.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/incidents/service.py): Implemented synchronous business service layer with PostgreSQL row-level locking (`with_for_update()`) in `register_investigation_run`.
- [`apps/api/main.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/main.py): Registered global error handlers and mounted incidents and investigations routers.
- [`pyproject.toml`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/pyproject.toml): Global `B008` ignore rule removed; all Ruff lint rules are active.

---

## 3. API Endpoints Implemented

| Method | Path | Status Code | Description |
|---|---|---|---|
| `POST` | `/api/v1/incidents` | `201 Created` | Creates a new incident. Status is automatically forced to `DETECTED`. Non-idempotent. |
| `GET` | `/api/v1/incidents/{incident_id}` | `200 OK` | Retrieves incident detail by UUID, including `investigation_run_count`. |
| `GET` | `/api/v1/incidents` | `200 OK` | Lists incidents with pagination (`limit`, `offset`), filtering (`status`, `environment`, `severity`), and deterministic sorting (`detected_at DESC, id DESC`). |
| `POST` | `/api/v1/incidents/{incident_id}/investigations` | `201 Created` | Registers a new automated investigation run in `PENDING` status. Race-safe via row-level locking. |
| `GET` | `/api/v1/investigations/{run_id}` | `200 OK` | Retrieves an investigation run by UUID. |

---

## 4. Business & Lifecycle Rules Implemented

1. **Initial Incident Status Guardrail**:
   - `IncidentCreate` does not accept a `status` field; extra fields are rejected (`extra="forbid"`).
   - All newly created incidents unconditionally start in `IncidentStatus.DETECTED`.
2. **Title Validation**:
   - Title is trimmed of leading and trailing whitespace. Empty or whitespace-only titles are rejected with HTTP 422 `VALIDATION_ERROR`.
3. **Investigation Run Creation**:
   - Runs are registered strictly in `InvestigationRunStatus.PENDING`.
   - Runtime model fields (`runtime_model_provider`, `runtime_model_name`, `prompt_context_version`) remain `None`/null.
   - Crucial rule: **Creating a `PENDING` run does not alter the incident status.**
4. **Race-Safe Active Run Concurrency Guardrail**:
   - Sequential requests: If an active run (`PENDING` or `RUNNING`) exists, registration is rejected with HTTP 409 and code `ACTIVE_INVESTIGATION_EXISTS`.
   - Concurrent requests: Registration executes inside a database transaction that first locks the parent incident row using `SELECT ... FOR UPDATE` (`with_for_update()`). Concurrent requests for the same incident serialize at the database level: the first transaction acquires the lock, confirms no active run, inserts the `PENDING` run, and commits. The blocked transaction unblocks, re-evaluates the active-run query under read-committed semantics, detects the newly committed active run, and raises `ACTIVE_INVESTIGATION_EXISTS`.
5. **Incident Eligibility Policy**:
   - Investigations may only be registered for incidents in:
     - `DETECTED`
     - `TRIAGING`
     - `INVESTIGATING`
     - `INCONCLUSIVE`
     - `INVESTIGATION_FAILED`
   - Attempts to register an investigation for closed/ineligible incidents (`ROOT_CAUSE_PROPOSED`, `REMEDIATION_PROPOSED`, `RESOLVED`, `POSTMORTEM_COMPLETE`, `CANCELLED`) are rejected with HTTP 409 and code `INCIDENT_NOT_INVESTIGATABLE`.
6. **Deterministic Pagination & Sorting**:
   - Incidents list orders by `Incident.detected_at.desc(), Incident.id.desc()` to guarantee stable ordering even when timestamps match.
   - Total count reflects the filtered dataset prior to applying `limit` and `offset`.

---

## 5. Error Contract Implementation

All API errors return the standardized JSON envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable explanation.",
    "details": {}
  }
}
```

### Domain Error Codes & Status Mapping

| Error Code | HTTP Status | Trigger Condition |
|---|---|---|
| `INCIDENT_NOT_FOUND` | `404 Not Found` | Requested incident UUID does not exist |
| `INVESTIGATION_NOT_FOUND` | `404 Not Found` | Requested investigation run UUID does not exist |
| `INCIDENT_NOT_INVESTIGATABLE` | `409 Conflict` | Incident is in an ineligible/closed status |
| `ACTIVE_INVESTIGATION_EXISTS` | `409 Conflict` | Incident already has a `PENDING` or `RUNNING` run (serial or concurrent) |
| `VALIDATION_ERROR` | `422 Unprocessable Content` | Request payload/parameter fails Pydantic validation or malformed UUID |
| `INTERNAL_ERROR` | `500 Internal Server Error` | Unhandled internal exception; logged safely without leaking internals |

---

## 6. Database / Migration Changes

- **DDL Changes:** **None.**
- Row-level locking relies natively on PostgreSQL's standard transaction engine without requiring new tables, triggers, or index changes.
- Verified with Alembic:
  - `uv run alembic current` -> `bc111d17ffb2 (head)`
  - `uv run alembic check` -> `No new upgrade operations detected.`

---

## 7. Automated Verification Results

### 7.1 Test Suite (`uv run pytest -v`)
**52 tests executed, 52 passed** (0 failures, 0 warnings) in 4.14s:

- **Health Probes (3 tests)**:
  - `test_health_live_endpoint`: PASSED
  - `test_health_ready_endpoint_connected`: PASSED
  - `test_health_ready_endpoint_disconnected`: PASSED
- **Control Plane API Integration (14 tests)**:
  - `test_create_incident_success`: PASSED
  - `test_get_incident_success`: PASSED
  - `test_get_incident_missing`: PASSED
  - `test_list_incidents_pagination`: PASSED
  - `test_list_incidents_filters`: PASSED
  - `test_list_incidents_deterministic_ordering`: PASSED
  - `test_register_investigation_run_success`: PASSED
  - `test_register_investigation_duplicate_active_rejected`: PASSED
  - `test_register_investigation_ineligible_incident_rejected`: PASSED
  - `test_get_investigation_run_success`: PASSED
  - `test_get_investigation_run_missing`: PASSED
  - `test_malformed_uuid_validation_error`: PASSED
  - `test_validation_error_envelope_on_blank_title`: PASSED
  - `test_concurrent_investigation_registration`: PASSED (**NEW** — multi-threaded barrier-synchronized concurrency test verifying serialization and single active run constraint)
- **PostgreSQL Connectivity & Timestamps (4 tests)**:
  - `test_postgres_live_connectivity`: PASSED
  - `test_incident_and_run_persistence_lifecycle`: PASSED
  - `test_incident_updated_at_advances`: PASSED
  - `test_investigation_run_updated_at_advances`: PASSED
- **Incident & Run Schemas (9 tests)**:
  - `test_incident_create_valid_minimal`: PASSED
  - `test_incident_create_whitespace_trimming`: PASSED
  - `test_incident_create_blank_title_rejected` (4 parameterized variants): PASSED
  - `test_incident_create_forbids_status_injection`: PASSED
  - `test_incident_detail_read_run_count`: PASSED
  - `test_error_response_structure`: PASSED
- **Lifecycle Policies (17 tests)**:
  - `test_is_incident_investigatable` (10 parameterized statuses): PASSED
  - `test_lifecycle_status_partition_completeness`: PASSED
  - `test_is_run_active` (6 parameterized statuses): PASSED
- **Pass 01 Domain Models & Settings (5 tests)**:
  - `test_incident_instantiation`: PASSED
  - `test_investigation_run_instantiation`: PASSED
  - `test_incident_investigation_run_relationship`: PASSED
  - `test_default_settings`: PASSED
  - `test_custom_settings_override`: PASSED

### 7.2 Linter (`uv run ruff check .`)
- Result: **All checks passed!** (0 errors).
- Note: `B008` ignore rule removed from `pyproject.toml`. All FastAPI router parameters conform via `typing.Annotated`.

### 7.3 Formatter (`uv run ruff format --check .`)
- Result: **68 files already formatted** (100% compliant).

### 7.4 Static Type Checking (`uv run mypy opsmind apps tests`)
- Result: **Success: no issues found in 52 source files** (strict typing).

### 7.5 Pipeline Check (`make check`)
- Result: Clean end-to-end execution of `ruff check`, `ruff format --check`, `mypy`, and `pytest`. Exit code 0.

---

## 8. Live API Smoke-Test Results

A live server instance was booted (`uvicorn apps.api.main:app --host 127.0.0.1 --port 8000`) and validated end-to-end via live HTTP requests against PostgreSQL:

```text
--- 1. Health Readiness ---
Status: 200, Body: {"status":"ready","database":"connected"}

--- 2. Create Incident (POST /api/v1/incidents) ---
HTTP 201: Incident 7833ea70-ab9b-4d27-9249-3c4a2c6cc594 created with status DETECTED

--- 3. Register Investigation Run ---
HTTP 201: Registered run a796398a-aa56-4403-92e1-37638c1b559c with status PENDING

--- 4. Sequential Duplicate Registration (Expect 409) ---
HTTP 409: Rejected with error code ACTIVE_INVESTIGATION_EXISTS

--- 5. Get Investigation Run ---
HTTP 200: Run status is PENDING

--- 6. Get Incident Detail with Run Count ---
HTTP 200: Investigation Run Count is 1

--- 7. List Incidents ---
HTTP 200: Total 1, items 1

--- 8. Malformed UUID (Expect 422) ---
HTTP 422: Validation error code VALIDATION_ERROR

All live smoke test checks succeeded!
```

---

## 9. Known Limitations

- **No Agent Execution / Worker:** Investigations remain in `PENDING` status until future worker passes are implemented.
- **No Public Status Mutation Endpoints:** Manual status updates (e.g. `DETECTED` -> `INVESTIGATING`) are deferred.
- **Non-Idempotent Incident Ingestion:** Multiple `POST /api/v1/incidents` requests with identical `external_ref` values create distinct records (idempotency keying deferred to alert webhook pass).
- **Synchronous Service Calls:** DB transactions operate synchronously per request within FastAPI's threadpool worker.

---

## 10. Architecture Deviation Requests

**`None`**  
The implementation strictly adhered to `OpsMind_Pass02_Design_Spec.md` and `OpsMind_Pass02_Review_Fixes_Prompt.md` without deviations or schema changes.

---

## 11. Git Commit History & Working Tree Status

- **Baseline Pass 02 Commit:** `5dcb7a6` (`feat: add incident and investigation control plane`)
- **Review Fixes Commit:** `8a0d057` (`fix: harden investigation registration concurrency`)
- **Branch:** `main`
- **Working Tree:** Clean.

---

## 12. Exact Next Recommended Step

**Pass 03: Telemetry Ingestion / Mock Collector & SUT Baseline**  
Awaiting review by Front A (ChatGPT with GPT-5.6 Sol High). Do not proceed to Pass 03 until Front A provides review feedback and design specifications.
