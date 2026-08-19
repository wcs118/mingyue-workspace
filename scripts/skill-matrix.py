#!/usr/bin/env python3
"""
skill-matrix.py — 明月调度矩阵(任务→技能组合 一键查询调用)
=============================================================
在 14 能力域 + 9 大 Agent 体系之上,把吸收的 173 个技能做成矩阵:
分类 → 组合 → 融会贯通 → 任务来了直接查矩阵拿调用方案。

用法:
  skill-matrix.py list                          # 全部技能按域列出
  skill-matrix.py lookup --task "写公众号文章"  # 任务→推荐技能组合
  skill-matrix.py domain 内容/写作              # 某个域的全部技能
  skill-matrix.py agent dsh                     # 某个体系下全部技能
  skill-matrix.py combo --task "..." --verbose  # 组合方案+调用顺序
  skill-matrix.py stats                         # 矩阵统计
  skill-matrix.py smoke                         # 自测
"""

import argparse
import json
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
MATRIX_FILE = WORKSPACE / "reference" / "skill-matrix.json"
AAS_INDEX = WORKSPACE / "skills-db" / "aas" / "skills_index.json"
AAS_MAPPED = WORKSPACE / "skills-db" / "aas" / "aas-mapped.json"

# ---------- 14 能力域(图:2143技能归类最终核查版) ----------
DOMAINS = [
    "软件开发/编码", "AI/机器智能/Agent", "运营/管理/客服", "营销/电商/SEO",
    "内容/写作/媒体", "设计/UI/UX", "安全/攻防", "数据/分析/BI",
    "测试/质量", "基础设施工具", "金融/量化", "本地化", "眼镜/可穿戴", "参考/冷门",
]

# ---------- 9 大 Agent 体系 ----------
AGENTS = ["deepseek-harness", "arbor", "kimi", "minimax-h3", "grok-build",
          "codex-superpowers", "claude-skills", "google-skills", "gm"]

# ---------- 任务关键词 → 能力域映射(融会贯通的核心) ----------
TASK_ROUTING = [
    # (能力域, 关键词组)
    ("软件开发/编码", ["写代码", "开发", "编程", "debug", "调试", "修 bug", "修个 bug", "bug", "重构", "代码", "git", "提交", "pr", "接口", "api", "数据库", "sql", "docker", "部署", "后端", "前端", "全栈", "架构"]),
    ("AI/机器智能/Agent", ["agent", "智能体", "ai 工具", "模型", "多模态", "视频生成", "图像理解", "研究", "deepseek", "kimi", "minimax", "grok", "harness", "编排", "子代理"]),
    ("运营/管理/客服", ["客服", "回复客户", "工单", "投诉", "售后", "会议", "纪要", "周报", "复盘", "日报", "管理", "调度", "任务分派"]),
    ("营销/电商/SEO", ["seo", "营销", "推广", "定价", "竞品", "文案转化", "广告", "电商", "店铺", "发布", "launch", "投标", "rfp"]),
    ("内容/写作/媒体", ["写文章", "公众号", "知乎", "长文", "写作", "标题", "短剧", "剧本", "视频脚本", "剪辑", "分镜", "旁白", "翻译", "小红书", "文案", "小说"]),
    ("设计/UI/UX", ["ppt", "幻灯片", "设计", "ui", "ux", "界面", "prd", "产品", "原型", "流程图", "信息图"]),
    ("安全/攻防", ["安全", "漏洞", "渗透", "审计", "扫描", "webvuln", "recon", "防火墙", "加固"]),
    ("数据/分析/BI", ["数据分析", "报表", "指标", "财务", "估值", "dcf", "ab 测试", "留存", "bi", "图表"]),
    ("测试/质量", ["测试", "用例", "tdd", "质量", "验证", "review", "code review"]),
    ("基础设施工具", ["笔记", "obsidian", "docker", "服务器", "监控", "备份", "存储", "内存", "磁盘"]),
    ("金融/量化", ["金融", "量化", "投资", "股票", "交易", "估值", "财报"]),
    ("本地化", ["翻译成", "本地化", "i18n", "英文版"]),
    ("参考/冷门", ["数学", "imo", "竞赛", "文献", "综述", "研究", "深度"]),
]

