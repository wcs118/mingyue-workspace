#!/bin/bash
# OpenClaw ↔ Obsidian 双向记忆+技能库同步
# 用法: bash scripts/vault-sync.sh [up|down|both|skills-up|skills-down]
#   up          : OpenClaw MEMORY.md + memory/*.md → Obsidian memory/all.md
#   down        : Obsidian 关键文件 → OpenClaw memory/vault-context.md
#   skills-up   : OpenClaw skills/ → Obsidian Wiki/技能体系/(覆盖式同步,Obsidian为主库时慎用)
#   skills-down : Obsidian Wiki/技能体系/ → OpenClaw skills/(Obsidian为真主库,推荐)
set -euo pipefail

WS="$HOME/.openclaw/workspace"
VAULT="/Volumes/Alean/Obsidian/Alean-Vault" # ← 新实例改成自己的 vault 路径
mkdir -p "$WS/memory"

# 技能库同步:Obsidian(Wiki/技能体系/) → 工作区(skills/)
skills_down() {
  local SRC="$VAULT/Wiki/技能体系"
  [[ -d "$SRC" ]] || { echo " ✗ Obsidian 技能库不存在"; return 1; }
  local count=0
  for f in "$SRC"/*.md; do
    local name base
    name=$(basename "$f" .md)
    [[ "$name" == "Skills数据库"* || "$name" == "README" ]] && continue
    base=$(grep -m1 '^name:' "$f" 2>/dev/null | sed 's/^name:[[:space:]]*//' || true)
    [[ -z "$base" ]] && base="$name"
    mkdir -p "$WS/skills/$base"
    cp "$f" "$WS/skills/$base/SKILL.md"
    count=$((count+1))
  done
  echo " ✓ 技能库下行: Obsidian Wiki/技能体系/ → skills/ ($count 个)"
}

# 技能库同步:工作区(skills/) → Obsidian(Wiki/技能体系/)
skills_up() {
  local DST="$VAULT/Wiki/技能体系"
  mkdir -p "$DST"
  local count=0
  for f in "$WS/skills"/*/SKILL.md; do
    [[ -f "$f" ]] || continue
    local base=$(basename "$(dirname "$f")")
    cp "$f" "$DST/$base.md"
    count=$((count+1))
  done
  echo " ✓ 技能库上行: skills/ → Obsidian Wiki/技能体系/ ($count 个)"
}

case "${1:-both}" in
up|both)
  bash "$VAULT/sync-memory.sh" up all >/dev/null 2>&1
  echo "✓ 上行: OpenClaw → Obsidian memory/all.md"
  ;;
esac

case "${1:-both}" in
down|both)
  DOWN="$WS/memory/vault-context.md"
  {
    echo "# Vault 下行上下文"
    echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "来源: $VAULT"
    echo ""
    for f in "Areas/我的判断知识库.md" "双轨记忆索引.md" "Index.md"; do
      if [[ -f "$VAULT/$f" ]]; then
        echo "## [$f]"
        cat "$VAULT/$f"
        echo ""
      fi
    done
  } > "$DOWN"
  echo "✓ 下行: Obsidian → $DOWN"
  ;;
esac

case "${1:-both}" in
skills-down)
  skills_down
  ;;
skills-up)
  skills_up
  ;;
esac
