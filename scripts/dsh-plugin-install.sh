#!/bin/bash
# dsh-plugin-install.sh — 把明月技能批量装入 dsh headless profile
# 用法:
#   bash scripts/dsh-plugin-install.sh                # 安装默认核心技能
#   bash scripts/dsh-plugin-install.sh --all          # 安装全部 169 个
#   bash scripts/dsh-plugin-install.sh skill1 skill2  # 安装指定技能
set -uo pipefail
export PATH="$PATH:$(npm prefix -g)/bin"
cd "$(dirname "$0")/.." || exit 1

DSH="/opt/dsh/node_modules/.bin/dsh"
PLUGINS_DIR="reference/dsh-plugins"
CORE=(arbor-agent-orchestrator arbor-research-agent deepseek-harness dragon-ppt-maker framework-ops frontend-design human-writing kimi-k2.5 math-olympiad)

if [ "${1:-}" = "--all" ]; then
  mapfile -t TARGETS < <(ls "$PLUGINS_DIR" 2>/dev/null)
elif [ $# -gt 0 ]; then
  TARGETS=("$@")
else
  TARGETS=("${CORE[@]}")
fi

OK=0; FAIL=0
for skill in "${TARGETS[@]}"; do
  if [ ! -d "$PLUGINS_DIR/$skill" ]; then
    echo "⚠ 跳过(无插件包): $skill"
    continue
  fi
  if timeout 60 "$DSH" plugin --profile headless add "$PWD/$PLUGINS_DIR/$skill" >/tmp/dsh-install.log 2>&1; then
    echo "✅ $skill"
    OK=$((OK+1))
  else
    # 已安装过会报错,算"已存在"不算失败
    if grep -qi "already\|exists\|duplicate" /tmp/dsh-install.log; then
      echo "✓ $skill (已装)"
      OK=$((OK+1))
    else
      echo "❌ $skill: $(tail -1 /tmp/dsh-install.log)"
      FAIL=$((FAIL+1))
    fi
  fi
done
echo ""
echo "安装完成: $OK 成功 / $FAIL 失败"
exit $FAIL
