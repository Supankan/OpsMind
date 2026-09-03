# OpsMind — Pass 03 Design Specification
## OpenTelemetry Demo SUT + Observability Baseline

**Status:** Front A approved design for Implementation Pass 03  
**Date:** 2026-09-03  
**Repository:** `F:\PycharmProjects\Random\RandomML\2026\OpsMind`  
**WSL path:** `/mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind`  
**Upstream SUT baseline:** OpenTelemetry Demo `3.0.0`

## 1. Objective

Pass 03 establishes a reproducible, real distributed system-under-test (SUT) and proves that its observability data is available before OpsMind implements telemetry clients or agent reasoning.

The SUT is the OpenTelemetry Demo / Astronomy Shop.

This pass must prove:
1. the selected Demo version runs reliably on this machine;
2. normal traffic is generated;
3. Prometheus metrics, OpenSearch logs, and Jaeger traces are available;
4. a known fault can be injected reproducibly;
5. that fault creates observable telemetry changes;
6. the environment can be reset to a known baseline.

The output is a **known-good diagnostic target**, not an AI subsystem.

## 2. Separation from later passes

```text
Pass 03: known-good SUT + known-good telemetry
                    ↓
Pass 04: typed OpsMind telemetry clients
                    ↓
Later: evidence system + retrieval + agent
```

Do not build OpsMind telemetry adapters while still validating the SUT.

## 3. Version and reproducibility

Pin OpenTelemetry Demo release/tag `3.0.0`.

Record:
- tag/release;
- exact upstream git commit;
- image version(s);
- initialization date;
- deployment mode;
- local overlay version.

Recommended layout:

```text
infra/otel-demo/
├── README.md
├── compose.opsmind.yaml
└── upstream/       # local clone, Git-ignored
```

Add `infra/otel-demo/upstream/` to `.gitignore`.

The helper setup process must clone/check out the pinned release when absent and must not silently follow upstream `main`.

Do not use a Git submodule unless the simple pinned-clone approach fails for a concrete reason.

## 4. Deployment mode

Use **minimal/core + official observability stack** first.

Do not use the upstream agentic mode.

Do not start the Demo Agent, MCP server, or Chatbot as part of OpsMind.

Reason:
- host has 16 GB RAM;
- Docker/WSL currently exposes about 7.7 GB;
- the first scenario does not require Kafka/accounting/fraud-detection;
- minimal mode is substantially lighter.

## 5. Resource policy

Before the Demo starts:
- OpsMind PostgreSQL may remain running;
- stop `~/milvus-readiness` without deleting its volumes;
- do not change Docker/WSL global memory limits preemptively.

Record `docker stats --no-stream` after stabilization.

If memory pressure prevents reliable operation, report measured behavior before changing global configuration.

## 6. Stable local backend access

Create an OpsMind-owned Compose overlay only where necessary so Pass 04 can access backends from the local development environment.

Target stable loopback endpoints:

```text
Web store / proxy   http://127.0.0.1:8080
Prometheus          http://127.0.0.1:9090
OpenSearch          http://127.0.0.1:9200
Jaeger              http://127.0.0.1:16686
```

Bind missing direct backend ports to `127.0.0.1`, not all interfaces, when possible.

Inspect the pinned upstream Compose first to avoid duplicate/conflicting mappings.

Do not directly modify upstream Compose files when an OpsMind overlay can provide the same behavior.

## 7. Required functional chain

The first scenario needs the core chain around:

```text
frontend
checkout
payment
cart
currency
product-catalog
shipping
email
flagd
load-generator
otel-collector
```

Observability:

```text
Prometheus
OpenSearch
Jaeger
```

Grafana may run because it belongs to the official observability layer, but future machine queries must target the real backends rather than scrape Grafana.

## 8. Reproducible helper workflow

Provide a small wrapper such as Make targets and/or scripts for:

```text
sut-setup
sut-start
sut-status
sut-stop
sut-reset
sut-verify
```

`sut-setup`:
- clones upstream if absent;
- verifies tag/commit;
- does not silently update.

`sut-start`:
- starts minimal + observability + OpsMind overlay;
- detached;
- no agentic mode.

`sut-status`:
- reports relevant container health.

`sut-stop`:
- stops SUT without deleting unrelated OpsMind state.

`sut-reset`:
- returns the fault to disabled;
- recreates/restarts services if necessary;
- documents whether telemetry backend state is cleared;
- provides a known clean observation window for future benchmarks.

## 9. Healthy-baseline verification

Before fault injection:

### Application
- frontend responds;
- load generation is active;
- normal shopping/checkout traffic exists.

### Prometheus
Verify through the HTTP API:
- backend reachable;
- query endpoint works;
- real service/collector metrics exist;
- identify at least one actual metric useful to checkout/payment investigation.

