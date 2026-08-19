#!/bin/bash
# daily-report.sh — 每日晨报：服务器巡检 + GitHub 热榜
# 由 cron 每日 08:00 调用，announce 推送到老板微信
# 用法: bash scripts/daily-report.sh

set -uo pipefail

# 统一用 BASH_SOURCE 相对定位, 避免 cron/sudo 下 $HOME 不一致
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WS" || exit 1

echo "🌙 明月晨报 $(date '+%Y-%m-%d %H:%M %A')"
echo ""

# ---------- 服务器巡检 ----------
echo "🖥️ 服务器巡检"
echo "----------------"
# 负载 & 运行时间
load=$(uptime | sed -E 's/.*load average: (.*)/\1/')
echo "负载: $load"

# 磁盘
disk=$(df -h / | awk 'NR==2 {print "使用率 "$5" (已用 "$3" / 共 "$2")"}')
echo "磁盘: $disk"

# 内存 (用 -k 原始数值算百分比, 避免 -h 人类可读单位被 awk 误当小数)
mem=$(free -k | awk '/^Mem/ {printf "使用率 %.0f%% (已用 %.1fG / 共 %.1fG)", $3/$2*100, $3/1024/1024, $2/1024/1024}')
echo "内存: $mem"

# 关键服务 (先确认有 systemd, 避免容器里误报)
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet openclaw-gateway 2>/dev/null; then
    echo "服务✅: openclaw-gateway"
  else
    echo "服务❌: openclaw-gateway ⚠️ 需要处理！"
  fi
else
  echo "服务: (无 systemd 环境, 跳过检查)"
fi
echo ""

# ---------- GitHub 热榜 ----------
echo "🔥 GitHub 热榜"
echo "----------------"
if bash scripts/trending-watch.sh >/dev/null 2>&1 && [ -s memory/trending-latest.md ]; then
  # 按 section 精简: 每段只留前 3 条完整条目(标题行+URL行), 跳过空段
  awk '
    /^# / {print; next}
    /^## / {line=0; skip=0}
    /^- / {line++; skip = (line > 3)}
    skip {next}
    {print}
  ' memory/trending-latest.md
else
  echo "⚠️ 热榜抓取失败(GitHub API 可能限流)，稍后可手动查看 memory/trending-latest.md"
fi
