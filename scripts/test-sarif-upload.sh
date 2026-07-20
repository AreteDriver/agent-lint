#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Test script: Generate SARIF from agent-lint and upload to GitHub Advanced
# Security (code scanning alerts).
#
# Prerequisites:
#   - agent-lint installed: pip install -e ".[dev]"
#   - gh CLI authenticated: gh auth status
#   - GITHUB_TOKEN with security_events write scope
#
# Usage:
#   # Local test (requires repo push access)
#   bash scripts/test-sarif-upload.sh
#
#   # CI mode (reads env vars)
#   GITHUB_TOKEN=xxx GITHUB_REPOSITORY=AreteDriver/agent-lint \
#     bash scripts/test-sarif-upload.sh
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO="${GITHUB_REPOSITORY:-AreteDriver/agent-lint}"
WORKFLOW_FILE="${1:-tests/fixtures/workflows/sample-agent-workflow.yaml}"
SARIF_FILE="${2:-/tmp/agent-lint-test.sarif}"
BRANCH="${GITHUB_REF_NAME:-main}"
COMMIT_SHA="${GITHUB_SHA:-$(git rev-parse HEAD 2>/dev/null || echo 'unknown')}"

# ---------------------------------------------------------------------------
# Step 1: Validate prerequisites
# ---------------------------------------------------------------------------
echo "=== Step 1: Validate prerequisites ==="

if ! command -v agent-lint >/dev/null 2>&1; then
    echo "ERROR: agent-lint not found. Install with: pip install -e ."
    exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: gh CLI not found. Install from https://cli.github.com"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: gh CLI not authenticated. Run: gh auth login"
    exit 1
fi

if [[ ! -f "$WORKFLOW_FILE" ]]; then
    echo "ERROR: Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

echo "  ✓ agent-lint found"
echo "  ✓ gh CLI authenticated"
echo "  ✓ Workflow file: $WORKFLOW_FILE"
echo

# ---------------------------------------------------------------------------
# Step 2: Generate SARIF
# ---------------------------------------------------------------------------
echo "=== Step 2: Generate SARIF output ==="

agent-lint lint "$WORKFLOW_FILE" --format sarif > "$SARIF_FILE"

# Validate SARIF is valid JSON.
if ! python3 -c "import json; json.load(open('$SARIF_FILE'))" 2>/dev/null; then
    echo "ERROR: Generated SARIF is not valid JSON"
    exit 1
fi

# Show summary.
FINDING_COUNT=$(python3 -c "
import json
with open('$SARIF_FILE') as f:
    data = json.load(f)
results = data.get('runs', [{}])[0].get('results', [])
props = data.get('runs', [{}])[0].get('properties', {})
print(f'Findings: {len(results)} | Score: {props.get(\"agent-lint-score\", \"N/A\")}')
")

echo "  ✓ SARIF generated: $SARIF_FILE"
echo "  ✓ $FINDING_COUNT"
echo

# ---------------------------------------------------------------------------
# Step 3: Validate SARIF structure
# ---------------------------------------------------------------------------
echo "=== Step 3: Validate SARIF structure ==="

python3 <<EOF
import json, sys

with open("$SARIF_FILE") as f:
    data = json.load(f)

assert data.get("version") == "2.1.0", "SARIF version must be 2.1.0"
assert "\$schema" in data, "Missing \$schema"

runs = data.get("runs", [])
assert len(runs) > 0, "No runs found"

run = runs[0]
assert "tool" in run, "Missing tool"
assert "driver" in run["tool"], "Missing tool.driver"
assert "rules" in run["tool"]["driver"], "Missing tool.driver.rules"
assert "results" in run, "Missing results"
assert "invocations" in run, "Missing invocations"
assert "properties" in run, "Missing properties"

print("  ✓ SARIF version: 2.1.0")
print(f"  ✓ Rules: {len(run['tool']['driver']['rules'])}")
print(f"  ✓ Results: {len(run['results'])}")
print(f"  ✓ Score: {run['properties'].get('agent-lint-score', 'N/A')}")
print()
EOF

# ---------------------------------------------------------------------------
# Step 4: Upload to GitHub Advanced Security
# ---------------------------------------------------------------------------
echo "=== Step 4: Upload to GitHub Advanced Security ==="
echo "  Repository: $REPO"
echo "  Branch:     $BRANCH"
echo "  Commit:     ${COMMIT_SHA:0:8}"
echo

# GitHub SARIF upload endpoint
UPLOAD_URL="https://api.github.com/repos/$REPO/code-scanning/sarifs"

# Build JSON payload.
PAYLOAD=$(python3 -c "
import json, base64
with open('$SARIF_FILE', 'rb') as f:
    encoded = base64.b64encode(f.read()).decode()
payload = {
    'commit_sha': '$COMMIT_SHA',
    'ref': 'refs/heads/$BRANCH',
    'sarif': encoded,
    'tool_name': 'agent-lint',
    'checkout_uri': 'file:///github/workspace'
}
print(json.dumps(payload))
")

# Upload via gh api.
RESPONSE=$(gh api \
    --method POST \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$UPLOAD_URL" \
    --input - <<<"$PAYLOAD" \
    2>&1 || true)

# Parse response.
if echo "$RESPONSE" | grep -q '"id"'; then
    UPLOAD_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','N/A'))" 2>/dev/null || echo "N/A")
    echo "  ✓ SARIF uploaded successfully"
    echo "  ✓ Upload ID: $UPLOAD_ID"
    echo
    echo "=== SUCCESS ==="
    echo "View alerts at: https://github.com/$REPO/security/code-scanning"
elif echo "$RESPONSE" | grep -q "No analysis found"; then
    echo "  ⚠ Upload accepted but no analysis found (first upload)"
    echo "  ⚠ Check back in a few minutes at:"
    echo "    https://github.com/$REPO/security/code-scanning"
    echo
    echo "=== SUCCESS (delayed) ==="
elif echo "$RESPONSE" | grep -q "Forbidden"; then
    echo "  ✗ Upload failed: Forbidden"
    echo "  ✗ Ensure GITHUB_TOKEN has 'security_events:write' scope"
    echo "  ✗ For private repos, GitHub Advanced Security must be enabled"
    echo
    echo "=== FAILED ==="
    exit 1
else
    echo "  ✗ Upload failed with response:"
    echo "$RESPONSE" | head -20
    echo
    echo "=== FAILED ==="
    exit 1
fi
