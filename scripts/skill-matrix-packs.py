#!/usr/bin/env python3
"""
skill-matrix.py — 明月调度矩阵 v2(含场景组合包)
=============================================
v2 新增: 场景组合包(COMBO_PACKS) — 把常见任务场景的完整技能链预组合,
任务来了直接调包,不用每次现拼。融会贯通的落地。

用法(新增):
  skill-matrix.py pack                          # 列出所有场景组合包
  skill-matrix.py pack --task "公众号文章"       # 查某场景的完整技能链
"""

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent

# ═══════════ 场景组合包(融会贯通层) ═══════════
# 把 170 技能按"任务场景"预组合成完整调用链
COMBO_PACKS = {
    "公众号长文": {
        "trigger": ["公众号", "长文", "文章"],
        "pipeline": [
            ("选题", ["brainstorming", "content-strategy", "khazix-aihot"]),
            ("写作", ["human-writing", "khazix-khazix-writer", "writing-rules"]),
            ("润色", ["humanizer", "taste-skill-v1"]),
            ("配图", ["baoyu-article-illustrator", "baoyu-image-gen"]),
            ("排版", ["baoyu-format-markdown", "baoyu-markdown-to-html"]),
            ("发布", ["baoyu-post-to-wechat", "baoyu-wechat-summary"]),
        ],
        "engine": "OpenClaw 明月 + dsh(human-writing 插件)",
        "note": "全链路: 选题→写作→润色→配图→排版→发布",
    },
    "短剧制作": {
        "trigger": ["短剧", "剧本", "微短剧"],
        "pipeline": [
            ("立项", ["ai-short-drama", "short-drama-knowhow", "micro-drama-script"]),
            ("剧本", ["short-drama-write", "short-drama-novel-analyze", "short-drama-develop"]),
            ("分镜", ["short-drama-storyboard", "video-shotcraft", "short-drama-video-prompts"]),
            ("素材", ["short-drama-image-prompts", "short-drama-assets", "image-video-framework"]),
            ("成片", ["minimax-h3", "jianying-editor", "narrator-ai-cli"]),
            ("复盘", ["short-drama-review", "retro"]),
        ],
        "engine": "OpenClaw + MiniMax H3 + 剪映",
        "note": "短剧全家桶 12 件套全链路",
    },
    "客服自动化": {
        "trigger": ["客服", "客户", "投诉", "售后", "工单"],
        "pipeline": [
            ("路由", ["cs-intent-classify", "inbox-triage"]),
            ("回复", ["ai-customer-reply", "customer-support"]),
            ("工单", ["cs-ticket-extract"]),
            ("复盘", ["meeting-analyzer", "retro"]),
        ],
        "engine": "OpenClaw + 微信通道",
        "note": "客服子公司 01 号方向",
    },
    "产品开发": {
        "trigger": ["开发", "产品", "功能", "写代码"],
        "pipeline": [
            ("规划", ["brainstorming", "create-prd", "user-stories", "outcome-roadmap"]),
            ("设计", ["senior-architect", "database-designer", "api-design-reviewer"]),
            ("实施", ["spec-driven-development", "incremental-implementation", "subagent-driven-development"]),
            ("测试", ["test-driven-development", "test-scenarios", "verification-before-completion"]),
            ("审查", ["code-review-and-quality", "requesting-code-review"]),
            ("交付", ["finishing-a-development-branch", "shipping-and-launch", "release-notes"]),
        ],
        "engine": "OpenClaw + 大掌柜 + dsh",
        "note": "全流程: 规划→设计→实施→测试→审查→交付",
    },
    "营销推广": {
        "trigger": ["营销", "推广", "seo", "广告", "电商"],
        "pipeline": [
            ("调研", ["competitive-intel", "seo-audit", "cohort-analysis"]),
            ("策略", ["content-strategy", "launch-strategy", "pricing-strategist"]),
            ("落地", ["ai-seo", "ab-test-analysis", "saas-metrics-coach"]),
            ("商务", ["deal-desk", "rfp-responder"]),
        ],
        "engine": "OpenClaw",
        "note": "增长子公司 04 号方向",
    },
    "AI 研究": {
        "trigger": ["研究", "调研", "deepseek", "agent", "模型"],
        "pipeline": [
            ("启动", ["arbor-agent-setup-intake", "arbor-research-agent"]),
            ("想法", ["arbor-agent-ideate", "arbor-agent-coordinator"]),
            ("执行", ["arbor-agent-executor", "arbor-agent-orchestrator"]),
            ("验证", ["arbor-agent-merge-eval", "arbor-agent-search", "fable-judge"]),
            ("报告", ["arbor-agent-resume-report", "session-report", "litreview"]),
        ],
        "engine": "Arbor 11 件套 + dsh",
        "note": "研发子公司 05 号方向",
    },
    "PPT 制作": {
        "trigger": ["ppt", "幻灯片", "演示"],
        "pipeline": [
            ("构思", ["idea-refine", "brainstorming"]),
            ("制作", ["dragon-ppt-maker", "guizang-ppt-skill"]),
            ("设计", ["frontend-design", "minimalist-skill", "taste-skill-v1"]),
            ("美化", ["baoyu-slide-deck", "baoyu-infographic"]),
        ],
        "engine": "OpenClaw",
        "note": "归藏 PPT + dragon-ppt 双引擎",
    },
    "数据分析": {
        "trigger": ["分析", "报表", "数据", "财务", "指标"],
        "pipeline": [
            ("取数", ["sql-queries", "database-designer"]),
            ("分析", ["financial-analyst", "khazix-hv-analysis", "cohort-analysis"]),
            ("验证", ["ab-test-analysis", "saas-metrics-coach"]),
            ("汇报", ["baoyu-infographic", "session-report"]),
        ],
        "engine": "OpenClaw",
        "note": "财务+HV 双分析引擎",
    },
    "科研论文": {
        "trigger": ["论文", "科研", "学术", "paper", "研究课题", "投稿"],
        "pipeline": [
            ("选题", ["brainstorming-research-ideas", "creative-thinking-for-research", "idea-evaluator"]),
            ("研究", ["vibe-research-workflow", "0-autoresearch-skill", "research-manager"]),
            ("写作", ["paper-writer", "intro-drafter", "ml-paper-writing", "tech-paper-template"]),
            ("配图", ["figure-designer", "academic-plotting", "drawio-reconstruction"]),
            ("审查", ["pre-submission-reviewer", "rigor-reviewer"]),
            ("润色", ["paper-polish", "humanizer"]),
        ],
        "engine": "Supervisor-Skills + AI-Research-SKILLs",
        "note": "港科大导师经验 + ML 研究全链路",
    },
    "ML 工程": {
        "trigger": ["模型", "训练", "推理", "llm", "rag", "向量", "agent 开发", "微调"],
        "pipeline": [
            ("框架", ["langchain", "llamaindex", "crewai", "dspy"]),
            ("数据", ["sentence-transformers", "qdrant"]),
            ("优化", ["flash-attention", "long-context", "model-merging", "speculative-decoding"]),
            ("部署", ["vllm", "lm-evaluation-harness"]),
        ],
        "engine": "AI-Research-SKILLs(98 全库)",
        "note": "ML 全领域技能库, 98 个入库可查",
    },
}


