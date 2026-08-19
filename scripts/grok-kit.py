#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grok-kit.py v2.0 — Grok 编码智能体全能力自研封装(明月系核心资产)
=====================================================================
老板指令(2026-08-17): 百分百写成自己的代码, 能力写全, 实测才算数。
Grok = xAI 的编码 agent。我们无 XAI key(被封锁), 但有模型无关内核:
默认 DeepSeek 驱动(免费优先), 有 XAI_API_KEY 自动切真 Grok。

覆盖能力面(9 命令):
  run        任务闭环(理解→计划→执行→观察→迭代→完成)
  plan       只出计划(不执行)
  verify     验证前置(语法检查+试运行+带参重试)
  report     交付报告(RESULT.md)
  session    会话持久化(多轮任务续跑)
  sandbox    沙箱安全(白名单/黑名单/危险拦截)
  tools      工具自检(六件套是否可用)
  models     驱动模型信息
  doctor     全链路自检

工具六件套(全部自研): list_dir / read_file / write_file / edit_file / grep / run

用法:
  python3 grok-kit.py run "写个脚本并验证" [--cwd 目录] [--model xxx] [--rounds 12]
  python3 grok-kit.py plan "任务" | verify [目录] | report [目录]
  python3 grok-kit.py session list|show|clear
  python3 grok-kit.py sandbox "rm -rf /"  # 演示拦截
  python3 grok-kit.py doctor
