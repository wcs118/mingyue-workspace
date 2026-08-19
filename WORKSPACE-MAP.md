# 🗺️ 工作区地图(2026-08-14 大扫除后)

> 家里布局一览。找东西先看这里，别乱翻。

## 顶层结构

| 目录/文件 | 是什么 | 怎么用 |
|---|---|---|
| `AGENTS.md` `SOUL.md` `IDENTITY.md` `USER.md` | 身份与行为契约 | 常驻，勿动 |
| `FRAMEWORK.md` + `rules/` | 三体系行为框架(R1-R8 规则) | 任务开始先读 path-routing |
| `MEMORY.md` | 长期记忆(精华) | 主会话维护 |
| `memory/` | 每日笔记 + 情报 + 事件账本 | `memory/YYYY-MM-DD.md` 当日记录, `events.log` 操作流水 |
| `skills/` | **激活技能库**(167个, 含子技能集合) | 干活时按需读 SKILL.md |
| `skills-db/` | 技能数据库: 上游仓库克隆 + 索引 + archive | `upstream.json` 追踪清单; `archive/` 归档废弃技能 |
| `scripts/` | 可执行脚本(15个) | 运维/吸收/视频/视觉, 直接 bash 调用 |
| `output/` | 产出物(视频/文档按项目分目录) | minimax/ zhipu/ baoyu-test/ |
| `media/` | 媒体文件 | `archive/` 历史暂存; 新收文件在 inbound 由系统管理 |
| `reference/` | 参考资料(grok 文档/阿里云升级指南) | 只读 |
| `config/` | 密钥与配置 | ⚠️ 权限敏感(minimax.env), 勿外传 |
| `.snapshots/` | 不死鸟快照(sha256) | phoenix-snapshot.sh 自动管理 |
| `.git/` | 版本历史 | 提交信息要写清改动 |

## skills/ 分类速查(常用)

- **框架/规则**: framework-ops
- **写作**: human-writing(中文活人感) / humanizer(英文润色)
- **PPT/内容**: dragon-ppt-maker / guizang-ppt-skill / baoyu-* 系列 / html-ppt
- **视频**: minimax-h3(9个官方技能) / video-shotcraft / jianying-editor / short-drama 系列 / zhipu-video
- **视觉/多模态**: kimi-k2.5(视觉理解) / image-video-framework
- **编码**: superpowers 12件套(systematic-debugging/TDD/plans等) / karpathy-coder / senior-* 系列
- **研究**: deep-research / arbor-*(自主研究套件) / litreview / recon
- **商业/产品**: product-strategist / pricing-strategist / saas-metrics-coach / deal-desk / competitive-intel
- **法律/合规**: opc-skills/legal-* 系列(NDA/风险/合同)
- **运营/效率**: adhd(发散创意) / i-have-adhd(输出适配) / inbox-triage / meeting-analyzer
- **子技能集合目录**: claude-inc/ minimax-h3/ opc-skills/ pro-workflow-learn/(内含多个 SKILL.md, 不算僵尸)

## 脚本速查

| 脚本 | 干什么 |
|---|---|
| `phoenix-snapshot.sh` | 不死鸟快照/回滚(status/snapshot/restore) |
| `evolution-cycle.sh` | 梦境循环(经验→规则) |
| `daily-report.sh` | 每日晨报(8:00 cron) |
| `trending-watch.sh` | GitHub 热榜(9:00 cron) |
| `top100-watch.sh` | TOP100 仓库跟踪(11:30 cron) |
| `skills-updater.sh` | 上游技能更新(10:00 cron) |
| `skill-absorb.sh` | 从 GitHub 吸收技能 |
| `security-check.sh` | 下载安检(隔离/回滚) |
| `kimi-vision.sh` | Kimi 多模态视觉理解(图像/视频) |
| `minimax-h3.sh` | MiniMax H3 文生视频 |
| `zhipu-video.sh` | 智谱视频生成 |
| `arbor-run.sh` | Arbor 自主研究冒烟 |
| `vault-sync.sh` | Obsidian 双轨同步(无 Obsidian 跳过) |
| `grok-deepseek-proxy.py` | Grok 编码 agent 代理 |

## 整理原则(大扫除纪律)

1. **技能吸收后** → `skills/` 激活, `skills-db/upstream.json` 登记, 不需要的源克隆放 archive
2. **产出物** → 一律进 `output/<项目>/`, 不散落 media
3. **临时文件** → 用完即清, 不留 .tmp
4. **记忆** → 当日写 `memory/YYYY-MM-DD.md`, 精华折进 `MEMORY.md`
5. **删东西前** → 先 `phoenix-snapshot.sh snapshot`, 快照可回滚
