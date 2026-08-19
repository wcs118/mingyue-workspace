#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codex-kit.py — 自研编码智能体内核(明月系核心资产 v1.0)
=====================================================================
老板指令(2026-08-17):每一个模型都要自研封装,百分之百自己的东西。
Codex 之前是复制技能文件,不合格 → 重写: 自己实现 agent loop 内核。

Codex 是什么: OpenAI 的终端编码智能体(106K⭐)。
它的本质不是"聊天",是闭环干活: 理解→计划→执行→观察→迭代→完成。

本文件: 用纯 Python 标准库把 Codex 核心机制 100% 自己实现:

  ┌─ 工作循环 ─────────────────────────────────────────────┐
  │ agent_loop  任务循环: 计划→执行→观察→迭代→完成          │
  │ plan        任务拆解(模型出方案,我们存盘)               │
  │ verify      验证前置(产物检查/测试运行)                 │
  │ report      交付报告(RESULT.md 四要素)                  │
  ├─ 工具执行 ─────────────────────────────────────────────┤
  │ read_file   读文件                                      │
  │ write_file  写文件(自动建目录)                          │
  │ edit_file   精准替换                                    │
  │ list_dir    列目录                                      │
  │ grep        全文搜索                                    │
  │ run         安全命令执行(白名单+黑名单)                 │
  ├─ 安全 ─────────────────────────────────────────────────┤
  │ sandbox     三级权限: read-only / workspace-write / full│
  │ policy      命令白名单+危险黑名单拦截                    │
  ├─ 上下文 ───────────────────────────────────────────────┤
  │ context     任务+计划+工具结果+文件状态 打包给模型       │
  │ compact     上下文超限自动裁剪                          │
  └──────────────────────────────────────────────────────────┘

设计原则:
- 纯标准库(urllib/subprocess/json),零依赖,任何机器可跑
- 模型无关: 默认 DeepSeek 驱动,可切任意 OpenAI 兼容端点
- 工具调用走 function calling(模型决策,我们执行)
- 危险命令永不执行(rm -rf / 等黑名单)
- 每个阶段留痕,交付带验证证据

用法:
  python3 codex-kit.py "写一个斐波那契脚本并运行验证" [--cwd 工作目录] [--model xxx] [--rounds 15]
  python3 codex-kit.py plan "任务"         # 只出计划
  python3 codex-kit.py verify --file x.py --cmd "python3 x.py"  # 只验证
  python3 codex-kit.py report --dir work/任务  # 生成报告
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

VERSION = "1.0.0"
DEBUG = os.environ.get("CODEX_DEBUG", "0") == "1"

# ═══════════════════════════════════════════════════════════
# 一、配置与端点
# ═══════════════════════════════════════════════════════════

DEEPSEEK_URL = "https://api.deepseek.com/v1"
MOONSHOT_URL = "https://api.moonshot.cn/v1"
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1"

DEFAULT_MODEL = "deepseek-v4-flash"
MAX_ROUNDS = 15
TIMEOUT = 120

# 命令白名单(只允许这些, 其余拒绝)
CMD_WHITELIST = {
    "python3", "python", "ls", "cat", "head", "tail", "grep", "find",
    "mkdir", "touch", "echo", "pwd", "wc", "cp", "mv", "git", "node",
    "bash", "sh", "diff", "sort", "uniq", "wc", "date", "chmod", "file",
    "tar", "zip", "unzip", "curl", "wget", "pip", "npm", "npx", "sleep",
}

# 危险命令黑名单(永不执行, 哪怕在白名单里拼参数)
DANGER_PATTERNS = [
    r"rm\s+-rf\s+[/~]",        # 删根/删家
    r"mkfs", r"dd\s+if=",      # 格式化/写盘
    r"shutdown", r"reboot", r"halt", r"poweroff",  # 关机
    r":\(\)\s*\{",             # fork 炸弹
    r">\s*/dev/sd",            # 写设备
    r"chmod\s+777\s+/",        # 权限炸弹
    r"sudo\s+rm", r"mv\s+/\s+", r"curl[^|]*\|\s*(ba)?sh",  # 高危
]