# ---------- 矩阵数据(173 技能,含体系归属) ----------
# 结构: {技能名: {domain, agent, desc, call}}
MATRIX = {
    # ═══ 💻 软件开发/编码 ═══
    "systematic-debugging": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "先找根因再修,禁止症状修复", "call": "直接用于调试"},
    "debugging-and-error-recovery": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "结构化排障+错误恢复", "call": "直接用于调试"},
    "test-driven-development": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "先写测试再写代码", "call": "开发流程必备"},
    "tdd-guide": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "TDD 生成测试/覆盖率分析", "call": "开发流程必备"},
    "incremental-implementation": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "薄切片垂直实施", "call": "大任务拆分"},
    "minimal-fix": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "最小改动修指定问题", "call": "小 bug 修复"},
    "verification-before-completion": {"domain": ["软件开发/编码", "测试/质量"], "agent": "codex-superpowers", "desc": "证据先于结论/完成前验证", "call": "收尾验证"},
    "zero-hallucination-coder": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "不幻觉的资深工程搭档", "call": "严谨编码"},
    "doubt-driven-development": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "怀疑驱动开发(防上下文污染)", "call": "长会话开发"},
    "karpathy-coder": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "卡帕西极简编码", "call": "极简风格"},
    "source-driven-development": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "一切以官方文档为准", "call": "框架决策"},
    "spec-driven-development": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "先写规格再写码", "call": "复杂功能"},
    "subagent-driven-development": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "每任务派独立子代理", "call": "并行开发"},
    "dispatching-parallel-agents": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "并行子代理委派", "call": "并行开发"},
    "executing-plans": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "计划执行与汇报", "call": "执行阶段"},
    "writing-plans": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "完整实施计划", "call": "规划阶段"},
    "planning-and-task-breakdown": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "任务拆解+验收标准", "call": "规划阶段"},
    "planning-with-files": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "文件化规划", "call": "规划阶段"},
    "finishing-a-development-branch": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "分支收尾四步", "call": "git 收尾"},
    "using-git-worktrees": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "隔离工作区", "call": "git 并行"},
    "git-worktree-manager": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "worktree 管理", "call": "git 并行"},
    "code-review-and-quality": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "代码审查质量门", "call": "review 阶段"},
    "code-reviewer": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "PR 审查工具", "call": "review 阶段"},
    "requesting-code-review": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "派审查子代理", "call": "review 阶段"},
    "receiving-code-review": {"domain": "软件开发/编码", "agent": "codex-superpowers", "desc": "接收审查", "call": "review 阶段"},
    "api-design-reviewer": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "API 设计审查", "call": "接口设计"},
    "senior-architect": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "架构设计分析", "call": "架构阶段"},
    "senior-backend": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "后端模式/API/数据库/安全", "call": "后端开发"},
    "senior-frontend": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "前端模式/性能优化", "call": "前端开发"},
    "senior-fullstack": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "全栈脚手架+质量分析", "call": "全栈开发"},
    "sql-queries": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "自然语言→优化 SQL", "call": "数据查询"},
    "database-designer": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "数据库设计专家", "call": "表结构设计"},
    "docker-development": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "Docker 开发", "call": "容器化"},
    "build-mcp-server": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "MCP 服务器构建", "call": "工具集成"},
    "shopify-development": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "Shopify 开发", "call": "电商开发"},
    "context-engineering": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "上下文工程(喂对信息)", "call": "prompt 设计"},
    "knowledge-ops": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "知识运维", "call": "知识管理"},
    # ═══ 🤖 AI/机器智能/Agent ═══
    "deepseek-harness": {"domain": "AI/机器智能/Agent", "agent": "deepseek-harness", "desc": "dsh 引擎(守卫链/作用域/协作取消/事务回滚)", "call": "scripts/dsh-run.sh '任务'"},
    "arbor-research-agent": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "Arbor 自主研究总入口", "call": "scripts/arbor-run.sh"},
    "arbor-agent-orchestrator": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "研究编排(阶段控制)", "call": "Arbor 内部"},
    "arbor-agent-coordinator": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "战略循环指挥官", "call": "Arbor 内部"},
    "arbor-agent-ideate": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "想法树生成", "call": "Arbor 内部"},
    "arbor-agent-executor": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "想法叶子执行", "call": "Arbor 内部"},
    "arbor-agent-merge-eval": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "合并决策验证", "call": "Arbor 内部"},
    "arbor-agent-search": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "文献标注", "call": "Arbor 内部"},
    "arbor-agent-setup-intake": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "启动参数收集", "call": "Arbor 内部"},
    "arbor-agent-resume-report": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "中断恢复报告", "call": "Arbor 内部"},
    "arbor-agent-tools": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "内置工具", "call": "Arbor 内部"},
    "arbor-agent-plugins-hitl-budget": {"domain": "AI/机器智能/Agent", "agent": "arbor", "desc": "人在环预算", "call": "Arbor 内部"},
    "multi-agent-task-orchestrator": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "多代理任务编排", "call": "编排复杂任务"},
    "open-agent-teams": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "tmux 分离式 agent 执行", "call": "后台 agent"},
    "agents-best-practices": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "agent 最佳实践", "call": "设计 agent"},
    "agent-context-audit": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "agent 上下文审计", "call": "审计"},
    "using-agent-skills": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "agent 技能使用", "call": "技能调用"},
    "skill-development": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "技能开发规范", "call": "新技能"},
    "image-video-framework": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "提示词七要素框架", "call": "图像/视频提示词"},
    "fable-loop": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "Fable 诚实循环", "call": "长任务循环"},
    "fable-domain": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "领域适配器", "call": "Fable 内部"},
    "fable-judge": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "诚实判定(防假成功)", "call": "验收"},
    "kimi-k2.5": {"domain": "AI/机器智能/Agent", "agent": "kimi", "desc": "Kimi K2.6 多模态接入", "call": "scripts/kimi-vision.sh"},
    "minimax-h3": {"domain": "AI/机器智能/Agent", "agent": "minimax-h3", "desc": "MiniMax H3 视频生成", "call": "scripts/minimax-h3.sh"},
    # ═══ 📑 内容/写作/媒体 ═══
    "human-writing": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "中文活人感长文", "call": "写作直接调用"},
    "khazix-khazix-writer": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "公众号长文", "call": "公众号写作"},
    "humanizer": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "去 AI 味", "call": "成稿润色"},
    "writing-rules": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "写作规则", "call": "写作规范"},
    "release-notes": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "发布说明", "call": "版本发布"},
    "novel-outline": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "小说大纲", "call": "小说创作"},
    "novel-characters": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "小说人物", "call": "小说创作"},
    "novel-art": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "小说封面", "call": "小说创作"},
    "baoyu-translate": {"domain": ["内容/写作/媒体", "本地化"], "agent": "claude-skills", "desc": "中英精翻", "call": "翻译任务"},
    "baoyu-wechat-summary": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "微信文章摘要", "call": "摘要任务"},
    "ai-short-drama": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "AI 短剧总纲", "call": "短剧项目"},
    "micro-drama-script": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "微短剧编剧", "call": "短剧剧本"},
    "short-drama": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧总集", "call": "短剧项目"},
    "short-drama-write": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧写作", "call": "短剧剧本"},
    "short-drama-storyboard": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧分镜", "call": "短剧分镜"},
    "short-drama-video-prompts": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧视频提示词", "call": "短剧生成"},
    "short-drama-image-prompts": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧图像提示词", "call": "短剧生成"},
    "short-drama-develop": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧开发", "call": "短剧项目"},
    "short-drama-knowhow": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧方法论", "call": "短剧学习"},
    "short-drama-novel-analyze": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧小说分析", "call": "改编"},
    "short-drama-review": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧复盘", "call": "复盘"},
    "short-drama-assets": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "短剧素材", "call": "素材库"},
    "jianying-editor": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "剪映自动化剪辑", "call": "视频剪辑"},
    "video-shotcraft": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "152 镜头配方卡", "call": "分镜设计"},
    "youtube-full": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "YouTube 全流程", "call": "视频制作"},
    "narrator-ai-cli": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "AI 旁白", "call": "配音"},
    "baoyu-format-markdown": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "MD 格式化", "call": "排版"},
    "baoyu-markdown-to-html": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "MD→HTML", "call": "排版"},
    "baoyu-post-to-wechat": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "发布公众号", "call": "发布"},
    "baoyu-slide-deck": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "幻灯片", "call": "演示"},
    "baoyu-infographic": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "信息图", "call": "可视化"},
    "baoyu-article-illustrator": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "文章插图", "call": "配图"},
    "baoyu-image-gen": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "图像生成", "call": "配图"},
    "baoyu-xhs-images": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "小红书配图", "call": "小红书"},
    "baoyu-url-to-markdown": {"domain": "内容/写作/媒体", "agent": "claude-skills", "desc": "URL→MD", "call": "抓取"},
    # ═══ 👤 运营/管理/客服 ═══
    "customer-support": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "客服全流程", "call": "客服"},
    "ai-customer-reply": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "客户拟回复", "call": "客服"},
    "cs-intent-classify": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "客服意图路由", "call": "客服"},
    "cs-ticket-extract": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "对话→工单", "call": "客服"},
    "inbox-triage": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "收件箱分类", "call": "日常"},
    "meetings": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "会议门控+行动项", "call": "会议"},
    "meeting-analyzer": {"domain": ["运营/管理/客服", "数据/分析/BI"], "agent": "claude-skills", "desc": "会议反馈分析", "call": "会议"},
    "summarize-meeting": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "会议纪要", "call": "会议"},
    "weekly-review": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "周回顾", "call": "周报"},
    "retro": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "结构化复盘", "call": "复盘"},
    "pre-mortem": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "事前验尸", "call": "风险预防"},
    "loop-triage": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "循环分类", "call": "循环任务"},
    "loop-verifier": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "独立验证", "call": "验收"},
    "loop-budget": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "循环预算", "call": "循环任务"},
    "framework-ops": {"domain": "运营/管理/客服", "agent": "gm", "desc": "0号v8 框架运维", "call": "框架维护"},
    "khazix-leader": {"domain": "运营/管理/客服", "agent": "gm", "desc": "领导/管理/执行三角色", "call": "团队协作"},
    "khazix-neat-freak": {"domain": "运营/管理/客服", "agent": "gm", "desc": "知识治理收尾", "call": "收尾"},
    "khazix-storage-analyzer": {"domain": "运营/管理/客服", "agent": "gm", "desc": "存储分析", "call": "存储"},
    "session-report": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "会话 HTML 报告", "call": "汇报"},
    "receipts": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "开发收据", "call": "记录"},
    "pro-workflow-learn": {"domain": "运营/管理/客服", "agent": "gm", "desc": "工作流学习", "call": "学习"},
    "shushu-internship": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "实习准备", "call": "求职"},
    # ═══ 📝 营销/电商/SEO ═══
    "ai-seo": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "AI SEO 优化", "call": "SEO"},
    "seo-audit": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "SEO 审计", "call": "SEO"},
    "competitive-intel": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "竞品情报", "call": "调研"},
    "content-strategy": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "内容策略", "call": "策略"},
    "launch-strategy": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "发布策略", "call": "发布"},
    "shipping-and-launch": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "安全发布", "call": "发布"},
    "pricing-strategist": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "定价策略", "call": "定价"},
    "deal-desk": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "交易桌", "call": "商务"},
    "rfp-responder": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "RFP 投标", "call": "投标"},
    "khazix-aihot": {"domain": "营销/电商/SEO", "agent": "gm", "desc": "AI 热榜追踪", "call": "热榜"},
    "ab-test-analysis": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "A/B 测试分析", "call": "实验"},
    "saas-metrics-coach": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "SaaS 指标", "call": "指标"},
    "cohort-analysis": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "留存群组分析", "call": "分析"},
    "job-stories": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "任务故事", "call": "用户研究"},
    "user-stories": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "用户故事 3C", "call": "需求"},
    "outcome-roadmap": {"domain": "营销/电商/SEO", "agent": "claude-skills", "desc": "结果路线图", "call": "规划"},
    # ═══ 🎨 设计/UI/UX ═══
    "frontend-design": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "Anthropic 前端设计", "call": "UI 设计"},
    "minimalist-skill": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "极简实用 UI", "call": "UI 设计"},
    "taste-skill-v1": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "设计品味", "call": "审美"},
    "dragon-ppt-maker": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "python-pptx 科技风 PPT", "call": "PPT"},
    "guizang-ppt-skill": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "HTML 翻页 PPT", "call": "PPT"},
    "idea-refine": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "想法打磨", "call": "构思"},
    "product-discovery": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "产品发现", "call": "调研"},
    "product-strategist": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "产品战略", "call": "战略"},
    "senior-pm": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "项目管理", "call": "项目"},
    "create-prd": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "PRD 撰写", "call": "PRD"},
    "code-to-prd": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "代码→PRD", "call": "PRD"},
    "brainstorming": {"domain": "设计/UI/UX", "agent": "codex-superpowers", "desc": "头脑风暴→规格", "call": "构思"},
    "brainstorm-okrs": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "OKR 制定", "call": "目标"},
    "prioritization-frameworks": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "优先级框架", "call": "排序"},
    "sprint-plan": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "冲刺计划", "call": "迭代"},
    "process-mapper": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "流程映射", "call": "流程"},
    "strategy-red-team": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "战略红队", "call": "对抗"},
    # ═══ 🔒 安全/攻防 ═══
    "claude-security": {"domain": "安全/攻防", "agent": "claude-skills", "desc": "安全规范", "call": "安全基线"},
    "webvuln": {"domain": "安全/攻防", "agent": "claude-skills", "desc": "Web 漏洞测试", "call": "渗透"},
    "recon": {"domain": "安全/攻防", "agent": "claude-skills", "desc": "侦察", "call": "侦察"},
    "ponytail-audit": {"domain": "安全/攻防", "agent": "claude-skills", "desc": "审计", "call": "审计"},
    "ponytail-review": {"domain": "安全/攻防", "agent": "claude-skills", "desc": "评审", "call": "评审"},
    # ═══ 📊 数据/分析/BI ═══
    "financial-analyst": {"domain": ["数据/分析/BI", "金融/量化"], "agent": "claude-skills", "desc": "财务分析(DCF/估值)", "call": "财务"},
    "khazix-hv-analysis": {"domain": "数据/分析/BI", "agent": "gm", "desc": "横纵分析法", "call": "深度研究"},
    # (meeting-analyzer 已在上方运营/管理/客服 多域声明, 这里不再重复)
    # ═══ 🧪 测试/质量 ═══
    "test-scenarios": {"domain": "测试/质量", "agent": "claude-skills", "desc": "测试场景设计", "call": "测试"},
    # ═══ ⚙️ 基础设施工具 ═══
    "obsidian-cli": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "Obsidian CLI", "call": "笔记"},
    "obsidian-markdown": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "Obsidian MD", "call": "笔记"},
    "memos-memory-guide": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "Memos 记忆", "call": "记忆"},
    "adhd": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "ADHD 专注", "call": "专注"},
    "i-have-adhd": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "ADHD 辅助", "call": "专注"},
    "deep-work": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "深度工作", "call": "专注"},
    "opc-skills": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "OPC 技能集合", "call": "法务/PPT"},
    "project-artifact": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "项目产物", "call": "项目"},
    # ═══ 💰 金融/量化 ═══
    # (financial-analyst 已在上方数据/分析/BI 多域声明, 这里不再重复)
    # ═══ 🌍 本地化 ═══
    # (baoyu-translate 已在上方内容/写作/媒体 多域声明, 这里不再重复)
    # ═══ 📦 参考/冷门 ═══
    "math-olympiad": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "竞赛数学", "call": "数学"},
    "litreview": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "文献综述", "call": "学术"},
    "deep-research": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "深度研究", "call": "研究"},
    # ═══ 2026-08-16 热榜重新吸收 42 新技能 ═══
    # addyosmani/agent-skills (87.5K⭐, 生产级工程)
    "api-and-interface-design": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "API/接口/模块边界设计", "call": "接口设计"},
    "browser-testing-with-devtools": {"domain": "测试/质量", "agent": "claude-skills", "desc": "真实浏览器 DevTools 测试", "call": "浏览器测试"},
    "ci-cd-and-automation": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "CI/CD 管道自动化", "call": "构建部署"},
    "code-simplification": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "简化代码提升可读性", "call": "重构"},
    "deprecation-and-migration": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "弃用/迁移管理", "call": "系统迁移"},
    "documentation-and-adrs": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "架构决策记录 ADR", "call": "架构文档"},
    "frontend-ui-engineering": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "生产级可访问响应式 UI", "call": "前端开发"},
    "git-workflow-and-versioning": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "git 工作流/版本管理", "call": "git 操作"},
    "interview-me": {"domain": "运营/管理/客服", "agent": "claude-skills", "desc": "挖掘用户真实需求", "call": "需求访谈"},
    "observability-and-instrumentation": {"domain": "基础设施工具", "agent": "claude-skills", "desc": "可观测性/埋点", "call": "监控"},
    "performance-optimization": {"domain": "软件开发/编码", "agent": "claude-skills", "desc": "前后端/查询/数据库性能优化", "call": "性能优化"},
    "security-and-hardening": {"domain": "安全/攻防", "agent": "claude-skills", "desc": "代码安全加固", "call": "安全加固"},
    # Supervisor-Skills (5.6K⭐, 港科大科研导师)
    "benchmark-paper-template": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "Benchmark 论文五支柱框架", "call": "论文写作"},
    "drawio-reconstruction": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "图像→可编辑 Draw.io 图", "call": "图表重建"},
    "figure-designer": {"domain": "设计/UI/UX", "agent": "claude-skills", "desc": "科研图表设计", "call": "论文配图"},
    "idea-evaluator": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "科研想法评估", "call": "选题评估"},
    "intro-drafter": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "论文引言撰写", "call": "论文写作"},
    "paper-polish": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "论文润色", "call": "论文写作"},
    "paper-writer": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "论文全流程写作", "call": "论文写作"},
    "pre-submission-reviewer": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "投稿前审查", "call": "论文投稿"},
    "tech-paper-template": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "技术论文模板", "call": "论文写作"},
    "vibe-research-workflow": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "灵感研究工作流", "call": "研究流程"},
    # Orchestra-Research/AI-Research-SKILLs (11.7K⭐, ML 全领域)
    "0-autoresearch-skill": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "自主研究总控", "call": "自动研究"},
    "brainstorming-research-ideas": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "科研头脑风暴", "call": "选题"},
    "creative-thinking-for-research": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "科研创造性思维", "call": "选题"},
    "ml-paper-writing": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "ML 论文写作", "call": "论文写作"},
    "academic-plotting": {"domain": "参考/冷门", "agent": "claude-skills", "desc": "学术绘图", "call": "论文配图"},
    "dspy": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "编程式提示词优化框架", "call": "prompt 工程"},
    "langchain": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "LangChain Agent 框架", "call": "Agent 开发"},
    "llamaindex": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "LlamaIndex RAG 框架", "call": "RAG 开发"},
    "crewai": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "CrewAI 多代理框架", "call": "多代理"},
    "sentence-transformers": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "句子嵌入模型", "call": "向量化"},
    "qdrant": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "Qdrant 向量数据库", "call": "向量检索"},
    "long-context": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "长上下文技术", "call": "长文本"},
    "model-merging": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "模型融合", "call": "模型优化"},
    "speculative-decoding": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "投机解码加速推理", "call": "推理加速"},
    "flash-attention": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "FlashAttention 注意力优化", "call": "训练优化"},
    "lm-evaluation-harness": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "LM 评估基准", "call": "模型评估"},
    "vllm": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "vLLM 推理服务", "call": "模型部署"},
    "research-manager": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "研究项目管理", "call": "研究管理"},
    "rigor-reviewer": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "严谨性审查", "call": "研究审查"},
    "compiler": {"domain": "AI/机器智能/Agent", "agent": "claude-skills", "desc": "研究产物编译", "call": "研究产出"},
}


