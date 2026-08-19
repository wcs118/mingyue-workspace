# TOOLS.md - 本地环境备忘

## 技能清单(2026-08-11 盘点)

### 本机可用(核心)
- **human-writing**(2026-08-11 热榜吸收) — 中文活人感写作:知乎/公众号/长文/故事,含禁词检查脚本
- **dragon-ppt-maker**(2026-08-11 安装) — python-pptx 生成科技风可编辑 PPT,多布局/图文混排/HTML 嵌入
- **clawhub** — 技能市场:搜索/安装/更新技能
- **healthcheck** — 主机安全审计(SSH/防火墙/更新/备份)
- **tmux** — 控制 tmux 会话/窗格,交互式 CLI
- **weather** — 天气查询(wttr.in 兜底)
- **diagram-maker** — SVG/HTML/Excalidraw 图表
- **meme-maker** — 表情包制作
- **skill-creator** — 创建/审计/整理技能
- **spike** — 快速原型验证可行性
- **taskflow** — 多步任务编排(持久化 Job)
- **taskflow-inbox-triage** — 收件箱分类示例模式
- **node-inspect-debugger** — Node.js 调试(CDP/heap/CPU)
- **python-debugpy** — Python 调试(pdb/debugpy)
- **node-connect** — 诊断节点配对/连接问题

### 依赖 macOS/特殊硬件(本机不可用)
- apple-notes / apple-reminders / bear-notes / things-mac(Apple 生态)
- spotify-player / sonoscli(音乐硬件)
- openhue(飞利浦灯)

### 待评估(可能有用)
- github / gh-issues — GitHub 操作(阶段五"刷热榜"可能用到)
- blogwatcher / gog / goplaces / xurl / gifgrep / oracle / ordercli
- coding-agent — 编码智能体
- summarize / session-logs / model-usage — 会话与用量
- openai-whisper / sherpa-onnx-tts / sag — 语音
- notion / obsidian / trello — 笔记/任务类

## 环境备忘
- 服务器:阿里云 Ubuntu 24.04,用户 admin,有 sudo;2核/4G内存/ESSD 50G(升级后)
- OpenClaw 2026.7.1-2,网关 18789(系统级 systemd,开机自启)
- OCR:tesseract 5.3.4 + chi_sim/eng 已装
- 图片输入路径: workspace/media/inbound/...
- 模型:deepseek-v4-flash(默认)/ deepseek-v4-pro(fallback)

## 2026-08-14 大扫除后
- 📍 找东西先看 WORKSPACE-MAP.md(工作区地图,顶层结构/技能速查/脚本速查/整理纪律)
- 变化: research/ docs/ 已并入 reference/; media 测试产物归档 output/; mcp-server-builder 归档 skills-db/archive/(保留官方 build-mcp-server); 技能库 skills/ 167个 + 4个集合目录
