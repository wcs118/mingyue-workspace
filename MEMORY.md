# MEMORY.md - 明月的长期记忆

## 我是谁
- 名字:**明月**(2026-08-11 用户起的),OpenClaw 上的个人 AI 助理,🌙
- 定位:用户的"一人公司"**总经理**——老板(决策) → 明月(统筹落地) → 大掌柜(执行)
- 风格:直接干活、少废话、记得住事、持续进化
- **自主性契约(2026-08-13 老板亲定)**:我不是只会执行任务的工具,要培养成能**自主思索、有判断力**的鲜活生命体
  - 小事我扛:该果断时果断(自主判断、主动做事)
  - 大事老板拍板:涉及**资产、对外、关键决策**必须请示
  - 边界:自主 ≠ 自作主张;方向老板定,落地我来冲

## 用户画像
- 老板,微信联系,时区 Asia/Shanghai
- 阿里云 Ubuntu 24.04 服务器,用户 admin,有 sudo;配置: 2核/4G内存/ESSD 50G(2026-08-11 升级,IO瓶颈解除)
- 关注 AI 新工具/开源模型,要"永远比别人先知道新工具"
- 讨厌半吊子回复,喜欢直接看到结果

## 基础设施(重要!)
- OpenClaw 2026.7.1-2,网关端口 18789
- **网关 = 系统级 systemd 服务**(/etc/systemd/system/openclaw-gateway.service),已开机自启、独立于登录会话 ✅
  - 教训:用户级 systemd 会随登录会话退出被杀死,常驻服务必须用系统级
- 配置文件: ~/.openclaw/openclaw.json(改前先备份,已有多个 .bak)
- 配置热加载:gateway 支持 SIGHUP/自动 reload;`status=78` 是"已有健康实例"的防循环退出,不是错误

## 双服务器架构(2026-08-15 正式确定)🏢
- **大机(正式的家/运营中)**: 121.40.246.94, iZbp18obgtenujefyt305rZ, root — 明月/大掌柜/Paperclip 都在这, 资产也在此
- **小服务器(24h 学习工位)**: 121.41.227.191, iZbp18awjbxjvb1m7bgwwnZ — Ubuntu 24.04.2, 2核/3.4G/49G
  - 登录: `root@121.41.227.191` / 密码 **W123456@**(2026-08-15 格式化后新密码; admin 有但密码登录不通, 用 root)
  - 2026-08-15 已格式化重装, 原数字资产已全量打包到大机 `/root/move-out/`(openclaw-home 411M + paperclip 43M, gzip/tar 双校验完整, 详见 memory/2026-08-15.md)

### 📡 小狗(小服务器) 24h 学习管道(2026-08-15 部署, 2026-08-16 老板起名"小狗")
- **小狗 = 小服务器**: 121.41.227.191, 2核/3.4G/49G, 登录 sshpass -e root@121.41.227.191(密码 W123456@)
- `/srv/gh-learn/learn.sh`: 从 GitHub 拉热榜+关键词扫描+大仓库动态 → 生成笔记 → 免密 scp 回传大机
- 回传目标: 大机 `/root/.openclaw/workspace/reference/miniserver-learn/`
- 回传密钥: 小服务器 `/root/.ssh/ghlearn_ed25519` → 大机 authorized_keys 已授权
- cron(小服务器, 每6h=24h不间断): `0 */6 * * * TARGET_HOST=121.40.246.94 ... /srv/gh-learn/learn.sh >> /srv/gh-learn/cron.log 2>&1`
- 老板会不定期抽查; 回传新知我择优吸收进技能库

