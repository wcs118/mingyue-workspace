# 🏢 OPC-Skills

> **OPC = One-Person Company（一人公司）**
> 一个人 + AI = 一支 300 人的团队。

这是一套给「AI 一人公司」的 Claude Code 技能合集。你一个人当老板，这里的每个技能就是你手下某个**部门**的 AI 员工——让 AI 替你干完战略、法务、内容、文档这些本来需要一整个团队才能撑起来的活。

> 适用人群：独立开发者、自由职业者、个人创业者、小团队负责人——任何想用 AI Agent 把自己放大十倍百倍的人。

---

## 🧭 虚拟团队编制

| 部门 | 职能（= 真实公司里的谁） | 本仓库技能 |
|---|---|---|
| 🧭 **战略决策室** | 评估需求/项目、判断接不接、报价合不合理 | `req-eval` |
| ⚖️ **法务合规部** | 合同审查/生成/风险/谈判/NDA/隐私条款 | `legal` 全家桶（14 个） |
| 📢 **市场内容部** | 小红书图文、HTML 演示文稿 | `xiaohongshu`、`html-ppt` |
| 📄 **文档行政部** | 正式 Word 文档（封面/目录/正文/页脚） | `word-doc` |

> 🚧 **路线图**（后续加入）：技术工程部（多模型接入/部署）、数据分析部（量化/BI）、创意设计部（图表/视频）、协作指挥部（多 Agent 编排），以及市场内容部的公众号三件套。

---

## 📦 包含的技能（18 个）

### 🧭 战略决策室
- **`req-eval`** — 需求评估器。按项目类型（外包/合作/自研/小工具）用不同镜头评估"能不能做、值不值得做、报价合不合理"。

### ⚖️ 法务合规部
- **`legal`** — 法务主调度器（入口）
- **`legal-review`** — 全面合同审查（旗舰）
- **`legal-risks`** — 逐条风险分析 + 财务敞口 + 整改建议
- **`legal-missing`** — 找出合同里缺失的关键条款
- **`legal-agreement`** — 商务协议生成
- **`legal-nda`** — 保密协议（NDA）生成
- **`legal-terms`** — 网站/SaaS 服务条款生成
- **`legal-privacy`** — 隐私政策生成
- **`legal-compliance`** — 合规差距分析
- **`legal-compare`** — 两版合同/两份合同对比
- **`legal-negotiate`** — 逐条反提案 + 谈判话术 + 邮件模板
- **`legal-plain`** — 把法律条文翻译成人话
- **`legal-freelancer`** — 自由职业者合同审查
- **`legal-report-pdf`** — 专业 PDF 报告生成

### 📢 市场内容部
- **`xiaohongshu`** — 任意内容转小红书风格图文
- **`html-ppt`** — 静态 HTML 演示文稿（多风格/布局/动画，模板驱动）

### 📄 文档行政部
- **`word-doc`** — 规范 Word .docx 生成（封面 + 目录 + 正文 + 页脚）

---

## 🚀 安装

### 方式一：一键脚本（推荐）

```bash
git clone https://github.com/Frog1205/OPC-Skills.git
cd OPC-Skills
./install.sh        # macOS / Linux / Git Bash
```

Windows PowerShell：
```powershell
git clone https://github.com/Frog1205/OPC-Skills.git
cd OPC-Skills
.\install.ps1
```

脚本会把 `skills/` 下所有技能复制到 `~/.claude/skills/`（同名技能会被覆盖）。安装后**重启 Claude Code** 生效。

### 方式二：手动

把 `skills/` 里你想要的子目录，复制到你 Agent 的技能目录（Claude Code 默认是 `~/.claude/skills/`）。

---

## 🎯 怎么用

安装后在 Claude Code（或任何兼容 Agent）里直接说人话即可触发，例如：

- "评估一下这个外包需求，报价合不合理" → 自动起 `req-eval`
- "审查这份合同的风险" → `legal-review` / `legal-risks`
- "把这篇内容做成小红书图文" → `xiaohongshu`
- "生成一份正式的项目方案 Word" → `word-doc`
- "做一份 HTML 演示文稿" → `html-ppt`

> 兼容所有能读 `~/.claude/skills/` 的 AI Agent（Claude Code、Codex、Cursor、Windsurf、Continue、Aider 等）。

---

## 📜 许可与致谢

- 本仓库的打包结构、README、安装脚本采用 **MIT** 许可。
- 各技能目录内保留各自的原作者与许可声明；部分技能整理自社区，欢迎在 Issue 里补充出处与署名。
- 如果你是一名「AI 一人公司」实践者，欢迎 PR 补充你自己的部门技能。

---

**一个人当老板，AI 当全公司。** 🤖👔
