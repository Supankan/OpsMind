#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${REPO_ROOT}/infra/otel-demo/upstream"
OVERLAY_FILE="${REPO_ROOT}/infra/otel-demo/compose.opsmind.yaml"

if [ ! -d "${UPSTREAM_DIR}/.git" ]; then
    echo "Error: Upstream SUT directory not found. Please run scripts/sut_setup.sh first."
    exit 1
fi

echo "=== Starting OpenTelemetry Demo SUT (Minimal + Observability + OpsMind Overlay) ==="
cd "${UPSTREAM_DIR}"

docker compose \
  --env-file .env \
  --env-file .env.override \
  -f compose.yaml \
  -f compose.observability.yaml \
  -f "${OVERLAY_FILE}" \
  up --remove-orphans --detach

echo "Waiting for core endpoints to become available..."

WAIT_TIMEOUT=90
ELAPSED=0

check_endpoint() {
    local url="$1"
    local name="$2"
    if curl -s -f -m 2 "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

until (check_endpoint "http://127.0.0.1:8080" "Frontend Proxy" && \
       check_endpoint "http://127.0.0.1:9090/-/ready" "Prometheus" && \
       check_endpoint "http://127.0.0.1:9200/_cluster/health" "OpenSearch" && \
       check_endpoint "http://127.0.0.1:16686/jaeger/ui" "Jaeger"); do
    if [ "$ELAPSED" -ge "$WAIT_TIMEOUT" ]; then
        echo "Warning: Timeout reached ($WAIT_TIMEOUT s). Some services may still be initializing."
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo "  Still waiting for services (${ELAPSED}s elapsed)..."
done

echo ""
echo "SUT started. Verifying status..."
"${REPO_ROOT}/scripts/sut_status.sh"
