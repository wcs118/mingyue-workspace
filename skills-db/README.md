# 技能库数据库（skills-db）

## 数据
- skills-top1000.json — GitHub 前 1000 高星 skills 仓库（topic:skills + topic:claude-skills，按 ⭐ 排序）
- skills-database.json — 早期精筛版（6 核心仓库 / 28 topSkills），保留作参考

## 脚本
- scripts/fetch-top1000-skills.sh — 重拉前 1000 高星 skills 仓库
- scripts/skill-absorb.sh <repo> <skill-path> [target-name] — 从 GitHub 吸收单个技能到 skills/

## 社区候选池工作流（O5）
1. 任务匹配不上现有技能 → 查 skills-top1000.json + awesome-openclaw-skills（5300+ 社区技能）
2. 找到候选 → scripts/skill-absorb.sh 吸收（外吸收）
3. 找不到但本工作区重复模式 ≥3 次 → 技能生长（内生长，见 framework-ops）
4. 吸收后更新分类统计

## 技能清单
### 内容/写作
- human-writing(热榜吸收)
- dragon-ppt-maker(热榜吸收)
- image-video-framework(自建, 2026-08-13: 图像七要素+视频双维度方法论, 用于AI图像/视频提示词)
### 框架
- framework-ops(自建)
### 编码(2026-08-11 Codex 能力吸收, obra/superpowers)
- systematic-debugging / test-driven-development / verification-before-completion
- writing-plans / executing-plans / subagent-driven-development / dispatching-parallel-agents
- requesting-code-review / receiving-code-review / brainstorming
- using-git-worktrees / finishing-a-development-branch
### 多模态视觉(2026-08-14 Kimi K2.5 真吸收)
- kimi-k2.5(开源多模态 agentic 模型, MoonshotAI/Kimi-K2.5 Modified MIT)
  - OpenClaw moonshot provider 已接入(国内端点 api.moonshot.cn/v1, 实际模型名 kimi-k2.6)
  - scripts/kimi-vision.sh 视觉理解一键调用(图像/视频), 实测通过
  - kimi-code CLI 编码通道(v0.34.0)
### 终端编码 Agent(2026-08-11 吸收, 2026-08-16 新增 dsh)
- kimi-code(CLI, DeepSeek 直连驱动)
- grok-build(CLI, DeepSeek 代理驱动:npm 包 @xai-official/grok-linux-x64 + 本地代理注入 thinking disabled)
- **deepseek-harness / dsh**(2026-08-16 真吸收, deepseek-ai/deepseek-harness ⭐11.6万 MIT)
  - DeepSeek 官方插件化 agent harness(Everything is a Plugin, 基于 Cordis), 无头编码 agent
  - 已装 /opt/dsh, 封装脚本 scripts/dsh-run.sh, 复用 DeepSeek key 零成本
  - 实测: 文件创建/bash 读取/子代理工具链全通; ⚠️ 开发者预览版, 有破坏性变更
### 视频生成(2026-08-11 MiniMax H3 官方技能吸收, skills/minimax-h3/)
- h3-prompt-writing(H3 五模式提示词) / 3d-animation-short-generator(3D动画短片)
- papercraft-stop-motion-explainer(纸艺定格动画) / paper-collage-explainer-generator(拼贴讲解)
- minimalist-product-ad-generator(极简产品广告) / brand-promo-video-generator(品牌短片)
- music-video-subtitle-generator(MV歌词字幕) / co-op-game-intro-generator(双人游戏开场)
- handdrawn-live-video-generator(手绘+实拍短片)

## 三技能升级(2026-08-11 22:35,老板16:48指令落地)
替换 OpenClaw 内置,全部来自 GitHub 大神作品:
- **上下文** → context-mode(mksglu,⭐19.8K)— 网关原生插件,ctx_execute 沙箱执行/FTS5知识库/BM25检索,上下文省98%
- **长效记忆** → MemOS(MemTensor,⭐10.7K)— memory 槽位插件,全写SQLite+混合检索+任务摘要+技能进化+团队共享
- **自我进化** → pro-workflow 三技能(rohitg00,⭐2.8K)— learn-rule(纠错成规则)/replay-learnings(开工前回放教训)/insights(学习统计)

### claude-skills 员工技能库(2026-08-12 热榜吸收, ⭐24.3K)
- 来源: alirezarezvani/claude-skills(MIT)— 345+ 技能/30+ agents/70+ commands,支持 11 种编码 agent
- 全量 362 个 SKILL.md → skills-db/claude-skills/(含 INDEX.md 索引)
- 核心 35 个已激活 → skills/(工程/研究/产品/商业/财务/运营/增长/效率/管理)
- 按需激活: bash scripts/skill-absorb.sh 或从 skills-db/claude-skills/INDEX.md 选技能复制

