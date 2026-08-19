#!/bin/bash
# 不死鸟快照与回滚（phoenix-snapshot）
# 用途：保存关键文件 SHA-256 基线（last-known-good），支持非清空式回滚
# 用法：
#   bash scripts/phoenix-snapshot.sh            # 保存快照
#   bash scripts/phoenix-snapshot.sh status     # 查看当前 vs 基线差异
#   bash scripts/phoenix-snapshot.sh restore    # 回滚到基线（非清空，保留记忆/日志）
#   bash scripts/phoenix-snapshot.sh list       # 列出所有快照
set -euo pipefail

WS="$HOME/.openclaw/workspace"
SNAP_DIR="$WS/.snapshots"
mkdir -p "$SNAP_DIR"

# 快照覆盖范围：框架与记忆核心文件
FILES=(
  "MEMORY.md"
  "AGENTS.md"
  "SOUL.md"
  "FRAMEWORK.md"
  "IDENTITY.md"
  "USER.md"
  "TOOLS.md"
  "HEARTBEAT.md"
)

latest_snapshot() {
  ls -1t "$SNAP_DIR"/snapshot-*.sha256 2>/dev/null | head -1
}

snapshot() {
  local stamp
  stamp="$(date '+%Y%m%d-%H%M%S')"
  local out="$SNAP_DIR/snapshot-$stamp.sha256"
  : > "$out"
  for f in "${FILES[@]}"; do
    if [[ -f "$WS/$f" ]]; then
      shasum -a 256 "$WS/$f" | sed "s|$WS/||" >> "$out"
    fi
  done
  # 记忆目录也纳入（每日笔记/规则/观察/进化日志）
  if [[ -d "$WS/memory" ]]; then
    find "$WS/memory" -type f -name "*.md" -maxdepth 2 2>/dev/null | sort | while read -r mf; do
      shasum -a 256 "$mf" | sed "s|$WS/||" >> "$out"
    done
  fi
  # 行为契约层也纳入（rules/ 规则 + skills/ 技能清单）——2026-08-09 补洞：
  # 之前只保护记忆层，规则/技能被改坏时快照看不到，回滚也够不着
  if [[ -d "$WS/rules" ]]; then
    find "$WS/rules" -type f -name "*.md" -maxdepth 1 2>/dev/null | sort | while read -r rf; do
      shasum -a 256 "$rf" | sed "s|$WS/||" >> "$out"
    done
  fi
  if [[ -d "$WS/skills" ]]; then
    find "$WS/skills" -type f -name "SKILL.md" -maxdepth 3 2>/dev/null | sort | while read -r sf; do
      shasum -a 256 "$sf" | sed "s|$WS/||" >> "$out"
    done
  fi
  echo "✓ 快照已保存：$(basename "$out")"
  echo "  文件数：$(wc -l < "$out")"
}

status() {
  local snap
  snap="$(latest_snapshot)"
  if [[ -z "$snap" ]]; then
    echo "✗ 无快照。先运行：bash scripts/phoenix-snapshot.sh"
    exit 1
  fi
  echo "基线：$(basename "$snap")"
  echo ""
  local changed=0
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local hash="${line%% *}"
    local path="${line#*  }"
    if [[ ! -f "$WS/$path" ]]; then
      echo "  DELETED : $path"
      changed=1
    else
      local cur
      cur="$(shasum -a 256 "$WS/$path" | awk '{print $1}')"
      if [[ "$cur" != "$hash" ]]; then
        echo "  CHANGED : $path"
        changed=1
      fi
    fi
  done < "$snap"
  if [[ "$changed" -eq 0 ]]; then
    echo "  无差异 ✓"
  fi
}

restore() {
  local snap
  snap="$(latest_snapshot)"
  if [[ -z "$snap" ]]; then
    echo "✗ 无快照可回滚。"
    exit 1
  fi
  echo "从 $(basename "$snap") 回滚（非清空式，保留记忆与日志）..."
  echo "警告：将覆盖以下文件到基线版本："
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line#*  }"
    echo "  - $path"
  done < "$snap"
  echo ""
  echo "确认？输入 yes 继续："
  read -r confirm
  if [[ "$confirm" != "yes" ]]; then
    echo "已取消。"
    exit 0
  fi
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line#*  }"
    if [[ -f "$WS/$path" ]]; then
      local cur
      cur="$(shasum -a 256 "$WS/$path" | awk '{print $1}')"
      local want="${line%% *}"
      if [[ "$cur" != "$want" ]]; then
        # 只能从 git 恢复（工作区已纳入 git）
        if git -C "$WS" cat-file -e "HEAD:$path" 2>/dev/null; then
          git -C "$WS" show "HEAD:$path" > "$WS/$path"
          echo "  ↩ $path"
        else
          echo "  ⚠ $path 不在 git HEAD 中，跳过（仅记录差异）"
        fi
      fi
    fi
  done < "$snap"
  echo "✓ 回滚完成（非清空：events.log / evolution-log / 每日笔记均保留）"
  echo "  注：快照记录的是基线哈希，回滚按基线哈希匹配 git HEAD 恢复；"
  echo "      若基线晚于当前 git HEAD，请先确认基线对应提交。"
}

case "${1:-}" in
  status) status ;;
  restore) restore ;;
  list) ls -1t "$SNAP_DIR"/snapshot-*.sha256 2>/dev/null || echo "无快照" ;;
  *) snapshot ;;
esac
