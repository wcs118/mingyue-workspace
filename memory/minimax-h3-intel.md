# MiniMax H3 情报(2026-08-11 开源吸收)

## 模型核心
- **MiniMax-AI/MiniMax-H3**(GitHub ⭐5110 / HF 下载 4.7万+,2026-08-11 更新):全模态(omni-modal)生成系统
- 能力:理解文本/图像/视频/音频,生成**带原生立体声音频的视频**,最高 2K 分辨率、最长 15 秒、24FPS、32kHz 立体声
- 11 种语言稳定对话(含中英)
- 三大模块:H3-Context-IR(多模态指令理解/提炼)→ H3-Base(生成 768p)→ H3-Regenerate-2K(2K 增强)
- 变体:H3-Base-FL2VA(首尾帧模式,0/1/2 图输入)、H3-Base-Ref2VA(全参考模式,≤9图/≤3视频/≤3音频,总≤12文件)
- 生成模式:T2VA(文生视频) I2VA(图生视频) FL2VA(首尾帧) L2VA(末帧) Ref2VA(全参考)
- License:minimax-h3-community-license-agreement(社区许可)

## 配套技能(已吸收 ✅ 9 个)
来源:github.com/MiniMax-AI/MiniMax-H3/tree/main/skills,全部带 SKILL.cn.md 中文版
1. **h3-prompt-writing** — H3 五模式提示词写作(integrated_multimodal_description / overall_soundscape / non_diegetic_music)
2. **3d-animation-short-generator** — 3D 动画短片全流程(故事→分镜→生成→合成→BGM)
3. **papercraft-stop-motion-explainer** — 纸艺定格动画科普视频
4. **paper-collage-explainer-generator** — 拼贴风格讲解视频
5. **minimalist-product-ad-generator** — 极简风产品广告短片
6. **brand-promo-video-generator** — 品牌推广短片
7. **music-video-subtitle-generator** — 音乐视频歌词字幕排版
8. **co-op-game-intro-generator** — 双人合作游戏开场动画
9. **handdrawn-live-video-generator** — 手绘+实拍混合超现实短片

## API/使用方式
- 官方 API:platform.minimax.io(全球)| platform.minimaxi.com(国内),video-generation-v2
- WebApp:hailuoai.video / hailuoai.com
- 本机 2C4G 无 GPU,模型本身不可本地跑;技能(提示词/工作流)已吸收,未来配 API key 即可出片

## 吸收结论
- 9 个官方技能 = 已吸收 ✅(含中文版,可指导任何视频生成工具)
- H3 模型本身 = 记入情报,需 API key 或 GPU 时启用