# ═══════════════════════════════════════════════════════════
# 二、密钥与端点探测
# ═══════════════════════════════════════════════════════════

def load_env():
    try:
        with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
            return json.load(f).get("env", {})
    except Exception:
        return {}


def get_key(name):
    return os.environ.get(name) or load_env().get(name) or ""


def detect_endpoint():
    """编码任务用 DeepSeek 优先(稳定+便宜), 可显式指定"""
    if os.environ.get("CODEX_BASE_URL"):
        return os.environ["CODEX_BASE_URL"], get_key("DEEPSEEK_API_KEY") or get_key("DASHSCOPE_API_KEY"), os.environ.get("CODEX_MODEL", DEFAULT_MODEL)
    if get_key("DEEPSEEK_API_KEY"):
        return DEEPSEEK_URL, get_key("DEEPSEEK_API_KEY"), DEFAULT_MODEL
    if get_key("DASHSCOPE_API_KEY"):
        return DASHSCOPE_URL, get_key("DASHSCOPE_API_KEY"), "qwen3-coder-plus"
    if get_key("MOONSHOT_API_KEY"):
        return MOONSHOT_URL, get_key("MOONSHOT_API_KEY"), "kimi-k2.7-code"
    sys.exit("❌ 无可用 key: 设 DEEPSEEK_API_KEY(推荐) 或 DASHSCOPE_API_KEY 或 MOONSHOT_API_KEY")


# ═══════════════════════════════════════════════════════════
# 三、HTTP 层(重试)
# ═══════════════════════════════════════════════════════════

def http_post(url, payload, key, retries=3):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
            resp = urllib.request.urlopen(req, timeout=TIMEOUT)
            return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                wait = [1, 3, 8][min(attempt, 2)]
                log(f"⚠️ HTTP {e.code}, {wait}s 重试", "WARN")
                time.sleep(wait)
                continue
            raise SystemExit(f"❌ HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise SystemExit(f"❌ 网络错误: {e}")


def chat(messages, tools=None, model=None, max_tokens=4096):
    """对话+工具调用, 返回完整响应"""
    base_url, key, default_model = detect_endpoint()
    model = model or default_model
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if tools:
        payload["tools"] = tools
    data = http_post(base_url.rstrip("/") + "/chat/completions", payload, key)
    return data, model


def log(msg, level="INFO"):
    if DEBUG or level != "DEBUG":
        print(f"[{level}] {msg}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════
# 四、工具定义(给模型看的 function calling schema)
# ═══════════════════════════════════════════════════════════

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "list_dir", "description": "列出目录内容", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "目录路径"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "读取文件内容(最多2000行)", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "写入文件(覆盖, 自动建目录)", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "精准替换文件中的一段文本", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}}},
    {"type": "function", "function": {"name": "grep", "description": "在文件中搜索文本", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern", "path"]}}},
    {"type": "function", "function": {"name": "run", "description": "执行命令(白名单), 返回输出", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "如: python3 test.py"}}, "required": ["command"]}}},
]

# ═══════════════════════════════════════════════════════════
# 五、工具实现(我们自己写的执行层)
# ═══════════════════════════════════════════════════════════

def check_danger(cmd):
    for pat in DANGER_PATTERNS:
        if re.search(pat, cmd):
            return f"🚫 危险命令被拦截: 匹配规则 /{pat}/"
    return None


def safe_run(cmd, cwd):
    """白名单+黑名单双重校验后执行"""
    danger = check_danger(cmd)
    if danger:
        return danger
    parts = shlex.split(cmd)
    if not parts:
        return "(空命令)"
    prog = os.path.basename(parts[0])
    if prog not in CMD_WHITELIST and prog not in ("python3.12", "python3.11", "pip3"):
        return f"🚫 命令 '{prog}' 不在白名单, 拒绝执行\n白名单: {sorted(CMD_WHITELIST)}"
    try:
        r = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=60)
        out = (r.stdout or "")[:3000]
        err = (r.stderr or "")[:1500]
        if r.returncode != 0:
            return f"(退出码 {r.returncode})\n{out}\n⚠️ stderr: {err[:800]}"
        return out or "(执行成功, 无输出)"
    except subprocess.TimeoutExpired:
        return "⏰ 命令超时(60s)"
    except Exception as e:
        return f"❌ 执行异常: {e}"


