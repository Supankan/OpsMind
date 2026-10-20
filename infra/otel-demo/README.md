# OpenTelemetry Demo — System-Under-Test (SUT) & Observability Baseline

This directory contains the project-owned infrastructure wrapper, overlay configuration, and operational documentation for running the **OpenTelemetry Demo / Astronomy Shop** as OpsMind's target distributed system-under-test.

---

## 1. Upstream Pinning & Version Details

- **Upstream Repository:** `https://github.com/open-telemetry/opentelemetry-demo.git`
- **Release Tag:** `3.0.0`
- **Exact Git Commit:** `1755859a9de82c2e5e225be68abc401a5ebf2b4f`
- **Container Images Tag:** `ghcr.io/open-telemetry/demo:3.0.0-*` (pinned via `DEMO_VERSION=3.0.0` in `.env.override`)
- **Local Vendor Location:** `infra/otel-demo/upstream/` (strictly `.gitignore`d; never committed)

---

## 2. Architecture & Deployment Mode

### Mode: Minimal Core + Official Observability
To respect local workstation memory limits (16 GB RAM host, ~7.7 GB WSL2 Docker limit), the Demo runs in **minimal/core** mode combined with the official observability stack.

- **Included Core Services:** `frontend`, `checkout`, `payment`, `cart`, `currency`, `product-catalog`, `shipping`, `email`, `flagd`, `flagd-ui`, `load-generator`, `valkey-cart`, `astronomy-db`, `frontend-proxy`.
- **Included Observability Services:** `otel-collector`, `prometheus`, `opensearch`, `jaeger`, `grafana`, `opamp-server`.
- **Explicitly Excluded Components:**
  - Full services: Kafka, Accounting, Fraud-detection.
  - Upstream AI components: **Agent, MCP server, Chatbot are DISABLED**. OpsMind provides its own AI reasoning framework in future passes.

---

## 3. Stable Local Endpoints & Host Binding Exposure

All services are accessible on stable loopback interfaces via the OpsMind Compose overlay (`compose.opsmind.yaml`):

| Component | Target URL | Protocol / Type | Host Binding Posture |
|---|---|---|---|
| **Web Store (Frontend Proxy)** | `http://127.0.0.1:8080/` | HTTP / Envoy Proxy | `0.0.0.0:8080`, `0.0.0.0:10000` (Upstream) |
| **Prometheus API** | `http://127.0.0.1:9090/` | HTTP / Prometheus 3.13.1 | `0.0.0.0:9090` (Upstream limitation) |
| **OpenSearch Cluster** | `http://127.0.0.1:9200/` | HTTP / REST API (OpenSearch 3.7.0) | `127.0.0.1:9200` (OpsMind overlay) |
| **Jaeger UI & Query API** | `http://127.0.0.1:16686/jaeger/ui` | HTTP / Jaeger 2.19.0 (`base_path: /jaeger/ui`) | `127.0.0.1:16686` (OpsMind overlay) |
| **Grafana** (Dashboard) | `http://127.0.0.1:8080/grafana/` | HTTP / Proxied through Envoy | Internal / Proxied |
| **Feature Flags UI** | `http://127.0.0.1:8080/feature/` | HTTP / Flagd UI | Internal / Proxied |