### trending-agents 热榜 Agent 技能库(2026-08-12 吸收)
- 来源: GitHub 热榜 agent 主题前 30 名精选 — 10 个技能仓库 180 个 SKILL.md 全量入库
- 核心 16 个已激活 → skills/: agents-best-practices / adhd / fable-loop|judge|domain / loop-triage|budget|verifier|minimal-fix / ponytail-review|audit / open-agent-teams / agent-context-audit / webvuln / recon / shushu-internship
- 大体积框架(omnigent/KiroCrew/lazycodex/Raven 等)记录为情报, 待评估安装

### skills-wave2 高星技能库第2波(2026-08-12 吸收)
- 来源: GitHub 高星 skills 搜索 — 11 个仓库 1,197 个 SKILL.md 全量入库
- 核心 46 个已激活 → skills/: addyosmani工程11 / PM技能16 / 宝玉内容创作11 / planning-with-files / humanizer / taste-skill / obsidian / i-have-adhd
- 特色: baoyu-* 系列(微信/小红书/翻译/PPT/配图, 中文内容创作利器) + PM 全套(PRD/OKR/用户故事/AB测试)
- 大合集(ComposioHQ 864 / wshobson 180)留索引库按需激活

### arbor 自主研究 Agent 技能套件(2026-08-13 热榜吸收并真实验证, ⭐1K)
- 来源: RUC-NLPIR/Arbor(Apache-2.0, 人大NLPIR, 论文 arXiv:2606.11926)— 假设树自主研究工作流, 声称比 Claude Code/Codex 快 2.5×
- **11 技能全量激活** → skills/arbor-*: research-agent(入口) / orchestrator(编排) / setup-intake(目标澄清) / ideate(假设生成) / executor(执行) / coordinator(协调) / merge-eval(合并评估) / search(相关检索) / tools(支撑脚本) / resume-report(恢复报告) / plugins-hitl-budget(人工介入+预算)
- **已真实验证**: arbor_state.py(1215行, stdlib-only)语法OK+15子命令可用; 本地入口 scripts/arbor-run.sh 冒烟全链路闭环通过✅(init→meta→add→record→report→check)
- 用法: bash scripts/arbor-run.sh smoke <项目目录> <run名> "<目标>"
- 亮点: keyless 可配自有模型(DeepSeek), 会话树存 .arbor/sessions/, 上游追踪已加入(共30仓库)

### video-skills 直播带货/短视频/短剧技能库(2026-08-12 吸收)
- 来源: GitHub 热榜视频类搜索 — 7 个仓库 18 个 SKILL.md 全部入库+激活
- 短剧: short-drama(10技能全链路) / micro-drama-script(50-100集剧本) / ai-short-drama(三阶段IP流水线) / novel-characters|outline|art(小说改编)
- 短视频: jianying-editor(剪映自动化剪辑) / video-shotcraft(Remotion电影级产品视频) / narrator-ai-cli(AI解说)
- 框架情报: MoneyPrinterTurbo(⭐102K一键短视频) / Toonflow(短剧创作) / Jellyfish(短剧工作台) 等 — 待评估安装

### TOP2000 批量吸收(2026-08-13 老板指令"真正吸收")
- 数据: skills-db/skills-top2000.json — topic:skills+topic:claude-skills 合并去重 1462 条(脚本 fetch-top1000-skills.sh 已升级 20 页)
- **归藏 PPT**(op7418/guizang-ppt-skill, ⭐23.8K)— guizang-ppt-skill: 单文件 HTML 横向翻页网页PPT(WebGL背景/演讲者视图/观众屏同步), 杂志风+瑞士国际主义两种风格 ✅激活
- **卡兹克技能**(KKKKhazix/khazix-skills, ⭐19.6K)— 6 技能全量 ✅激活: leader(想法拆解成目标任务书) / aihot(AI资讯热点日报) / hv-analysis / khazix-writer / neat-freak(整理癖) / storage-analyzer(磁盘清理, mac/win)
- **Anthropic 官方插件技能**(⭐33.5K)— 精选 9 个 ✅激活: frontend-design / math-olympiad / project-artifact / session-report / skill-development / receipts(发票处理) / claude-security / build-mcp-server / writing-rules
- **Google 官方技能**(⭐17.9K)— 109 个入库待激活(ads/analytics/cloud 三类, 谷歌产品向)
- 未吸收记情报: agents/commands 格式插件(code-review/feature-dev 等, 非 SKILL.md 体系)

### AAS 巨型技能注册中心(2026-08-16 老板指定吸收, ⭐45K)
- 来源: sickn33/agentic-awesome-skills(V15.13.0, MIT)— 2009 技能/101 分类/6341 SKILL.md, 覆盖开发/AI/云/安全/营销/设计/研究全领域
- **全量落地 1861 新技能** → skills/(1917 目录, 51 与已有重叠跳过), 技能库 215→2081
- 索引三件套 → skills-db/aas/: CATALOG.md(官方分类目录) + skills_index.json(2009 结构化索引) + aas-mapped.json(14 域映射)
- **矩阵并入**: load_matrix() 自动合并 AAS, 矩阵 212→2170 技能; lookup/stats/domain/agent 全覆盖
- 上游追踪已加(upstream.json +1, 每日 10:00 自动检查更新)
