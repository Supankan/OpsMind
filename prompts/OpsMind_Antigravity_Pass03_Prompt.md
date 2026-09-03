# Antigravity Prompt — OpsMind Implementation Pass 03
## OpenTelemetry Demo SUT + Observability Baseline

Work only in:

```text
F:\PycharmProjects\Random\RandomML\2026\OpsMind
```

WSL:

```bash
/mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind
```

Use `OpsMind_Pass03_Design_Spec.md` as the authoritative specification.

Your role is implementation/execution. Architecture/review is handled separately in ChatGPT with GPT-5.6 Sol High.

## Objective

Establish a reproducible OpenTelemetry Demo system-under-test with real Prometheus metrics, OpenSearch logs, and Jaeger traces, and prove that `paymentServiceUnreachable` produces observable telemetry.

Do not implement OpsMind telemetry clients or an AI agent.

## Upstream pin

Use OpenTelemetry Demo release/tag:

```text
3.0.0
```

Record the exact upstream git commit.

Do not finish this pass on unpinned `main`.

Recommended local clone:

```text
infra/otel-demo/upstream/
```

Git-ignore it. Do not commit the vendor repo.

Provide a repeatable setup helper.

## Deployment

Use **minimal/core + observability** first.

Do not use `make start-agentic`.

Do not add upstream Agent, MCP, or Chatbot to OpsMind.

Before starting, stop `~/milvus-readiness` without deleting volumes.

Do not change Docker/WSL memory configuration unless measured failure proves it necessary.

## OpsMind-owned wrapper

Create only small project-owned infrastructure around upstream, such as:

```text
infra/otel-demo/README.md
infra/otel-demo/compose.opsmind.yaml
scripts/sut_setup.sh
scripts/sut_start.sh
scripts/sut_status.sh
scripts/sut_stop.sh
scripts/sut_reset.sh
scripts/sut_verify.*
```

Simplify the number of scripts if cleaner.

Prefer overlays/wrappers over modifying upstream files.

## Stable local endpoints

Inspect 3.0.0 first, then ensure/document stable loopback access to:

```text
127.0.0.1:8080   web/proxy
127.0.0.1:9090   Prometheus
127.0.0.1:9200   OpenSearch
127.0.0.1:16686  Jaeger
```

Bind missing direct ports to localhost only.

## Healthy baseline

Verify using backend APIs, not only dashboards:

- frontend responds;
- load generation active;
- Prometheus API returns real service data and actual useful metric names;
- OpenSearch cluster responds, actual log index and service/timestamp fields identified;
- Jaeger API can list services/retrieve recent traces;
- at least one normal checkout-related trace exists.

Record `docker stats --no-stream`.

## Fault experiment

Use official flag:

```text
paymentServiceUnreachable
```

Do not edit Checkout/Payment source.

Perform:

```text
healthy baseline
→ enable fault
→ record UTC activation time
→ continue traffic
→ capture evidence
→ disable fault
→ record recovery
→ verify recovery
```

Capture:
- trace evidence: required;
- log evidence: required;
- metric evidence: use a trustworthy signal if available.

Do not invent metric names or force an unsupported interpretation.

## Evaluator manifest

Create:

```text
evaluation/baselines/payment_service_unreachable_v1.yaml
```

Record release/commit, scenario, UTC windows, verified backends and verification queries/references.

Clearly mark evaluator baseline/ground-truth paths as excluded from future Milvus ingestion.

Do not put exact fault-answer documentation in `knowledge/`.

## Regression checks

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

No schema changes.

## Explicit non-goals

Do not implement:
- OpsMind Prometheus/OpenSearch/Jaeger client classes;
- evidence models;
- LangGraph;
- runtime LLM;
- Milvus/retrieval;
- frontend;
- Kubernetes;
- remediation;
- worker/queue;
- alert webhook ingestion.

## Git

Commit only OpsMind-owned wrapper/config/docs/evaluator files.

Suggested commit:

```text
feat: establish otel demo observability baseline
```

Do not add `infra/otel-demo/upstream/`.

## Final handoff

Create/update:

```text
docs/handoffs/PASS_03_SUMMARY.md
```

Return:

1. Files created/changed
2. Pinned release and exact upstream commit
3. Deployment mode/effective Compose files
4. Containers/services running
5. Stable local endpoints
6. Healthy baseline verification
7. Prometheus findings
8. OpenSearch findings
9. Jaeger findings
10. `paymentServiceUnreachable` experiment
11. Recovery/reset verification
12. Measured resource usage
13. OpsMind regression results
14. Known limitations
15. Architecture deviation requests
16. Git commit hash and working tree
17. Exact next recommended step

Include concrete command/query/output details sufficient for Front A review.

Do not start Pass 04.
