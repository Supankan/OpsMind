#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${REPO_ROOT}/infra/otel-demo/upstream"
OVERLAY_FILE="${REPO_ROOT}/infra/otel-demo/compose.opsmind.yaml"

if [ ! -d "${UPSTREAM_DIR}/.git" ]; then
    echo "Upstream directory not found; nothing to stop."
    exit 0
fi

echo "=== Stopping OpenTelemetry Demo SUT ==="
cd "${UPSTREAM_DIR}"

docker compose \
  --env-file .env \
  --env-file .env.override \
  -f compose.yaml \
  -f compose.observability.yaml \
  -f "${OVERLAY_FILE}" \
  stop

echo "SUT containers stopped successfully (volumes preserved)."
