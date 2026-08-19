# Kimi K3 情报(2026-08-11 开源吸收)

## 模型核心
- **MoonshotAI/Kimi-K3**(GitHub ⭐8349,2026-08-11 更新):2.8T 参数 MoE 开源模型,全球首个开源 3T 级模型
- 激活参数 104B / 896 专家激活 16 / 93 层 / 1M token 上下文
- 架构:Kimi Delta Attention (KDA) + Attention Residuals (AttnRes) + Stable LatentMoE
- 原生多模态(文本+图像,MoonViT-V2 视觉编码器 401M),MXFP4 量化
- 能力:长程编码(GPU kernel/编译器/CAD/芯片设计)、深度研究、多模态 agentic 工作

## 配套工具(已吸收)
- **kimi-code CLI v0.34.0**(MoonshotAI/kimi-code,⭐6353,MIT):终端 AI 编码 agent
  - 单二进制安装:~/.kimi-code/bin/kimi(官方脚本已装)
  - 特性:视频输入、MCP 配置、子代理(coder/explore/plan)、ACP 协议、生命周期钩子
  - **已配置 DeepSeek provider**(deepseek-v4-flash 默认),实测跑通 ✅
  - kimi-cli(旧版,Python,⭐11160)正被 kimi-code 取代,无需装
- Kimi K3 官方 API:platform.kimi.ai(OpenAI/Anthropic 兼容,模型名 kimi-k3),本地部署需 vLLM/SGLang/TokenSpeed(2.8T 模型远超本机资源)

## 部署要求(本机不可行)
- 2.8T 参数需多卡 H20/H100 级 GPU;本机 2C4G 只能走 API 或借道 kimi-code 连第三方 provider

## 吸收结论
- kimi-code CLI = 已安装吸收 ✅(DeepSeek 驱动,零额外成本)
- Kimi K3 模型本身 = 记入情报,待有 API key 或高端 GPU 时启用

## 2026-08-12 更新:官方 API key 已接入 ✅
- 老板提供 Kimi 官方 key,已配置进 kimi-code(config.toml)
- 正确端点:**https://api.moonshot.cn/v1**(必须带 /v1,否则 404;api.moonshot.ai 会 Invalid Authentication)
- 可用模型: kimi-k2.7-code(编码旗舰,262k ctx) / kimi-k2.6(262k ctx)
- 实测:两个模型 kimi-code -p 均跑通 ✅
- 用法: kimi -m kimi/kimi-k2.7-code / kimi -m kimi/kimi-k2.6
- 注:API 上暂无 kimi-k3 模型名,实际为 k2.7-code/k2.6
