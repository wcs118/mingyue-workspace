#!/bin/bash
# fetch-top1000-skills.sh — 拉取 GitHub 前 2000 高星 skills 仓库
# 策略: topic:skills + topic:claude-skills 合并去重, 按 star 排序
# 输出: skills-db/skills-top2000.json (工作区)
set -euo pipefail

WS="$HOME/.openclaw/workspace"
OUT="$WS/skills-db/skills-top2000.json"
TMP1="$WS/skills-db/.tmp-skills.json"
TMP2="$WS/skills-db/.tmp-claude.json"
mkdir -p "$WS/skills-db"

# 拉取一页, 带重试
fetch_page() {
  local q="$1" page="$2"
  local url="https://api.github.com/search/repositories?q=${q}&sort=stars&order=desc&per_page=100&page=${page}"
  for attempt in 1 2 3; do
    local resp
    resp="$(curl -s -H 'Accept: application/vnd.github+json' "$url")"
    # 检查限流
    if echo "$resp" | grep -q '"API rate limit exceeded"'; then
      echo "[rate-limit] 等待 60s 后重试 (q=$q page=$page attempt=$attempt)" >&2
      sleep 60
      continue
    fi
    echo "$resp"
    return 0
  done
  echo '{"items":[]}' >&2
  echo "WARN: 拉取失败 q=$q page=$page" >&2
}

echo "=== 拉取 topic:skills 前 20 页 (2000 条) ==="
: > "$TMP1"
for p in $(seq 1 20); do
  fetch_page "topic:skills" "$p" | python3 -c "
import json,sys
d = json.load(sys.stdin)
for r in d.get('items', []):
    print(json.dumps(r))
" >> "$TMP1"
  echo "  page $p done ($(wc -l < "$TMP1") 条累计)"
  sleep 6.5 # 限速: 10 req/min → 每 6.5s 一页
done

echo ""
echo "=== 拉取 topic:claude-skills 补充 (最多 20 页) ==="
: > "$TMP2"
for p in $(seq 1 20); do
  fetch_page "topic:claude-skills" "$p" | python3 -c "
import json,sys
d = json.load(sys.stdin)
for r in d.get('items', []):
    print(json.dumps(r))
" >> "$TMP2"
  echo "  page $p done ($(wc -l < "$TMP2") 条累计)"
  sleep 6.5
done

echo ""
echo "=== 合并去重 + 排序 ==="
python3 << 'EOF'
import json

def load(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

a = load('.tmp-skills.json')
b = load('.tmp-claude.json')
print(f'topic:skills 原始: {len(a)} | topic:claude-skills 原始: {len(b)}')

# 按 full_name 去重
merged = {}
for r in a + b:
    merged[r['full_name']] = r
print(f'合并去重后: {len(merged)}')

# 按 star 排序
items = sorted(merged.values(), key=lambda r: -r['stargazers_count'])

# 精简字段
records = [{
    'rank': i+1,
    'full_name': r['full_name'],
    'stars': r['stargazers_count'],
    'description': (r.get('description') or '')[:200],
    'language': r.get('language'),
    'topics': r.get('topics', [])[:10],
    'html_url': r['html_url'],
    'updated_at': r.get('updated_at', '')[:10],
    'archived': r.get('archived', False),
} for i, r in enumerate(items)]

doc = {
    'schemaVersion': '1.0',
    'generated': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
    'source': 'GitHub Search API (topic:skills + topic:claude-skills, sort=stars)',
    'scope': 'top-2000-high-star-skills-repos',
    'total': len(records),
    'skills': records,
}
with open('skills-top2000.json', 'w') as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)

print(f'✓ 已写入 skills-top2000.json: {len(records)} 条')
print(f'  最高星: {records[0]["stars"]}★ {records[0]["full_name"]}')
EOF

rm -f "$TMP1" "$TMP2"
echo ""
echo "=== 完成 ==="