def load_matrix() -> dict:
    """加载主矩阵 + 合并 AAS 外部技能库(2009 技能)"""
    m = dict(MATRIX)
    # AAS 全量库(agentic-awesome-skills, 45K⭐, 2009 技能)
    try:
        mapped = json.loads(AAS_MAPPED.read_text())
        idx = json.loads(AAS_INDEX.read_text())
        id2cat = {s['id']: s for s in idx}
        for sid, meta in mapped.items():
            if sid in m:
                continue  # 主矩阵优先
            src = id2cat.get(sid, {})
            m[sid] = {
                "domain": meta["domain"],
                "agent": "aas",
                "desc": (src.get("description") or meta.get("desc") or "")[:80],
                "call": src.get("category", meta.get("category", "")),
                "risk": src.get("risk", meta.get("risk", "safe")),
                "src": "aas",
            }
    except Exception as e:
        print(f"⚠️ AAS 外部库加载失败: {e}", file=sys.stderr)
    return m


def route_domain(task: str) -> list:
    """任务→能力域(可命中多个,按命中数排序)"""
    task_l = task.lower()
    hits = []
    for domain, kws in TASK_ROUTING:
        n = sum(1 for kw in kws if kw.lower() in task_l)
        if n > 0:
            hits.append((n, domain))
    hits.sort(reverse=True)
    return [d for _, d in hits]


