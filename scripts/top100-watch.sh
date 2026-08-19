#!/bin/bash
# top100-watch.sh — 跟踪 GitHub 高星技能仓库 TOP 100 更新 (2026-08-13)
# 用法: bash scripts/top100-watch.sh          # 静默检查, 仅更新基线
#       bash scripts/top100-watch.sh --report # 输出报告(供 cron 推送)
# 原理: 搜索 API 拉 topic:skills + topic:claude-skills 前100条,
#        合并按 star 取 TOP100, 与 skills-db/top100-state.json 对比
#        检测 updated_at/stars 变化 与 新入/跌出
set -euo pipefail

WS="$HOME/.openclaw/workspace"
STATE="$WS/skills-db/top100-state.json"
TMP1="$WS/skills-db/.top100-a.json"
TMP2="$WS/skills-db/.top100-b.json"
LOG="$WS/memory/events.log"
REPORT=0
[[ "${1:-}" == "--report" ]] && REPORT=1

fetch_page() {
  local q="$1"
  local url="https://api.github.com/search/repositories?q=${q}&sort=stars&order=desc&per_page=100&page=1"
  for attempt in 1 2 3; do
    local resp
    resp="$(curl -s -m 20 -H 'Accept: application/vnd.github+json' "$url")"
    if echo "$resp" | grep -q '"API rate limit exceeded"'; then
      echo "[rate-limit] 等待60s重试 (attempt=$attempt)" >&2
      sleep 60
      continue
    fi
    echo "$resp"
    return 0
  done
  echo '{"items":[]}'
}

echo "=== 拉取当前 TOP 状态 ==="
fetch_page "topic:skills" > "$TMP1"
fetch_page "topic:claude-skills" > "$TMP2"

# python: 对比并输出结果, 同时更新基线
RESULT=$(cd "$WS/skills-db" && python3 << 'EOF'
import json, datetime

def load(p):
    d = json.load(open(p))
    return d.get('items', [])

a = load('.top100-a.json')
b = load('.top100-b.json')
merged = {}
for r in a + b:
    merged[r['full_name']] = r
items = sorted(merged.values(), key=lambda r: -r['stargazers_count'])[:100]

old = json.load(open('top100-state.json'))
old_repos = old.get('repos', {})

lines = []
changed = False

for s in items:
    fn = s['full_name']
    cur = {
        'stars': s['stargazers_count'],
        'updated_at': (s.get('updated_at') or '')[:10],
        'description': (s.get('description') or '')[:120],
    }
    if fn in old_repos:
        o = old_repos[fn]
        if cur['updated_at'] != o.get('updated_at') or cur['stars'] != o.get('stars'):
            changed = True
            parts = []
            if cur['updated_at'] != o.get('updated_at'):
                parts.append('有更新 ' + o.get('updated_at', '?') + '→' + cur['updated_at'])
            if cur['stars'] != o.get('stars'):
                parts.append(str(o.get('stars')) + '★→' + str(cur['stars']) + '★')
            lines.append('  🔄 ' + fn + ' ' + ' '.join(parts))

old_names = set(old_repos.keys())
cur_names = {s['full_name'] for s in items}
new_names = sorted(cur_names - old_names)
dropped = sorted(old_names - cur_names)

if new_names:
    changed = True
    lines.append('  🆕 新入TOP100: ' + ', '.join(new_names))
if dropped:
    changed = True
    lines.append('  📉 跌出TOP100: ' + ', '.join(dropped))

out = {
    'schemaVersion': '1.0',
    'generated': datetime.datetime.now().isoformat(timespec='seconds'),
    'scope': 'top-100-skills-repos',
    'repos': {s['full_name']: {
        'stars': s['stargazers_count'],
        'updated_at': (s.get('updated_at') or '')[:10],
        'description': (s.get('description') or '')[:120],
    } for s in items},
}
json.dump(out, open('top100-state.json', 'w'), ensure_ascii=False, indent=2)

print('CHANGED' if changed else 'NO_CHANGES')
if changed:
    for l in lines:
        print(l)
EOF
)

echo "$RESULT"

if [[ "$RESULT" == CHANGED* ]]; then
  echo "$(date '+%Y-%m-%d %H:%M') | top100-watch | 检测到更新: $(echo "$RESULT" | wc -l) 行" >> "$LOG"
  # --report 模式: 组装微信推送报告
  if [[ $REPORT == 1 ]]; then
    echo ""
    echo "📡 TOP100 技能仓库有更新:"
    echo "$RESULT" | tail -n +2 | head -15
  fi
else
  if [[ $REPORT == 1 ]]; then
    echo ""
    echo "📡 TOP100 技能仓库跟踪 $(date '+%m-%d %H:%M'): 无更新 ✅"
  fi
fi
