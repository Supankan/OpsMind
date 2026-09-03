# OpsMind — Pass 02 Handoff Summary
## Incident & Investigation Control Plane

**Status:** Completed and verified  
**Date:** 2026-09-03  
**Implementation Front:** Antigravity (Gemini 3.8 Flash)  
**Architecture/Review Front:** ChatGPT (GPT-5.6 Sol High)  
**Baseline Commit:** `41954c9a6248f31f66eef431d564c827332ef864`  

---

## 1. Executive Summary

Pass 02 implements the **Incident and Investigation Control Plane** for OpsMind, building directly on the verified Pass 01 modular-monolith foundation. 

This pass introduces the durable API and service layer for creating, querying, and listing operational incidents, as well as registering and inspecting automated investigation runs. In accordance with non-goals, this pass strictly creates and inspects durable state; it does not execute investigations or integrate runtime AI models.

All 5 API operations, lifecycle guardrails, concurrency conflict protections, and standardized error envelopes have been implemented, verified through 51 automated unit and integration tests (100% pass), and confirmed via live API smoke testing against the running FastAPI application and PostgreSQL 16 Alpine database.

---

## 2. Files Created & Changed

### Created Files
- [`opsmind/incidents/lifecycle.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/incidents/lifecycle.py): Defines investigatable incident statuses, non-investigatable incident statuses, active run statuses, and helper predicate functions.
- [`apps/api/errors.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/errors.py): Implements application error formatting and global exception handlers for `OpsMindError`, `RequestValidationError` (422), and fallback internal server errors.
- [`apps/api/routers/__init__.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/routers/__init__.py): Router package exports.
- [`apps/api/routers/incidents.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/routers/incidents.py): Route handlers for `POST /api/v1/incidents`, `GET /api/v1/incidents/{id}`, `GET /api/v1/incidents`, and `POST /api/v1/incidents/{id}/investigations`.
- [`apps/api/routers/investigations.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/routers/investigations.py): Route handler for `GET /api/v1/investigations/{run_id}`.
- [`tests/unit/test_lifecycle.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/tests/unit/test_lifecycle.py): Unit tests for lifecycle eligibility partition and active run status detection.
- [`tests/unit/test_incident_schemas.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/tests/unit/test_incident_schemas.py): Unit tests for Pydantic validation rules, whitespace trimming, blank title rejection, forbidden extra fields, and error payload structure.
- [`tests/integration/test_incident_control_plane.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/tests/integration/test_incident_control_plane.py): Full integration test suite (18 scenarios) against PostgreSQL.
- [`docs/handoffs/PASS_02_SUMMARY.md`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/docs/handoffs/PASS_02_SUMMARY.md): This comprehensive handoff document.

