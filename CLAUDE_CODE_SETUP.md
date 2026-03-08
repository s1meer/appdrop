# AppDrop — Claude Code Setup Command

## One-shot command (run in Claude Code terminal):

```bash
cd ~/Downloads/appdrop && \
python3 -m venv .venv && source .venv/bin/activate && \
pip install fastapi uvicorn pydantic pytest pytest-asyncio httpx websockets -q && \
sed -i '' 's/python -m pytest/.venv\/bin\/python -m pytest/g' fix_and_push.sh && \
sed -i '' 's/grep -q/grep -qE/g' live_test.sh && \
python3 -c "
t = open('live_test.sh').read()
t = t.replace('\"ready\\\\|error\"','\"ready|error\"')
t = t.replace('\"\\\"status\\\"\\\\|\\\"detail\\\"\"','\"status|detail\"')
t = t.replace('\"\\\"deleted\\\"\"','\"deleted\"')
open('live_test.sh','w').write(t)
" && \
npm install && \
echo '=== RUNNING ALL TESTS ===' && \
.venv/bin/python -m pytest tests/ -q --tb=short && \
npm test && npm run build && \
echo '=== LIVE API TEST ===' && \
bash live_test.sh && \
echo '=== PUSHING TO GITHUB ===' && \
git add -A && \
git commit -m "feat: Week 5 — Full React UI, Tauri desktop shell, Next.js web, 195 tests" && \
git push origin main
```
