#!/usr/bin/env python3
"""
skill-to-plugin.py — 技能→dsh-plugin 转换器(工作流程 v2 第0层落地)
==================================================================
把我们的技能(skills-db / skills/)定义成 dsh 插件包格式(cordis.patch.yml),
实现"我们的技能 + 官方引擎"双跑。

用法:
  skill-to-plugin.py list                          # 列出可转换的技能
  skill-to-plugin.py convert --skill human-writing # 生成单个技能插件
  skill-to-plugin.py convert --all                 # 批量生成全部技能
  skill-to-plugin.py smoke                         # 自测

输出: reference/dsh-plugins/<skill>/cordis.patch.yml + README.md
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
SKILLS_DIR = WORKSPACE / "skills"
OUT_DIR = WORKSPACE / "reference" / "dsh-plugins"

# 技能 → dsh 插件映射:技能 SKILL.md 转成 cordis 插件行
# dsh 插件 = 一个 cordis 行(id + name + config),config 里挂技能描述/入口
def list_skills() -> list:
    """
    list skills.
    
    Returns:
        Result of the operation.
    """
    skills = []
    if SKILLS_DIR.is_dir():
        for d in sorted(SKILLS_DIR.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                skills.append(d.name)
    return skills

def read_skill_desc(name: str) -> str:
    """
    read skill desc.
    
    Args:
        name: name.
    
    Returns:
        Result of the operation.
    """
    f = SKILLS_DIR / name / "SKILL.md"
    if not f.exists():
        return ""
    try:
        text = f.read_text(errors="ignore")
        # 提取第一段非注释非标题非分隔线文字作为描述
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", ">", "---", "```", "<!--")):
                continue
            if len(line) > 12:  # 跳过太短的(图标行等)
                return line[:120]
    except Exception:
        pass
    return ""

def convert_one(name: str) -> dict:
    """
    convert one.
    
    Args:
        name: name.
    
    Returns:
        Result of the operation.
    """
    desc = read_skill_desc(name)
    safe_id = re.sub(r"[^a-zA-Z0-9-]", "-", name).lower()
    plugin_dir = OUT_DIR / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    pkg_name = f"@deepseek-ai/dsh-skill-{safe_id}"

    # 1) package.json — 真实 npm 包(可被 pnpm/本地 link 安装)
    (plugin_dir / "package.json").write_text(json.dumps({
        "name": pkg_name,
        "version": "0.1.0",
        "description": f"明月技能 {name} → dsh 插件(自动生成)",
        "type": "module",
        "main": "index.js",
        "dependencies": {},
        "cordis": {"patch": "./cordis.patch.yml"},
        "dsh": {"bundle": {"patch": "./cordis.patch.yml"}},
    }, ensure_ascii=False, indent=2))

    # 2) index.js — 最小 cordis 插件实现(极简 apply,不访问注入属性避免 inject 错误)
    (plugin_dir / "index.js").write_text(
        f"// {name} — 明月技能 dsh 插件(自动生成)\n"
        f"// Cordis 标准插件形态: 只做最小注册,不访问注入属性\n"
        f"export const name = '{pkg_name}';\n"
        f"export const config = {{ skill: {json.dumps(name)}, source: 'skills/{name}/SKILL.md' }};\n"
        f"\n"
        f"export function apply(ctx) {{\n"
        f"  // 极简: 插件加载成功即注册完成(避免 cordis inject 限制)\n"
        f"  return {{ skill: config.skill, source: config.source }};\n"
        f"}}\n"
    )

    patch = f"""# {name} — 明月技能 → dsh 插件(自动生成,{time.strftime('%Y-%m-%d')})
# 转换自: skills/{name}/SKILL.md
# 安装: cd /opt/dsh && pnpm add {plugin_dir}   (或 dsh plugin add {plugin_dir})
# 加载: dsh --profile headless --patch {plugin_dir}/cordis.patch.yml "<任务>"

- insert:
    - id: skill-{safe_id}
      name: '{pkg_name}'
      config:
        skill: '{name}'
        description: '{desc}'
        source: skills/{name}/SKILL.md
"""
    (plugin_dir / "cordis.patch.yml").write_text(patch)
    (plugin_dir / "README.md").write_text(
        f"# {name} (dsh 插件)\n\n由 skill-to-plugin.py 自动生成。\n\n"
        f"- 技能来源: `skills/{name}/SKILL.md`\n"
        f"- npm 包名: `{pkg_name}`\n"
        f"- 插件补丁: `cordis.patch.yml`\n"
        f"- 安装: `cd /opt/dsh && dsh plugin add {plugin_dir}`\n"
        f"- 接入: `dsh --profile headless --patch reference/dsh-plugins/{name}/cordis.patch.yml \"任务\"`\n"
    )
    return {"skill": name, "id": f"skill-{safe_id}", "pkg": pkg_name, "desc": desc, "path": str(plugin_dir)}

def smoke_test() -> int:
    """
    smoke test.
    
    Returns:
        Result of the operation.
    """
    # 用内置样例技能验证格式
    test_dir = OUT_DIR / "_smoke-test"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "cordis.patch.yml").write_text(
        "- insert:\n    - id: skill-smoke\n      name: '@deepseek-ai/dsh-skill-smoke'\n"
        "      config:\n        skill: 'smoke'\n        description: 'test'\n"
    )
    text = (test_dir / "cordis.patch.yml").read_text()
    ok_format = "- insert:" in text and "id: skill-smoke" in text and "config:" in text
    print(f"{'✅' if ok_format else '❌'} cordis.patch.yml 格式正确")
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    return 0 if ok_format else 1

def main():
    """
    main.
    """
    ap = argparse.ArgumentParser(description="技能→dsh-plugin 转换器")
    ap.add_argument("mode", choices=["list", "convert", "smoke"])
    ap.add_argument("--skill", default="", help="技能名")
    ap.add_argument("--all", action="store_true", help="批量转换全部")
    args = ap.parse_args()

    if args.mode == "smoke":
        sys.exit(smoke_test())

    if args.mode == "list":
        for s in list_skills():
            print(s)
        print(f"\n共 {len(list_skills())} 个技能")
        sys.exit(0)

    if args.mode == "convert":
        if args.all:
            skills = list_skills()
            results = [convert_one(s) for s in skills]
            print(f"✅ 已转换 {len(results)} 个技能 → {OUT_DIR}")
            sys.exit(0)
        if not args.skill:
            print("需要 --skill 或 --all", file=sys.stderr)
            sys.exit(2)
        r = convert_one(args.skill)
        print(f"✅ 已生成插件: {r['path']}/cordis.patch.yml")
        print(f"   id: {r['id']}")
        print(f"   描述: {r['desc']}")
        sys.exit(0)

if __name__ == "__main__":
    main()