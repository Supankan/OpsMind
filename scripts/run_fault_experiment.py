#!/usr/bin/env python3
"""Run the paymentServiceUnreachable fault experiment against OpenTelemetry Demo SUT.

Executes Phase A (Healthy), Phase B (Fault Injection), and Phase C (Recovery).
Captures trace, log, and metric evidence across all three phases.
"""

import json
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FLAGD_PATH = REPO_ROOT / "infra" / "otel-demo" / "upstream" / "src" / "flagd" / "demo.flagd.json"
RESULTS_PATH = REPO_ROOT / "evaluation" / "baselines" / "experiment_raw_evidence.json"


def query_url(url: str, post_data: dict | None = None) -> dict:
    if post_data is not None:
        data = json.dumps(post_data).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def set_flag(flag_name: str, variant: str) -> None:
    print(f"Setting flag {flag_name} -> {variant}...")
    with open(FLAGD_PATH) as f:
        data = json.load(f)
    if flag_name in data.get("flags", {}):
        data["flags"][flag_name]["defaultVariant"] = variant
    with open(FLAGD_PATH, "w") as f:
        json.dump(data, f, indent=2)

    # Trigger flagd restart to ensure immediate client uptake
    compose_cmd = [
        "docker",
        "compose",
        "--env-file",
        ".env",
        "--env-file",
        ".env.override",
        "-f",
        "compose.yaml",
        "-f",
        "compose.observability.yaml",
        "-f",
        "../compose.opsmind.yaml",
        "restart",
        "flagd",
    ]
    subprocess.run(
        compose_cmd,
        cwd=REPO_ROOT / "infra" / "otel-demo" / "upstream",
        check=True,
        capture_output=True,
    )
    print("Flag updated and flagd restarted.")