"""

import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.request
import urllib.error

VERSION = "2.0.0"
SESS_DIR = os.path.expanduser("~/.openclaw/workspace/data/grok-sessions")


# ═══════════════════════════════════════════════════════════
# 一、端点探测与密钥
# ═══════════════════════════════════════════════════════════
def load_env():
    try:
        return json.load(open(os.path.expanduser("~/.openclaw/openclaw.json"))).get("env", {})
    except Exception:
        return {}


def detect():
    """返回 (base_url, key, model)"""
    xai = os.environ.get("XAI_API_KEY", "") or load_env().get("XAI_API_KEY", "")
    if xai:
        return "https://api.x.ai/v1", xai, "grok-4"
    ds = os.environ.get("DEEPSEEK_API_KEY", "") or load_env().get("DEEPSEEK_API_KEY", "")
    if ds:
        return "https://api.deepseek.com/v1", ds, "deepseek-v4-flash"
    ds2 = os.environ.get("DASHSCOPE_API_KEY", "") or load_env().get("DASHSCOPE_API_KEY", "")
    if ds2:
        return "https://dashscope.aliyuncs.com/compatible-mode/v1", ds2, "qwen3-coder-plus"
    sys.exit("❌ 无可用 key: XAI_API_KEY(真grok) / DEEPSEEK_API_KEY(推荐代理) / DASHSCOPE_API_KEY")


def http_post(url, payload, key, retries=4):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST")
    for i in range(retries):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=180).read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                wait = [2, 5, 12, 20][i]
                print(f"⚠️ HTTP {e.code}, {wait}s 重试", file=sys.stderr)
                time.sleep(wait)
                continue
            sys.exit(f"❌ HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            if i < retries - 1:
                time.sleep(2)
                continue
            sys.exit(f"❌ 网络: {e}")


def chat(messages, tools=None, model=None, max_tokens=8192):
    base, key, default = detect()
    model = model or default
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if tools:
        payload["tools"] = tools
    data = http_post(base.rstrip("/") + "/chat/completions", payload, key)
    return data, model


# ═══════════════════════════════════════════════════════════
# 二、工具定义(模型可见的 function schema)
# ═══════════════════════════════════════════════════════════
TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "list_dir", "description": "列出目录内容",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "读取文件(最多3000字符)",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "写入文件(覆盖, 自动建目录)",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "精准替换文件片段",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}}},
    {"type": "function", "function": {"name": "grep", "description": "搜索文件内容",
     "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern", "path"]}}},
    {"type": "function", "function": {"name": "run", "description": "执行命令(白名单内)",
     "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
]

# 命令白名单
WHITELIST = {"python3", "python", "ls", "cat", "head", "tail", "grep", "find", "mkdir",
             "touch", "echo", "pwd", "wc", "cp", "mv", "git", "node", "bash", "sh",
             "diff", "date", "chmod", "file", "tar", "sort", "uniq", "sleep", "printf"}

# 危险命令黑名单(永不执行)
DANGER_PATTERNS = [
    r"rm\s+-rf\s+[/~]", r"rm\s+-fr\s+[/~]", r"rm\s+-rf\s+--no-preserve-root",
    r"mkfs", r"dd\s+if=", r"shutdown", r"reboot", r"halt", r"poweroff",
    r":\(\)\s*\{", r">\s*/dev/sd", r"chmod\s+777\s+/", r"sudo\s+rm",
    r"curl[^|]*\|\s*(ba)?sh", r"wget[^|]*\|\s*(ba)?sh", r"mv\s+/\s+/",
]


def do_tool(name, args, cwd):
    """工具执行(全部自研)"""
    if name == "list_dir":
        try:
            items = sorted(os.listdir(args.get("path", ".")))
            return "\n".join(items[:80]) or "(空目录)"
        except Exception as e:
            return f"❌ {e}"
    if name == "read_file":
        try:
            with open(args.get("path", ""), encoding="utf-8", errors="replace") as f:
                return f.read()[:3000]
        except Exception as e:
            return f"❌ {e}"
    if name == "write_file":
        try:
            p = args.get("path", "")
            os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(args.get("content", ""))
            return f"✅ 已写入 {p} ({len(args.get('content',''))} 字符)"
        except Exception as e:
            return f"❌ {e}"
    if name == "edit_file":
        try:
            p, o, n = args.get("path", ""), args.get("old", ""), args.get("new", "")
            with open(p, encoding="utf-8") as f:
                s = f.read()
            if o not in s:
                return f"❌ 未找到: {o[:60]}"
            with open(p, "w", encoding="utf-8") as f:
                f.write(s.replace(o, n, 1))
            return f"✅ 已替换 {p}"
        except Exception as e:
            return f"❌ {e}"
    if name == "grep":
        try:
            r = subprocess.run(["grep", "-rn", args.get("pattern", ""), args.get("path", ".")],
                               capture_output=True, text=True, timeout=30)
            return (r.stdout or "(无匹配)")[:2000]
        except Exception as e:
            return f"❌ {e}"
    if name == "run":
        return safe_run(args.get("command", ""), cwd)
    return f"❌ 未知工具 {name}"


def safe_run(cmd, cwd):
    """白名单+黑名单双重校验"""
    for pat in DANGER_PATTERNS:
        if re.search(pat, cmd):
            return f"🚫 危险命令拦截(规则 /{pat}/)"
    try:
        parts = shlex.split(cmd)
    except Exception as e:
        return f"❌ 命令解析失败: {e}"
    if not parts:
        return "(空命令)"
    prog = os.path.basename(parts[0])
    if prog not in WHITELIST:
        return f"🚫 '{prog}' 不在白名单\n白名单: {sorted(WHITELIST)}"
    try:
        r = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=60)
        out = (r.stdout or "")[:3000]
        err = (r.stderr or "")[:800]
        if r.returncode != 0:
            return f"(退出码 {r.returncode})\n{out}\n⚠️ {err}"
        return out or "(执行成功, 无输出)"
    except subprocess.TimeoutExpired:
        return "⏰ 超时(60s)"
    except Exception as e:
        return f"❌ {e}"


# ═══════════════════════════════════════════════════════════
# 三、run 任务闭环
# ═══════════════════════════════════════════════════════════
SYSTEM_PROMPT = """你是 Grok 风格编码智能体(明月自研 grok-kit v2.0 驱动)。
工作方式:
1. 理解任务 → 拆解步骤 → 规划文件
2. 用工具执行: 写文件 → 运行 → 看结果 → 修复
3. 失败就分析原因再试, 不要放弃
4. 完成后用 run 验证产物, 拿到证据
5. 最后一步不调工具, 输出交付说明(做了什么/验证证据/如何运行)
规则: 只调用可用工具; 写文件用 write_file; 改文件用 edit_file;
运行脚本用 run("python3 xxx.py") 并查看输出。全部中文回答。"""


def cmd_run(args):
    opts, pos = parse(args, {"--cwd": 1, "--model": 1, "--rounds": 1, "--session": 1})
    task = " ".join(pos).strip()
    if not task:
        sys.exit("用法: grok-kit.py run <任务> [--cwd 目录] [--session 会话名]")
    cwd = os.path.abspath(opts.get("--cwd", os.getcwd()))
    os.makedirs(cwd, exist_ok=True)
    model = opts.get("--model")
    rounds = int(opts.get("--rounds", "12"))
    session = opts.get("--session")
    base, key, real_model = detect()
    model = model or real_model
    print(f"🤖 grok-kit | 驱动: {model} @ {base}")
    print(f"📁 {cwd}\n📋 {task}")

    # 会话续跑: 恢复历史
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if session:
        p = sess_path(session)
        if os.path.isfile(p):
            hist = json.load(open(p))
            msgs.extend(hist.get("messages", []))
            print(f"🔄 恢复会话 {session} ({len(hist.get('messages', []))} 条历史)")
    msgs.append({"role": "user", "content": f"任务: {task}\n目录: {cwd}"})

    for rnd in range(1, rounds + 1):
        print(f"━━━ 第 {rnd}/{rounds} 轮 ━━━")
        data, _ = chat(msgs, tools=TOOL_SCHEMAS, model=model)
        msg = data["choices"][0]["message"]
        if msg.get("content"):
            print(f"💬 {msg['content'][:200]}")
        tcs = msg.get("tool_calls")
        if not tcs:
            print("\n🔍 验证产物:")
            v = verify(cwd)
            print(v)
            if session:
                save_sess(session, msgs + [msg])
            return {"done": True, "rounds": rnd, "verify": v}
        msgs.append(msg)
        for tc in tcs:
            try:
                a = json.loads(tc["function"]["arguments"] or "{}")
            except Exception:
                a = {}
            print(f"  🔧 {tc['function']['name']}({json.dumps(a, ensure_ascii=False)[:80]})")
            r = do_tool(tc["function"]["name"], a, cwd)
            print(f"     ↳ {r[:120]}")
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": r})
        # 每轮存会话(断点续跑)
        if session:
            save_sess(session, msgs)
    print("⚠️ 轮数用尽")
    if session:
        save_sess(session, msgs)
    return {"done": False}


# ═══════════════════════════════════════════════════════════
# 四、verify 验证
# ═══════════════════════════════════════════════════════════
def verify(cwd):
    out = []
    pys = [f for f in os.listdir(cwd) if f.endswith(".py")][:3]
    if not pys:
        return "⚠️ 无 python 产物(检查目录)"
    for pf in pys:
        p = os.path.join(cwd, pf)
        r = subprocess.run(["python3", "-m", "py_compile", p], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            out.append(f"✅ 语法OK: {pf}")
            r2 = subprocess.run(["python3", p], capture_output=True, text=True, timeout=30)
            if r2.returncode != 0:
                r2 = subprocess.run(["python3", p, "10"], capture_output=True, text=True, timeout=30)
            if r2.returncode == 0:
                out.append(f"✅ 运行OK: {pf} → {r2.stdout.strip()[:100]}")
            else:
                out.append(f"⚠️ 退出{r2.returncode}: {r2.stderr.strip()[:100]}")
        else:
            out.append(f"❌ 语法错: {pf}: {r.stderr[:100]}")
    return "\n".join(out)


# ═══════════════════════════════════════════════════════════
# 五、session 会话持久化
# ═══════════════════════════════════════════════════════════
def sess_path(name):
    os.makedirs(SESS_DIR, exist_ok=True)
    return os.path.join(SESS_DIR, f"{name}.json")


def save_sess(name, msgs):
    p = sess_path(name)
    json.dump({"messages": msgs[-20:], "updated": time.strftime("%Y-%m-%d %H:%M")},
              open(p, "w"), ensure_ascii=False, indent=2)


def cmd_session(args):
    if not args:
        sys.exit("用法: grok-kit.py session list|show <名>|clear <名>")
    act = args[0]
    if act == "list":
        if not os.path.isdir(SESS_DIR):
            print("(无会话)")
            return
        for f in sorted(os.listdir(SESS_DIR)):
            try:
                h = json.load(open(os.path.join(SESS_DIR, f)))
                print(f"  {f[:-5]}: {len(h.get('messages', []))} 条 | {h.get('updated', '?')}")
            except Exception:
                pass
    elif act == "show" and len(args) > 1:
        p = sess_path(args[1])
        if not os.path.isfile(p):
            sys.exit(f"❌ 会话 {args[1]} 不存在")
        h = json.load(open(p))
        for m in h.get("messages", [])[-8:]:
            role, c = m.get("role", "?"), (m.get("content") or "")[:100]
            print(f"  [{role}] {c}")
    elif act == "clear" and len(args) > 1:
        p = sess_path(args[1])
        if os.path.isfile(p):
            os.remove(p)
            print(f"🗑️ 已删除会话 {args[1]}")
        else:
            sys.exit(f"❌ 会话 {args[1]} 不存在")
    else:
        sys.exit("用法: session list | show <名> | clear <名>")


# ═══════════════════════════════════════════════════════════
# 六、plan / report / sandbox / models / doctor
# ═══════════════════════════════════════════════════════════
def cmd_verify(args):
    cwd = os.path.abspath(args[0]) if args else os.getcwd()
    print(verify(cwd))


def cmd_plan(args):
    task = " ".join(args).strip()
    if not task:
        sys.exit("用法: grok-kit.py plan <任务>")
    data, model = chat([
        {"role": "system", "content": "你是资深工程师。拆解任务为可执行步骤(每步: 做什么/建什么文件/如何验证)。只输出计划, 不执行。"},
        {"role": "user", "content": task}], max_tokens=2048)
    print(f"📋 计划({model}):\n{data['choices'][0]['message']['content']}")


def cmd_report(args):
    cwd = os.path.abspath(args[0]) if args else os.getcwd()
    lines = [f"# RESULT.md — grok-kit 交付报告",
             f"- 时间: {time.strftime('%Y-%m-%d %H:%M')}",
             f"- 目录: {cwd}", "", "## 交付物"]
    for f in sorted(os.listdir(cwd)):
        if not f.startswith("."):
            lines.append(f"- {f}")
    lines.append("\n## 验证")
    lines.append(verify(cwd))
    with open(os.path.join(cwd, "RESULT.md"), "w") as f:
        f.write("\n".join(lines))
    print(f"✅ 报告已生成: {cwd}/RESULT.md")


def cmd_sandbox(args):
    cmd = " ".join(args).strip() or "rm -rf /"
    print(f"🛡️ 沙箱测试命令: {cmd}")
    print(safe_run(cmd, os.getcwd()))


def cmd_models(args=None):
    base, key, model = detect()
    print(f"📦 grok-kit 驱动: {model} @ {base}")
    print("  (模型无关内核: 有 XAI_API_KEY 切真 Grok, 否则 DeepSeek 免费驱动)")


def cmd_tools(args=None):
    print("🔧 工具六件套(全部自研):")
    for t in TOOL_SCHEMAS:
        print(f"  - {t['function']['name']}: {t['function']['description']}")
    print("🛡️ 白名单:", len(WHITELIST), "个命令 | 黑名单:", len(DANGER_PATTERNS), "条规则")
    print("🧪 拦截测试: rm -rf / →", safe_run("rm -rf /", os.getcwd()))


def cmd_doctor(args=None):
    print(f"🔬 grok-kit v{VERSION} 自检")
    try:
        base, key, model = detect()
        print(f"  ✅ 驱动: {model} @ {base}")
    except SystemExit as e:
        print(f"  ❌ {e}")
        return
    print(f"  🔧 工具: {len(TOOL_SCHEMAS)} 个 | 白名单 {len(WHITELIST)} | 黑名单 {len(DANGER_PATTERNS)}")
    print("  🛡️ 沙箱拦截演示:")
    print(f"     {safe_run('rm -rf /', os.getcwd())}")
    try:
        data, _ = chat([{"role": "user", "content": "回复'连通'"}], max_tokens=10)
        print(f"  🧪 模型连通: ✅ {data['choices'][0]['message']['content'][:30]}")
    except SystemExit as e:
        print(f"  🧪 模型连通: ❌ {e}")


def parse(args, spec):
    opts, pos = {}, []
    i = 0
    while i < len(args):
        if args[i] in spec:
            opts[args[i]] = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        else:
            pos.append(args[i])
            i += 1
    return opts, pos


HELP = f"""grok-kit.py v{VERSION} — Grok 编码智能体全能力自研封装
  run "<任务>" [--cwd 目录] [--model xxx] [--rounds 12] [--session 会话名]
  plan "<任务>" | verify [目录] | report [目录]
  session list|show <名>|clear <名>
  sandbox "<命令>" | tools | models | doctor
"""

def main():
    if len(sys.argv) < 2:
        print(HELP)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    handlers = {
        "run": cmd_run, "plan": cmd_plan, "verify": cmd_verify, "report": cmd_report,
        "session": cmd_session, "sandbox": cmd_sandbox, "tools": cmd_tools,
        "models": cmd_models, "doctor": cmd_doctor,
    }
    fn = handlers.get(cmd)
    if not fn:
        sys.exit(f"❌ 未知命令: {cmd}\n可用: {list(handlers.keys())}")
    fn(args)

if __name__ == "__main__":
    main()
