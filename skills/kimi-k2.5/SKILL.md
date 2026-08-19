---
name: kimi-k2.5
description: Kimi K2.5 开源多模态 agentic 模型调用(视觉理解/视频理解/Agent Swarm),已接入 OpenClaw moonshot provider 与 kimi-code CLI
version: 1.0.0
source: https://github.com/MoonshotAI/Kimi-K2.5
license: Modified MIT
tags: [kimi, moonshot, vision, multimodal, agentic, open-source]
---

# Kimi K2.5 — 开源多模态 Agentic 模型

## 模型情报(2026-08-14 吸收)

- **MoonshotAI/Kimi-K2.5**(⭐2.3K, Modified MIT):"Open Visual Agentic Intelligence"
- 架构:MoE 1T 总参 / **32B 激活**,61 层,384 专家(每 token 8),MLA 注意力,SwiGLU
- 上下文:**256K**,词汇 160K,视觉编码器 MoonViT(400M)
- 训练:Kimi-K2-Base 上 ~15T 混合视觉+文本 token 持续预训练
- **原生多模态**:图像+视频输入,视觉知识/跨模态推理/基于视觉的 agentic 工具使用
- **Coding with Vision**:从 UI 设计图/视频工作流等视觉规格生成代码
- **Agent Swarm**:单 agent → 自协调 swarm,分解并行子任务由动态实例化领域 agent 执行
- 双模式:**Thinking**(reasoning_content)/ **Instant**(thinking disabled)
- 部署:官方 API(OpenAI/Anthropic 兼容)或本地 vLLM/SGLang/KTransformers(需 4.57.1+)

## 本机接入状态(真吸收 ✅)

### 1. OpenClaw moonshot provider(主通道)
- 插件 `@openclaw/moonshot-provider` 已装并 enabled
- 配置:env.MOONSHOT_API_KEY + models.providers.moonshot(国内端点 https://api.moonshot.cn/v1)
- 可用模型引用:`moonshot/kimi-k2.6`(text+image, 262k)、`moonshot/kimi-k2.7-code`、目录含 `moonshot/kimi-k2.5`
- ⚠️ **关键坑**:国内端点 API 上模型名 `kimi-k2.5` 返回 404(Not found),实际可用名为 **`kimi-k2.6`**(同系列多模态,支持图像/视频/推理)。OpenClaw 目录里 moonshot/kimi-k2.5 是占位,调用会失败,用 kimi-k2.6。
- 实测(2026-08-14):图像理解 ✅ 文本+推理 ✅(MiniMax 密钥管理页截图识别准确)

### 2. kimi-code CLI(编码通道)
- v0.34.0 已装(~/.kimi-code/bin/kimi),config.toml 已配 kimi provider(api.moonshot.cn/v1)
- 用法:`kimi -m kimi/kimi-k2.6 "任务"` 或 `kimi -m kimi/kimi-k2.7-code`

### 3. 直接 API(脚本通道)
- 端点:https://api.moonshot.cn/v1(带 /v1)
- 模型:kimi-k2.6 / kimi-k2.7-code(支持 image_url + video_url 输入)
- Thinking 模式:默认开启(返回 reasoning_content);Instant:`extra_body={'thinking': {'type': 'disabled'}}`
- 推荐参数:Thinking 温度 1.0,Instant 温度 0.6,top_p 0.95

## 调用示例

### OpenClaw 内切换模型(会话级)
```
/session model moonshot/kimi-k2.6   # 或 /model moonshot/kimi-k2.6
```

### 视觉理解(直接 API)
```bash
bash scripts/kimi-vision.sh <图片路径> "<问题>"
# 或 python3 直连(参考 scripts/kimi-vision.py,base64 编码 image_url)
```

### 视频理解(官方 API 实验特性)
content 中传 `{"type": "video_url", "video_url": {"url": "data:video/mp4;base64,..."}}`

### kimi-code 编码
```bash
~/.kimi-code/bin/kimi -m kimi/kimi-k2.6 "分析这个仓库的结构"
```

## 适用场景
- 截图/UI 设计图理解与代码生成(Coding with Vision)
- 图片 OCR/内容提取(OmniDocBench 88.8, OCRBench 92.3)
- 视频内容理解(VideoMMMU 86.6, VideoMME 87.4)
- 深度推理+工具调用(SWE-Bench Verified 76.8, AIME 96.1)
- Agent Swarm 并行子任务(需要多 agent 编排场景)

## 上游追踪
- GitHub: MoonshotAI/Kimi-K2.5(master 分支,已入 upstream.json)
- 注意 API 模型名可能随版本变化,新模型出现时先 `curl /v1/models` 验证
