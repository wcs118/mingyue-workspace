# HEARTBEAT.md - 定期检查清单

## 每轮心跳轮换检查(2-4 次/天)
- [ ] **GitHub 热榜**(阶段五):日常热榜已由 cron 每日 9:00 自动推送(0hao-trending-radar)
      心跳时仅抽查: 快速看看今日有无高价值新工具(可运行 bash scripts/trending-watch.sh 更新)
      注意:热榜出现高价值 AI Skill 时,记入 memory 并在合适时机向用户推荐吸收
- [ ] 微信/邮件:有无未读重要消息
- [ ] 服务器健康:磁盘、内存、gateway 进程存活(必要时 openclaw status)

## 状态
- lastChecks 记录在 memory/heartbeat-state.json(如需要)

## 提醒
- 夜间 23:00-08:00 保持安静,除非紧急
- 热榜发现值得吸收的技能/模型时,先记 memory,再问用户是否安装


## 0号v8 框架巡检(轮换 2-4 项)
- 不死鸟健康: bash scripts/phoenix-snapshot.sh status
- 梦境候选: bash scripts/evolution-cycle.sh --dry
- 双轨同步: bash scripts/vault-sync.sh up (无 Obsidian 时跳过)
- 事件账本: 重要操作已追加 memory/events.log

## ⚠️ 微信同步专项检查(每次网关重启后必做,2026-08-17 老板铁律)
- 核对 sessions.json 与运行时映射一致:
  journalctl -u openclaw-gateway --since "5 minutes ago" | grep "sessionKey=agent:main:openclaw-weixin" | tail -3
  python3 -c "import json; d=json.load(open('/root/.openclaw/agents/main/sessions/sessions.json')); k='agent:main:openclaw-weixin:6b4cecfbb17b-im-bot:direct:o9cq803kqb_albzwlv4ioyjhzsvs@im.wechat'; print(d.get(k,{}).get('sessionId','?'))"
- 两者必须指向同一 sessionId(当前活跃 939760d9);不一致 = 立即修索引+重启
- 改 sessions.json 前必须 cp 备份; 旧会话文件永不删除
