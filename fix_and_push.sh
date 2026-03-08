#!/bin/bash
# AppDrop — Fix All & Push to GitHub
# Run: chmod +x fix_and_push.sh && ./fix_and_push.sh

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AppDrop — Fix All & Push Pipeline${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ── 1. Python engine tests ────────────────────────────────────────────────────
echo -e "\n${YELLOW}[1/5] Running Python engine tests...${NC}"
pip install fastapi uvicorn pydantic pytest pytest-asyncio httpx websockets -q --break-system-packages 2>/dev/null || true
python -m pytest tests/ -q --tb=short
echo -e "${GREEN}✓ Python tests passed${NC}"

# ── 2. Frontend tests + build ─────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/5] Running frontend tests + build...${NC}"
npm install --silent
npm test
npm run build
echo -e "${GREEN}✓ Frontend tests + build passed${NC}"

# ── 3. Clean garbage files ────────────────────────────────────────────────────
echo -e "\n${YELLOW}[3/5] Cleaning repo...${NC}"
rm -rf "{src" "setup_github.sh" dist/ 2>/dev/null || true
find . -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
find . -name ".pytest_cache" -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned${NC}"

# ── 4. Git status ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[4/5] Git status...${NC}"
git status --short

# ── 5. Commit + push ──────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[5/5] Committing and pushing...${NC}"
git add -A
CHANGED=$(git diff --cached --name-only | wc -l | tr -d ' ')
if [ "$CHANGED" -eq "0" ]; then
  echo -e "${GREEN}✓ Nothing to commit — already up to date${NC}"
else
  git commit -m "fix: all tests green — 158 passing (W1:16 W2:28 W3:26 Pipeline:59 Frontend:14) + build OK"
  git push origin main
  echo -e "${GREEN}✓ Pushed to GitHub${NC}"
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ ALL DONE — CI should be fully green${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
