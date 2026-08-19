#!/bin/bash
# 梦境自进化循环（evolution-cycle）v2 — 验证驱动进化
# 核心:晋升不再是终点。晋升时生成行为验证标准,下轮自动检查符合度,无效则回滚(不死鸟 restore)。
# 用法:
#   bash scripts/evolution-cycle.sh          # 完整一轮
#   bash scripts/evolution-cycle.sh --dry    # 只读分析，不写文件
#   bash scripts/evolution-cycle.sh --record # 只记录 observation（交互式）
#   bash scripts/evolution-cycle.sh --verify # 只跑验证阶段(检查已晋升规则的行为符合度)
set -euo pipefail

WS="$HOME/.openclaw/workspace"
MEM="$WS/memory"
OBS="$MEM/observations.md"
RULES="$MEM/learned-rules.md"
VERIFY="$MEM/rule-verification.md"
EVO="$MEM/evolution-log.md"
EVENTS="$MEM/events.log"
mkdir -p "$MEM"

# 确保文件存在
for f in "$OBS" "$RULES" "$VERIFY" "$EVO" "$EVENTS"; do
  [[ -f "$f" ]] || { echo "# 候选观察（未晋升）" > "$OBS"; echo "# 已晋升规则" > "$RULES"; echo "# 规则验证台账" > "$VERIFY"; echo "# 进化日志" > "$EVO"; echo "# 事件账本（append-only）" > "$EVENTS"; }
done

stamp() { date '+%Y-%m-%d %H:%M:%S'; }

log_event() { echo "[$(stamp)] $1" >> "$EVENTS"; }

# --record：追加一条候选观察
record_obs() {
  echo ""
  echo "输入观察内容（Ctrl-D 结束）："
  local content
  content="$(cat)"
  [[ -z "$content" ]] && { echo "空内容，取消。"; exit 0; }
  {
    echo ""
    echo "- $(date '+%Y-%m-%d') $(stamp | cut -d' ' -f2) | source=dreaming-narrative | evidence=1 | scope=all"
    echo "  $content"
  } >> "$OBS"
  log_event "record_observation"
  echo "✓ 已追加到 observations.md（候选层，未晋升）"
}

# --verify：验证已晋升规则的行为符合度
verify_rules() {
  echo "=== 规则验证阶段 $(stamp) ==="
  echo ""
  local vcount
  vcount="$(grep -c '^- ' "$VERIFY" 2>/dev/null || true)"
  echo "待验证规则：$vcount 条"
  if [[ "$vcount" -eq 0 ]]; then
    echo "无待验证规则。本轮晋升时将为新规则生成验证标准。"
    return 0
  fi
  echo ""
  echo "--- 验证标准（下轮巡检时逐条检查行为符合度）---"
  local i=0
  while IFS= read -r line; do
    [[ "$line" == "- "* ]] || continue
    i=$((i+1))
    echo "  [$i] ${line#- }"
  done < "$VERIFY"
  echo ""
  echo "检查方法：本轮工作中是否观察到规则描述的行为?符合→保留;不符合→回滚。"
  echo "（手动处理：符合请在 rule-verification.md 对应行标注 ✅ 并移除;"
  echo "  不符合标注 ❌ 并执行 bash scripts/phoenix-snapshot.sh restore 回滚相关改动）"
}

# --dry / 正常：分析候选观察，尝试晋升
analyze() {
  local dry="${1:-}"
  echo "=== 梦境进化循环 $(stamp) ==="
  echo ""

  local obs_count rules_count
  obs_count="$(grep -c '^- ' "$OBS" 2>/dev/null || true)"
  rules_count="$(grep -c '^- ' "$RULES" 2>/dev/null || true)"
  echo "候选观察：$obs_count 条 | 已晋升规则：$rules_count 条"

  if [[ "$obs_count" -eq 0 ]]; then
    echo "无候选观察，本轮无需晋升。"
    verify_rules
    return 0
  fi

  echo ""
  echo "--- 候选观察（需证据晋升门：Preference≥2 / Policy≥3 独立 Episode）---"
  local i=0
  while IFS= read -r line; do
    [[ "$line" == "- "* ]] || continue
    i=$((i+1))
    echo "  [$i] ${line#- }"
  done < "$OBS"

  if [[ -n "$dry" ]]; then
    echo ""
    echo "(--dry 模式：不写入。手动晋升请编辑 learned-rules.md 并更新 MEMORY.md)"
    return 0
  fi

  echo ""
  echo "本轮建议：候选观察证据不足（单条 Episode），保持候选层，不强行晋升。"
  echo "晋升规则：同一经验出现 ≥2（Preference）或 ≥3（Policy）次独立 Episode 才晋升。"
  echo "（用户明确认可/要求晋升的除外，直接晋升并生成验证标准）"
  echo ""
  echo "如需人工确认晋升，输入 yes（将把候选合并进 learned-rules 归档区并清空候选）："
  read -r confirm
  if [[ "$confirm" == "yes" ]]; then
    # v3(2026-08-09): 晋升 = 归档 + 提示人工重构，不再无脑叠加
    # 教训: v2 把整个 observations.md(含标题)追加进 learned-rules，6 批后堆积 7 个"梦境合并"节头
    # 且验证编号每批重置。改为: 候选归档到历史区，规则结构由人工/重构脚本维护。
    local merged
    merged="$(grep -c '^- ' "$OBS" || true)"
    {
      echo ""
      echo "## $(date '+%Y-%m-%d') 晋升归档（source=skill-absorption, 人工确认）"
      cat "$OBS"
    } >> "$EVO"
    # 验证标准: 每条候选的摘要进验证台账，编号用日期+序号防重复
    {
      echo ""
      echo "## $(date '+%Y-%m-%d') 新晋升候选（待重构进 R 编号）"
      local j=0
      while IFS= read -r line; do
        [[ "$line" == "- "* ]] || continue
        j=$((j+1))
        echo "- [ ] $(date '+%m%d')-$j 待重构：$(echo "$line" | cut -c1-120)"
      done < "$OBS"
    } >> "$VERIFY"
    {
      echo ""
      echo "- $(date '+%Y-%m-%d %H:%M') | 晋升归档 $merged 条候选 → evolution-log + 验证台账（待人工重构为 R 编号规则）"
    } >> "$EVO"
    echo "# 候选观察（未晋升）" > "$OBS"
    log_event "dream_consolidation: archived $merged candidates (v3 no-append)"
    echo "✓ 已归档 $merged 条候选到 evolution-log（不再叠加进 learned-rules）"
    echo "  下一步: 人工/重构脚本合并去重 → learned-rules.md 的 R 编号规则"
    echo "  下轮巡检: bash scripts/evolution-cycle.sh --verify 检查 R1-R8 行为符合度"
  else
    echo "保持候选层，未晋升。"
    log_event "dream_consolidation: skipped"
  fi
}

case "${1:-}" in
  --record) record_obs ;;
  --dry) analyze dry ;;
  --verify) verify_rules ;;
  *) analyze ;;
esac
