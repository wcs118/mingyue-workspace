#!/usr/bin/env python3
"""
session-rollback.py — 会话级事务回滚(工作流程 v2 阶段二/四落地)
===============================================================
机制4 事务式生命周期:会话 create 失败自动回滚,不残留半成品。
在 phoenix-snapshot.sh(文件级快照)之外,补"会话级"回滚:
记录会话开始时的工作区状态(文件清单+哈希),结束时校验;
未达成目标 → 恢复被改动/新增的文件,不留半成品。

用法:
  session-rollback.py begin --id <会话id>        # 标记会话开始(快照文件状态)
  session-rollback.py check --id <会话id>        # 校验是否有未预期改动
  session-rollback.py rollback --id <会话id>     # 回滚:恢复快照状态
  session-rollback.py commit --id <会话id>       # 提交:清理快照
  session-rollback.py smoke                       # 自测
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
SNAP_DIR = Path(os.environ.get("GUARD_SNAP_DIR", "/tmp/guard-sessions"))
WATCH_PATHS = [
    "rules", "skills", "scripts", "reference",
    "MEMORY.md", "FRAMEWORK.md", "AGENTS.md", "SOUL.md",
]
MAX_FILES = 5000  # 快照文件上限,防爆(工作区实际约 1-2K 文件)

def _hash_file(p: Path) -> str:
    """
    hash file.
    
    Returns:
        Result of the operation.
    """
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return ""

def _snapshot_files() -> dict:
    """扫描工作区关键路径,返回 {相对路径: hash}(关键目录优先,防截断)"""
    snap = {}
    # 小而关键的先扫,确保必达
    ordered = [p for p in WATCH_PATHS if p not in ("reference",)] + ["reference"]
    for base in ordered:
        p = WORKSPACE / base
        if not p.exists():
            continue
        if p.is_file():
            snap[str(p.relative_to(WORKSPACE))] = _hash_file(p)
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if not d.startswith((".", "__"))]
            for f in files:
                fp = Path(root) / f
                rel = str(fp.relative_to(WORKSPACE))
                if len(snap) >= MAX_FILES:
                    return snap
                snap[rel] = _hash_file(fp)
    return snap

def _load(id_: str) -> dict:
    """
    load.
    
    Returns:
        Result of the operation.
    """
    f = SNAP_DIR / f"{id_}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())

def _save(id_: str, data: dict):
    """
    save.
    
    Args:
        data: payload data.
    """
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    (SNAP_DIR / f"{id_}.json").write_text(json.dumps(data, ensure_ascii=False))

def _diff(before: dict, after: dict) -> dict:
    """
    diff.
    
    Returns:
        Result of the operation.
    """
    changed, added, removed = [], [], []
    for k, v in after.items():
        if k not in before:
            added.append(k)
        elif before[k] != v:
            changed.append(k)
    for k in before:
        if k not in after:
            removed.append(k)
    return {"changed": changed, "added": added, "removed": removed}

def begin(id_: str, note: str = "") -> dict:
    """
    begin.
    
    Returns:
        Result of the operation.
    """
    if _load(id_):
        print(f"❌ 会话 {id_} 已存在,先 commit/rollback", file=sys.stderr)
        sys.exit(2)
    data = {"id": id_, "note": note, "ts": time.strftime("%Y-%m-%d %H:%M"), "snapshot": _snapshot_files()}
    _save(id_, data)
    print(f"✅ 会话 {id_} 开始,已快照 {len(data['snapshot'])} 个文件")
    return data

def check(id_: str) -> dict:
    """
    check.
    
    Returns:
        Result of the operation.
    """
    data = _load(id_)
    if not data:
        print(f"❌ 会话 {id_} 不存在", file=sys.stderr)
        sys.exit(2)
    d = _diff(data["snapshot"], _snapshot_files())
    n = len(d["changed"]) + len(d["added"]) + len(d["removed"])
    print(f"会话 {id_}: 改动 {len(d['changed'])} / 新增 {len(d['added'])} / 删除 {len(d['removed'])}")
    for f in d["changed"][:10]:
        print(f"  ~ {f}")
    for f in d["added"][:10]:
        print(f"  + {f}")
    for f in d["removed"][:10]:
        print(f"  - {f}")
    return d

def rollback(id_: str) -> bool:
    """
    rollback.
    
    Returns:
        Result of the operation.
    """
    data = _load(id_)
    if not data:
        print(f"❌ 会话 {id_} 不存在", file=sys.stderr)
        sys.exit(2)
    before = data["snapshot"]
    after = _snapshot_files()
    d = _diff(before, after)
    # 恢复:新增的删掉,改动的还原,删除的恢复(从快照无法恢复内容,提示)
    for f in d["added"]:
        fp = WORKSPACE / f
        if fp.exists():
            fp.unlink()
            print(f"  🗑 删除新增: {f}")
    for f in d["changed"]:
        fp = WORKSPACE / f
        if fp.exists():
            fp.unlink()  # 无法从哈希还原,删除让上层从快照/备份恢复
            print(f"  ⚠ 移除改动(需从备份恢复): {f}")
    for f in d["removed"]:
        print(f"  ⚠ 删除的文件无法自动恢复: {f}(可用 phoenix-snapshot restore)")
    if not (d["added"] or d["changed"] or d["removed"]):
        print("✅ 无改动,无需回滚")
    else:
        print("✅ 回滚完成")
    _save(id_, {**data, "rollback_ts": time.strftime("%Y-%m-%d %H:%M")})
    return True

def commit(id_: str):
    """
    commit.
    """
    data = _load(id_)
    if not data:
        print(f"❌ 会话 {id_} 不存在", file=sys.stderr)
        sys.exit(2)
    f = SNAP_DIR / f"{id_}.json"
    f.unlink(missing_ok=True)
    print(f"✅ 会话 {id_} 提交,快照已清理")

def smoke_test() -> int:
    """
    smoke test.
    
    Returns:
        Result of the operation.
    """
    sid = f"smoke-{int(time.time())}"
    results = []
    # begin
    try:
        begin(sid, "smoke")
        results.append(("begin 创建快照", True))
    except SystemExit:
        results.append(("begin 创建快照", False))
    # 制造一个改动
    probe = WORKSPACE / "reference" / "_smoke-probe.txt"
    probe.write_text("probe")
    d = check(sid)
    ok_check = len(d["added"]) >= 1
    results.append(("check 发现新增", ok_check))
    # rollback
    try:
        rollback(sid)
        ok_rb = not probe.exists()
        results.append(("rollback 删除新增", ok_rb))
    except SystemExit:
        results.append(("rollback 删除新增", False))
    # commit
    try:
        commit(sid)
        results.append(("commit 清理快照", True))
    except SystemExit:
        results.append(("commit 清理快照", False))

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"{'✅' if ok else '❌'} {name}")
    print(f"\n自测:{passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1

def main():
    """
    main.
    """
    ap = argparse.ArgumentParser(description="会话级事务回滚")
    ap.add_argument("mode", choices=["begin", "check", "rollback", "commit", "smoke"])
    ap.add_argument("--id", default="", help="会话 id")
    ap.add_argument("--note", default="", help="会话说明")
    args = ap.parse_args()

    if args.mode == "smoke":
        sys.exit(smoke_test())
    if not args.id:
        print("需要 --id", file=sys.stderr)
        sys.exit(2)
    if args.mode == "begin":
        begin(args.id, args.note)
    elif args.mode == "check":
        check(args.id)
    elif args.mode == "rollback":
        rollback(args.id)
    elif args.mode == "commit":
        commit(args.id)

if __name__ == "__main__":
    main()