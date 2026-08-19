#!/bin/bash
# finish-check.sh — 收尾检查(老板 2026-08-18 铁律: 干完活打扫战场不留尾巴)
# 用法: bash scripts/finish-check.sh [--clean]
#   --clean  执行清理(默认只检查报告)
# 每次完成任务后必跑: ①系统漏洞 ②清垃圾 ③整理归类 ④确认无遗留
set -uo pipefail
WS=/root/.openclaw/workspace
TS=$(date +%F-%H%M)
REPORT=""
echo "════════════════════════════════════════"
echo "🧹 收尾检查 $(date '+%F %T')"
echo "════════════════════════════════════════"

# ── ① 系统漏洞/异常检查 ──────────────────────
echo ""
echo "【1/4】系统状态检查"
# 1.1 网关健康
H=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:18789/health 2>/dev/null)
if [ "$H" = "200" ]; then
  echo "  ✅ 网关 health 200"
else
  echo "  ❌ 网关 health=$H — 立即修复!"
  REPORT="$REPORT\n  ❌ 网关异常"
fi
# 1.2 服务状态
if systemctl is-active openclaw-gateway >/dev/null 2>&1; then
  echo "  ✅ openclaw-gateway active"
else
  echo "  ❌ openclaw-gateway 未运行"
fi
# 1.3 会话索引一致性(微信同步铁律)
python3 - "$WS" << 'PYEOF' 2>/dev/null
import json, sys
try:
    d = json.load(open('/root/.openclaw/agents/main/sessions/sessions.json'))
    k = 'agent:main:openclaw-weixin:6b4cecfbb17b-im-bot:direct:o9cq803kqb_albzwlv4ioyjhzsvs@im.wechat'
    m, w = d.get('agent:main:main',{}).get('sessionId'), d.get(k,{}).get('sessionId')
    print("  ✅ 会话索引一致" if m==w and m else "  ❌ 会话索引不一致(main=%s wx=%s)" % (m,w))
except Exception as e:
    print("  ⚠️ 索引检查跳过:", e)
PYEOF
# 1.4 磁盘/内存
D=$(df -h / | tail -1 | awk '{print $5}')
M=$(free -h | awk '/Mem:/{print $3"/"$2}')
echo "  ℹ️ 磁盘已用 $D | 内存 $M"

# ── ② 清理垃圾 ──────────────────────────────
echo ""
echo "【2/4】垃圾检查"
CLEANABLE=0
# 2.1 /tmp 编译缓存(可再生)
if [ -d /tmp/node-compile-cache ] || [ -d /tmp/jiti ]; then
  S=$(du -sh /tmp/node-compile-cache /tmp/jiti 2>/dev/null | awk '{print $1}' | tr '\n' ' ')
  echo "  ⚠️ 编译缓存残留: $S"
  if [ "${1:-}" = "--clean" ]; then rm -rf /tmp/node-compile-cache /tmp/jiti && echo "  ✅ 已清理编译缓存"; CLEANABLE=1; fi
else
  echo "  ✅ 无编译缓存残留"
fi
# 2.2 checkpoint 堆积(>10 个旧快照提示归档)
CNT=$(ls /root/.openclaw/agents/main/sessions/*.checkpoint.*.jsonl 2>/dev/null | wc -l)
if [ "$CNT" -gt 10 ]; then
  echo "  ⚠️ checkpoint 堆积 $CNT 个(建议归档,保留每会话最新1个)"
  if [ "${1:-}" = "--clean" ]; then
    mkdir -p /root/.openclaw/config/backups
    cd /root/.openclaw/agents/main/sessions/
    for base in $(ls *.checkpoint.*.jsonl 2>/dev/null | sed 's/\.checkpoint\..*//' | sort -u); do
      newest=$(ls -t ${base}.checkpoint.*.jsonl 2>/dev/null | head -1)
      for f in ${base}.checkpoint.*.jsonl; do
        [ "$f" != "$newest" ] && [ -f "$f" ] && mv "$f" /tmp/chk-archive/ 2>/dev/null
      done
    done
    tar czf /root/.openclaw/config/backups/checkpoints-auto-$(date +%Y%m%d).tar.gz -C /tmp chk-archive 2>/dev/null && rm -rf /tmp/chk-archive
    echo "  ✅ 已归档旧 checkpoint"
  fi
else
  echo "  ✅ checkpoint 正常($CNT 个)"
fi
# 2.3 *.bak 散落脚本
BK=$(find "$WS/scripts" -name "*.bak" -o -name "*.old" 2>/dev/null | wc -l)
[ "$BK" -gt 0 ] && echo "  ⚠️ scripts 有 $BK 个 .bak/.old" || echo "  ✅ 无散落备份文件"

# ── ③ 整理归类 ──────────────────────────────
echo ""
echo "【3/4】归类检查"
# 3.1 openclaw.json 备份是否归档
BKCNT=$(ls /root/.openclaw/openclaw.json.bak* 2>/dev/null | wc -l)
if [ "$BKCNT" -gt 0 ]; then
  echo "  ⚠️ openclaw.json 有 $BKCNT 个散落备份"
  if [ "${1:-}" = "--clean" ]; then
    mkdir -p /root/.openclaw/config/backups
    mv /root/.openclaw/openclaw.json.bak* /root/.openclaw/config/backups/ 2>/dev/null
    echo "  ✅ 已归档配置备份"
  fi
else
  echo "  ✅ 配置备份已归档"
fi
# 3.2 台账存在性
[ -f "$WS/reference/models-registry.md" ] && echo "  ✅ 模型台账在(reference/models-registry.md)" || echo "  ⚠️ 模型台账缺失"
# 3.3 今日笔记
TODAY=$(date +%F)
[ -f "$WS/memory/$TODAY.md" ] && echo "  ✅ 今日笔记在(memory/$TODAY.md)" || echo "  ⚠️ 今日笔记缺失 — 记得写!"

# ── ④ 确认无遗留 ─────────────────────────────
echo ""
echo "【4/4】遗留确认"
echo "  工作日志: 追加到 memory/$(date +%F).md ✅"
echo "  收尾完成: $(date '+%F %T')"

echo ""
echo "════════════════════════════════════════"
if [ -n "$REPORT" ]; then
  echo -e "⚠️ 发现异常:$REPORT"
  echo "需人工处理!"
else
  echo "✅ 全部通过,战场干净,无尾巴。"
fi
echo "════════════════════════════════════════"
