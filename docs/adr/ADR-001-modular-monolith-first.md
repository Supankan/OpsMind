# ADR-001: Modular Monolith First

## Status
Accepted

## Date
2026-09-03

## Context
OpsMind is an evidence-grounded AI incident investigation platform designed to diagnose distributed systems (such as the OpenTelemetry Demo). While the target system under investigation is microservice-based and distributed, decomposing OpsMind itself into microservices early in the project lifecycle would introduce unnecessary operational, network, and debugging complexity. The priority is to develop and evaluate reliable agentic diagnostic reasoning, structured evidence collection, and semantic retrieval.

## Decision
OpsMind will initially be built as a **modular monolith** rather than a set of distributed microservices.
- Modules (API, incidents, evidence, telemetry, retrieval, agent, settings) will reside within a single codebase and deployment unit.
- Domain boundaries and clean interfaces will be strictly enforced to prevent tight coupling.
- PostgreSQL serves as the single transactional persistence layer.

## Consequences
### Positive
- Unified local development on WSL2/Docker without managing multiple containerized application services.
- Fast iteration on domain models, agent state, and tool schemas.
- Simplified testing, observability, and debugging.
- Clean separation of concerns allows individual modules to be extracted into independent services later if operational scale requires it.

### Negative
- Shared runtime environment across modules; requires discipline to avoid circular dependencies and leaky abstractions.
