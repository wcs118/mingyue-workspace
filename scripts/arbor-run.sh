#!/bin/bash
# arbor-run — Arbor 自主研究工作流本地入口 (2026-08-13 真正吸收适配)
# 把 RUC-NLPIR/Arbor 的假设树研究工作流包装为可直接调用的工具
# 用法:
#   bash scripts/arbor-run.sh init <项目目录> <run名> "<目标契约>"
#   bash scripts/arbor-run.sh smoke <项目目录> <run名> "<目标契约>"   # 冒烟(推荐先跑)
#   bash scripts/arbor-run.sh view <项目目录> <run名>
#   bash scripts/arbor-run.sh status <项目目录> <run名>
# 依赖: skills/arbor-agent-tools/scripts/arbor_state.py (stdlib only)
set -euo pipefail

WS="$HOME/.openclaw/workspace"
TOOLS="$WS/skills/arbor-agent-tools/scripts/arbor_state.py"
LOG="$WS/memory/events.log"

CMD="${1:-}"
PROJ="${2:-}"
RUN="${3:-}"
CONTRACT="${4:-}"

if [ -z "$CMD" ] || [ -z "$PROJ" ] || [ -z "$RUN" ]; then
  echo "用法: bash scripts/arbor-run.sh <init|smoke|view|status> <项目目录> <run名> [目标契约]"
  echo "示例: bash scripts/arbor-run.sh smoke ~/myproj run1 \"优化代码性能\""
  exit 1
fi

mkdir -p "$PROJ"
PROJ=$(cd "$PROJ" && pwd)

case "$CMD" in
  init)
    [ -z "$CONTRACT" ] && { echo "❌ init 需要目标契约(第4参)"; exit 1; }
    python3 "$TOOLS" init --cwd "$PROJ" --run-name "$RUN" --task "$CONTRACT"
    echo "✅ 已初始化: $PROJ/.arbor/sessions/$RUN/"
    ;;
  smoke)
    [ -z "$CONTRACT" ] && { echo "❌ smoke 需要目标契约(第4参)"; exit 1; }
    echo "==> 1/5 初始化会话"
    python3 "$TOOLS" init --cwd "$PROJ" --run-name "$RUN" --task "$CONTRACT"
    echo "==> 2/5 写入基线元数据"
    python3 "$TOOLS" meta --cwd "$PROJ" --run-name "$RUN" --set baseline_score=0 --set trunk_score=0 --set metric_direction=maximize
    echo "==> 3/5 生成假设(ideate)"
    python3 "$TOOLS" add --cwd "$PROJ" --run-name "$RUN" --parent-id ROOT --hypothesis "$CONTRACT"
    echo "==> 4/5 生成执行器提示(smoke) + 实验工件"
    python3 "$TOOLS" prompt-executor --cwd "$PROJ" --run-name "$RUN" --node-id 1 --smoke > /dev/null 2>&1
    EXP_DIR="$PROJ/.arbor/sessions/$RUN/experiments/1"
    mkdir -p "$EXP_DIR"
    cat > "$EXP_DIR/report.md" << 'ART'
# Experiment 1 (smoke)
- Hypothesis: smoke 验证
- Status: done
- Score: 1 (mocked, smoke-only)
- Insight: arbor_state.py 全链路可用
ART
    cat > "$EXP_DIR/metrics.json" << 'ART'
{"node_id":1,"status":"done","score":1,"smoke":true}
ART
    echo "==> 5/5 产出报告 + 闭环检查"
    python3 "$TOOLS" report --cwd "$PROJ" --run-name "$RUN"
    python3 "$TOOLS" check --cwd "$PROJ" --run-name "$RUN" --require-report --require-experiment --require-executor-prompt && echo "✅ 冒烟全链路闭环通过"
    ;;
  view)
    python3 "$TOOLS" view --cwd "$PROJ" --run-name "$RUN" --format constraints
    ;;
  status)
    echo "=== 会话文件 ==="
    ls -la "$PROJ/.arbor/sessions/$RUN/.coordinator/" 2>/dev/null || echo "❌ 会话不存在"
    echo "=== 树状态 ==="
    python3 "$TOOLS" view --cwd "$PROJ" --run-name "$RUN" 2>/dev/null || echo "(无树)"
    ;;
  *)
    echo "❌ 未知命令: $CMD (支持 init/smoke/view/status)"
    exit 1
    ;;
esac

echo "$(date '+%Y-%m-%d %H:%M') | arbor-run | $CMD $PROJ/$RUN" >> "$LOG"