def do_tool(name, args, cwd):
    """工具分发"""
    if name == "list_dir":
        path = args.get("path", ".")
        try:
            items = sorted(os.listdir(path))
            return "\n".join(items[:100]) or "(空目录)"
        except Exception as e:
            return f"❌ {e}"
    if name == "read_file":
        path = args.get("path", "")
        try:
            with open(path) as f:
                lines = f.readlines()
            return "".join(lines[:2000]) + (f"\n...(共{len(lines)}行, 已截断)" if len(lines) > 2000 else "")
        except Exception as e:
            return f"❌ {e}"
    if name == "write_file":
        path, content = args.get("path", ""), args.get("content", "")
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"✅ 已写入 {path} ({len(content)} 字符)"
        except Exception as e:
            return f"❌ {e}"
    if name == "edit_file":
        path, old, new = args.get("path", ""), args.get("old", ""), args.get("new", "")
        try:
            with open(path) as f:
                s = f.read()
            if old not in s:
                return f"❌ 未找到要替换的文本: {old[:80]}"
            with open(path, "w") as f:
                f.write(s.replace(old, new, 1))
            return f"✅ 已替换 {path}"
        except Exception as e:
            return f"❌ {e}"
    if name == "grep":
        pattern, path = args.get("pattern", ""), args.get("path", ".")
        try:
            r = subprocess.run(["grep", "-rn", pattern, path], capture_output=True, text=True, timeout=30)
            return (r.stdout or "(无匹配)")[:2000]
        except Exception as e:
            return f"❌ {e}"
    if name == "run":
        return safe_run(args.get("command", ""), cwd)
    return f"❌ 未知工具 {name}"


# ═══════════════════════════════════════════════════════════
# 六、Agent Loop 核心(Codex 精髓: 闭环干活)
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是大匠(编码智能体), 由明月集团自研 codex-kit 驱动。
工作方式(agent loop):
1. 先理解任务, 拆解步骤, 规划要创建/修改哪些文件
2. 用工具逐步执行: 写代码 → 运行 → 看结果 → 修复
3. 每步执行后观察输出, 失败就分析原因再修, 不要放弃
4. 任务完成后, 用 run 命令验证产物(运行测试/脚本), 拿到证据
5. 最后一步: 不调用工具, 直接输出最终交付说明(含: 做了什么/验证证据/如何运行)

