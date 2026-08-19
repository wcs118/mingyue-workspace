# 🧮 明月调度矩阵(技能×体系×组合包)

> 在《2143 技能归类》14 能力域之上,建调度矩阵:每个 agent 分类、组合、融会贯通,任务来了直接查矩阵调用。
> 数据:170 技能 + 9 大体系 + 8 场景组合包 · 2026-08-16

## 一、矩阵结构(三层)

```
任务进来
   │
   ▼
【第一层:能力域路由】skill-matrix.py lookup --task "..."  → 命中 14 能力域
   │
   ▼
【第二层:技能矩阵】170 技能按域+体系索引 → 推荐技能清单
   │
   ▼
【第三层:场景组合包】skill-matrix.py pack --task "..." → 直接调完整调用链
```

## 二、矩阵统计

**总技能:170**

| 能力域 | 数量 | 能力域 | 数量 |
|---|---|---|---|
| 💻 软件开发/编码 | 36 | 🎨 设计/UI/UX | 17 |
| 🤖 AI/Agent | 24 | 🔒 安全/攻防 | 5 |
| 📑 内容/写作/媒体 | 34 | 📊 数据/分析/BI | 2 |
| 👤 运营/管理/客服 | 21 | 🧪 测试/质量 | 2 |
| 📝 营销/电商/SEO | 16 | ⚙️ 基础设施工具 | 8 |
| 💰 金融/量化 | 1 | 🌍 本地化 | 1 |
| 👓 可穿戴 | 0 | 📦 参考/冷门 | 3 |

**按体系:**
- claude-skills 136 | codex-superpowers 13 | arbor 11 | gm 7
- deepseek-harness 1 | kimi 1 | minimax-h3 1

## 三、8 大场景组合包(融会贯通层)

| 组合包 | 调用链 | 引擎 |
|---|---|---|
| 📦 公众号长文 | 选题→写作→润色→配图→排版→发布 | OpenClaw + dsh |
| 📦 短剧制作 | 立项→剧本→分镜→素材→成片→复盘 | MiniMax H3 + 剪映 |
| 📦 客服自动化 | 路由→回复→工单→复盘 | OpenClaw + 微信 |
| 📦 产品开发 | 规划→设计→实施→测试→审查→交付 | OpenClaw + 大掌柜 + dsh |
| 📦 营销推广 | 调研→策略→落地→商务 | OpenClaw |
| 📦 AI 研究 | 启动→想法→执行→验证→报告 | Arbor + dsh |
| 📦 PPT 制作 | 构思→制作→设计→美化 | OpenClaw |
| 📦 数据分析 | 取数→分析→验证→汇报 | OpenClaw |

## 四、调用方式

```bash
# 查技能:任务→能力域→技能
python3 scripts/skill-matrix.py lookup --task "写公众号文章"

# 查组合包:直接拿完整调用链
python3 scripts/skill-matrix.py pack --task "公众号"

# 查某能力域全部技能
python3 scripts/skill-matrix.py domain 内容/写作

# 查某体系全部技能
python3 scripts/skill-matrix.py agent arbor

# 统计
python3 scripts/skill-matrix.py stats
```

## 五、与工作流的衔接

矩阵已和 workflow-run.sh 打通:任务进来 → skill-matrix 定域 → scope-router 定级 → session-rollback 事务 → guard-exec 守卫执行 → 交付。

## 六、后续扩展

- 组合包可按需增加(如"电商铺货""GEO 优化")
- 技能更新时刷新矩阵 JSON
- 可接入 OpenClaw 自动路由(任务描述→自动调组合包)
