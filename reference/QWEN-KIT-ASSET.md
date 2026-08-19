# Qwen-Kit v2.0 自研完整封装库 — 明月系核心资产档案

> **性质**: 自己写的代码,谁也拿不走 🔒
> **版本**: v2.0.0(2026-08-17 老板指令升级:不能只写 440 行,要完整宝藏)
> **位置**: `/root/.openclaw/workspace/scripts/qwen-kit.py`(1234 行, 52KB)
> **依赖**: 纯 Python 标准库(urllib/threading/json),零第三方依赖
> **备份**: v1 精简版在 `scripts/qwen-kit-lite.py.bak`

## 一、能力全景(17 个命令,全部实测)

| # | 命令 | 能力 | 实测状态 |
|---|---|---|---|
| 1 | `chat` | 多轮对话(系统提示/温度/历史) | ✅ |
| 2 | `reasoning` | 推理深度控制(xhigh/high/medium/low) | ✅ |
| 3 | `json` | 结构化 JSON 抽取 | ✅ |
| 4 | `schema` | JSON Schema 强约束输出 | ✅ |
| 5 | `vision` | 图像理解(单图/多图对比) | ✅ 双图实测 |
| 6 | `video` | 视频理解(ffmpeg 抽帧) | ✅ 红苹果实测 |
| 7 | `stream` | 流式输出(思考+正文双通道) | ✅ |
| 8 | `tools` | function calling 完整闭环(多轮) | ✅ calc 实测 |
| 9 | `embed` | 文本向量化 | ⏳ 待百炼 key |
| 10 | `batch` | 批量并发(线程池+限速) | ✅ 3 文件实测 |
| 11 | `router` | 模型路由/故障切换 | ✅ |
| 12 | `image_gen` | 文生图(万相,异步任务) | ⏳ 待百炼 key |
| 13 | `audio_asr` | 语音识别 | ⏳ 待百炼 key |
| 14 | `audio_tts` | 语音合成 | ⏳ 待百炼 key |
| 15 | `context` | 上下文管理(token 估算/裁剪) | ✅ |
| 16 | `models` | 千问全家桶清单(18 模型) | ✅ |
| 17 | `doctor` | 自检所有能力 | ✅ |

## 二、工程化亮点(比 v1 强在哪)

1. **自动重试**: 429/5xx 指数退避(1s→3s→8s),网络错误也重试
2. **全局限速器**: 令牌桶 RateLimiter(默认 RPM=2,`QWEN_RPM` 可调),并发安全
3. **智能降级**: 端点限流/不支持时自动切换
   - chat: kimi 429 → 自动降 DeepSeek
   - vision/video: deepseek → 自动切 kimi 多模态
   - embed: 不支持的端点 → 自动切可用端点
4. **多端点探测**: DASHSCOPE > OPENROUTER > MOONSHOT > DEEPSEEK(按能力智能选)
5. **工具函数**: 内置 get_time / calc / search 三个工具,可扩展
6. **批处理**: 线程池并发 + 结果汇总 JSON

## 三、千问全家桶(18 模型拆解)

- **对话**: qwen3.8-27b / 3.8-max / 3.8-flash / 3.5-plus / 3.5-turbo
- **编码**: qwen3-coder-plus / next / flash
- **视觉**: qwen3-vl-plus / flash
- **语音**: qwen3-audio
- **向量**: text-embedding-v3 / v4
- **图像**: wanx2.1-t2i-turbo / wan2.2-t2i-flash

## 四、用法速查

```bash
python3 scripts/qwen-kit.py chat "你好" --system "你是明月"
python3 scripts/qwen-kit.py reasoning "解题" --level high
python3 scripts/qwen-kit.py json "张三28岁北京" --fields 姓名,年龄,城市
python3 scripts/qwen-kit.py vision a.png b.png "对比"
python3 scripts/qwen-kit.py video clip.mp4 "描述"
python3 scripts/qwen-kit.py tools "算 (12+34)*5"
python3 scripts/qwen-kit.py stream "写首诗"
python3 scripts/qwen-kit.py embed "文本"          # 需百炼
python3 scripts/qwen-kit.py batch f1.txt f2.txt
python3 scripts/qwen-kit.py router "你好" --models a,b,c
python3 scripts/qwen-kit.py image_gen "猫,赛博朋克"  # 需百炼
python3 scripts/qwen-kit.py context bigfile.md
python3 scripts/qwen-kit.py doctor
```

## 五、待激活(等老板百炼 key)

`DASHSCOPE_API_KEY` 一到,自动激活:qwen3.8-27b 真身 / embed / image_gen / audio_asr / audio_tts

## 六、维护约定

- 新能力 = 新增 `cmd_xxx` 函数 + 注册进 `handlers` 字典 + 更新 HELP
- 所有网络请求必须走 `throttled_request`(限速+重试)
- 测试: `python3 scripts/qwen-kit.py doctor` + 每个命令冒烟
