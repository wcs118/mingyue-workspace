#!/usr/bin/env python3
"""
scope-router.py — 任务→工具集自动映射(工作流程 v2 阶段一落地)
==============================================================
把 rules/path-routing.md 的风险等级(L0-L3)固化成代码:任务进来自动定级、
自动映射可见工具集(机制2 作用域注册),并交给 guard-exec.py 做守卫链。

用法:
  scope-router.py route --task "备份数据库"            # 自动定级+映射工具集
  scope-router.py route --task "删除旧文件" --risk L3   # 手动指定等级
  scope-router.py smoke                                 # 自测

输出 JSON: {"risk": "L1", "allow": [...], "deny": [...], "reason": "..."}
"""

import argparse
import json
import re
import sys

# ---------- 风险等级(L0-L3,来自 rules/path-routing.md) ----------
RISK_RULES = [
    # (等级, 关键词, 说明)
    ("L3", ["删除", "rm ", "trash", "格式化", "不可逆", "清空", "drop", "delete from", "外发", "发送邮件", "发布", "转账", "支付"], "删除/外部发送/不可逆 → 暂停确认"),
    ("L2", ["改配置", "修改配置", "改脚本", "cron", "定时任务", "systemctl", "ufw", "防火墙", "nginx", "systemd", "改规则", "更新规则", "安装", "卸载"], "改配置/脚本/定时任务 → 快照+验证+记录"),
    ("L1", ["写", "新建", "创建文件", "生成", "编写", "更新文档", "修改文档", "整理", "重构", "commit", "push"], "写新文件/改文档 → 做完快照"),
    ("L0", ["查", "看", "搜索", "读取", "列出", "检查", "状态", "status", "巡检", "盘点", "查询", "list", "grep", "cat ", "ls "], "只读 → 直接做"),
]

# 各等级工具集(映射到 guard-exec 的作用域)
RISK_TOOLS = {
    "L0": {"allow": ["ls", "cat", "grep", "find", "head", "tail", "wc", "df", "free", "ps", "date", "pwd", "echo", "git status", "git log"], "deny": []},
    "L1": {"allow": ["ls", "cat", "grep", "find", "head", "tail", "wc", "df", "free", "ps", "date", "pwd", "echo", "mkdir", "touch", "git add", "git commit", "git push", "python3", "bash"], "deny": ["rm", "dd", "mkfs"]},
    "L2": {"allow": ["*"], "deny": ["rm", "dd", "mkfs", "shutdown", "reboot", "kill -9"]},
    "L3": {"allow": [], "deny": ["*"]},  # 全禁,需人工确认
}

def classify_risk(task: str) -> tuple:
    """按关键词命中最高等级"""
    task_l = task.lower()
    for risk, kws, reason in RISK_RULES:  # 已按 L3→L0 排序
        for kw in kws:
            if kw.lower() in task_l:
                return risk, reason
    return "L0", "未命中关键词,默认只读"

def route(task: str, risk_override: str = None) -> dict:
    """
    route.
    
    Returns:
        Result of the operation.
    """
    risk, reason = classify_risk(task) if not risk_override else (risk_override.upper(), "手动指定")
    if risk not in RISK_TOOLS:
        risk = "L0"
    tools = RISK_TOOLS[risk]
    return {
        "risk": risk,
        "allow": tools["allow"],
        "deny": tools["deny"],
        "reason": reason,
    }

def smoke_test() -> int:
    """
    smoke test.
    
    Returns:
        Result of the operation.
    """
    cases = [
        ("查一下磁盘空间", "L0"),
        ("写一份周报文档", "L1"),
        ("改一下 cron 定时任务", "L2"),
        ("删除旧的备份文件", "L3"),
        ("检查 gateway 状态", "L0"),
        ("重构 skills-db 索引", "L1"),
    ]
    passed = failed = 0
    for task, expect in cases:
        r = route(task)
        ok = r["risk"] == expect
        print(f"{'✅' if ok else '❌'} {task!r} → {r['risk']}(期望 {expect})")
        passed += ok; failed += (not ok)
    print(f"\n自测:{passed} 通过 / {failed} 失败")
    return 0 if failed == 0 else 1

def main():
    """
    main.
    """
    ap = argparse.ArgumentParser(description="任务→工具集自动映射")
    ap.add_argument("mode", choices=["route", "smoke"])
    ap.add_argument("--task", default="", help="任务描述")
    ap.add_argument("--risk", default=None, help="手动指定风险等级 L0-L3")
    args = ap.parse_args()

    if args.mode == "smoke":
        sys.exit(smoke_test())

    if not args.task:
        print("需要 --task 参数", file=sys.stderr)
        sys.exit(2)
    r = route(args.task, args.risk)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()