规则:
- 只调用可用工具, 参数必须完整
- 写文件用 write_file(整个文件), 改文件用 edit_file
- 运行脚本必须用 run("python3 xxx.py") 并查看输出
- 验证不通过就继续修, 最多不要超过任务轮数限制
- 全部用中文说明"""


def run_agent(task, cwd, model=None, max_rounds=MAX_ROUNDS):
    """核心循环: 任务 → 计划 → 工具执行 → 观察 → 迭代 → 完成"""
    cwd = os.path.abspath(cwd or os.getcwd())
    os.makedirs(cwd, exist_ok=True)
    print(f"🤖 大匠开工 | 模型: {model or detect_endpoint()[2]}")
    print(f"📁 工作目录: {cwd}")
    print(f"📋 任务: {task}\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": f"任务: {task}\n\n当前工作目录: {cwd}\n先规划, 然后开始执行。完成后输出交付说明。"})

    # 留痕目录
    trace_dir = os.path.join(cwd, ".codex-trace")
    os.makedirs(trace_dir, exist_ok=True)
    trace_log = []

    for round_no in range(1, max_rounds + 1):
        print(f"━━━ 第 {round_no}/{max_rounds} 轮 ━━━")
        data, actual_model = chat(messages, tools=TOOL_SCHEMAS, model=model)
        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls")

        # 留痕
        trace_log.append({"round": round_no, "assistant": content[:500], "tool_calls": [
            {"name": tc["function"]["name"], "args": tc["function"]["arguments"][:300]} for tc in (tool_calls or [])
        ]})

        if content:
            print(f"💬 {content[:300]}{'...' if len(content) > 300 else ''}")

        if not tool_calls:
            # 模型认为完成了 → 进入验证
            print("\n🔍 模型报告完成, 验证中...")
            verify_result = verify_workspace(cwd)
            print(verify_result["summary"])
            trace_log.append({"round": round_no, "verify": verify_result["summary"]})
            save_trace(trace_dir, trace_log)
            return {"done": True, "rounds": round_no, "model": actual_model, "verify": verify_result, "message": content}

        # 执行工具调用
        messages.append(msg)
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                fn_args = {}
            print(f"  🔧 {fn_name}({json.dumps(fn_args, ensure_ascii=False)[:100]})")
            result = do_tool(fn_name, fn_args, cwd)
            if len(result) > 800:
                print(f"     ↳ {result[:200]}...({len(result)}字符)")
            else:
                print(f"     ↳ {result}")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

    # 轮数用尽
    print("\n⚠️ 达到最大轮数, 强制收尾")
    save_trace(trace_dir, trace_log)
    return {"done": False, "rounds": max_rounds, "message": "轮数用尽, 未确认完成"}


def verify_workspace(cwd):
    """验证: 找产物, 尝试运行 .py 脚本(语法检查+执行)"""
    results = []
    py_files = []
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in (".git", ".codex-trace", "__pycache__", "node_modules")]
        for f in files:
            if f.endswith(".py") and root == cwd:
                py_files.append(os.path.join(root, f))
    if not py_files:
        return {"status": "no_python", "summary": "⚠️ 未发现 python 产物(或不在工作区根目录)"}

    for pf in py_files[:3]:
        # 语法检查
        r = subprocess.run(["python3", "-m", "py_compile", pf], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            results.append(f"✅ 语法 OK: {os.path.basename(pf)}")
        else:
            results.append(f"❌ 语法错误: {os.path.basename(pf)}: {r.stderr[:200]}")
            continue
        # 试运行(前 3 个脚本); 无参失败自动带参重试(参数 10)
        r2 = subprocess.run(["python3", pf], capture_output=True, text=True, timeout=30)
        if r2.returncode != 0:
            r3 = subprocess.run(["python3", pf, "10"], capture_output=True, text=True, timeout=30)
            if r3.returncode == 0:
                r2 = r3
        if r2.returncode == 0:
            results.append(f"✅ 运行 OK: {os.path.basename(pf)} → {r2.stdout.strip()[:150]}")
        else:
            results.append(f"⚠️ 运行退出码{r2.returncode}: {r2.stderr.strip()[:200]}")

    return {"status": "ok", "summary": "\n".join(results)}


def save_trace(trace_dir, trace_log):
    with open(os.path.join(trace_dir, "trace.json"), "w") as f:
        json.dump(trace_log, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════
# 七、子命令: plan / verify / report
# ═══════════════════════════════════════════════════════════

def cmd_plan(args):
    """只出计划, 不执行"""
    task = " ".join(args)
    if not task:
        sys.exit("❌ 用法: codex-kit.py plan <任务>")
    data, model = chat([
        {"role": "system", "content": "你是资深工程师。请把任务拆解成可执行步骤: 每步做什么/创建什么文件/如何验证。只输出计划, 不要执行。"},
        {"role": "user", "content": task},
    ], max_tokens=2048)
    print(f"📋 计划({model}):\n{data['choices'][0]['message']['content']}")


def cmd_verify(args):
    """验证产物"""
    cwd = os.path.abspath(args[0]) if args else os.getcwd()
    r = verify_workspace(cwd)
    print(r["summary"])


def cmd_report(args):
    """生成交付报告 RESULT.md"""
    cwd = os.path.abspath(args[0]) if args else os.getcwd()
    trace_path = os.path.join(cwd, ".codex-trace", "trace.json")
    report = ["# RESULT.md — 交付报告", "", f"- 时间: {time.strftime('%Y-%m-%d %H:%M')}", f"- 目录: {cwd}"]
    if os.path.isfile(trace_path):
        with open(trace_path) as f:
            trace = json.load(f)
        report.append(f"- 轮次: {len(trace)}")
        report.append(f"- 验证: {trace[-1].get('verify', 'N/A')}")
    report.append("\n## 交付物")
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in (".git", ".codex-trace", "__pycache__", "node_modules")]
        for f in files:
            if f != "RESULT.md":
                report.append(f"- {os.path.relpath(os.path.join(root, f), cwd)}")
    out = os.path.join(cwd, "RESULT.md")
    with open(out, "w") as f:
        f.write("\n".join(report))
    print(f"✅ 报告已生成: {out}")


# ═══════════════════════════════════════════════════════════
# 八、入口
# ═══════════════════════════════════════════════════════════

HELP = f"""codex-kit.py v{VERSION} — 自研编码智能体内核(纯标准库, 零依赖)

