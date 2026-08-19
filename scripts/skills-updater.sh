#!/bin/bash
# skills-updater.sh — 技能自主更新迭代：检查已吸收仓库 upstream 版本，有更新自动拉新入库
# 用法: bash scripts/skills-updater.sh [--force]  (--force=忽略状态强制全量检查)
# 日志: memory/events.log + skills-db/upstream-state.json(记录各仓库最新 commit)

set -uo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM=$WS/skills-db/upstream.json
STATE=$WS/skills-db/upstream-state.json
LOG=$WS/memory/events.log
TMP=/tmp/skills-update
mkdir -p "$TMP"

# 初始化 state
[ -f "$STATE" ] || echo '{}' > "$STATE"

UA='Accept: application/vnd.github+json'
UAG='User-Agent: mingyue-updater'
updated=0; changed=0; failed=0
CHANGED_LIST=""

# 读取 repo 列表 (local_dir|owner/repo|branch)
mapfile -t REPOS < <(python3 -c "
import json
d = json.load(open('$UPSTREAM'))
for local, info in d['repos'].items():
    print(f\"{local}|{info['repo']}|{info['branch']}\")
")

for entry in "${REPOS[@]}"; do
    IFS='|' read -r local repo branch <<< "$entry"
    owner_repo="$repo"
    latest_sha=$(curl -s --max-time 20 -H "$UA" -H "$UAG" \
        "https://api.github.com/repos/$owner_repo/commits/$branch" 2>/dev/null \
        | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('sha',''))" 2>/dev/null)
    if [ -z "$latest_sha" ]; then
        echo "  ⚠ $repo: 获取 commit 失败(限流/网络)" | tee -a "$LOG"
        failed=$((failed+1)); continue
    fi
    prev_sha=$(python3 -c "
import json
s = json.load(open('$STATE'))
print(s.get('$repo',''))" 2>/dev/null)
    if [ "$prev_sha" = "$latest_sha" ] && [ "${1:-}" != "--force" ]; then
        continue  # 无更新
    fi
    # 有更新(或首次): 下载新 tarball 对比
    changed=$((changed+1))
    name=$(basename "$local")
    url="https://codeload.github.com/$owner_repo/tar.gz/refs/heads/$branch"
    if curl -sL --max-time 120 -o "$TMP/$name.tar.gz" "$url" 2>/dev/null && [ -s "$TMP/$name.tar.gz" ]; then
        newdir="$TMP/$name-new"; rm -rf "$newdir"; mkdir -p "$newdir"
        if tar -xzf "$TMP/$name.tar.gz" -C "$newdir" --strip-components=1 2>/dev/null; then
            old_skills=$(find "$WS/skills-db/$local" -name SKILL.md 2>/dev/null | wc -l)
            new_skills=$(find "$newdir" -name SKILL.md 2>/dev/null | wc -l)
            # 备份旧版 → 更新
            if [ -d "$WS/skills-db/$local" ]; then
                rm -rf "$WS/skills-db/$local.bak"
                mv "$WS/skills-db/$local" "$WS/skills-db/$local.bak"
            fi
            mkdir -p "$WS/skills-db/$local"
            cp -r "$newdir/." "$WS/skills-db/$local/"
            # 安全检查: 更新入库后立即扫描
            if [[ -f "$WS/scripts/security-check.sh" ]]; then
              bash "$WS/scripts/security-check.sh" "$WS/skills-db/$local" >/dev/null 2>&1 || {
                echo "  ⛔ $repo 安全检查未通过,回滚到旧版" | tee -a "$LOG"
                rm -rf "$WS/skills-db/$local"
                cp -r "$WS/skills-db/$local.bak" "$WS/skills-db/$local" 2>/dev/null
                rm -rf "$WS/skills-db/$local.bak"
                failed=$((failed+1)); continue
              }
            fi
            rm -rf "$WS/skills-db/$local.bak"
            # 更新 state
            python3 -c "
import json
s = json.load(open('$STATE'))
s['$repo'] = '$latest_sha'
json.dump(s, open('$STATE','w'), ensure_ascii=False, indent=2)"
            updated=$((updated+1))
            CHANGED_LIST="$CHANGED_LIST\n  ✅ $repo: $old_skills→$new_skills SKILL.md"
            echo "[$(date '+%Y-%m-%d %H:%M')] skills-updater: $repo 更新($old_skills→$new_skills SKILL.md)" >> "$LOG"
        else
            echo "  ⚠ $repo: 解压失败" | tee -a "$LOG"; failed=$((failed+1))
        fi
    else
        echo "  ⚠ $repo: 下载失败" | tee -a "$LOG"; failed=$((failed+1))
    fi
    sleep 2  # 限流保护
done

echo "=== skills-updater 完成: 检查 ${#REPOS[@]} 仓库, 更新 $updated, 失败 $failed ==="
[ -n "$CHANGED_LIST" ] && echo -e "变更:$CHANGED_LIST"
# 静默模式: 无更新无失败时不输出(供 cron 判断是否推送)
if [ "$updated" -eq 0 ] && [ "$failed" -eq 0 ]; then
  exit 0
fi