### Modified Files
- [`opsmind/common/errors.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/common/errors.py): Added domain error classes: `IncidentNotFoundError` (404), `InvestigationNotFoundError` (404), `IncidentNotInvestigatableError` (409), `ActiveInvestigationExistsError` (409), and `ValidationError` (422).
- [`opsmind/incidents/schemas.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/incidents/schemas.py): Implemented `IncidentCreate`, `IncidentRead`, `IncidentDetailRead`, `IncidentListResponse`, `InvestigationRunRead`, and `ErrorResponse`.
- [`opsmind/incidents/service.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/opsmind/incidents/service.py): Implemented synchronous business service layer (`create_incident`, `get_incident`, `list_incidents`, `register_investigation_run`, `get_investigation_run`).
- [`apps/api/main.py`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/apps/api/main.py): Registered global error handlers and mounted incidents and investigations routers.
- [`pyproject.toml`](file:///f:/PycharmProjects/Random/RandomML/2026/OpsMind/pyproject.toml): Configured Ruff lint ignore for rule `B008` (function calls in FastAPI `Depends`/`Query` defaults).

---

## 3. API Endpoints Implemented

| Method | Path | Status Code | Description |
|---|---|---|---|
| `POST` | `/api/v1/incidents` | `201 Created` | Creates a new incident. Status is automatically forced to `DETECTED`. Non-idempotent. |
| `GET` | `/api/v1/incidents/{incident_id}` | `200 OK` | Retrieves incident detail by UUID, including `investigation_run_count`. |
| `GET` | `/api/v1/incidents` | `200 OK` | Lists incidents with pagination (`limit`, `offset`), filtering (`status`, `environment`, `severity`), and deterministic sorting (`detected_at DESC, id DESC`). |
| `POST` | `/api/v1/incidents/{incident_id}/investigations` | `201 Created` | Registers a new automated investigation run in `PENDING` status. Rejects if incident is closed or has an active run. |
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
4. **Active Run Concurrency Guardrail**:
   - If an incident already has an investigation run in `PENDING` or `RUNNING` status, attempts to register a new run are rejected with HTTP 409 and code `ACTIVE_INVESTIGATION_EXISTS`.
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
| `ACTIVE_INVESTIGATION_EXISTS` | `409 Conflict` | Incident already has a `PENDING` or `RUNNING` run |
| `VALIDATION_ERROR` | `422 Unprocessable Content` | Request payload/parameter fails Pydantic validation or malformed UUID |
| `INTERNAL_ERROR` | `500 Internal Server Error` | Unhandled internal exception; logged safely without leaking internals |

---

## 6. Database / Migration Changes

- **DDL Changes:** **None.**
- The initial migration `20260903_0818_bc111d17ffb2_create_initial_incident_and_.py` already contained all necessary tables, columns, indexes, and foreign keys.
- Verified with Alembic:
  - `uv run alembic current` -> `bc111d17ffb2 (head)`
  - `uv run alembic check` -> `No new upgrade operations detected.`

---

## 7. Automated Verification Results

### 7.1 Test Suite (`uv run pytest -v`)
**51 tests executed, 51 passed** (0 failures, 0 warnings) in 4.11s:

- **Health Probes (3 tests)**:
  - `test_health_live_endpoint`: PASSED
  - `test_health_ready_endpoint_connected`: PASSED
  - `test_health_ready_endpoint_disconnected`: PASSED
- **Control Plane API Integration (13 tests)**:
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
- **PostgreSQL Connectivity & Timestamps (4 tests)**:
  - `test_postgres_live_connectivity`: PASSED
  - `test_incident_and_run_persistence_lifecycle`: PASSED
  - `test_incident_updated_at_advances`: PASSED (Pass 01 regression verified)
  - `test_investigation_run_updated_at_advances`: PASSED (Pass 01 regression verified)
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

### 7.3 Formatter (`uv run ruff format --check .`)
- Result: **66 files already formatted** (100% compliant).

### 7.4 Static Type Checking (`uv run mypy opsmind apps tests`)
- Result: **Success: no issues found in 52 source files** (strict typing).

### 7.5 Pipeline Check (`make check`)
- Result: Clean end-to-end execution of `ruff check`, `ruff format --check`, `mypy`, and `pytest`. Exit code 0.

---

## 8. Live API Smoke-Test Results

A live server instance was booted (`uvicorn apps.api.main:app --host 127.0.0.1 --port 8000`) and validated end-to-end via live HTTP requests against PostgreSQL:

```text
--- 1. Testing Health Readiness ---
Status: 200, Body: {"status":"ready","database":"connected"}

--- 2. Testing Incident Creation (POST /api/v1/incidents) ---
HTTP Status: 201
Created Incident ID: c2109699-9ebe-4a58-9ff3-55540573a91f
Status: DETECTED
Title: Checkout Service 500 Spike

--- 3. Testing Incident Detail Retrieval (GET /api/v1/incidents/{id}) ---
HTTP Status: 200
Incident Title: Checkout Service 500 Spike
Investigation Run Count: 0

--- 4. Testing Investigation Run Registration (POST /api/v1/incidents/{id}/investigations) ---
HTTP Status: 201
Registered Run ID: f98fec95-c213-439e-8132-a1183a8f9627
Run Status: PENDING
Model Provider: None

--- 5. Testing Duplicate Active Run Rejection (POST .../investigations) ---
HTTP Status (Expected 409): 409
Error Code: ACTIVE_INVESTIGATION_EXISTS
Error Message: Incident c2109699-9ebe-4a58-9ff3-55540573a91f already has an active investigation run (f98fec95-c213-439e-8132-a1183a8f9627).

--- 6. Testing Investigation Retrieval (GET /api/v1/investigations/{id}) ---
HTTP Status: 200
Run ID: f98fec95-c213-439e-8132-a1183a8f9627
Run Status: PENDING

--- 7. Testing Incident Listing (GET /api/v1/incidents?status=DETECTED) ---
HTTP Status: 200
Total Matches: 1
Items Returned: 1
First Item Title: Checkout Service 500 Spike

--- 8. Testing Malformed UUID (GET /api/v1/incidents/invalid-uuid) ---
HTTP Status (Expected 422): 422
Error Code: VALIDATION_ERROR
Validation Error Message: Request validation failed.

All live smoke test assertions succeeded cleanly!
```

---

## 9. Known Limitations

- **No Public Status Mutation Endpoints:** Transitioning incidents between states (e.g. `DETECTED` -> `INVESTIGATING` -> `RESOLVED`) is currently reserved for the future execution worker/agent.
- **No Background Execution:** Investigation runs remain in `PENDING` status; no worker or queue processes them yet.
- **No Idempotency-Key Header:** Duplicate incident creation with identical `external_ref` values succeeds and creates distinct records as specified for V0.
- **Synchronous Service Calls:** DB transactions operate synchronously per request within FastAPI's threadpool worker.

---

## 10. Architecture Deviation Requests

**`None`**  
The implementation strictly adhered to `OpsMind_Pass02_Design_Spec.md` without deviations or schema changes.

---

## 11. Git Commit Hash & Working Tree Status

- **Commit Message:** `feat: add incident and investigation control plane`
- **Branch:** `main`
- **Working Tree:** Clean.

---

## 12. Exact Next Recommended Step

**Pass 03: Telemetry Ingestion / Mock Collector & SUT Baseline**  
Awaiting review by Front A (ChatGPT with GPT-5.6 Sol High). Do not proceed to Pass 03 until Front A provides review feedback and design specifications.