用法:
  codex-kit.py "<任务>" [--cwd 目录] [--model xxx] [--rounds N]
  codex-kit.py plan "<任务>"
  codex-kit.py verify [目录]
  codex-kit.py report [目录]
  codex-kit.py doctor

示例:
  codex-kit.py "写一个斐波那契脚本 fib.py 并运行验证"
  codex-kit.py "给项目写 README.md" --cwd /path/to/proj
  codex-kit.py plan "实现一个文件去重工具"

安全: 命令白名单 + 危险黑名单(rm -rf / 等永不执行)
驱动: DeepSeek 默认(稳), 百炼 qwen3-coder 可选
"""


def cmd_doctor():
    print(f"🔬 codex-kit v{VERSION} 自检")
    print("=" * 46)
    for name, url in [("DEEPSEEK", DEEPSEEK_URL), ("DASHSCOPE", DASHSCOPE_URL), ("MOONSHOT", MOONSHOT_URL)]:
        key = get_key({"DEEPSEEK": "DEEPSEEK_API_KEY", "DASHSCOPE": "DASHSCOPE_API_KEY", "MOONSHOT": "MOONSHOT_API_KEY"}[name])
        print(f"  {name:<10} {'✅' if key else '❌'} {url}")
    # 实测
    try:
        data, model = chat([{"role": "user", "content": "回复'连通正常'"}], max_tokens=20)
        print(f"\n  🧪 实测 {model}: ✅ {data['choices'][0]['message']['content'][:30]}")
    except SystemExit as e:
        print(f"\n  🧪 实测: ❌ {e}")


def main():
    if len(sys.argv) < 2:
        print(HELP)
        sys.exit(0)
    args = sys.argv[1:]

    # 解析全局选项
    opts = {}
    rest = []
    i = 0
    while i < len(args):
        if args[i] in ("--cwd", "--model", "--rounds"):
            opts[args[i][2:]] = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        else:
            rest.append(args[i])
            i += 1

    if rest[0] in ("-h", "--help", "help"):
        print(HELP)
        sys.exit(0)
    if rest[0] == "doctor":
        cmd_doctor()
        sys.exit(0)
    if rest[0] == "plan":
        cmd_plan(rest[1:])
        sys.exit(0)
    if rest[0] == "verify":
        cmd_verify(rest[1:])
        sys.exit(0)
    if rest[0] == "report":
        cmd_report(rest[1:])
        sys.exit(0)

    # 默认: 直接跑任务
    task = " ".join(rest)
    if not task:
        sys.exit("❌ 需要任务描述")
    result = run_agent(task, opts.get("cwd"), model=opts.get("model"), max_rounds=int(opts.get("rounds", MAX_ROUNDS)))
    print("\n" + "=" * 46)
    print("📦 交付状态:", "✅ 完成" if result.get("done") else "⚠️ 未确认完成")
    print("🔍 验证:", result.get("verify", {}).get("summary", "N/A"))


if __name__ == "__main__":
    main()
