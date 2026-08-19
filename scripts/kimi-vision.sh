#!/usr/bin/env bash
# kimi-vision.sh — Kimi K2.5/K2.6 视觉理解一键调用(图像/视频)
# 用法: bash scripts/kimi-vision.sh <图片或视频路径> ["问题描述"]
# 示例: bash scripts/kimi-vision.sh screenshot.png "这张图里有什么按钮?"
set -euo pipefail

MEDIA_PATH="${1:?用法: kimi-vision.sh <媒体路径> [问题]}"
QUESTION="${2:-请描述这个图片/视频的主要内容,用中文回答}"
KEY="$(grep '^api_key' ~/.kimi-code/config.toml | head -1 | awk -F'"' '{print $2}')"
MODEL="${KIMI_MODEL:-kimi-k2.6}"

[ -f "$MEDIA_PATH" ] || { echo "❌ 文件不存在: $MEDIA_PATH"; exit 1; }

EXT="${MEDIA_PATH##*.}"
case "$EXT" in
  jpg|jpeg|png|gif|webp|bmp) MTYPE="image"; CT="image/jpeg" ;;
  mp4|mov|avi|mkv|webm)      MTYPE="video"; CT="video/mp4" ;;
  *) echo "⚠️ 未知格式 $EXT,按图片处理"; MTYPE="image"; CT="image/jpeg" ;;
esac

echo "📤 发送 $MTYPE 到 Kimi ($MODEL): $MEDIA_PATH"
python3 - "$MEDIA_PATH" "$QUESTION" "$KEY" "$MODEL" "$CT" << 'PYEOF'
import base64, json, sys, urllib.request, urllib.error

media_path, question, key, model, ctype = sys.argv[1:6]
with open(media_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

media_field = "image_url" if "image" in ctype else "video_url"
payload = {
    "model": model,
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": media_field, media_field: {"url": f"data:{ctype};base64,{b64}"}}
    ]}],
    "max_tokens": 1024
}
req = urllib.request.Request(
    "https://api.moonshot.cn/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        d = json.loads(resp.read())
    msg = d["choices"][0]["message"]
    print("✅ 回答:", msg["content"])
    if msg.get("reasoning_content"):
        print(f"🧠 推理过程({d['usage']['completion_tokens_details'].get('reasoning_tokens', '?')} tokens):")
        print(msg["reasoning_content"][:500])
except urllib.error.HTTPError as e:
    print("❌ HTTP", e.code, e.read().decode()[:400])
except Exception as e:
    print("❌", e)
PYEOF