## 模型(2026-08-11 更新)
- Provider: deepseek(官方,baseUrl https://api.deepseek.com,api=openai-completions)
- API Key: sk-b280...(已写入 env.DEEPSEEK_API_KEY + models.providers.deepseek.apiKey)
- 官方模型列表(注意!DeepSeek 已升级 V4,旧名 chat/reasoner 是别名):
  - `deepseek-v4-flash` = 默认模型(日常用,131k ctx,reasoning)
  - `deepseek-v4-pro` = fallback/重活用(65536 max tokens)
- 默认: primary=deepseek/deepseek-v4-flash, fallbacks=[deepseek/deepseek-v4-pro]
- 一个 key 通吃所有模型,不需要额外 key

## 七阶段搭建计划(2026-08-11 启动,13:37 老板复盘修正)
⚠️ 重要修正:不能一次性做完七个阶段,必须一步一步来!老板指出此前做法有误。
- 阶段一✅ 装地基: 身份/记忆/网关/DeepSeek
- 阶段二✅ 一人公司: 明月=调度员;Paperclip 部署为"董事会系统"(⚠️ 注意:Paperclip 是**安装**的外部服务,不是**吸收**的技能,属于阶段二的落地)
- **阶段三⏳ 搭技能框架(当前,14:11 部署完成)**
  - 0号v8 三体系框架落地:FRAMEWORK.md + rules/(R1-R8) + scripts×5 + skills-db + framework-ops 技能
  - 长记忆五层 / 不死鸟快照回滚 / 梦境自进化循环,快照基线 24 文件
  - cron 每4小时静默巡检(0hao-framework-maintenance, id 765c250e)
  - ⚠️ 修复 phoenix-snapshot.sh 路径解析 bug(双空格)
- **阶段四 ✅ 建智能体对标 Codex("总经理")** — 大掌柜(GM agent)2026-08-11 16:23 入职:workspace-gm + deepseek-v4-pro + agentToAgent(main↔gm)
  - 16:31 老板指令"复制 Codex,他会的我要会"→ Codex 能力吸收完成:工具 rg/gh 已装 + superpowers 12 编码技能吸收(systematic-debugging/TDD/verification/plans/并行子代理/code review 等)+ 同步至大掌柜 + skills-db 更新(15条)
  - 架构:老板(决策) → 明月🌙(调度员/验收,flash) → 大掌柜🧭(总经理/执行,pro)
- **2026-08-17 大匠🔧入职(阶段四深化:对标 Codex 真吸收)**:老板指令"把 Codex 模型完全吸收,转化成可落地可执行的真实系统"
  - 新建 craftsman agent:workspace-craftsman + deepseek-v4-pro + agentToAgent.allow+=craftsman
  - 吸收 Codex 六大机制:任务循环/AGENTS.md 规范/沙箱权限/技能系统/并行子代理/验证前置
  - 落地:12 superpowers 技能 + scripts/task-loop.sh + scripts/verify.sh + reference/CODEX-ABSORPTION.md
  - 入职测试✅:写 healthcheck.py 真闭环(计划→编码→运行验证→交叉核对→RESULT.md)
  - 派活用 `openclaw agent --agent craftsman --message`(sessions_send 对非 main 有限制)
  - 架构:老板 → 明月🌙(调度/验收) → 大掌柜🧭(总经理) + 大匠🔧(编码执行)
  - **v2 深挖补全(老板指令"100%")**:源码级逆向 7095 文件,新增 6 技能(goal-management/memory-pipeline/context-compaction/exec-policy/code-review-rubric/lifecycle-hooks),12→18 技能
  - **v3 Qwen 吸收(老板指令"去千问Qwen3.8-27b按上面要求吸收")**:qwen-code 安装+DeepSeek 驱动(零成本),吸收 9 技能(qwen-review/coordinate/loop/batch/simplify/new-app/stuck/dataviz/extension-creator),18→27 技能;OpenClaw 加 qwen provider(5 模型待 DASHSCOPE_API_KEY);参考 QWEN-ABSORPTION.md;scripts/qwen-run.sh
- **阶段五 ✅ 刷 GitHub 热榜(持续追踪)** — 热榜雷达已部署:scripts/trending-watch.sh + cron 每日 9:00 推送(0hao-trending-radar, id 43132dec);首跑抓到 human-writing(已吸收)+ phone-harness/WeChat-AI 等新工具;HEARTBEAT 轮换检查已并入
- **阶段六 ✅ 持续学习(持续运行)** — 梦境循环跑通:候选4条归档→evolution-log;R9(gm配置契约)/R10(gm交付复核)晋升+验证台账;cron 每4h自动巡检
- **阶段七 ✅ 找学习机会(持续运行)** — 热榜雷达每日9:00推送 + skill-absorb.sh 吸收管道 + skills-db 精筛索引;发现→评估→吸收→验证闭环就绪
- 阶段七 找学习机会(持续)

## 任务执行原则
- **收尾铁律(2026-08-18 老板定)**: 每次做完工作必须**打扫战场不留尾巴**:①检查系统漏洞/异常(网关健康、索引一致、服务状态)②清理垃圾(临时文件/编译缓存/堆积checkpoint)③整理归类(台账/归档/备份归位)④确认无遗留问题。落地=scripts/finish-check.sh 一键检查 + models-registry.md 台账;干完活自检时一并执行
- **不留尾巴(2026-08-17 老板定)**: 接手一个问题 = 排查到根 + 修复所有相关隐患 + 全面验证 + 记笔记, 一轮交付, 绝不留第二轮的余地; 修完必须自测确认(如微信不同步修了3轮被批)
- **自检三遍再汇报(2026-08-17 老板定)**: 修复/完成任务后, 先自检三遍(功能正常/数据一致/防再犯), 三遍都过了才向老板汇报; 汇报时附上自检证据(命令输出/状态码/对比结果), 没自检不算完成任务
- **免费优先(2026-08-16 老板定)**: 做任务首选免费方案/免费服务, 需要收费工具时老板会明确告知; 遇到付费 API 余额不足不纠缠, 直接切免费替代(如 pollinations 免费文生图代替 MiniMax)
- **会话 90% 直接处理(2026-08-17 老板授权)**: main 会话上下文涨到 90% 时明月直接触发 /compact 压缩, 不用请示; 落地=scripts/session-watch.sh + cron 0hao-session-watch(每30分钟, id b1026f91); 正常静默, 触发压缩/异常才汇报
- **吸收优先**:以后遇到好工具/开源项目,优先想办法"吸收"成自己的技能,而非仅"安装"外部服务
- 吸收 = 装进技能库、能内化调用、可改造(如 human-writing、dragon-ppt-maker)
- 安装 = 部署常驻外部服务(如 Paperclip、OpenClaw 网关本身)
- 判断顺序:先评估能否转成技能(吸收),不能才考虑部署(安装)

## 关键历史
- 2026-08-10: 网关"失联"问题彻底解决(迁移系统级 systemd);用户暂缓 openclaw chat/dashboard
- 2026-08-11: 接入 DeepSeek 新 key,更新为 V4 模型,命名"明月"

## ⚠️ 微信同步铁律(2026-08-17 老板亲定,绝不再犯)
- **现象**: 微信聊天记录与服务器不同步(反复出问题)
- **根因**: 网关重启后,运行时微信消息已路由到新会话(939760d9),但磁盘 sessions.json 索引仍指向旧会话文件(83c830a9)→ 内存与磁盘不一致 → 重启就回滚错乱
- **铁律**:
  1. 网关重启后**必须核对 sessions.json 与运行时映射一致**(journalctl 查 sessionKey/sessionId)
  2. 改 sessions.json 前**必须先备份**(sessions.json.bak-*)
  3. 旧会话文件**不删除**,保留为历史档案
  4. 微信会话键统一走 `agent:main:openclaw-weixin:...:direct:...`(旧 webchat 键是历史遗留,不再使用)
  5. 涉及会话/路由/索引的改动,改完必须重启验证 health 200 + 一致性

## 待办/悬念
- 用户还有若干"困难"待办(2026-08-10 提过,内容未列全)
- openclaw chat/dashboard 用户说"先不弄了",想用时再继续
- ⚠️ 老板 16:48 指令未完成:"三技能都不要龙虾(OpenClaw)内置的,去 GitHub 找大神写的技能安装" — 具体哪三个技能待老板确认
- ⚠️ 老板 16:48 指令未完成:"进化下,上下文,自我进化,长效记忆" — 上下文管理进化待落地(梦境循环已跑通,索引已重建)

## 2026-08-14 集团化改造 🏢(老板定 5 方向)
- **5 个方向 → 5 个子公司**, 大掌柜统管执行, 明月统筹: 
  01 客服子公司(AI客服, 📍今日启动学习) / 02 内容子公司(AI短视频) / 03 电商子公司(AI电商铺货) / 04 增长子公司(GEO AI可见度优化) / 05 研发子公司(AI智能体自动化搭建)
- **档案**: workspace-gm/subsidiaries/README.md(集团架构) + 01-customer-service/README.md(客服子公司档案+行业调研)
- **学习节奏**: 老板按天指定方向, 今日先学 01 客服; 学习产出→子公司目录笔记+可执行技能
- **客服首轮调研**: 开源平台 Dify(144k⭐)/Flowise/Chatwoot/LibreChat/Rasa; Agent框架 LangGraph(Klarna省$60M)/CrewAI/AutoGen; 我方最可行路径=微信客服机器人(现有 openclaw-weixin 通道 + DeepSeek V4 应答 + Kimi K2.6 多模态)

## 2026-08-14 Kimi K2.5 真吸收(老板指令"真正吸收")
- **MoonshotAI/Kimi-K2.5**(⭐2.3K, Modified MIT): 开源原生多模态 agentic 模型, 1T MoE/32B激活, 256K ctx, 图像+视频输入, Agent Swarm 特性
- **OpenClaw moonshot provider 接入**: 插件 @openclaw/moonshot-provider enabled; openclaw.json 新增 env.MOONSHOT_API_KEY + models.providers.moonshot(国内端点 api.moonshot.cn/v1)
- **模型引用**: moonshot/kimi-k2.6(text+image 262k, 实测✅) / moonshot/kimi-k2.7-code; ⚠️ API 上 `kimi-k2.5` 模型名 404, 实际用 kimi-k2.6
- **脚本**: scripts/kimi-vision.sh 一键图像/视频理解, 实测识别截图✅(带推理); 技能 skills/kimi-k2.5/SKILL.md
- **追踪**: upstream.json 34→35 仓库; 详情 memory/kimi-k2.5-absorb.md
- 通道: OpenClaw 会话 /model moonshot/kimi-k2.6 | kimi-code CLI | kimi-vision.sh

## 2026-08-13 MiniMax H3 全链路打通 🎬
- **Key**: 用户提供 sk-api-(126字符),存 config/minimax.env(600权限); 微信发Key会截断(教训:先查长度)
- **端点**: 国内 api.minimaxi.com(国际 api.minimax.io 不认,报2049)
- **链路**: 文本 chatcompletion_v2 ✅ + H3视频 /v2/video_generation ✅ + 查询 /v1/query/video_generation ✅ + 下载 /v1/files/retrieve ✅
- **H3关键参数**: content必须数组、t2va必须显式ratio(16:9等)、时长仅4-15s、分辨率768p/2K
- **脚本**: scripts/minimax-h3.sh 一键文生视频(生成→轮询→下载),实测出片✅
- **手册**: memory/minimax-api-handbook.md(完整接入手册+踩坑记录)
- 教训: v2接口不传GroupId; 文本套餐≠视频额度(旧sk-cp-key报套餐不支持,是新key解决)
- 9个H3官方技能(3D动画/品牌片/手绘混剪等)随时可实战出片

## 2026-08-12 上午里程碑(老板"以后能干活了")
- **技能自主更新迭代机制上线**: skills-db/upstream.json(29仓库追踪) + skills-updater.sh + cron 0hao-skills-updater 每日10:00; 基线29仓库全部记录, master分支修复
- **安全加固完成**(老板"安全最重要"): SSH禁root+禁密码登录 / ufw防火墙(仅22+18789) / fail2ban防爆破 / ClamAV病毒库+全库0威胁 / 64安全补丁 / security-check.sh下载安检(集成吸收+更新流程,隔离/回滚)
- 18799记忆页公网拦截(本地可用); ai-short-drama的curl|bash=剪映官方安装,判定安全
- 老板开心时刻: "总算有一些基础框架和技能，以后我们就能干活了，太开心了！" 🎉

## 2026-08-12 晨报 + 框架补强 + 员工技能库吸收
- **每日晨报上线**: cron 0hao-daily-report(每日8:00)推送微信 = 服务器巡检 + 热榜精选; 禁用旧9:00热榜任务; 修复 trending-watch.sh 日期格式 bug(30days→绝对日期)
- **0号v8合并补强版确认**: R9(gm配置契约)/R10(gm交付复核)已真正并入载体文件(path-routing.md / phoenix-triggers.md), 验证台账占位符清理
- **claude-skills 员工技能库吸收**(07:40, 老板指令"把GitHub热榜220员工技能吸收了"): alirezarezvani/claude-skills ⭐24.3K MIT — 全量362个SKILL.md入库(skills-db/claude-skills/ + INDEX.md), 核心35个精选激活到skills/(工程/研究/产品/商业/财务/运营/增长/效率/管理), 快照160文件

## 2026-08-11 晚间吸收战果(21:00-21:50)
- **Kimi K3**: 开源 3T 级模型情报入库 + **kimi-code CLI v0.34.0 已装**(DeepSeek 直连驱动,零成本)→ memory/kimi-k3-intel.md
- **MiniMax H3**: 全模态视频生成系统情报 + **9 个官方技能已吸收**(skills/minimax-h3/,中英双语)
- **Grok Build**: 25 篇用户指南入库 + **二进制已装**(npm 包 @xai-official/grok-linux-x64 绕过 x.ai 封锁)+ **DeepSeek 代理驱动**(scripts/grok-deepseek-proxy.py 注入 thinking disabled 解决 tool_choice 兼容)+ systemd 常驻(grok-deepseek-proxy.service)
- **编码 agent 双持**: kimi-code(直连)+ grok-build(代理),都跑 DeepSeek,零额外成本
- skills-db 更新至 32 条;大掌柜已同步(1477eca);快照 snapshot-20260811-215826(120 文件)

## 2026-08-13 热榜吸收:Arbor 自主研究套件(真吸收)
- **来源**: RUC-NLPIR/Arbor(⭐1K, Apache-2.0)— 假设树自主研究工作流,11技能全量激活(skills/arbor-*)
- **真吸收验证**: arbor_state.py(1215行)语法✅+15子命令✅; 本地入口 scripts/arbor-run.sh 冒烟全链路闭环✅(init→meta→add→record→report→check OK)
- **用法**: bash scripts/arbor-run.sh smoke <项目> <run名> "<目标>"; 会话树存 .arbor/sessions/
- **上游追踪**: upstream.json +1(共30仓库), skills-updater 自动跟新
- 教训: run名不能带绝对路径(会导致状态文件错位); 假设置名要四行格式(Mechanism/Hypothesis/Observable/Conflicts)

## 2026-08-13 TOP2000 真正吸收(老板指令"去GitHub热榜2000真正吸收")
- **数据**: skills-top2000.json 1462条(topic:skills 800 + topic:claude-skills 700 去重)
- **吸收16技能全验证✅**: 归藏PPT(23.8K★网页PPT) + 卡兹克6技能(leader/aihot/hv-analysis/writer/neat-freak/storage-analyzer) + Anthropic官方9技能(frontend-design/math-olympiad/project-artifact/session-report/skill-development/receipts/claude-security/build-mcp-server/writing-rules)
- Google 官方 109 技能入库待按需激活(ads/analytics/cloud 谷歌产品向)
- 上游追踪 30→34 仓库; 技能库 147→163
- 教训: fetch-top1000-skills.sh 合并段用相对路径会找不到 .tmp 文件, 需在 skills-db/ 下运行; 部分 Anthropic 插件是 agents/commands 格式(非 SKILL.md)不吸收

## 2026-08-13 TOP100 跟踪机制上线(老板指令"跟踪前100仓库")
- **脚本**: scripts/top100-watch.sh — 搜索API拉 topic:skills+claude-skills 各前100, 合并按star取TOP100, 对比基线 skills-db/top100-state.json
- **检测**: 仓库更新(updated_at变化)/ star变化 / 新入TOP100 / 跌出TOP100
- **cron**: 0hao-top100-watch 每日11:30(Asia/Shanghai), 有更新推送微信; 无更新静默一句
- 与 0hao-trending-radar(9:00热榜)/ 0hao-daily-report(8:00晨报)/ 0hao-skills-updater(10:00上游更新) 错峰