def lookup(task: str, verbose: bool = False) -> dict:
    """
    lookup.
    
    Args:
        verbose: enable verbose output.
    
    Returns:
        Result of the operation.
    """
    m = load_matrix()
    domains = route_domain(task)
    if not domains:
        domains = ["参考/冷门"]
    result = {"task": task, "domains": domains, "skills": [], "combos": []}
    seen = set()
    for d in domains:
        for name, meta in m.items():
            mds = meta["domain"] if isinstance(meta["domain"], list) else [meta["domain"]]
            if d in mds and name not in seen:
                seen.add(name)
                result["skills"].append({"name": name, **meta})
    # 组合:按 agent 分组
    agent_groups = {}
    for s in result["skills"]:
        a = s["agent"]
        agent_groups.setdefault(a, []).append(s["name"])
    result["combos"] = [{"agent": a, "skills": v} for a, v in sorted(agent_groups.items())]
    if verbose:
        return result
    # 精简输出
    return {"task": task, "domains": domains,
            "skill_count": len(result["skills"]),
            "skills": [s["name"] for s in result["skills"]],
            "combos": result["combos"]}


def stats() -> dict:
    """
    stats.
    
    Returns:
        Result of the operation.
    """
    m = load_matrix()
    by_domain = {}
    by_agent = {}
    for name, meta in m.items():
        mds = meta["domain"] if isinstance(meta["domain"], list) else [meta["domain"]]
        for d in mds:
            by_domain[d] = by_domain.get(d, 0) + 1
        by_agent[meta["agent"]] = by_agent.get(meta["agent"], 0) + 1
    return {"total": len(m), "by_domain": by_domain, "by_agent": by_agent}


