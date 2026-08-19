# GitHub 热榜技能评估 2026-08-13

## ✅ 已吸收
### RUC-NLPIR/Arbor(⭐1K, Apache-2.0)— 自主研究 agent 技能套件
- 声称比 Claude Code/Codex 快 2.5× 的假设树研究工作流(人大 NLPIR 出品,有论文 arXiv:2606.11926)
- **11 个技能全量入库**(skills/arbor-*):
  - `arbor-research-agent`(入口)+ `arbor-agent-orchestrator`(编排)
  - `arbor-agent-setup-intake`(目标澄清)/ `arbor-agent-ideate`(假设生成)
  - `arbor-agent-executor`(执行)/ `arbor-agent-coordinator`(协调)
  - `arbor-agent-merge-eval`(合并评估)/ `arbor-agent-search`(搜索)
  - `arbor-agent-tools`(工具)/ `arbor-agent-resume-report`(恢复报告)
  - `arbor-agent-plugins-hitl-budget`(人工介入+预算)
- 用途:拿自然语言目标 → 自主跑"提出假设→改代码→跑评测→合并"闭环研究
- 上游追踪已加入 upstream.json(共30仓库)
- 亮点:keyless,可用自有模型(DeepSeek)驱动;带 MCP 服务器

## 📋 评估未吸收(记情报,后续按需)
- **omnigent-ai/omnigent**(⭐8.7K)— agent meta-harness,统一编排 Claude Code/Codex/Cursor 等,pip 可装(0.9.0),终端+浏览器+手机多端会话同步
- **yc-software/qm**(⭐13.3K)— YC 出品多人 agent 协作 harness
- **genspark-ai/genoffice**(⭐2.7K)— 开源 AI 办公套件(Word/PPT/Excel 类)
- **guillaumemeyer/watermarks-remover**(⭐2.6K)— 去 AI 溯源水印(Unicode 文本清洗+统计)
- **antirez/h3.c**(⭐1.6K)— MiniMax H3 原生推理引擎(Apple Silicon Metal,本机 Linux 用不了,但说明 H3 生态在长)
- **fancyboi999/ai-engineering-from-scratch-zh**(⭐940)— Agent 工程师 503 课学习路径(中文,20阶段),适合阶段六持续学习
- **elder-plinius/T3MP3ST**(⭐5.5K)/ **UditAkhourii/adhd**(⭐3.5K)— 已在库
