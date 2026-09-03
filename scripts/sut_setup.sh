#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="${REPO_ROOT}/infra/otel-demo/upstream"
PINNED_TAG="3.0.0"
EXPECTED_COMMIT="1755859a9de82c2e5e225be68abc401a5ebf2b4f"

echo "=== OpenTelemetry Demo SUT Setup ==="
echo "Target directory: ${UPSTREAM_DIR}"
echo "Pinned release:   ${PINNED_TAG}"
echo "Expected commit:  ${EXPECTED_COMMIT}"

if [ ! -d "${UPSTREAM_DIR}/.git" ]; then
    echo "Cloning upstream repository at tag ${PINNED_TAG}..."
    git clone --depth 1 --branch "${PINNED_TAG}" https://github.com/open-telemetry/opentelemetry-demo.git "${UPSTREAM_DIR}"
else
    echo "Upstream directory already exists. Validating checkout..."
fi

cd "${UPSTREAM_DIR}"
CURRENT_COMMIT="$(git rev-parse HEAD)"

if [ "${CURRENT_COMMIT}" != "${EXPECTED_COMMIT}" ]; then
    echo "WARNING: Upstream commit ${CURRENT_COMMIT} does not match expected ${EXPECTED_COMMIT}."
    echo "Checking out pinned tag ${PINNED_TAG}..."
    git fetch --tags
    git checkout "tags/${PINNED_TAG}"
    CURRENT_COMMIT="$(git rev-parse HEAD)"
fi

echo "Verified SUT checkout:"
echo "  Commit: ${CURRENT_COMMIT}"
echo "  Tag:    ${PINNED_TAG}"

# Ensure DEMO_VERSION is pinned to 3.0.0 in .env.override so images are pinned to 3.0.0
if ! grep -q "^DEMO_VERSION=" "${UPSTREAM_DIR}/.env.override" 2>/dev/null; then
    echo "DEMO_VERSION=${PINNED_TAG}" >> "${UPSTREAM_DIR}/.env.override"
fi
echo "  Image tag: ${PINNED_TAG} (pinned in .env.override)"

# Set HOST_FILESYSTEM=/tmp in .env.override to avoid Windows/WSL 9p mountinfo parsing error in otel-collector
if ! grep -q "^HOST_FILESYSTEM=" "${UPSTREAM_DIR}/.env.override" 2>/dev/null; then
    echo "HOST_FILESYSTEM=/tmp" >> "${UPSTREAM_DIR}/.env.override"
fi
echo "Setup completed successfully."