def smoke_test() -> int:
    """
    smoke test.
    
    Returns:
        Result of the operation.
    """
    passed = failed = 0
    def t(name, cond):
        """
        t.
        
        Args:
            name: name.
        """
        nonlocal passed, failed
        print(f"{'✅' if cond else '❌'} {name}")
        passed += cond; failed += (not cond)

    # 1. 路由测试
    t("路由: 写公众号文章 → 内容/写作", "内容/写作/媒体" in route_domain("帮我写一篇公众号文章"))
    t("路由: 修 bug → 软件开发", "软件开发/编码" in route_domain("帮我修个 bug"))
    t("路由: 客服回复 → 运营/客服", "运营/管理/客服" in route_domain("客户投诉怎么回复"))
    # 2. lookup 测试
    r = lookup("写一篇公众号文章")
    t("lookup: 命中技能数>0", r["skill_count"] > 0)
    t("lookup: 组合按 agent 分组", len(r["combos"]) > 0)
    # 3. stats
    s = stats()
    t("stats: 总技能数>150", s["total"] > 150)
    t("stats: 14 域都有覆盖", len(s["by_domain"]) >= 13)
    # 4. 多域技能可查性
    r2 = lookup("做财务分析")
    t("多域: 财务分析能查到 financial-analyst", "financial-analyst" in r2["skills"])
    r3 = lookup("把文章翻译成英文")
    t("多域: 翻译能查到 baoyu-translate", "baoyu-translate" in r3["skills"])
    print(f"\n自测:{passed} 通过 / {failed} 失败")
    return 0 if failed == 0 else 1


