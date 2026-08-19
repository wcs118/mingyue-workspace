#!/bin/bash
# trending-watch.sh — 每日 GitHub 热榜雷达(阶段五)
# 抓取: ①近7天新仓库高星榜 ②AI/Agent 关键词热榜 ③skills 仓库榜
# 输出: memory/trending-latest.md (只保留最新一期, 供心跳/汇报读取)
# 用法: bash scripts/trending-watch.sh [--json]
set -euo pipefail

WS="$HOME/.openclaw/workspace"
OUT="$WS/memory/trending-latest.md"
TMP="$WS/memory/.trending-tmp.md"
mkdir -p "$WS/memory"

# GitHub API 拉取(带限流检测: 403/限流时输出错误到 stderr 并返回非零)
fetch() {
  local q="$1" per="$2"
  local url="https://api.github.com/search/repositories?q=${q}&sort=stars&order=desc&per_page=${per}"
  local tmp
  tmp=$(mktemp)
  local code
  code=$(curl -s -o "$tmp" -w '%{http_code}' -H 'Accept: application/vnd.github+json' --max-time 20 "$url")
  if [ "$code" != "200" ]; then
    echo "  ⚠️ GitHub API 错误 (HTTP $code), 可能限流" >&2
    rm -f "$tmp"
    return 1
  fi
  cat "$tmp"
  rm -f "$tmp"
}

fmt() {
  python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception as e:
    print('  (解析失败: %s)' % e, file=sys.stderr); sys.exit(1)
items = d.get('items', [])
if not items:
    print('  (无数据)')
for r in items[:10]:
    stars = r.get('stargazers_count', 0)
    name = r.get('full_name', '?')
    desc = (r.get('description') or '')[:70]
    lang = r.get('language') or '-'
    url = r.get('html_url', '')
    print(f'- ⭐{stars:,} {name} [{lang}] {desc}')
    print(f'  {url}')
"
}

{
  echo "# 📡 GitHub 热榜雷达 $(date '+%Y-%m-%d %H:%M')"
  echo ""
  echo "## 🔥 近 7 天新仓库 TOP(created:>7天前)"
  fetch "created:%3E$(date -d '7 days ago' +%Y-%m-%d)+stars:%3E50" 10 | fmt
  echo ""
  echo "## 🤖 AI/Agent 主题热榜"
  fetch "topic:ai+created:%3E$(date -d '30 days ago' +%Y-%m-%d)+stars:%3E100" 8 | fmt
  echo ""
  echo "## 🧩 AI Agent 框架热榜"
  fetch "topic:agents+created:%3E$(date -d '90 days ago' +%Y-%m-%d)+stars:%3E200" 8 | fmt
  echo ""
  echo "## 🛠️ skills 仓库热榜(可吸收候选)"
  fetch "topic:skills+stars:%3E100" 5 | fmt
} > "$TMP" || { echo "❌ 热榜抓取失败(API 限流或网络错误), 保留旧数据" >&2; rm -f "$TMP"; exit 1; }

mv "$TMP" "$OUT"
echo "✓ 热榜已更新: $OUT"