### Host Binding Posture & Prometheus `0.0.0.0` Note
- **Loopback-Only Components (`OpenSearch`, `Jaeger`):** Upstream defines internal container ports without host bindings. `compose.opsmind.yaml` binds them strictly to `127.0.0.1:9200` and `127.0.0.1:16686`.
- **Prometheus (`0.0.0.0:9090`):** Upstream `compose.observability.yaml` binds `${PROMETHEUS_PORT}:${PROMETHEUS_PORT}` (`0.0.0.0:9090`). Docker Compose merges list-type configuration fields across multiple files by appending rather than replacing. Attempting to declare `127.0.0.1:9090:9090` in an overlay creates duplicate host bindings on port 9090, resulting in Docker port allocation errors (`address already in use`). Furthermore, `${PROMETHEUS_PORT}` is referenced internally by `PROMETHEUS_ADDR=${PROMETHEUS_HOST}:${PROMETHEUS_PORT}` for inter-service communication (e.g. Jaeger's Prometheus metrics backend); setting it to `127.0.0.1:9090` corrupts inter-container DNS and fails Docker port validation. Consequently, `prometheus` remains bound to `0.0.0.0:9090` as a known local-development characteristic of the upstream 3.0.0 Compose structure.
- **Frontend Proxy (`0.0.0.0:8080`, `0.0.0.0:10000`):** Defined upstream in `compose.yaml` to handle simulated web store traffic and Envoy admin egress.

---

## 4. Lifecycle Operations & Helper Workflows

Lifecycle management is encapsulated in standard `Makefile` targets and helper scripts in `scripts/`:

### Setup
Clones the upstream repository at tag `3.0.0`, pins `DEMO_VERSION=3.0.0` and `HOST_FILESYSTEM=/tmp` in `.env.override`:
```bash
make sut-setup
```

### Start
Starts the SUT containers in detached mode and waits for health checks:
```bash
make sut-start
```

### Status
Reports container statuses, checks the 4 loopback endpoints, and outputs memory stats:
```bash
make sut-status
```

### Automated Infrastructure Verification
Runs the standalone Python probe to verify that frontend, Prometheus, OpenSearch, and Jaeger return real data:
```bash
make sut-verify
```

### Reset
Restores feature flags in `demo.flagd.json` to their clean off state and restarts `flagd`:
```bash
make sut-reset
```

### Stop
Gracefully stops SUT containers without deleting data volumes:
```bash
make sut-stop
```

---

## 5. Fault Injection: `paymentServiceUnreachable`

The first diagnostic scenario targets payment failure from the checkout service:

- **Feature Flag Name:** `paymentUnreachable` (defined in `src/flagd/demo.flagd.json`).
- **Mechanism:** When set to `on`, the checkout service attempts to charge cards using `badAddress:50051`, simulating network unreachability / gRPC name resolution failure.
- **Manifest Reference:** Detailed ground-truth specification is maintained in `evaluation/baselines/payment_service_unreachable_v1.yaml`.
- **Trigger via Script:**
  ```bash
  python3 scripts/run_fault_experiment.py
  ```

---

## 6. Ground-Truth Isolation & Benchmark Telemetry Leakage Policy

> [!WARNING]
> Files under `evaluation/` (including `evaluation/baselines/payment_service_unreachable_v1.yaml`) are evaluator ground-truth artifacts. They must **never** be copied into `knowledge/` or ingested into the future Milvus vector store. The AI diagnostic agent must reason strictly from live observability data and operational playbooks, never by retrieving the benchmark solution.

### Telemetry Leakage Prevention (Raw vs. Agent-Visible)
In the upstream OpenTelemetry Demo, services utilize OpenFeature to toggle simulated faults. As a consequence, raw traces and logs may contain explicit feature-flag evaluation metadata:
- `feature_flag.key = "paymentUnreachable"`
- `feature_flag.result.variant = "on"`
- `feature_flag.result.value = true`

These attributes directly disclose the injected fault name, creating a benchmark telemetry-leakage vector.

To preserve benchmark evaluation integrity while maintaining full observability fidelity:
```text
RAW TELEMETRY (evaluator)
    includes feature_flag.* for ground-truth verification and Oracle assertion

AGENT-VISIBLE TELEMETRY (future Pass 04)
    feature_flag.* attributes MUST be redacted/filtered before returning telemetry to the agent
```

**Key Constraints:**
1. Upstream OpenTelemetry Demo source files are **not** modified to strip OpenFeature hooks; upstream telemetry remains authentic.
2. Raw evaluator evidence retains full-fidelity telemetry.
3. Future agent-facing telemetry normalization tools (Pass 04) must sanitize and filter benchmark-forbidden prefixes (`feature_flag.*`) before delivering trace or log payloads to the OpsMind diagnostic reasoning agent.

---

## 7. Platform Troubleshooting Notes

1. **Docker Desktop on Windows WSL2 9p Mount Bug (`otel-collector`):**
   - *Issue:* When `HOST_FILESYSTEM=/` is mounted to `/hostfs:ro`, the Go cgroup memory limiter in `otel-collector-contrib` fails to parse `/proc/self/mountinfo` due to backslashes and spaces in Windows 9p mounts (`C:\Program Files\Docker\...`).
   - *Fix:* `scripts/sut_setup.sh` sets `HOST_FILESYSTEM=/tmp` in `.env.override`, avoiding the 9p mount line in mountinfo.
2. **OpenSearch Cold-Start Timing:**
   - *Issue:* OpenSearch JVM and plugins can take up to 70 seconds to initialize on cold start.
   - *Fix:* `compose.opsmind.yaml` configures `start_period: 30s` with `retries: 20` to prevent premature startup failure.
3. **Jaeger Base Path:**
   - Upstream Jaeger 2.19 is configured with `base_path: /jaeger/ui`. Query API calls must target `http://127.0.0.1:16686/jaeger/ui/api/*`.