Do not invent metric names. Record the names present in the pinned 3.0.0 environment.

### OpenSearch
Verify through HTTP API:
- cluster health;
- OTel log index exists after traffic;
- recent logs can be queried;
- actual service-name/timestamp fields are identified.

Record real index and field names.

### Jaeger
Verify through API where possible:
- backend reachable;
- services discoverable;
- recent traces retrievable;
- at least one normal trace demonstrates checkout/downstream activity.

Record the query API shape useful for Pass 04.

## 10. Initial fault

Use the official feature flag:

```text
paymentServiceUnreachable
```

For this scenario the Checkout service uses a bad PaymentService address, making Payment appear unavailable.

Use the Demo's supported feature-flag mechanism. Do not edit Checkout/Payment source to simulate the failure.

Prefer a deterministic mechanism that can later be scripted.

## 11. Fault experiment

### Phase A — healthy
1. fault disabled;
2. traffic active;
3. short stabilization period;
4. capture representative metric/log/trace evidence.

### Phase B — fault
1. enable `paymentServiceUnreachable`;
2. record exact activation UTC time;
3. continue traffic;
4. capture observable changes.

Required evidence:
- TRACE: required;
- LOG: required;
- METRIC: required if a reliable relevant signal exists.

Do not fabricate metric evidence. If the scenario produces no trustworthy metric change, document that limitation and the closest useful metric signal.

### Phase C — recovery
1. disable fault;
2. record recovery time;
3. verify later traffic trends back toward normal;
4. document telemetry retention/delay.

## 12. Evaluator-only baseline manifest

Create:

```text
evaluation/baselines/payment_service_unreachable_v1.yaml
```

Include:
- scenario ID;
- SUT release and exact commit;
- fault flag;
- baseline/fault/recovery UTC windows;
- verified backends;
- queries/references used to verify evidence.

This is evaluator infrastructure.

Files under evaluator ground-truth/baseline paths must **never** be ingested into the future Milvus knowledge corpus.

Do not copy fault-answer documentation into `knowledge/`.

## 13. Ground-truth isolation

```text
evaluation/ground_truth + evaluation/baselines
                    X
         future Milvus corpus
```

The future agent must diagnose from normal operational knowledge plus live telemetry, not retrieve the hidden feature-flag answer.

## 14. Verification automation

Add a lightweight infrastructure verifier, e.g. `scripts/sut_verify.py` or shell equivalent.

It may check:
- frontend;
- Prometheus API;
- OpenSearch cluster/API;
- Jaeger API;
- expected key containers.

It must remain infrastructure verification code, not a production `opsmind.telemetry` implementation.

## 15. Documentation

Create/update:

```text
infra/otel-demo/README.md
docs/handoffs/PASS_03_SUMMARY.md
```

README must document:
- pin/tag/commit;
- setup/start/stop/reset;
- backend endpoints;
- fault activation/reset;
- resource notes;
- troubleshooting;
- explicit non-use of upstream Agent/MCP/Chatbot.

The handoff summary must contain measured results.

## 16. Verification requirements

At minimum:
1. existing OpsMind tests remain green;
2. lint/typecheck remain green;
3. Alembic remains clean;
4. SUT setup is safely rerunnable;
5. SUT starts;
6. required services stabilize;
7. frontend responds;
8. Prometheus API returns real data;
9. OpenSearch contains logs;
10. Jaeger returns services/traces;
11. fault can be enabled;
12. fault creates trace evidence;
13. fault creates log evidence;
14. metric evidence is captured or limitation documented;
15. fault can be disabled;
16. recovery/reset works;
17. actual container memory is recorded.

## 17. Acceptance criteria

Pass 03 is accepted only if:
- Demo 3.0.0 is pinned reproducibly;
- minimal + observability runs reliably;
- agentic mode is not used;
- stable local backend access is documented;
- Prometheus/OpenSearch/Jaeger contain real data;
- payment-unreachable is reproducibly injectable;
- telemetry effects are demonstrated;
- reset/recovery works;
- evaluator data is isolated from future retrieval knowledge;
- no OpsMind telemetry client or AI agent is implemented;
- regression suite stays green;
- upstream source is not accidentally committed into OpsMind.

## 18. Explicit non-goals

Do not implement:
- `opsmind.telemetry` clients;
- EvidenceItem/Hypothesis models;
- LangGraph;
- runtime AI model/provider;
- Milvus;
- embeddings/RAG;
- agent reasoning;
- frontend;
- Kubernetes;
- remediation;
- background worker;
- alert webhook ingestion.

## 19. Stop condition

After Pass 03 succeeds: **STOP**.

Pass 04 will define typed Prometheus, OpenSearch, and Jaeger contracts only after Front A review.
