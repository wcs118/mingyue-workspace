#!/bin/bash
# dsh-run.sh — DeepSeek Harness (dsh) 无头任务封装
# 用法: bash scripts/dsh-run.sh "<任务描述>"
# 自动从 OpenClaw 配置提取 DeepSeek key,零额外配置

set -uo pipefail

if [ $# -lt 1 ]; then
  echo "用法: bash scripts/dsh-run.sh \"<任务描述>\""
  exit 1
fi

TASK="$1"
DSH_BIN="/opt/dsh/node_modules/.bin/dsh"

if [ ! -x "$DSH_BIN" ]; then
  echo "❌ dsh 未安装。先执行: cd /opt/dsh && npm install @deepseek-ai/dsh"
  exit 1
fi

KEY=$(grep -oE 'sk-[a-zA-Z0-9]{20,}' "$HOME/.openclaw/openclaw.json" | head -1)
if [ -z "$KEY" ]; then
  echo "❌ 未找到 DeepSeek API key(检查 ~/.openclaw/openclaw.json)"
  exit 1
fi

# 🔒 守卫链: dsh 执行前先过 guard(红线/沙箱/需确认检查 + 任务定级)
GUARD="$HOME/.openclaw/workspace/scripts/guard-exec.py"
SCOPER="$HOME/.openclaw/workspace/scripts/scope-router.py"
if [ -f "$SCOPER" ]; then
  RISK=$(python3 "$SCOPER" route --task "$TASK" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['risk'])" 2>/dev/null)
  if [ "$RISK" = "L3" ]; then
    echo "⛔ 守卫拦截: 任务被定为 L3 高风险(删除/外发/不可逆),需老板确认后显式执行"
    exit 3
  fi
  echo "✅ 任务定级: $RISK"
fi
if [ -f "$GUARD" ]; then
  python3 "$GUARD" check --cmd "dsh --profile headless $TASK" >/dev/null 2>&1
  GC=$?
  if [ $GC -eq 2 ]; then
    echo "⛔ 守卫链拒绝: dsh 任务含红线/需确认/沙箱风险,未执行"
    echo "   (如需放行: 人工复核后显式执行)"
    exit 2
  fi
fi

echo "🤖 dsh headless 运行中: $TASK"
echo "----------------------------------------"
DEEPSEEK_API_KEY="$KEY" timeout 600 "$DSH_BIN" --profile headless "$TASK"
RC=$?
echo "----------------------------------------"
echo "EXIT=$RC"
