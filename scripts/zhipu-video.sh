#!/bin/bash
# 智谱清影免费出片脚本 (2026-08-13 实测可用)
# 用法: bash scripts/zhipu-video.sh "<提示词>" [时长] [尺寸] [比例]
# 例:   bash scripts/zhipu-video.sh "夕阳下的海边,电影质感" 10 1920x1080 16:9
set -euo pipefail

CONFIG=~/.openclaw/zhipu.key
OUT_DIR=~/.openclaw/workspace/output/zhipu
mkdir -p "$OUT_DIR"

if [ ! -f "$CONFIG" ]; then echo "❌ 缺少 $CONFIG"; exit 1; fi
set -a; . "$CONFIG"; set +a
KEY="${ZHIPU_API_KEY:-}"
if [ -z "$KEY" ]; then echo "❌ ZHIPU_API_KEY 为空"; exit 1; fi

PROMPT="${1:?用法: zhipu-video.sh <提示词> [时长] [尺寸]}"
DURATION="${2:-10}"
SIZE="${3:-1920x1080}"
BASE="https://open.bigmodel.cn/api/paas/v4"

echo "📝 提示词: $PROMPT"
echo "⏱️  $DURATION 秒 | $SIZE | 智谱清影 cogvideox-flash(免费)"

# 1. 提交任务
RESP=$(curl -s -m 60 -X POST "$BASE/videos/generations" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d "{\"model\":\"cogvideox-flash\",\"prompt\":\"$PROMPT\",\"image_size\":\"$SIZE\",\"duration\":$DURATION}")
TASK_ID=$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
if [ -z "$TASK_ID" ]; then echo "❌ 提交失败: $RESP"; exit 1; fi
echo "✅ 任务已创建: $TASK_ID"

# 2. 轮询状态(最长 ~15 分钟)
echo "⏳ 生成中..."
for i in $(seq 1 30); do
  sleep 30
  STATUS=$(curl -s -m 30 "$BASE/async-result/$TASK_ID" -H "Authorization: Bearer $KEY")
  S=$(echo "$STATUS" | python3 -c "import json,sys; print(json.load(sys.stdin).get('task_status','?'))" 2>/dev/null)
  echo "  第${i}次($(date +%H:%M:%S)): $S"
  if [ "$S" = "SUCCESS" ]; then break; fi
  if [ "$S" = "FAIL" ]; then echo "❌ 生成失败: $STATUS"; exit 1; fi
  if [ "$i" = "30" ]; then echo "❌ 超时"; exit 1; fi
done

# 3. 取下载地址并下载
DL_URL=$(echo "$STATUS" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['video_result'][0]['url'])" 2>/dev/null)
if [ -z "$DL_URL" ]; then echo "❌ 无下载地址: $STATUS"; exit 1; fi
TS=$(date +%Y%m%d-%H%M%S)
OUT="$OUT_DIR/zhipu_${TS}.mp4"
echo "⬇️ 下载中..."
curl -s -m 300 -o "$OUT" "$DL_URL"
SIZE_B=$(stat -c%s "$OUT")
echo "🎬 完成: $OUT ($SIZE_B 字节)"
