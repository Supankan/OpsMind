# OpsMind

Evidence-grounded SRE incident investigation platform for distributed systems.

OpsMind autonomously investigates alerts and incidents, forms hypotheses, gathers metrics, logs, and traces from observability backends, corroborates findings with operational knowledge, and presents an evidence-backed root-cause analysis (RCA) or abstains when evidence is inconclusive.

---

## Architecture Principles

- **Modular Monolith First**: Clean module separation within a single deployable service.
- **PostgreSQL as Transactional Source of Truth**: Incidents, investigation runs, evidence, hypotheses, recommendations, and audit logs are persisted in PostgreSQL.
- **Milvus as Derived Semantic Retrieval/Memory**: Runbooks, architecture documentation, and historical incident postmortems (Milvus integration deferred to future passes).
- **Evidence Before Narrative**: All diagnostic claims must cite concrete evidence items.
- **Read-Only Telemetry Exploration**: Diagnostic actions are strictly read-only.
- **Deferred Runtime AI Model**: Runtime reasoning model selection is deferred to subsequent passes.

---

## Prerequisites

- **Host**: Windows 10/11 with WSL2 (Ubuntu 24.04/26.04)
- **Python**: Python 3.13+ managed via [uv](https://docs.astral.sh/uv/)
- **Docker & Docker Compose**: Docker Desktop with WSL2 integration
- **Make** (optional, task runner)

---

## Getting Started

### 1. Clone & Setup Environment

```bash
# Navigate to the repository
cd /mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind

# Copy environment variables template
cp .env.example .env

# Create virtual environment and install dependencies
uv venv --python 3.13
uv sync
```

### 2. Start PostgreSQL

Start the local PostgreSQL 16 container using Docker Compose:

```bash
docker compose up -d postgres
```

Verify that the database container is healthy:

```bash
docker compose ps
```

### 3. Run Database Migrations

Apply the initial Alembic migration to create the `incidents` and `investigation_runs` tables:

```bash
uv run alembic upgrade head
```

### 4. Run the API

Start the FastAPI application with `uvicorn`:

```bash
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Check the health endpoints:

- **Liveness Probe**: `curl http://localhost:8000/health/live`
  - Returns `{"status": "ok"}`
- **Readiness Probe**: `curl http://localhost:8000/health/ready`
  - Returns `{"status": "ready", "database": "connected"}`

---

## Development & Quality Commands

```bash
# Lint code with Ruff
uv run ruff check .

# Check formatting with Ruff
uv run ruff format --check .

# Format code with Ruff
uv run ruff format .

# Static type checking with Mypy
uv run mypy opsmind apps tests

# Run unit tests
uv run pytest tests/unit

# Run integration tests (requires PostgreSQL running)
uv run pytest tests/integration

# Run all tests
uv run pytest
```

Alternatively, use the provided `Makefile`:

```bash
make lint
make typecheck
make test
make run
```

---

## Repository Layout

```text
opsmind/
├── apps/
│   └── api/                  # FastAPI control plane (endpoints, routers, lifespan)
├── opsmind/
│   ├── agent/                # LangGraph investigation agent (deferred to future pass)
│   ├── incidents/            # Incidents domain: models, schemas, services
│   ├── evidence/             # Evidence collection, normalization, storage (future pass)
│   ├── retrieval/            # Knowledge retrieval & Milvus integration (future pass)
│   ├── telemetry/            # Observability adapters: Prometheus, OpenSearch, Jaeger (future pass)
│   ├── memory/               # Historical incident memory (future pass)
│   ├── runtime/              # Runtime reasoning provider (deferred)
│   ├── db/                   # Database session, base class, migrations
│   ├── settings/             # Application configuration via Pydantic Settings
│   └── common/               # Shared utilities: IDs, time, errors, logging
├── evaluation/               # Benchmark scenarios, ground truth, runner, metrics
├── knowledge/                # Runbooks, service specs, architecture references
├── infra/                    # Docker, compose, and SUT configs
├── tests/                    # Unit, contract, integration, and e2e test suites
├── docs/                     # Architecture specifications and ADRs
├── compose.yaml              # Local infrastructure (PostgreSQL)
├── pyproject.toml            # Project dependencies and tool configuration
└── uv.lock                   # Deterministic dependency lockfile
```
