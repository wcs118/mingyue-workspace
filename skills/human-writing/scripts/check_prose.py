#!/usr/bin/env python3
"""检查中文成稿的硬禁令与常见模型化形状。只报警,不自动改文。"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from dataclasses import dataclass
from pathlib import Path


HARD_STOPS = (
    "说白了",
    "说穿了",
    "先说结论",
)

HARD_JARGON = (
    "赋能",
    "抓手",
    "商业闭环",
    "价值闭环",
    "能力沉淀",
    "拉通",
    "底层逻辑",
    "顶层设计",
    "认知跃迁",
    "价值释放",
    "颗粒度",
    "组合拳",
    "护城河",
    "第二曲线",
    "降维打击",
    "心智",
    "链路",
    "闭环",
    "对齐",
    "共建",
    "生态位",
    "飞轮",
    "模型腔",
)

# 翻案腔模式
PATTERNS = (
    re.compile(r"不是[^。]{2,20}而是"),
    re.compile(r"并非[^。]{2,20}而是"),
    re.compile(r"不在于[^。]{2,20}而在于"),
    re.compile(r"与其说[^。]{2,20}不如说"),
    re.compile(r"表面[^。]{2,20}实际"),
    re.compile(r"看似[^。]{2,20}实则"),
    re.compile(r"你以为[^。]{2,20}其实"),
    re.compile(r"回头才发现"),
    re.compile(r"答案恰恰相反"),
)

DASH = re.compile(r"[—–]")
PROMPT_COLON = re.compile(r"(一句话总结|核心是|重点是|关键在于|总结一下)[:：]")


def check_text(text: str) -> list[str]:
    issues: list[str] = []
    for pat in PATTERNS:
        for m in pat.finditer(text):
            issues.append(f"翻案腔: {m.group(0)}")
    for word in HARD_STOPS:
        if word in text:
            issues.append(f"口头黑话: {word}")
    for word in HARD_JARGON:
        if word in text:
            issues.append(f"商业黑话: {word}")
    if DASH.search(text):
        issues.append("破折号: 出现 — 或 –")
    for m in PROMPT_COLON.finditer(text):
        issues.append(f"提示性冒号: {m.group(0)}")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="检查中文成稿禁词")
    ap.add_argument("path", nargs="?", help="稿件路径")
    ap.add_argument("--stdin", action="store_true", help="从标准输入读取")
    args = ap.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.path:
        text = Path(args.path).read_text(encoding="utf-8")
    else:
        ap.print_help()
        return 2

    issues = check_text(text)
    if issues:
        print(f"发现 {len(issues)} 处问题:")
        for i in issues:
            print(f"  - {i}")
        return 1
    print("OK: 未发现硬禁令命中。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
