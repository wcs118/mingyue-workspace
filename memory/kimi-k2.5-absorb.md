# Kimi K2.5 吸收记录(2026-08-14,真吸收 ✅)

## 是什么
- **MoonshotAI/Kimi-K2.5**(GitHub ⭐2.3K, Modified MIT):"Open Visual Agentic Intelligence"
- 开源原生多模态 agentic 模型:1T MoE / **32B 激活**,256K 上下文,384 专家
- 视觉编码器 MoonViT(400M),原生图像+视频输入
- 三大能力:原生多模态 / Coding with Vision(UI图→代码)/ **Agent Swarm**(单agent→自协调swarm并行)
- 双模式:Thinking(带 reasoning_content)/ Instant(thinking disabled)
- 评测:SWE-Bench Verified 76.8 / AIME 96.1 / MMMU-Pro 78.5 / VideoMMMU 86.6 / OCRBench 92.3
- 权重+代码 Modified MIT,可商用

## 真吸收做了什么(区别于"记情报")
1. **OpenClaw moonshot provider 接入**:插件 @openclaw/moonshot-provider 已装并 enabled
   - openclaw.json 新增 env.MOONSHOT_API_KEY + models.providers.moonshot(国内端点)
   - 模型引用:`moonshot/kimi-k2.6`(text+image 262k)、`moonshot/kimi-k2.7-code`
   - ⚠️ 坑:API 模型名 `kimi-k2.5` 返回 404,实际用 **`kimi-k2.6`**(同系列多模态,支持图像/视频/推理)
2. **kimi-vision.sh 视觉调用脚本**:scripts/kimi-vision.sh 一键图像/视频理解,实测通过
   - 实测:识别 MiniMax 密钥管理页截图 ✅ 带 228 tokens 推理过程
3. **技能文件**:skills/kimi-k2.5/SKILL.md(调用手册+参数+场景)
4. **上游追踪**:skills-db/upstream.json +1(共35仓库),skills-updater 每日自动跟新

## 现有通道
- OpenClaw 会话内:`/model moonshot/kimi-k2.6` 切换(主通道)
- kimi-code CLI:`kimi -m kimi/kimi-k2.6`(编码通道,v0.34.0)
- 直接 API:scripts/kimi-vision.sh(脚本通道)

## 教训
- API 模型名与开源版本名不一致(k2.5 开源 → API 上是 k2.6/k2.7-code),新模型先 curl /v1/models 验证
- openclaw agent --local 会因 context-mode 插件缺构建产物报错,属既有环境问题,不影响网关
