# Antigravity — OpsMind Pass 03 Review Fixes

Work only in the existing OpsMind repository:

```text
F:\PycharmProjects\Random\RandomML\2026\OpsMind
```

WSL path:

```bash
/mnt/f/PycharmProjects/Random/RandomML/2026/OpsMind
```

This is a small corrective/documentation pass after Front A review of Pass 03. Do **not** start Pass 04.

## Fix 1 — Explicitly close the benchmark telemetry-leakage hole

The Pass 03 fault experiment proved the SUT and telemetry are working, but the captured Jaeger trace includes explicit OpenFeature attributes:

```text
feature_flag.key = "paymentUnreachable"
feature_flag.result.variant = "on"
feature_flag.result.value = True
```

Those fields reveal the injected benchmark fault directly.

That is acceptable for evaluator-side ground truth, but they must **not** be visible to the future OpsMind diagnostic agent during benchmark evaluation, otherwise the benchmark can be solved by reading the injected fault name rather than diagnosing from operational symptoms.

### Required changes

1. Update `evaluation/baselines/payment_service_unreachable_v1.yaml` with an explicit leakage policy, conceptually:

```yaml
agent_visibility_policy:
  forbidden_trace_attribute_prefixes:
    - feature_flag.
  rationale: >
    Feature-flag telemetry directly reveals the injected benchmark fault and
    is evaluator-only for this scenario.
```

Use a cleaner schema if appropriate, but preserve the meaning.

2. Update `infra/otel-demo/README.md` and/or evaluator documentation to state:
   - feature-flag attributes may exist in raw SUT telemetry;
   - raw telemetry is evaluator-visible;
   - future agent-facing telemetry tools must redact/filter benchmark-forbidden attributes before returning trace/log content to the agent;
   - this filtering requirement will be enforced in Pass 04 telemetry normalization/contract design.

3. Do **not** modify the upstream OTel Demo to remove OpenFeature instrumentation.
4. Do **not** delete the raw evaluator evidence. Evaluators should retain full-fidelity telemetry.
5. Do not implement the actual OpsMind telemetry sanitizer/client yet; that belongs to Pass 04.

### Acceptance condition

The benchmark design must distinguish:

```text
RAW TELEMETRY (evaluator)
    includes feature_flag.*

AGENT-VISIBLE TELEMETRY (future Pass 04)
    feature_flag.* removed/redacted for this benchmark
```

## Fix 2 — Record Git traceability correctly

The current `PASS_03_SUMMARY.md` does not clearly report the final Pass 03 implementation commit hash and working-tree status.

Update the summary to include:

- Pass 02 baseline/head from which Pass 03 started;
- Pass 03 implementation commit hash;
- this corrective documentation commit hash if separate;
- branch;
- working tree status.

Do not relabel the Pass 03 implementation commit as a baseline commit.

## Fix 3 — Document host binding exposure

The observed container table shows:

```text
frontend-proxy -> 0.0.0.0:8080 and 0.0.0.0:10000
prometheus     -> 0.0.0.0:9090
opensearch     -> 127.0.0.1:9200
jaeger         -> 127.0.0.1:16686
```

Our preferred development posture is loopback-only exposure for observability backends.

### Required action

Inspect whether the pinned 3.0.0 Compose setup can cleanly override Prometheus to `127.0.0.1:9090` using the OpsMind overlay without editing upstream files or making the Compose wrapper brittle.

- If cleanly possible, do it and verify.
- If the upstream Compose merge semantics make this unnecessarily brittle, do **not** force a fragile workaround. Document Prometheus's current `0.0.0.0:9090` exposure as a local-development limitation and why it remains.
- Frontend exposure is less important for this pass; document it accurately. Do not spend disproportionate effort rewriting upstream networking.

No firewall/system-level changes.

## Verification

After documentation/config changes, run:

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run mypy opsmind apps tests
make check
uv run alembic current
uv run alembic check
make sut-verify
```

If the Compose overlay changes, also verify frontend, Prometheus, OpenSearch, and Jaeger.

No need to repeat the full fault experiment unless the SUT/network configuration change could affect telemetry. If not repeated, say so explicitly.

## Scope restrictions

Do not implement:

- Pass 04 telemetry clients;
- telemetry normalization code inside `opsmind/`;
- evidence models;
- LangGraph;
- runtime LLM/provider;
- Milvus;
- RAG;
- frontend;
- Kubernetes;
- remediation.

## Git

Commit the correction separately.

Suggested commit message:

```text
docs: harden pass 03 benchmark isolation
```

If network-binding configuration is changed, a `fix:` commit is acceptable.

## Final report

Return:

1. Files changed
2. Benchmark leakage issue and policy added
3. Raw-vs-agent-visible telemetry rule
4. Prometheus/frontend binding outcome
5. Verification results
6. Whether the fault experiment was rerun
7. Pass 03 implementation commit hash
8. Corrective commit hash
9. Branch and working-tree status
10. Architecture deviation requests (`None` if none)

Stop after this corrective pass.
