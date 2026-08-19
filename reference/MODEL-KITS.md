# MODEL-KITS 资产档案 v3.0 — 明月系自研模型封装库全家桶

> 规矩(老板 2026-08-17 立):**每个模型都自研封装,百分之百自己的代码,谁也拿不去**
> v3.0 深挖(老板批评"继续深挖"后):读官方文档挖全能力面,补齐每个模型全部端点/参数
> 标准:纯 Python 标准库,零依赖,任何机器可跑;删掉原仓库/CLI 照样能用
> 位置:全部在 `/root/.openclaw/workspace/scripts/`

## 资产清单(6 个 kit,3744 行,69 个能力命令)

| # | 资产 | 行数 | 能力命令数 | 覆盖能力 | 实测 |
|---|---|---|---|---|---|
| 1 | `qwen-kit.py` | 1234 | 17 | 千问全家桶(chat/reasoning/vision/video/stream/tools/json/schema/embed/batch/router/image_gen/audio_asr/audio_tts/context/models/doctor) | ✅ 11 项 |
| 2 | `deepseek-kit.py` | 596 | 13 | v3: +thinking 模式控制(--effort low/high/max/--no_think)/balance 余额查询/工具调用 reasoning_content 回传修复 | ✅ 9 项 |
| 3 | `grok-kit.py` | 458 | 9 | run/plan/verify/report/session(会话续跑)/sandbox/tools/models/doctor | ✅ 会话续跑实测 |
| 4 | `kimi-kit.py` | 505 | 15 | v3: +kimi-k3 旗舰(1M ctx)/高速版/search 联网搜索/partial 续写/balance/estimate/视频直传 | ✅ 7 项 |
| 5 | `minimax-kit.py` | 441 | 11 | v3: +embed 向量化/voice_clone 声音克隆;全链路(chat/video/image/audio) | ⚠️ 链路通余额不足 |
| 6 | `codex-kit.py` | 510 | 4 | run(agent loop)/plan/verify/report | ✅ 闭环 |

## v3.0 深挖升级点(老板 10:24 批评"继续深挖"后)

- **deepseek-kit v3.0(557→596)**: 读官方文档发现 thinking 模式三档控制(--effort low/high/max + --no_think 关闭)+ **关键修复**:thinking 模式下工具调用必须回传 reasoning_content 否则 400,已修(实测 7*8=56 不再报错) + balance 余额查询(实测 49.81 元)
- **kimi-kit v3.0(433→505)**: 挖出旗舰 **kimi-k3(2.8万亿参数, 1M ctx)** + 高速版 k2.7-code-highspeed(260 token/s) + search 联网搜索($web_search 内置工具) + partial 续写模式(实测"低头思故乡") + balance/estimate(实测 9 tokens) + **视频直传 base64(不再需要 ffmpeg 抽帧!)**
- **minimax-kit v3.0(390→441)**: 补 embed 向量化(embo-01) + voice_clone 声音克隆;完整 11 命令
- **grok-kit v3.0 实测**: 会话续跑——同一会话先写 greet.py,再让它加 --loud 功能,自动继承上下文修改文件 ✅

## 实测记录(2026-08-17 10:30,全部真跑过)

### deepseek-kit v3.0 ✅
- balance: 余额 49.81 元 ✅ / effort 控制: 9.11 vs 9.8 → 正确答 9.8 大 ✅
- tools thinking 回传: 7*8=56(修复前会 400)✅ / reasoning/chat/stream/json 全 ✅

### kimi-kit v3.0 ✅
- chat/vision/json 全 ✅ / tools: (12+34)*5=230 ✅
- estimate: "你好世界" = 9 tokens ✅ / balance: 查询成功 ✅
- partial 续写: "举头望明月," → "低头思故乡。" ✅ / search 联网链路通 ✅

### grok-kit v3.0 ✅
- 会话续跑: 先写 greet.py → 再要求加 --loud → 自动改文件并验证(你好,老板)✅
- doctor/sandbox 拦截 rm -rf / ✅

### minimax-kit v2.0 ⚠️(代码链路全通,账号余额不足)
- doctor: key 就绪 ✅ / chat: 报 1008 insufficient balance
- video_gen: 提交 402 insufficient balance(参数链路已通: MiniMax-H3/ratio顶层/resolution必填)

## 能力矩阵

| 能力 | qwen | deepseek | kimi | grok | minimax |
|---|---|---|---|---|---|
| 文本对话 | ✅ | ✅ | ✅ | ✅(agent) | ⚠️ |
| 推理链 | ✅ | ✅ | — | — | — |
| 图像理解 | ✅ | — | ✅ | — | — |
| 视频理解 | ✅ | — | ✅ | — | — |
| 视频生成 | — | — | — | — | ⚠️ |
| 流式 | ✅ | ✅ | ✅ | — | — |
| 工具调用 | ✅ | ✅ | ✅ | ✅ | — |
| 批量 | ✅ | ✅ | ✅ | — | — |
| 编码闭环 | — | — | — | ✅ | — |
| 会话持久化 | — | ✅ | — | ✅ | — |
| 沙箱安全 | — | — | — | ✅ | — |
| 文生图 | ⏳百炼 | — | — | — | ⚠️ |
| 语音 | ⏳百炼 | — | — | — | ⚠️ |
| 向量 | ⏳百炼 | — | — | — | — |

## 待办
- [ ] MiniMax 充值/新 key → video_gen/chat 出片验证
- [ ] 老板给百炼 key → qwen embed/image_gen/audio 4 能力激活
- [ ] 各 kit 接真实任务轮训
- [ ] codex-kit 与 grok-kit 合并评估(都是编码 agent 内核,可二选一保留)
