# 📊 自研/接入模型总台账(2026-08-18 整理)

> 老板指令:昨天自研的模型进行分类、整理、腾出空间、不留尾巴。
> 本表为唯一权威台账,所有模型相关资产在此登记。

## 一、OpenClaw Provider 配置(openclaw.json models.providers)

| Provider | 来源 | 模型数 | 状态 | Key | 一键脚本 | 技能 | 手册 |
|---|---|---|---|---|---|---|---|
| `deepseek` | 官方 | 2 (v4-flash/v4-pro) | ✅ **主模型** | DEEPSEEK_API_KEY ✅ | deepseek-kit.py | deepseek-harness | — |
| `moonshot` | Kimi K2.6/K2.7 | 2 | ✅ 可用 | MOONSHOT_API_KEY ✅ | kimi-kit.py / kimi-vision.sh | kimi-k2.5 | kimi-k2.5-absorb.md |
| `zhipu` | GLM-5.2 等 6 模型 | 6 | ⏸️ **待 key** | ZHIPU_API_KEY 空 | glm-run.sh | glm-5.2 | glm-5.2-absorb.md |
| `qwen` | Qwen3.8-27b 等 5 模型 | 5 | ⏸️ **待 key** | DASHSCOPE_API_KEY 空 | qwen-kit.py | qwen(27个) | 2026-08-17-qwen.md |
| `minimax` | MiniMax H3 视频 | — | ✅ 可用(有 key) | config/minimax.env | minimax-h3.sh | minimax-h3 | minimax-api-handbook.md |
| `grok` | Grok Build(代理) | 1 | ✅ 可用 | DeepSeek 代理 | grok-deepseek-proxy.py | grok-build | grok-build-intel.md |

## 二、脚本清单(workspace/scripts/)

| 脚本 | 用途 | 状态 |
|---|---|---|
| deepseek-kit.py | DeepSeek 官方模型调用 | ✅ 保留(主模型) |
| kimi-kit.py | Kimi K2.6/K2.7 调用 | ✅ 保留 |
| kimi-vision.sh | 图像/视频理解(多模态) | ✅ 保留 |
| minimax-h3.sh | 文生视频(H3) | ✅ 保留 |
| minimax-kit.py | MiniMax 文本/视频 | ✅ 保留 |
| glm-run.sh | GLM-5.2 调用 | ✅ 保留(待 key) |
| qwen-kit.py | Qwen 调用 | ✅ 保留(待 key) |
| grok-deepseek-proxy.py | Grok 代理服务 | ✅ 保留 |
| ~~qwen-kit-lite.py.bak~~ | Qwen 旧版备份 | 🗑️ **已清理** |

## 三、清理记录(打扫战场)

| 项目 | 大小 | 处置 | 日期 |
|---|---|---|---|
| qwen-kit-lite.py.bak | 17KB | 🗑️ 删除(被 qwen-kit.py 取代) | 2026-08-18 |
| openclaw.json.bak-* 旧备份 | 14个 | 📦 归档到 config/backups/ | 2026-08-18 |
| npm cache | 清理 | 🗑️ 清理 | 2026-08-18 |
| /tmp 编译缓存 | 32M | 🗑️ 清理(node-compile-cache/jiti) | 2026-08-18 |
| 会话 checkpoint 旧快照 | 226M | 📦 归档压缩(63M tar.gz) | 2026-08-18 |
| skills-db 原始仓库 ×12 | 693M | 📦 归档压缩(303M tar.gz,已吸收技能不受影响) | 2026-08-18 |

**⚠️ 踩坑教训(必记)**:provider 的 apiKey 不能用 `${ENV_VAR}` 模板引用空变量——OpenClaw 会把缺失 env 当成 required secret,导致网关启动崩溃(重启 197 次)。正确做法:apiKey 留空字符串 `""`(与 qwen 一致),key 到位后再填。

## 四、模型使用决策
- **主模型**: deepseek-v4-flash(日常)/ v4-pro(重活)——默认,不动
- **待激活**: zhipu(等老板发 ZHIPU_API_KEY)、qwen(等 DASHSCOPE_API_KEY)
- **已激活备用**: moonshot(Kimi 多模态)、minimax(视频)、grok(代理)
- 需要哪个模型时,按台账取脚本/技能即可

## 五、MiniMax H3 开源吸收(2026-08-18)
- **开源状态**: 2026-07-31 发布,08-02 开放权重(open-weights,非完全开源);官方仓库 MiniMax-AI/MiniMax-H3
- **能力**: 33.1B 全模态,文生视频/图生视频/参考生视频 + 原生立体声,4-15s/24FPS/768p(2K 需 API)
- **本地部署**: 需 GPU(≥24G 显存 4bit),本机 4核/7G/无GPU **不可部署** → 用壹镜工坊 4090D 或云 GPU
- **新技能**: skills/minimax-h3-local/(部署决策+四种后端+ComfyUI 步骤)
- **新脚本**: scripts/h3-local-deploy.sh(--check/--comfyui/--diffusers)
- **追踪**: upstream.json +2(minimax-h3, minimax-h3-comfyui),总 44
- **授权**: MiniMax H3 Community License,中国大陆可用 ✅
- **省钱路径**: 部署到壹镜工坊 4090D 后,出片不再花 API token(只花 2.22/时 GPU 费)
