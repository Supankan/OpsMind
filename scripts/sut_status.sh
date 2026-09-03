#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${REPO_ROOT}/infra/otel-demo/upstream"
OVERLAY_FILE="${REPO_ROOT}/infra/otel-demo/compose.opsmind.yaml"

cd "${UPSTREAM_DIR}"

echo "=== SUT Container Status ==="
docker compose \
  --env-file .env \
  --env-file .env.override \
  -f compose.yaml \
  -f compose.observability.yaml \
  -f "${OVERLAY_FILE}" \
  ps

echo ""
echo "=== Loopback Endpoint Probes ==="
test_url() {
    local name="$1"
    local url="$2"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "$url" || echo "ERR")
    echo "  ${name} (${url}): HTTP ${code}"
}

test_url "Frontend Proxy" "http://127.0.0.1:8080"
test_url "Prometheus API" "http://127.0.0.1:9090/-/ready"
test_url "OpenSearch Health" "http://127.0.0.1:9200/_cluster/health"
test_url "Jaeger UI / API" "http://127.0.0.1:16686/jaeger/ui"

echo ""
echo "=== SUT Resource Usage (docker stats --no-stream) ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"
