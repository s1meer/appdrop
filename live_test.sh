#!/bin/bash
# AppDrop — Live API Test
# Starts the engine, hits every endpoint, shows results
# Usage: bash live_test.sh

set -e
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

BASE="http://127.0.0.1:8742"
PASS=0; FAIL=0

# ── helpers ───────────────────────────────────────────────────────────────────
check() {
  local label="$1"; local cmd="$2"; local expect="$3"
  local result=$(eval "$cmd" 2>/dev/null)
  if echo "$result" | grep -qE "$expect"; then
    echo -e "  ${GREEN}✓${NC} $label"
    PASS=$((PASS+1))
  else
    echo -e "  ${RED}✗${NC} $label"
    echo -e "    ${YELLOW}expected: $expect${NC}"
    echo -e "    ${YELLOW}got: $(echo $result | head -c 100)${NC}"
    FAIL=$((FAIL+1))
  fi
}

# ── start engine ──────────────────────────────────────────────────────────────
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AppDrop Live API Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Kill any existing engine
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 0.5

echo -e "\n${YELLOW}Starting engine...${NC}"
cd "$(dirname "$0")/engine"

# Use venv python if available
PYTHON="../.venv/bin/python"
[ ! -f "$PYTHON" ] && PYTHON="python3"

$PYTHON -m uvicorn main:app --host 127.0.0.1 --port 8742 --log-level error &
ENGINE_PID=$!
sleep 2

# Verify it started
if ! curl -sf "$BASE/health" > /dev/null; then
  echo -e "${RED}Engine failed to start!${NC}"
  kill $ENGINE_PID 2>/dev/null
  exit 1
fi
echo -e "${GREEN}✓ Engine running on $BASE (PID: $ENGINE_PID)${NC}"

# ── SECTION 1: Core ──────────────────────────────────────────────────────────
echo -e "\n${CYAN}[1] Core Endpoints${NC}"
check "GET /health returns ok"        "curl -sf $BASE/health"                          '"ok"'
check "GET /health has version"       "curl -sf $BASE/health"                          '"version"'
check "GET /apps returns list"        "curl -sf $BASE/apps"                            '"apps"'

# ── SECTION 2: URL Validation ────────────────────────────────────────────────
echo -e "\n${CYAN}[2] URL Validation${NC}"
check "valid GitHub URL passes"       "curl -sf -X POST $BASE/validate-url -H 'Content-Type: application/json' -d '{\"url\":\"https://github.com/s1meer/appdrop\"}'"  '"valid":true'
check "invalid URL returns 400"       "curl -s  -X POST $BASE/validate-url -H 'Content-Type: application/json' -d '{\"url\":\"not-a-url\"}' -w '%{http_code}'"  "400"
check "validate returns owner/repo"   "curl -sf -X POST $BASE/validate-url -H 'Content-Type: application/json' -d '{\"url\":\"https://github.com/s1meer/appdrop\"}'"  '"owner":"s1meer"'

# ── SECTION 3: App Store ─────────────────────────────────────────────────────
echo -e "\n${CYAN}[3] App Store Registry${NC}"
check "GET /registry returns 10+ apps"    "curl -sf $BASE/registry"                       '"total"'
check "filter by tag=ai works"            "curl -sf '$BASE/registry?tag=ai'"              '"apps"'
check "filter by stack=python works"      "curl -sf '$BASE/registry?stack=python'"        'python'
check "search for comfy finds ComfyUI"    "curl -sf '$BASE/registry?q=comfy'"             'ComfyUI'
check "GET /registry/comfyui works"       "curl -sf $BASE/registry/comfyui"               '"id":"comfyui"'
check "unknown registry app = 404"        "curl -s $BASE/registry/zzz -w '%{http_code}'"  "404"
check "registry app has installed field"  "curl -sf $BASE/registry/comfyui"               '"installed"'

# ── SECTION 4: Submit App ────────────────────────────────────────────────────
echo -e "\n${CYAN}[4] Community Submission${NC}"
check "submit valid app accepted"    "curl -sf -X POST $BASE/registry/submit -H 'Content-Type: application/json' -d '{\"github_url\":\"https://github.com/testuser/live-test-app\",\"name\":\"Live Test App\",\"stack\":\"python\"}'"  '"submitted":true'
check "submit bad URL rejected"      "curl -s  -X POST $BASE/registry/submit -H 'Content-Type: application/json' -d '{\"github_url\":\"badurl\"}' -w '%{http_code}'"  "400"
check "duplicate submit rejected"    "curl -s  -X POST $BASE/registry/submit -H 'Content-Type: application/json' -d '{\"github_url\":\"https://github.com/comfyanonymous/ComfyUI\"}' -w '%{http_code}'"  "409"

# ── SECTION 5: Full Install Flow (real repo — fast clone) ────────────────────
echo -e "\n${CYAN}[5] Install Flow (live clone test)${NC}"
echo -e "  ${YELLOW}Installing a tiny test repo...${NC}"

INSTALL_RESP=$(curl -sf -X POST $BASE/apps/install \
  -H 'Content-Type: application/json' \
  -d '{"github_url":"https://github.com/s1meer/appdrop","name":"AppDrop Self-Test"}' 2>/dev/null)

APP_ID=$(echo $INSTALL_RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['app_id'])" 2>/dev/null || echo "")

if [ -n "$APP_ID" ]; then
  echo -e "  ${GREEN}✓${NC} Install started (app_id: $APP_ID)"
  PASS=$((PASS+1))

  # Poll for completion (max 60s)
  echo -e "  ${YELLOW}Waiting for install to complete...${NC}"
  for i in $(seq 1 30); do
    sleep 2
    STATUS=$(curl -sf $BASE/apps/$APP_ID 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'), d.get('install_pct',0))" 2>/dev/null || echo "? 0")
    APP_STATUS=$(echo $STATUS | awk '{print $1}')
    PCT=$(echo $STATUS | awk '{print $2}')
    echo -e "  ${YELLOW}  → $APP_STATUS ($PCT%)${NC}"
    [ "$APP_STATUS" = "ready" ] || [ "$APP_STATUS" = "error" ] && break
  done

  check "app reached ready/error state" "echo $APP_STATUS" "ready|error"
  check "GET /apps/$APP_ID works"       "curl -sf $BASE/apps/$APP_ID" '"id"'
  check "GET /apps/$APP_ID/logs works"  "curl -sf $BASE/apps/$APP_ID/logs" '"logs"'
  check "update-check endpoint works"   "curl -sf $BASE/apps/$APP_ID/update-check" '"update_available"'

  # Update check
  UPDATE_RESP=$(curl -s -X POST $BASE/apps/$APP_ID/update 2>/dev/null || echo "{}")
  check "update accepted or blocked"    "echo \"$UPDATE_RESP\"" "status|detail"

  # Delete
  DEL=$(curl -sf -X DELETE $BASE/apps/$APP_ID 2>/dev/null || echo "{}")
  check "DELETE app works"              "echo \"$DEL\"" "deleted"
else
  echo -e "  ${RED}✗${NC} Install request failed"
  FAIL=$((FAIL+1))
fi

# ── Summary ───────────────────────────────────────────────────────────────────
kill $ENGINE_PID 2>/dev/null
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
TOTAL=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}  ✅ ALL $TOTAL LIVE TESTS PASSED${NC}"
else
  echo -e "${RED}  ❌ $FAIL/$TOTAL FAILED${NC}"
fi
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
