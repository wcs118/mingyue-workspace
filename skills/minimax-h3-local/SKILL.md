---
name: minimax-h3-local
description: MiniMax H3 开源本地部署方案(2026-08-02 开放权重)。H3 = 33.1B 参数全模态视频生成系统,支持文生视频/图生视频/参考生视频 + 原生立体声,4-15秒/24FPS/768p(2K 需 API)。本技能含部署决策、ComfyUI/SGLang/vLLM/diffusers 四种后端、Turbo LoRA 2x 加速。⚠️ 需要 GPU(≥24G 显存可 4bit 量化),本机(4核/7G/无GPU)不可直接部署。
---

# MiniMax H3 本地部署(吸收自开源)

> 官方仓库: https://github.com/MiniMax-AI/MiniMax-H3 (open-weights, 2026-08-02)
> ComfyUI 集成: https://github.com/MiniMaxH3ComfyUI/MiniMax-H3-ComfyUI (含 Turbo LoRA)
> 权重: HuggingFace `MiniMaxAI/MiniMax-H3` / ModelScope `minimax`

## 一、这是什么
- **H3-Base FL2VA**: 文生视频 / 首帧图生视频 / 首尾帧生视频
- **H3-Base Ref2VA**: 多模态参考生视频(≤9图 + ≤3视频 + ≤3音频)
- 原生 32kHz 立体声音频同轨生成,无需单独 TTS
- 11 种语言对话稳定支持(含中英文)
- 输出: 4–15 秒, 24 FPS, 768p 短边(2K 需 H3-Regenerate-2K API)

## 二、⚠️ 部署前提(先看这个!)
| 条件 | 要求 | 本机(4核/7G/无GPU) |
|---|---|---|
| GPU | ≥24G 显存(4bit 量化) / 官方示例 4×GPU | ❌ 无 GPU |
| 磁盘 | ≥100G 权重+依赖 | ❌ 仅 27G 可用 |
| 内存 | ≥32G 推荐 | ❌ 7G |

**结论:本机不可本地部署 H3。** 可选路径:
1. 壹镜工坊 4090D 实例(2.22/时)——ComfyUI 已集成 H3,直接可用 ✅
2. 云 GPU 租用后跑 scripts/h3-local-deploy.sh 一键部署
3. 继续用 MiniMax API(花 token)

## 三、四种推理后端
| 后端 | 特点 | 适用 |
|---|---|---|
| **ComfyUI** | 可视化工作流,社区模板多,Turbo LoRA 2x 加速 | 壹镜工坊/可视化操作 |
| **SGLang** | 官方文档示例,吞吐高 | 服务化/批量 |
| **vLLM** | 生态成熟 | 服务化 |
| **diffusers** | Python 直调,灵活 | 脚本/集成 |

## 四、ComfyUI 部署步骤(有 GPU 机器上)
```bash
# 1. 装 ComfyUI(需 v0.31.0+)
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI && pip install -r requirements.txt
# 2. 装 H3 自定义节点
git clone https://github.com/MiniMaxH3ComfyUI/MiniMax-H3-ComfyUI custom_nodes/MiniMax-H3-ComfyUI
# 3. 下载权重(HuggingFace MiniMaxAI/MiniMax-H3,约 66G fp16 / 量化更小)
# 4. 可选:Turbo LoRA(2x 加速, MiniMaxAI/MiniMax-H3-Turbo-Lora)
# 5. 启动
python main.py --listen 0.0.0.0 --port 8188
```
工作流模板:T2V / I2V / R2V / turbo-lora / audio-video / batch 六种,仓库内 workflow JSON 直接拖入 ComfyUI。

## 五、diffusers 直调示例(有 GPU 机器)
```python
from diffusers import MiniMaxH3Pipeline  # 按官方文档
pipe = MiniMaxH3Pipeline.from_pretrained("MiniMaxAI/MiniMax-H3", torch_dtype=torch.bfloat16)
pipe.to("cuda")
video = pipe(prompt="a cat walking on the moon", duration=5).video
```

## 六、关键参数速查
| 参数 | 值 | 说明 |
|---|---|---|
| duration | 4–15s | 生成时长 |
| fps | 24 | 帧率 |
| resolution | 768p 短边 | 2K 需 API |
| aspect | 21:9~9:16 | 任意比例 |
| audio | 32kHz 立体声 | 原生生成 |
| turbo lora | 2x 加速 | 轻微质量损失 |

## 七、授权注意
- 自定义 **MiniMax H3 Community License**(非 OSI 标准)
- 默认排除美国/欧盟/英国/韩国(正式许可需申请)——中国大陆不受影响 ✅
- 商用有条件(收入门槛/义务),个人使用没问题

## 八、Prompt 技能
写提示词用已有技能 `skills/minimax-h3/h3-prompt-writing/`(T2VA/I2VA/FL2VA/Ref2VA 结构)。