def find_packs(task: str) -> list:
    """任务→匹配的组合包"""
    task_l = task.lower()
    hits = []
    for name, pack in COMBO_PACKS.items():
        n = sum(1 for t in pack["trigger"] if t.lower() in task_l)
        if n > 0:
            hits.append((n, name, pack))
    hits.sort(reverse=True)
    return [(n, name, p) for n, name, p in hits]


def pack_info(name: str, verbose: bool = False) -> dict:
    """
    pack info.
    
    Args:
        name: name.
        verbose: enable verbose output.
    
    Returns:
        Result of the operation.
    """
    pack = COMBO_PACKS[name]
    info = {"pack": name, "trigger": pack["trigger"], "engine": pack["engine"], "note": pack["note"]}
    if verbose:
        info["pipeline"] = pack["pipeline"]
    else:
        info["steps"] = [s[0] for s in pack["pipeline"]]
        all_skills = [sk for _, skills in pack["pipeline"] for sk in skills]
        info["skills"] = all_skills
        info["skill_count"] = len(all_skills)
    return info


def main_pack(args) -> int:
    """
    main pack.
    
    Args:
        args: positional arguments.
    
    Returns:
        Result of the operation.
    """
    if not args.task:
        print("📦 场景组合包清单:")
        for name, pack in COMBO_PACKS.items():
            steps = " → ".join(s[0] for s in pack["pipeline"])
            print(f"  📦 {name}: {steps}")
            print(f"     引擎: {pack['engine']}")
        print(f"\n共 {len(COMBO_PACKS)} 个组合包。查某个: skill-matrix.py pack --task \"公众号\"")
        return 0
    hits = find_packs(args.task)
    if not hits:
        print(f"无匹配组合包: {args.task}")
        return 1
    for _, name, _ in hits:
        print(json.dumps(pack_info(name, verbose=args.verbose), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    # 与 skill-matrix.py 主程序共存时由主程序调用;独立运行时提供 pack 功能
    ap = argparse.ArgumentParser(description="明月调度矩阵组合包")
    ap.add_argument("--task", default="")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    sys.exit(main_pack(args))