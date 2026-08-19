# Grok Build 情报(2026-08-11 开源吸收)

## 项目核心
- **xai-org/grok-build**(GitHub ⭐24664,2026-08-11 更新):SpaceXAI(xAI)的终端 AI 编码 agent
- 全屏 TUI 交互,理解代码库、改文件、跑 shell、搜网页、管理长任务;支持交互/无头(脚本/CI)/ACP 嵌入编辑器
- Rust 编写(Apache 2.0);安装产物名 `grok`(源码二进制 xai-grok-pager)
- 源码仓库从 SpaceXAI monorepo 周期同步(SOURCE_REV=a51a1dc);外部贡献不接受
- 默认模型 grok-4.5(xAI 托管);认证:浏览器登录 grok.com / XAI_API_KEY(console.x.ai)/ OIDC SSO / 外部 auth provider

## 关键能力(与 kimi-code 类似,终端编码 agent)
- 支持 **自定义模型端点**(OpenAI chat_completions / responses / Anthropic messages 三种 backend)
  - ~/.grok/config.toml 配 [model.<name>]: model/base_url/api_key/env_key/api_backend/context_window 等
  - **可接 DeepSeek 等任意 OpenAI 兼容 provider**(同 kimi-code 思路,零额外成本)
- 技能系统:SKILL.md 目录,发现路径 ~/.grok/skills/ + .claude/skills/ + .cursor/skills/(兼容 Claude/Cursor 技能!)
- MCP servers、插件、hooks、子代理、沙箱、计划模式、后台任务、Dashboard、监控用量
- 无头模式(41KB 文档)、权限安全(29KB)、配置(42KB)文档极全

## 已吸收 ✅
- **完整用户指南 25 篇文档**(~548KB)→ workspace/reference/grok-build-docs/(getting-started/认证/快捷键/命令/配置/主题/MCP/技能/插件/hooks/自定义模型/项目规则/记忆/无头/agent/子代理/会话/沙箱/计划/后台任务/终端/权限/仪表盘/用量监控)
- **二进制已装 ✅(2026-08-11 深夜深挖突破)**
  - 发现 npm 官方包 `@xai-official/grok-linux-x64`(绕过 x.ai 域名封锁),v0.1.220
  - 解压出 grok 二进制 → /usr/local/bin/grok 软链,124.5MB
  - 源码 tarball 也拿到了(13.8MB,SOURCE_REV=a51a1dc)
- 情报沉淀:本文件

## 安装状态 ✅(已突破!)
- 官方路径 x.ai 域名不通(IPv4/IPv6 全超时)→ **npm 包路径绕过成功**
- `npm i -g @xai-official/grok-linux-x64` → 包内含预编译二进制
- **DeepSeek 驱动成功**:~/.grok/config.toml 配 [model.deepseek-v4-flash/pro],api_backend=chat_completions

## ⚠️ 关键坑:thinking 模式 vs tool_choice
- **DeepSeek V4 thinking 模式不支持 tool_choice=required/指定函数**(只支持 auto/none)→ grok 工具调用报 400
- **解法:本地代理注入 `thinking:{"type":"disabled"}`** → 所有 tool_choice 可用
- 代理:`scripts/grok-deepseek-proxy.py`(127.0.0.1:18800 转发 api.deepseek.com + 注入 thinking disabled)
- **systemd 常驻**:grok-deepseek-proxy.service(开机自启,Restart=always)
- 已验证:grok -p 创建 hello.py + 运行成功 ✅(--yolo 自动批准工具)

## 使用备忘
- 对话:grok -p "..."(无头单次)
- 工具调用:grok -p "..." --yolo(自动批准)
- 交互 TUI:grok(全屏界面)
- 配置:~/.grok/config.toml;技能:SKILL.md 兼容 Claude/Cursor

## 吸收结论
- 文档知识 = 已吸收 ✅(25 篇指南)
- 二进制 = 已安装 ✅(npm 包绕过 x.ai)
- DeepSeek 驱动 = 已跑通 ✅(代理注入 thinking disabled)
- 编码 agent 工具箱再添一员:kimi-code(DeepSeek 直连) + grok(代理驱动)双持
- 与 kimi-code 定位重叠(都是终端编码 agent),grok 强在全屏 TUI + 生态(ACP/MCP/插件)