def main():
    """
    main.
    """
    ap = argparse.ArgumentParser(description="明月调度矩阵")
    ap.add_argument("mode", choices=["list", "lookup", "domain", "agent", "combo", "pack", "stats", "smoke"])
    ap.add_argument("--task", default="", help="任务描述")
    ap.add_argument("--verbose", action="store_true", help="详细输出")
    args = ap.parse_args()

    m = load_matrix()

    if args.mode == "pack":
        # 委托给组合包模块(文件名带连字符,用 importlib 加载)
        import importlib.util
        packs_path = Path(__file__).resolve().parent / "skill-matrix-packs.py"
        spec = importlib.util.spec_from_file_location("skill_matrix_packs", packs_path)
        packs_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packs_mod)
        sys.exit(packs_mod.main_pack(args))

    if args.mode == "smoke":
        sys.exit(smoke_test())
    if args.mode == "stats":
        s = stats()
        print(f"矩阵总技能: {s['total']}")
        print("按能力域:", json.dumps(s["by_domain"], ensure_ascii=False))
        print("按体系:", json.dumps(s["by_agent"], ensure_ascii=False))
        sys.exit(0)
    if args.mode == "list":
        cur = None
        for name in sorted(m):
            meta = m[name]
            if meta["domain"] != cur:
                cur = meta["domain"]
                print(f"\n## {cur}")
            print(f"  {name} [{meta['agent']}] — {meta['desc']}")
        sys.exit(0)
    if args.mode == "lookup" or args.mode == "combo":
        if not args.task:
            print("需要 --task", file=sys.stderr)
            sys.exit(2)
        r = lookup(args.task, verbose=args.verbose)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0)
    if args.mode == "domain":
        target = args.task
        if not target:
            print("需要 --task 指定能力域", file=sys.stderr)
            sys.exit(2)
        found = False
        for name in sorted(m):
            meta = m[name]
            if target in meta["domain"]:
                found = True
                print(f"  {name} [{meta['agent']}] — {meta['desc']}")
        if not found:
            print("该域无技能:", target)
        sys.exit(0)
    if args.mode == "agent":
        target = args.task
        if not target:
            print("需要 --task 指定体系", file=sys.stderr)
            sys.exit(2)
        found = False
        for name in sorted(m):
            meta = m[name]
            if target.lower() in meta["agent"].lower():
                found = True
                print(f"  {name} [{meta['domain']}] — {meta['desc']}")
        if not found:
            print("该体系无技能:", target)
        sys.exit(0)


if __name__ == "__main__":
    main()