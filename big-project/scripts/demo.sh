#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost:8000"
TOKEN="demo-token-12345"
AUTH="Authorization: Bearer $TOKEN"

echo "=== AI Knowledge Hub - Demo Script ==="
echo ""

# Start backend in background
echo "[1/7] Starting backend..."
cd "$(dirname "$0")/.."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 3

cleanup() { kill $SERVER_PID 2>/dev/null || true; }
trap cleanup EXIT

# Health check
echo "[2/7] Health check..."
curl -s "$BASE_URL/health" | python -m json.tool
echo ""

# Video generate
echo "[3/7] Generating video task..."
VIDEO_RESP=$(curl -s -X POST "$BASE_URL/api/video/generate" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"prompt":"一只猫在阳光下打盹","style":"cinematic","duration":10}')
echo "$VIDEO_RESP" | python -m json.tool
TASK_ID=$(echo "$VIDEO_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('task_id',''))")
echo ""

# Video task status
echo "[4/7] Checking video task status..."
curl -s "$BASE_URL/api/video/tasks/$TASK_ID" -H "$AUTH" | python -m json.tool
echo ""

# Comment analyze
echo "[5/7] Analyzing comment sentiment..."
curl -s -X POST "$BASE_URL/api/comment/analyze" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"text":"这个产品真的太棒了！","platform":"weibo"}' | python -m json.tool
echo ""

# Knowledge ask
echo "[6/7] Querying knowledge base..."
curl -s -X POST "$BASE_URL/api/knowledge/ask" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"question":"平台支持哪些视频风格？"}' | python -m json.tool
echo ""

# Admin stats
echo "[7/7] Fetching admin stats..."
curl -s "$BASE_URL/api/admin/stats" -H "$AUTH" | python -m json.tool
echo ""

echo "=== Demo complete! ==="