def main() -> None:
    print("==================================================")
    print("Starting paymentServiceUnreachable Fault Experiment")
    print("==================================================")

    evidence = {
        "scenario_id": "payment_service_unreachable_v1",
        "flag_name": "paymentUnreachable",
        "description": "Simulates payment service unreachable from checkout service (badAddress:50051)",
    }

    # ----------------------------------------------------
    # PHASE A: Healthy Baseline
    # ----------------------------------------------------
    print("\n--- PHASE A: Healthy Baseline ---")
    set_flag("paymentUnreachable", "off")
    print("Waiting 30 seconds for clean baseline traffic...")
    phase_a_start = datetime.now(UTC).isoformat()
    time.sleep(30)
    phase_a_end = datetime.now(UTC).isoformat()

    # Capture healthy trace
    healthy_traces = query_url(
        "http://127.0.0.1:16686/jaeger/ui/api/traces?service=checkout&limit=5"
    )
    healthy_trace = None
    for t in healthy_traces.get("data", []):
        # Find trace without error tag
        has_error = any(
            any(tag.get("key") == "error" and tag.get("value") is True for tag in s.get("tags", []))
            for s in t.get("spans", [])
        )
        if not has_error:
            healthy_trace = {
                "traceID": t["traceID"],
                "spans_count": len(t["spans"]),
                "services": list({p["serviceName"] for p in t["processes"].values()}),
            }
            break

    print(f"Healthy trace captured: {healthy_trace}")

    # Capture healthy log count
    healthy_logs = query_url(
        "http://127.0.0.1:9200/_search",
        post_data={
            "query": {"bool": {"must": [{"match": {"resource.service.name": "checkout"}}]}},
            "size": 2,
            "sort": [{"@timestamp": {"order": "desc"}}],
        },
    )
    healthy_log_sample = healthy_logs.get("hits", {}).get("hits", [])

    evidence["phase_a_healthy"] = {
        "start_utc": phase_a_start,
        "end_utc": phase_a_end,
        "trace": healthy_trace,
        "log_sample": [
            {
                "timestamp": h["_source"].get("@timestamp"),
                "service": h["_source"].get("resource", {}).get("service.name"),
                "body": h["_source"].get("body"),
                "severity": h["_source"].get("severity", {}).get("text"),
            }
            for h in healthy_log_sample
        ],
    }

    # ----------------------------------------------------
    # PHASE B: Fault Injection
    # ----------------------------------------------------
    print("\n--- PHASE B: Fault Injection (paymentUnreachable -> on) ---")
    fault_start = datetime.now(UTC).isoformat()
    set_flag("paymentUnreachable", "on")
    print("Fault enabled. Waiting 60 seconds for fault traffic to accumulate...")
    time.sleep(60)
    fault_end = datetime.now(UTC).isoformat()

    # Capture fault trace
    fault_traces = query_url(
        "http://127.0.0.1:16686/jaeger/ui/api/traces?service=checkout&limit=15"
    )
    error_trace = None
    for t in fault_traces.get("data", []):
        error_spans = [
            s
            for s in t.get("spans", [])
            if any(
                tag.get("key") == "error" and tag.get("value") is True for tag in s.get("tags", [])
            )
        ]
        if error_spans:
            error_trace = {
                "traceID": t["traceID"],
                "spans_count": len(t["spans"]),
                "error_spans_count": len(error_spans),
                "sample_error_span": {
                    "operationName": error_spans[0].get("operationName"),
                    "tags": error_spans[0].get("tags", []),
                },
            }
            break

    print(f"Error trace captured: {error_trace}")

    # Capture fault logs (checkout errors)
    fault_logs = query_url(
        "http://127.0.0.1:9200/_search",
        post_data={
            "query": {
                "bool": {
                    "must": [
                        {"match": {"resource.service.name": "checkout"}},
                        {"match_phrase": {"body": "could not charge the card"}},
                    ]
                }
            },
            "size": 2,
            "sort": [{"@timestamp": {"order": "desc"}}],
        },
    )
    fault_log_hits = fault_logs.get("hits", {}).get("hits", [])
    print(f"Error logs matched: {fault_logs.get('hits', {}).get('total', {})}")

    # Capture metric evidence: span metrics error count
    metric_res = query_url(
        "http://127.0.0.1:9090/api/v1/query?query="
        + urllib.parse.quote('traces_span_metrics_calls_total{status_code="STATUS_CODE_ERROR"}')
    )
    metric_sample = metric_res.get("data", {}).get("result", [])

    evidence["phase_b_fault"] = {
        "start_utc": fault_start,
        "end_utc": fault_end,
        "trace": error_trace,
        "log_sample": [
            {
                "timestamp": h["_source"].get("@timestamp"),
                "service": h["_source"].get("resource", {}).get("service.name"),
                "body": h["_source"].get("body"),
                "severity": h["_source"].get("severity", {}).get("text"),
            }
            for h in fault_log_hits
        ],
        "metric_sample": metric_sample[:3]
        if metric_sample
        else "No STATUS_CODE_ERROR counter active",
    }

    # ----------------------------------------------------
    # PHASE C: Recovery
    # ----------------------------------------------------
    print("\n--- PHASE C: Recovery (paymentUnreachable -> off) ---")
    recovery_start = datetime.now(UTC).isoformat()
    set_flag("paymentUnreachable", "off")
    print("Fault disabled. Waiting 45 seconds for recovery...")
    time.sleep(45)
    recovery_end = datetime.now(UTC).isoformat()

    # Verify recovery trace
    recent_traces = query_url(
        "http://127.0.0.1:16686/jaeger/ui/api/traces?service=checkout&limit=5"
    )
    recovery_trace = None
    for t in recent_traces.get("data", []):
        has_error = any(
            any(tag.get("key") == "error" and tag.get("value") is True for tag in s.get("tags", []))
            for s in t.get("spans", [])
        )
        if not has_error:
            recovery_trace = {
                "traceID": t["traceID"],
                "spans_count": len(t["spans"]),
                "status": "healthy_cleared_errors",
            }
            break

    print(f"Recovery trace captured: {recovery_trace}")

    evidence["phase_c_recovery"] = {
        "start_utc": recovery_start,
        "end_utc": recovery_end,
        "recovery_trace": recovery_trace,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(evidence, f, indent=2)

    print(f"\nExperiment finished successfully! Evidence saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
