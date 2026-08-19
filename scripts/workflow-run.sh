#!/bin/bash
# workflow-run.sh — 明月调度器工作流程 v2 一键执行入口
# 把五阶段串成一条命令: 解析定级 → 作用域 → 事务启动 → 守卫执行 → 收尾交付
#
# 用法:
#   bash scripts/workflow-run.sh "任务描述" [--cmd "具体命令"] [--yes] [--risk L2]
#
# 流程:
#   阶段一 scope-router 定级+映射工具集
#   阶段二 session-rollback begin(事务快照)
#   阶段三 guard-exec 守卫链执行(超时/重试/熔断/取消)
#   阶段四 session-rollback check → 成功 commit / 失败 rollback
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

TASK="${1:-}"
if [ -z "$TASK" ]; then
  echo "用法: bash scripts/workflow-run.sh \"任务描述\" [--cmd \"命令\"] [--yes] [--risk L2]"
  exit 2
fi
shift

CMD=""
YES=""
RISK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --cmd) CMD="$2"; shift 2 ;;
    --yes) YES="--yes"; shift ;;
    --risk) RISK="--risk $2"; shift 2 ;;
    *) shift ;;
  esac
done

SID="wf-$(date +%s)"
echo "🌙 明月调度器工作流程 v2 启动"
echo "📋 任务: $TASK"

# ── 阶段一: 任务解析 + 作用域注册 ──
echo ""
echo "── 阶段一 · 作用域注册 ──"
SCOPE=$(python3 scripts/scope-router.py route --task "$TASK" $RISK)
echo "$SCOPE" | python3 -m json.tool --no-ensure-ascii 2>/dev/null || echo "$SCOPE"
RISK_LVL=$(echo "$SCOPE" | python3 -c "import sys,json;print(json.load(sys.stdin)['risk'])" 2>/dev/null || echo "L0")
if [ "$RISK_LVL" = "L3" ]; then
  echo "⛔ L3 高风险(删除/外发/不可逆):暂停,需老板确认后再执行"
  exit 3
fi

# ── 阶段二: 事务式会话启动 ──
echo ""
echo "── 阶段二 · 事务式启动(会话 $SID)──"
python3 scripts/session-rollback.py begin --id "$SID" --note "$TASK"

# ── 阶段三: 守卫链执行 ──
echo ""
echo "── 阶段三 · 守卫链执行 ──"
if [ -z "$CMD" ]; then
  echo "ℹ 未指定 --cmd,跳过实际执行(只做事务演练)"
  CMD="true"
fi
python3 scripts/guard-exec.py run --cmd "$CMD" $YES
GUARD_EXIT=$?

# ── 阶段四: 事务式收尾 ──
echo ""
echo "── 阶段四 · 收尾 ──"
if [ $GUARD_EXIT -eq 0 ]; then
  python3 scripts/session-rollback.py check --id "$SID"
  echo "✅ 目标达成,提交会话"
  python3 scripts/session-rollback.py commit --id "$SID"
  echo ""
  echo "🎉 交付完成: $TASK (risk=$RISK_LVL)"
  exit 0
else
  echo "❌ 执行失败(exit=$GUARD_EXIT),回滚会话"
  python3 scripts/session-rollback.py rollback --id "$SID"
  echo "⚠ 已回滚。可修复后重试;同一问题 3 次未解决 → 升级老板"
  exit $GUARD_EXIT
fi
