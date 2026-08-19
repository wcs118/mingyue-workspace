#!/bin/bash
# session-watch.sh — 监控 main 会话上下文使用率,>=90% 自动触发压缩
# 老板授权(2026-08-17):会话涨到 90% 明月直接处理,不打扰
# cron: */30 * * * * (Asia/Shanghai), command 类型(仅异常时输出→announce 推送)
export PATH=$PATH:/root/.npm-global/bin
THRESHOLD=90
LOG=/root/.openclaw/workspace/memory/events.log
STAMP=$(date '+%F %T')

# 解析 main 会话使用率
OUT=$(timeout 30 openclaw sessions --json --agent main --limit 5 2>/dev/null | grep -vE "plugins|memos|AiToEarn|Telemetry|Database")
PCT=$(echo "$OUT" | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    print(-1); sys.exit()
for s in d.get('sessions',[]):
    if s.get('key')=='agent:main:main':
        ct=s.get('contextTokens') or 131072
        tt=s.get('totalTokens') or 0
        print(int(tt*100/ct) if ct else 0)
        break
else:
    print(-1)
")

if [ "$PCT" -lt 0 ]; then
    echo "$STAMP [session-watch] ⚠️ 无法读取会话状态(检查网关)" >> "$LOG"
    echo "⚠️ [session-watch] 无法读取 main 会话状态,请检查网关"   # 异常→推送
    exit 0
fi

if [ "$PCT" -ge "$THRESHOLD" ]; then
    echo "$STAMP [session-watch] ⚠️ main 会话 ${PCT}% >= ${THRESHOLD}%,自动触发 /compact" >> "$LOG"
    RESULT=$(timeout 180 openclaw sessions compact agent:main:main 2>&1 | grep -vE "plugins|memos|AiToEarn|Telemetry|Database" | tail -5)
    echo "$STAMP [session-watch] 压缩结果: $RESULT" >> "$LOG"
    echo "⚠️ [session-watch] main 会话已达 ${PCT}%,已自动触发 /compact"
    echo "压缩结果: $RESULT"
else
    echo "$STAMP [session-watch] 正常(${PCT}% < ${THRESHOLD}%),无需处理" >> "$LOG"
    # 正常时无 stdout 输出 → announce 无消息可推 → 天然静默 ✅
fi
exit 0
