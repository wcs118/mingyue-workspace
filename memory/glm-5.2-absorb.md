# GLM-5.2 智谱真吸收(2026-08-17)

## 情报总览
- **GLM-5.2**(智谱 AI / Z.ai):2026-06-17 发布,旗舰基座模型
- **开源**:MIT License,753B 参数 MoE(单次激活 ~40B),体积约 1.51TB
- **上下文**:1M(真正可用,项目级工程上下文),最大输出 128K
- **定位**:长程任务时代旗舰,Coding 开源 SOTA,"从需求到多端可部署产物"一次完成
- **能力**:思考模式(reasoning_effort: high/max)、流式、Function Call、MCP、结构化输出、上下文缓存
- **开源仓库**:github.com/zai-org/GLM-5 | huggingface.co/zai-org/GLM-5.2 | modelscope.cn/models/ZhipuAI/GLM-5.2
- **推理框架**:vLLM / SGLang / Transformers / KTransformers / llama.cpp;官方 4-bit/8-bit 量化
- **部署硬件**:最小单节点 8×H100 或 4×MI300 → **本机(2核4G)无法本地部署,走 API 自建 provider**

## API 接入(OpenAI 兼容)
- **Base URL**: `https://open.bigmodel.cn/api/paas/v4/`
- **模型 ID**: `glm-5.2` / `glm-5.1` / `glm-5` / `glm-4.7` / `glm-4.7-flash`(免费)/ `glm-5v-turbo`(多模态)
- **Key**: 智谱开放平台 bigmodel.cn → API Keys 创建;环境变量建议 `ZAI_API_KEY`
- **验证**: 无 key 访问 /models 返回 401 code 1001(端点可达✅)

## OpenClaw 自建 provider(已落地)
- `openclaw.json` models.providers.zhipu 已写入 6 模型(glm-5.2 旗舰 / 5.1 / 5 / 4.7 / 4.7-flash 免费 / 5v-turbo 视觉)
- env.ZHIPU_API_KEY 占位,key 到手后填 `config/zhipu.env`(600 权限)
- 一键调用: `bash scripts/glm-run.sh "prompt" [model] [thinking]`
- 会话内切换: `/model zhipu/glm-5.2`

## 思考模式调用
```python
client = OpenAI(api_key=..., base_url="https://open.bigmodel.cn/api/paas/v4/")
resp = client.chat.completions.create(
    model="glm-5.2",
    messages=[...],
    stream=True,
    extra_body={"thinking": {"type": "enabled"}}
)
# 推理内容在 delta.reasoning_content,正文在 delta.content
```

## 上游追踪
- upstream.json 加入: `zai-org/GLM-5`(GitHub,追踪更新)

## 待办
- [ ] 老板发 ZHIPU_API_KEY → 写入 config/zhipu.env → 重启网关 → 实测 glm-5.2 对话 ✅
- [ ] 实测后更新本文件"实测记录"段
- [ ] 可选:GLM Coding Plan(glm-code CLI?)若存在再吸收

## 踩坑记录
- 第一次 web_search 返回"2025 年知识"误导(GL-5.2 被当成未发布),以官方 docs.bigmodel.cn 为准
- 脚本 export 空变量会泄露所有环境变量 → 已修(先判空再 export)
