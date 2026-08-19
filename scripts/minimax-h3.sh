#!/bin/bash
# MiniMax H3 一键文生视频 (2026-08-13 实测可用)
# 用法: bash scripts/minimax-h3.sh "<提示词>" [时长] [分辨率] [比例]
# 例:   bash scripts/minimax-h3.sh "a red apple on a wooden table, cinematic lighting" 6 768p 16:9
set -euo pipefail

CONFIG=~/.openclaw/workspace/config/minimax.env
OUT_DIR=~/.openclaw/workspace/output/minimax
mkdir -p "$OUT_DIR"

# 加载配置 (KEY=xxx 格式)
if [ ! -f "$CONFIG" ]; then echo "❌ 缺少 $CONFIG"; exit 1; fi
set -a
# shellcheck disable=SC1090
. "$CONFIG"
set +a
KEY="${MINIMAX_API_KEY:-}"

PROMPT="${1:?用法: minimax-h3.sh <提示词> [时长] [分辨率] [比例]}"
DURATION="${2:-6}"
RESOLUTION="${3:-768p}"
RATIO="${4:-16:9}"
BASE="https://api.minimaxi.com"

# 参数校验
if [ "$DURATION" -lt 4 ] || [ "$DURATION" -gt 15 ]; then
  echo "❌ H3 支持时长 4-15 秒, 收到 $DURATION"
  exit 1
fi
case "$RATIO" in
  16:9|4:3|1:1|3:4|9:16|21:9) ;;
  *) echo "❌ ratio 必须是 16:9/4:3/1:1/3:4/9:16/21:9, 收到 $RATIO"; exit 1 ;;
esac

echo "📝 提示词: $PROMPT"
echo "⏱️  $DURATION 秒 | $RESOLUTION | $RATIO"

# 1. 创建任务
RESP=$(curl -s -m 120 -X POST "$BASE/v2/video_generation" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d "{\"model\":\"MiniMax-H3\",\"content\":[{\"type\":\"text\",\"text\":\"$PROMPT\"}],\"duration\":$DURATION,\"resolution\":\"$RESOLUTION\",\"ratio\":\"$RATIO\"}")
TASK_ID=$(echo "$RESP" | grep -o '"task_id":"[^"]*"' | sed 's/"task_id":"//;s/"$//')
if [ -z "$TASK_ID" ]; then echo "❌ 任务创建失败: $RESP"; exit 1; fi
echo "✅ 任务已创建: $TASK_ID"

# 2. 轮询状态 (最长 ~5 分钟)
echo "⏳ 生成中..."
STATUS=""
for i in $(seq 1 60); do
  sleep 15
  STATUS=$(curl -s -m 30 "$BASE/v1/query/video_generation?task_id=$TASK_ID" -H "Authorization: Bearer $KEY")
  S=$(echo "$STATUS" | grep -o '"status":"[^"]*"' | head -1)
  echo "  第${i}次: $S"
  if echo "$STATUS" | grep -q '"status":"Success"'; then break; fi
  if echo "$STATUS" | grep -q '"status":"Fail"'; then echo "❌ 生成失败: $STATUS"; exit 1; fi
  if [ "$i" = "60" ]; then echo "❌ 超时"; exit 1; fi
done

# 3. 取下载地址
FILE_ID=$(echo "$STATUS" | grep -o '"file_id":"[^"]*"' | sed 's/"file_id":"//;s/"$//')
if [ -z "$FILE_ID" ]; then echo "❌ 无 file_id: $STATUS"; exit 1; fi
FILE_RESP=$(curl -s -m 30 "$BASE/v1/files/retrieve?file_id=$FILE_ID" -H "Authorization: Bearer $KEY")
DL_URL=$(echo "$FILE_RESP" | grep -o '"download_url":"[^"]*"' | sed 's/"download_url":"//;s/"$//')
if [ -z "$DL_URL" ]; then echo "❌ 取下载地址失败: $FILE_RESP"; exit 1; fi

# 4. 下载
TS=$(date +%Y%m%d-%H%M%S)
OUT="$OUT_DIR/h3_${TS}.mp4"
echo "⬇️ 下载中..."
curl -s -m 300 -o "$OUT" "$DL_URL"
SIZE=$(stat -c%s "$OUT")
echo "🎬 完成: $OUT ($SIZE 字节)"
