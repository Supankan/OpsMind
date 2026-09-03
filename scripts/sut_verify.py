#!/usr/bin/env python3
"""Infrastructure verifier for OpenTelemetry Demo SUT and Observability backends."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def check_url(name: str, url: str) -> dict | str:
    print(f"Checking {name} at {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OpsMind-SUT-Verifier"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
            print(f"  [OK] HTTP {resp.status}")
            try:
                return json.loads(content)
            except Exception:
                return content
    except urllib.error.HTTPError as e:
        print(f"  [FAILED] HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"  [FAILED] Connection error: {e}")
        sys.exit(1)


def main() -> None:
    print("=== OpsMind SUT Infrastructure Verification ===")

    # 1. Frontend Proxy
    check_url("Frontend Proxy (Web Store)", "http://127.0.0.1:8080/")

    # 2. Prometheus
    check_url("Prometheus Readiness", "http://127.0.0.1:9090/-/ready")
    prom_data = check_url("Prometheus Query API", "http://127.0.0.1:9090/api/v1/query?query=up")
    if isinstance(prom_data, dict):
        results = prom_data.get("data", {}).get("result", [])
        print(f"  Prometheus targets active: {len(results)}")
        if not results:
            print("  [WARN] No Prometheus targets reporting 'up' yet.")

    # 3. OpenSearch
    os_health = check_url("OpenSearch Cluster Health", "http://127.0.0.1:9200/_cluster/health")
    if isinstance(os_health, dict):
        status = os_health.get("status")
        print(f"  OpenSearch cluster status: {status} (nodes: {os_health.get('number_of_nodes')})")

    # 4. Jaeger
    jaeger_services = check_url(
        "Jaeger Services API", "http://127.0.0.1:16686/jaeger/ui/api/services"
    )
    if isinstance(jaeger_services, dict):
        services = jaeger_services.get("data", [])
        print(f"  Jaeger discovered services ({len(services)}): {', '.join(services[:6])}...")
        if "frontend" in services or "checkout" in services:
            print("  Core services discovered in Jaeger trace store.")

    print("\nAll SUT observability backends verified successfully!")


if __name__ == "__main__":
    main()
