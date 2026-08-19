#!/bin/bash
# skill-absorb — 从 GitHub 高星仓库吸收技能到本地技能体系
# 用法:
#   bash scripts/skill-absorb.sh <repo> <skill-path> [target-name]
# 示例:
#   bash scripts/skill-absorb.sh anthropics/skills skills/skill-creator skill-creator
#   bash scripts/skill-absorb.sh obra/superpowers skills/systematic-debugging systematic-debugging
set -euo pipefail

WS="$HOME/.openclaw/workspace"
DB="$WS/skills-db/skills-database.json"
LOG="$WS/memory/events.log"

if [[ $# -lt 2 ]]; then
  echo "用法: bash scripts/skill-absorb.sh <repo> <skill-path> [target-name]"
  echo "示例: bash scripts/skill-absorb.sh anthropics/skills skills/skill-creator skill-creator"
  exit 1
fi

REPO="$1"
SKILL_PATH="$2"
TARGET="${3:-$(basename "$SKILL_PATH")}"
DEST="$WS/skills/$TARGET"

# 路径防呆: 第2参是仓库内相对路径(如 skills/engineering/tdd), 不是目标名
case "$SKILL_PATH" in
  *"$TARGET"/*"$TARGET") echo " ✗ 路径重复: $SKILL_PATH 已含 $TARGET, 第2参应传仓库内相对路径"; exit 1 ;;
esac

if [[ "$TARGET" == *"/"* ]]; then
  echo " ✗ 第3参(目标名)含斜杠: $TARGET → 只传目录名"; exit 1
fi

# 防呆补强: 第2参以 skills/ 开头不一定是误传(仓库内路径就是 skills/...)，警告但不拦截
if [[ "$SKILL_PATH" == skills/"$TARGET" ]]; then
  echo " ⚠ 提示: 第2参=$SKILL_PATH 与目标名$TARGET 同层——确认仓库内路径无误"
fi

# 防覆盖: 目标名已存在本地技能时警告, 需显式确认
if [[ -d "$WS/skills/$TARGET" && -n "$TARGET" ]]; then
  echo " ⚠ 目标已存在: skills/$TARGET/ (将被覆盖)"
  read -r -p "  继续? [y/N] " ans
  [[ "$ans" == [yY] ]] || { echo "  已取消"; exit 1; }
fi

echo "▶ 吸收 $REPO/$SKILL_PATH → skills/$TARGET"
mkdir -p "$DEST"

# 下载 SKILL.md
URL="https://raw.githubusercontent.com/$REPO/main/$SKILL_PATH/SKILL.md"
echo "  获取 $URL"
if curl -sf "$URL" -o "$DEST/SKILL.md"; then
  echo "  ✓ SKILL.md 已下载 ($(wc -c < "$DEST/SKILL.md") bytes)"
else
  echo "  ✗ main 分支失败,尝试 master..."
  URL="https://raw.githubusercontent.com/$REPO/master/$SKILL_PATH/SKILL.md"
  curl -sf "$URL" -o "$DEST/SKILL.md" || {
    echo "  ✗ 下载失败"
    if [[ -d "$DEST" && -z "$(ls -A "$DEST" 2>/dev/null)" ]]; then
      rmdir "$DEST" 2>/dev/null && echo "  ✓ 已清理空目录 skills/$TARGET/"
    fi
    exit 1
  }
  echo "  ✓ SKILL.md 已下载 (master)"
fi

# 安全检查(防病毒+危险模式): 下载后立即扫描
if [[ -f "$WS/scripts/security-check.sh" ]]; then
  echo "  🔍 安全检查..."
  bash "$WS/scripts/security-check.sh" "$DEST" || {
    echo "  ⛔ 安全检查未通过,已隔离 $TARGET"
    QDIR="/tmp/quarantine-$(date +%Y%m%d%H%M%S)"
    mkdir -p "$QDIR"
    mv "$DEST" "$QDIR/" 2>/dev/null
    echo "  → 隔离位置: $QDIR"
    exit 1
  }
fi

# 追加来源标注
cat >> "$DEST/SKILL.md" << EOF

---

> 来源:https://github.com/$REPO ($(date '+%Y-%m-%d') 吸收)
> 原始路径:$SKILL_PATH
EOF

echo "[$(date '+%Y-%m-%d %H:%M:%S')] skill_absorb: $REPO/$SKILL_PATH -> skills/$TARGET" >> "$LOG"
echo "✓ 完成。技能位置: skills/$TARGET/SKILL.md"
echo "  提示: 根据 OpenClaw 环境适配 frontmatter 与路径后使用"
