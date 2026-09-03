# Antigravity Prompt — OpsMind Implementation Pass 01

You are the implementation/coding front for the **OpsMind** project.

A separate architecture/reasoning/review front is being handled in ChatGPT with GPT-5.6 Sol High. Your job in this pass is to implement the approved specification faithfully, test it locally, and report results. Do not expand the scope or redesign the architecture on your own.

## Critical clarification

The two AI models being used to **develop** OpsMind are external development tools:

- GPT-5.6 Sol High in ChatGPT -> architecture, planning, analysis, evaluation design, implementation review.
- Gemini 3.8 Flash in Antigravity -> coding, execution, testing, routine implementation debugging.

These are **not** assumed to be the AI models used inside OpsMind at runtime.

The runtime AI model/provider for OpsMind is intentionally **TBD** and will be selected later. Do not add Google/OpenAI/Gemini runtime integrations, API keys, provider abstractions beyond a harmless placeholder, or runtime prompt engineering in this pass.

## Authoritative specification

Use the accompanying file:

`OpsMind_Pass1_Architecture_Spec_v2.md`

as the authoritative architecture baseline.

If implementation reveals a need to change a major architectural decision, do not silently change it. Record an **architecture deviation request** in your final report.

## Environment

Develop only on this PC, using the existing WSL2 Ubuntu environment.

Authoritative project location on Windows:

```text
F:\PycharmProjects\Random\RandomML\2026\OpsMind
```

When running commands inside WSL, use the same folder through:

```bash
/mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind
```

This folder is already loaded as the Antigravity project context.

Do **not** create another repository at `/home/user/projects/opsmind` or any other path.

The machine already has working:

- Windows 10 + WSL2
- Ubuntu 26.04 LTS
- Docker Desktop with WSL integration
- Docker Compose
- PostgreSQL container testing
- Milvus 2.6.22 testing

Do not alter or reset WSL/Docker system configuration unless explicitly necessary and approved.

For the application project, use a project-managed Python runtime. Prefer Python 3.13 via `uv` as specified, rather than relying on Ubuntu's system Python 3.14.

---

# Implementation Pass 01 — Repository Bootstrap

## Objective

Create the OpsMind repository foundation without implementing agent behavior, telemetry integration, or Milvus retrieval yet.

## Required work

1. Create the repository structure defined in the architecture specification.
2. Configure a Python 3.13 project using `uv`.
3. Create `pyproject.toml`, dependency lock, Ruff, and static type checking.
4. Add FastAPI with:
   - `GET /health/live`
   - `GET /health/ready`
5. Add configuration using Pydantic settings.
6. Add PostgreSQL to the project's local `compose.yaml`.
7. Add SQLAlchemy 2 + Alembic.
8. Create initial database models only for:
   - `Incident`
   - `InvestigationRun`
9. Create the initial Alembic migration.
10. Add structured application logging.
11. Add unit tests for settings/domain models.
12. Add an integration test for PostgreSQL connectivity.
13. Add `.env.example`.
14. Add a minimal `Makefile` or equivalent task commands.
15. Add CI-friendly commands for:
    - lint
    - typecheck
    - test
16. Write a concise development README.
17. Copy the authoritative architecture specification into `docs/`.
18. Create the ADR directory and implement ADR-001 through ADR-003 as short accepted records.

## Explicit non-goals

Do **not** implement:

- LangGraph;
- agent reasoning;
- any runtime LLM/model/provider integration;
- runtime model selection;
- runtime prompt engineering;
- Milvus retrieval;
- embeddings;
- Prometheus;
- OpenSearch;
- Jaeger;
- OpenTelemetry Demo integration;
- frontend;
- Celery;
- Redis;
- Kubernetes;
- remediation;
- incident memory.

Do not add dependencies for these future features merely because they may be used later.

## Architectural constraints

- OpsMind begins as a modular monolith.
- PostgreSQL is the transactional source of truth.
- Milvus will later be a derived semantic retrieval/memory system, not the source of truth.
- No generic shell/network/SQL capability should be introduced for a future agent.
- Runtime model/provider remains TBD.
- Keep future modules represented by directories/placeholders only where the specification explicitly calls for them; do not implement them.
- Avoid unnecessary abstractions that are not required by this pass.

## Acceptance criteria

The pass is complete only if:

- a clean environment bootstrap works;
- the FastAPI app starts successfully;
- `/health/live` succeeds;
- `/health/ready` correctly reports PostgreSQL readiness;
- Alembic migration creates the two initial tables;
- unit tests pass;
- PostgreSQL integration test passes;
- Ruff/lint passes;
- static type checking passes;
- the app can run locally from WSL;
- the application has a working Dockerfile or a clearly documented containerization stub, as appropriate to the specification;
- no out-of-scope architecture has been implemented.

## Work style

Proceed incrementally.

Before making a broad/system-level change, explain why it is required.

You may fix routine implementation issues autonomously, but stop and report rather than making unapproved changes to:

- architecture;
- database responsibilities;
- major dependencies;
- runtime model strategy;
- agent-state semantics;
- security boundaries;
- evaluation methodology.

Do not begin Pass 02 automatically.

## Final implementation report

At completion, return exactly these sections:

1. **Files created/changed**
2. **Commands run**
3. **Dependency versions selected**
4. **Tests run and results**
5. **Lint/typecheck results**
6. **Local run verification**
7. **Known limitations**
8. **Architecture deviation requests** — write `None` if there are none
9. **Exact next recommended implementation step**

Also include the current Git status and, if Git was initialized, the current commit hash.

Stop after the report and wait for review.
