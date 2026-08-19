#!/bin/bash
# glm-run.sh — 智谱 GLM 一键调用脚本(OpenAI 兼容)
# 用法:
#   bash glm-run.sh "你好"                      # 默认 glm-4.7-flash(免费)
#   bash glm-run.sh "写个快速排序" glm-5.2       # 指定模型
#   bash glm-run.sh "1+1=?" glm-5.2 thinking     # 思考模式
# 依赖: 环境变量 ZHIPU_API_KEY(或 /root/.openclaw/config/zhipu.env)
set -euo pipefail

# 加载 key
if [ -z "${ZHIPU_API_KEY:-}" ] && [ -f /root/.openclaw/config/zhipu.env ]; then
    ENV_CONTENT=$(grep -v '^#' /root/.openclaw/config/zhipu.env | grep -v '^$' || true)
    if [ -n "$ENV_CONTENT" ]; then
        export $ENV_CONTENT
    fi
fi
if [ -z "${ZHIPU_API_KEY:-}" ]; then
    echo "❌ 未设置 ZHIPU_API_KEY(export ZHIPU_API_KEY=... 或写入 /root/.openclaw/config/zhipu.env)" >&2
    exit 1
fi

PROMPT="${1:?用法: glm-run.sh <prompt> [model] [thinking]}"
MODEL="${2:-glm-4.7-flash}"
MODE="${3:-}"

BASE_URL="https://open.bigmodel.cn/api/paas/v4/"

# 组装请求体
if [ "$MODE" = "thinking" ]; then
    REQ=$(python3 -c "
import json,sys
print(json.dumps({
    'model': '$MODEL',
    'messages': [{'role':'user','content': sys.argv[1]}],
    'thinking': {'type':'enabled'},
    'stream': True
}, ensure_ascii=False))" "$PROMPT")
    echo "🧠 思考模式..."
    curl -sN --max-time 300 "$BASE_URL"chat/completions \
        -H "Authorization: Bearer $ZHIPU_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$REQ" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line.startswith('data:'): continue
    data = line[5:].strip()
    if data == '[DONE]': break
    try:
        d = json.loads(data)
        if d.get('choices'):
            delta = d['choices'][0].get('delta', {})
            if delta.get('reasoning_content'): print(delta['reasoning_content'], end='', flush=True)
            elif delta.get('content'): print(delta['content'], end='', flush=True)
    except Exception: pass
print()
"
else
    REQ=$(python3 -c "
import json,sys
print(json.dumps({
    'model': '$MODEL',
    'messages': [{'role':'user','content': sys.argv[1]}],
    'stream': True
}, ensure_ascii=False))" "$PROMPT")
    curl -sN --max-time 300 "$BASE_URL"chat/completions \
        -H "Authorization: Bearer $ZHIPU_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$REQ" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line.startswith('data:'): continue
    data = line[5:].strip()
    if data == '[DONE]': break
    try:
        d = json.loads(data)
        if d.get('choices') and d['choices'][0].get('delta', {}).get('content'):
            print(d['choices'][0]['delta']['content'], end='', flush=True)
    except Exception: pass
print()
"
fi
