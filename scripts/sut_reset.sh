#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLAGD_FILE="${REPO_ROOT}/infra/otel-demo/upstream/src/flagd/demo.flagd.json"

echo "=== Resetting OpenTelemetry Demo Fault Flags ==="

if [ ! -f "${FLAGD_FILE}" ]; then
    echo "Error: ${FLAGD_FILE} not found."
    exit 1
fi

# Reset paymentUnreachable to defaultVariant "off"
python3 -c "
import json
with open('${FLAGD_FILE}', 'r') as f:
    data = json.load(f)

# Reset all faults to off
for flag_name in ['paymentUnreachable', 'cartFailure', 'paymentFailure', 'adFailure']:
    if flag_name in data.get('flags', {}):
        data['flags'][flag_name]['defaultVariant'] = 'off'

with open('${FLAGD_FILE}', 'w') as f:
    json.dump(data, f, indent=2)

print('Feature flags reset to clean baseline (paymentUnreachable: off).')
"

# Restart flagd to ensure immediate evaluation update across clients
echo "Restarting flagd to apply clean baseline..."
cd "${REPO_ROOT}/infra/otel-demo/upstream"
docker compose \
  --env-file .env \
  --env-file .env.override \
  -f compose.yaml \
  -f compose.observability.yaml \
  -f "${REPO_ROOT}/infra/otel-demo/compose.opsmind.yaml" \
  restart flagd

echo "Reset completed successfully."
