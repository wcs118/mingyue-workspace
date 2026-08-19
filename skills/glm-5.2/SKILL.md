---
name: glm-5.2
description: 智谱 GLM-5.2 模型接入与调用(1M上下文旗舰, OpenAI 兼容 API)。用于 GLM 系列模型对话、编码、长程任务、思考模式推理。需要 ZHIPU_API_KEY。
---

# GLM-5.2 智谱接入技能

## 快速调用
```bash
# 默认免费模型 glm-4.7-flash
bash /root/.openclaw/workspace/scripts/glm-run.sh "你的问题"

# 旗舰 GLM-5.2
bash /root/.openclaw/workspace/scripts/glm-run.sh "写个快速排序" glm-5.2

# 思考模式(推理)
bash /root/.openclaw/workspace/scripts/glm-run.sh "证明哥德巴赫猜想" glm-5.2 thinking
```

## 会话内切换模型
```
/model zhipu/glm-5.2
/model zhipu/glm-4.7-flash   # 免费
```

## 可用模型
| ID | 说明 | 上下文 | 输出 |
|---|---|---|---|
| glm-5.2 | 旗舰·1M | 1M | 128K |
| glm-5.1 | 长程·Coding对齐Opus 4.6 | 200K | 128K |
| glm-5 | 编程对齐 Opus 4.5 | 200K | 128K |
| glm-4.7 | 通用 | 200K | 128K |
| glm-4.7-flash | **免费** | 200K | 128K |
| glm-5v-turbo | 多模态Coding | 200K | 128K |

## API 关键参数
- Base URL: `https://open.bigmodel.cn/api/paas/v4/`
- 思考模式: `extra_body={"thinking": {"type": "enabled"}}`;推理内容在 `delta.reasoning_content`
- 流式输出: `stream=True`

## Key 配置
1. 老板提供 ZHIPU_API_KEY
2. 写入 `/root/.openclaw/config/zhipu.env`(格式 `ZHIPU_API_KEY=xxx`,600 权限)
3. 验证: `bash scripts/glm-run.sh "你好" glm-5.2`

## 详细情报
见 `memory/glm-5.2-absorb.md`
