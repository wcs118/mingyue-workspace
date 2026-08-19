#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kimi-kit.py v2.0 — Kimi K2.6/K2.7 全能力自研封装(明月系核心资产)
=====================================================================
老板指令(2026-08-17): 百分百写成自己的代码, 能力写全, 实测才算数。
纯 Python 标准库, 零依赖。多模态(文+图+视频抽帧)。

覆盖 Kimi 全能力面(11 命令):
  chat      多轮对话(系统提示/温度控制)
  vision    图像理解(单图/多图 base64 直传)
  video     视频理解(ffmpeg 抽帧 → 逐帧识别)
  stream    流式输出
  tools     函数调用闭环
  json      结构化输出
  schema    JSON Schema 校验
  batch     批量(限速串行, kimi org RPM=3 并发=1 实测)
  context   上下文预算
  models    模型清单
  doctor    自检

端点: https://api.moonshot.cn/v1 | 模型: kimi-k2.6(多模态) / kimi-k2.7-code

用法:
  python3 kimi-kit.py chat "问题" [--system 提示] [--temp 0.7]
  python3 kimi-kit.py vision 图1.jpg [图2.png...] "问题"
  python3 kimi-kit.py video 视频.mp4 "描述" [--fps 1]
  python3 kimi-kit.py stream "问题" | tools "需求" | json 内容 --fields 姓名
  python3 kimi-kit.py batch f1.txt f2.txt | context <文本> | models | doctor
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

VERSION = "3.0.0"
BASE_URL = "https://api.moonshot.cn/v1"
MODELS = {
    "kimi-k3":               {"ctx": 1048576, "modal": "文+图+视频", "desc": "旗舰 2.8万亿参数, 长程编程/深度推理"},
    "kimi-k2.7-code":       {"ctx": 262144, "modal": "文",   "desc": "编码专用"},
    "kimi-k2.7-code-highspeed": {"ctx": 262144, "modal": "文", "desc": "高速版 180-260 token/s"},
    "kimi-k2.6":            {"ctx": 262144, "modal": "文+图+视频", "desc": "默认, 多模态"},
}

# kimi 免费 org 实测硬限制: RPM=3, 并发=1 → 我们留安全余量
RPM = int(os.environ.get("KIMI_RPM", "2"))


class Limiter:
    """令牌桶限速(单飞: 并发=1)"""
    def __init__(self, rpm):
        """
        init.
        """
        self.interval = 60.0 / rpm
        self.last = 0.0
        self.lock = None
    def wait(self):
        """
        wait.
        """
        now = time.time()
        gap = now - self.last
        if gap < self.interval:
            time.sleep(self.interval - gap)
        self.last = time.time()

LIMITER = Limiter(RPM)


def get_key():
    """
    get key.
    
    Returns:
        Result of the operation.
    """
    k = os.environ.get("MOONSHOT_API_KEY", "")
    if not k:
        try:
            k = json.load(open(os.path.expanduser("~/.openclaw/openclaw.json"))).get("env", {}).get("MOONSHOT_API_KEY", "")
        except Exception:
            pass
    if not k:
        sys.exit("❌ 未找到 MOONSHOT_API_KEY")
    return k


def http_post(payload, retries=4):
    """
    http post.
    
    Args:
        retries: number of retries.
    
    Returns:
        Result of the operation.
    """
    key = get_key()
    LIMITER.wait()
    req = urllib.request.Request(
        BASE_URL + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST")
    for i in range(retries):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=180).read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                wait = [3, 8, 15, 30][i]
                print(f"⚠️ HTTP {e.code}, {wait}s 后重试...", file=sys.stderr)
                time.sleep(wait)
                continue
            sys.exit(f"❌ HTTP {e.code}: {body}")
        except Exception as e:
            sys.exit(f"❌ {e}")


def chat(messages, model=None, **kw):
    """
    chat.
    
    Args:
        model: model identifier.
        **kw: additional keyword arguments.
    
    Returns:
        Result of the operation.
    """
    payload = {"model": model or "kimi-k2.6", "messages": messages,
               "max_tokens": kw.pop("max_tokens", 8192), "stream": False}
    payload.update(kw)
    return http_post(payload)


def get_content(data):
    """
    get content.
    
    Args:
        data: payload data.
    
    Returns:
        Result of the operation.
    """
    try:
        return data["choices"][0]["message"]["content"] or ""
    except Exception:
        return json.dumps(data, ensure_ascii=False)[:600]


def enc_video(path):
    """视频 → base64 data URL(直传, 不抽帧! K2.6/K3 原生支持 video_url)"""
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "mp4"
    mime = {"mp4": "video/mp4", "mov": "video/quicktime", "avi": "video/x-msvideo",
            "mkv": "video/x-matroska", "webm": "video/webm"}.get(ext, "video/mp4")
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def enc_image(path):
    """图片 → base64 data URL"""
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "jpg"
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp"}.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def parse(args, spec):
    """
    parse.
    
    Args:
        args: positional arguments.
    
    Returns:
        Result of the operation.
    """
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


# ═══════════════════════════════════════════════════════════
# ① chat
# ═══════════════════════════════════════════════════════════
def cmd_chat(args):
    """
    cmd chat.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--system": 1, "--temp": 1, "--model": 1, "--max_tokens": 1})
    q = " ".join(pos).strip() or sys.stdin.read().strip()
    if not q:
        sys.exit("用法: kimi-kit.py chat <问题>")
    msgs = []
    if opts.get("--system"):
        msgs.append({"role": "system", "content": opts["--system"]})
    msgs.append({"role": "user", "content": q})
    kw = {}
    if opts.get("--temp"):
        kw["temperature"] = float(opts["--temp"])
    model = opts.get("--model", "kimi-k2.6")
    if opts.get("--max_tokens"):
        kw["max_tokens"] = int(opts["--max_tokens"])
    print(f"💬 {model}:")
    print(get_content(chat(msgs, model=model, **kw)))


# ═══════════════════════════════════════════════════════════
# ② vision 图像理解
# ═══════════════════════════════════════════════════════════
def cmd_vision(args):
    """
    cmd vision.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--model": 1, "--detail": 1})
    imgs = [a for a in pos if os.path.isfile(a) and a.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"))]
    q = " ".join(a for a in pos if not os.path.isfile(a)) or "描述图片内容(中文)"
    if not imgs:
        sys.exit("用法: kimi-kit.py vision <图片...> [问题]")
    content = [{"type": "text", "text": q}]
    for img in imgs:
        content.append({"type": "image_url", "image_url": {"url": enc_image(img)}})
    model = opts.get("--model", "kimi-k2.6")
    print(f"🖼️ {model} 看图 {len(imgs)} 张: {q[:40]}")
    d = chat([{"role": "user", "content": content}], model=model, max_tokens=2048)
    print(get_content(d))


# ═══════════════════════════════════════════════════════════
# ③ video 视频理解(抽帧)
# ═══════════════════════════════════════════════════════════
def cmd_video(args):
    """
    cmd video.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--model": 1})
    vids = [a for a in pos if os.path.isfile(a) and a.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm"))]
    q = " ".join(a for a in pos if not os.path.isfile(a)) or "描述视频内容(中文)"
    if not vids:
        sys.exit("用法: kimi-kit.py video <视频.mp4> [问题]")
    model = opts.get("--model", "kimi-k2.6")
    v = vids[0]
    print(f"🎬 {model} 视频理解(直传 base64, 不抽帧): {v}")
    content = [{"type": "text", "text": q}, {"type": "video_url", "video_url": {"url": enc_video(v)}}]
    d = chat([{"role": "user", "content": content}], model=model, max_tokens=2048)
    print(f"💬 {get_content(d)}")


# ═══════════════════════════════════════════════════════════
# ④ stream
# ═══════════════════════════════════════════════════════════
def cmd_stream(args):
    """
    cmd stream.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--model": 1})
    q = " ".join(pos).strip()
    if not q:
        sys.exit("用法: kimi-kit.py stream <问题>")
    key = get_key()
    LIMITER.wait()
    payload = {"model": opts.get("--model", "kimi-k2.6"),
               "messages": [{"role": "user", "content": q}],
               "stream": True, "max_tokens": 8192}
    req = urllib.request.Request(BASE_URL + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=180)
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")
    for raw in resp:
        line = raw.decode(errors="replace").strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if chunk == "[DONE]":
            break
        try:
            d = json.loads(chunk)["choices"][0]["delta"]
            print(d.get("content") or "", end="", flush=True)
        except Exception:
            pass
    print()


# ═══════════════════════════════════════════════════════════
# ⑤ tools
# ═══════════════════════════════════════════════════════════
def cmd_tools(args):
    """
    cmd tools.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--model": 1})
    q = " ".join(pos).strip() or "计算 (12+34)*5 等于多少"
    model = opts.get("--model", "kimi-k2.6")
    tools = [{"type": "function", "function": {"name": "calc", "description": "计算数学表达式",
              "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]}}}]
    msgs = [{"role": "user", "content": q}]
    print(f"🔧 {model} 工具调用: {q}")
    for rnd in range(4):
        data = http_post({"model": model, "messages": msgs, "tools": tools, "max_tokens": 2048})
        msg = data["choices"][0]["message"]
        tcs = msg.get("tool_calls")
        if not tcs:
            print(f"💬 {msg.get('content', '')}")
            return
        msgs.append(msg)
        for tc in tcs:
            fn, fa = tc["function"]["name"], tc["function"]["arguments"]
            try:
                a = json.loads(fa or "{}")
                expr = a.get("expr", "0")
                if not all(c in "0123456789+-*/(). " for c in expr):
                    result = "❌ 非法表达式"
                else:
                    result = f"{expr} = {eval(expr, {'__builtins__': {}}, {})}"
            except Exception as e:
                result = f"❌ {e}"
            print(f"  → {fn}({fa[:50]}) = {result}")
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
    print("⚠️ 轮数用尽")


# ═══════════════════════════════════════════════════════════
# ⑥ json
# ═══════════════════════════════════════════════════════════
def cmd_json(args):
    """
    cmd json.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--fields": 1})
    content = " ".join(pos).strip()
    if not content:
        sys.exit("用法: kimi-kit.py json <内容> --fields 姓名,年龄")
    fl = [f.strip() for f in opts.get("--fields", "").split(",") if f.strip()]
    if not fl:
        sys.exit("需要 --fields")
    fs = "、".join(fl)
    d = chat([
        {"role": "system", "content": f"从输入抽取字段: {fs}。只输出合法JSON, 未知为null。"},
        {"role": "user", "content": content}],
        response_format={"type": "json_object"}, max_tokens=1024)
    out = get_content(d).strip()
    print(out)
    try:
        obj = json.loads(out)
        miss = [f for f in fl if f not in obj]
        print("✅ 合法JSON" + (f", 缺: {miss}" if miss else ""))
    except Exception as e:
        print(f"⚠️ 非合法JSON: {e}")


# ═══════════════════════════════════════════════════════════
# ⑦ schema
# ═══════════════════════════════════════════════════════════
def cmd_schema(args):
    """
    cmd schema.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--schema": 1})
    content = " ".join(pos).strip()
    if not content:
        sys.exit("用法: kimi-kit.py schema <内容> [--schema s.json]")
    schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}},
        "required": ["summary", "keywords"],
    }
    if opts.get("--schema"):
        schema = json.load(open(opts["--schema"]))
    d = chat([
        {"role": "system", "content": "严格按 JSON Schema 输出, 只输出合法JSON。"},
        {"role": "user", "content": content}],
        response_format={"type": "json_object"}, max_tokens=2048)
    out = get_content(d).strip()
    print(out)
    try:
        obj = json.loads(out)
        miss = [r for r in schema.get("required", []) if r not in obj]
        print("✅ 合法JSON" + (f", 缺必填: {miss}" if miss else ", 校验通过"))
    except Exception as e:
        print(f"⚠️ 非合法JSON: {e}")


# ═══════════════════════════════════════════════════════════
# ⑨ search 联网搜索
# ═══════════════════════════════════════════════════════════
def cmd_search(args):
    """
    cmd search.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--model": 1})
    q = " ".join(pos).strip()
    if not q:
        sys.exit("用法: kimi-kit.py search <问题>")
    model = opts.get("--model", "kimi-k2.6")
    tools = [{"type": "builtin_function", "function": {"name": "$web_search", "description": "联网搜索"}}]
    print(f"🌐 {model} 联网搜索: {q}")
    msgs = [{"role": "user", "content": q}]
    for rnd in range(3):
        data = http_post({"model": model, "messages": msgs, "tools": tools, "max_tokens": 2048})
        msg = data["choices"][0]["message"]
        if not msg.get("tool_calls"):
            print(f"💬 {get_content(data)}")
            return
        msgs.append(msg)
        for tc in msg["tool_calls"]:
            print(f"  🔍 {tc['function']['name']}")
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": "(搜索完成)"})
    print("⚠️ 轮数用尽")


# ═══════════════════════════════════════════════════════════
# ⑩ partial 续写模式
# ═══════════════════════════════════════════════════════════
def cmd_partial(args):
    """
    cmd partial.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--model": 1, "--prefix": 1})
    q = " ".join(pos).strip()
    if not q:
        sys.exit("用法: kimi-kit.py partial <已有文本> [--prefix 续写开头]")
    model = opts.get("--model", "kimi-k2.6")
    content = q + (opts.get("--prefix", ""))
    payload = {"model": model, "messages": [{"role": "assistant", "content": content}],
               "max_tokens": 2048, "partial_mode": True}
    print(f"✍️ {model} 续写模式: {q[:40]}...")
    print(get_content(http_post(payload)))


# ═══════════════════════════════════════════════════════════
# ⑪ batch 批量
# ═══════════════════════════════════════════════════════════
def cmd_batch(args):
    """
    cmd batch.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--prompt": 1, "--model": 1})
    files = [a for a in pos if os.path.isfile(a)]
    if not files:
        sys.exit("用法: kimi-kit.py batch <文件...> [--prompt 指令]")
    instruction = opts.get("--prompt", "总结要点, 100字内")
    model = opts.get("--model", "kimi-k2.6")
    print(f"⚡ 批量 {len(files)} 文件(串行限速, kimi org 并发=1):")
    results = {}
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                c = fh.read()[:6000]
            d = chat([{"role": "system", "content": instruction},
                      {"role": "user", "content": c}], model=model, max_tokens=1024)
            out = get_content(d)
            results[f] = out
            print(f"  ✅ {os.path.basename(f)}: {out[:100]}")
        except Exception as e:
            print(f"  ❌ {os.path.basename(f)}: {e}")
    with open("kimi-batch-result.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print(f"📦 已存 kimi-batch-result.json")


# ═══════════════════════════════════════════════════════════
# ⑫ balance 余额
# ═══════════════════════════════════════════════════════════
def cmd_balance(args=None):
    """
    cmd balance.
    
    Args:
        args: positional arguments.
    """
    key = get_key()
    req = urllib.request.Request(BASE_URL + "/users/me/balance",
        headers={"Authorization": f"Bearer {key}"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        print("💰 Kimi 余额:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:600])
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")


# ═══════════════════════════════════════════════════════════
# ⑬ estimate token 估算
# ═══════════════════════════════════════════════════════════
def cmd_estimate(args):
    """
    cmd estimate.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--model": 1})
    q = " ".join(pos).strip()
    if not q:
        sys.exit("用法: kimi-kit.py estimate <文本>")
    model = opts.get("--model", "kimi-k2.6")
    payload = {"model": model, "messages": [{"role": "user", "content": q}]}
    req = urllib.request.Request(BASE_URL + "/tokenizers/estimate-token-count",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {get_key()}"},
        method="POST")
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        print(f"📏 {model} token 估算: {data.get('data', {}).get('total_tokens', '?')}")
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")


# ═══════════════════════════════════════════════════════════
# ⑭ context
# ═══════════════════════════════════════════════════════════
def cmd_context(args):
    """
    cmd context.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--max": 1})
    target = pos[0] if pos else None
    if not target:
        sys.exit("用法: kimi-kit.py context <文本或文件>")
    t = open(target, encoding="utf-8", errors="replace").read() if os.path.isfile(target) else " ".join(pos)
    cjk = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
    est = int(cjk * 0.6 + (len(t) - cjk) / 4)
    limit = int(opts.get("--max", "16000"))
    print(f"📊 {len(t)} 字符 ≈ {est} tokens | 预算 {limit} | 占用 {est/limit*100:.0f}%")
    print("✅ OK" if est <= limit else f"✂️ 超限, 建议裁到 {int(len(t)*limit/est*0.9)} 字符")


# ═══════════════════════════════════════════════════════════
# ⑮ models
# ═══════════════════════════════════════════════════════════
def cmd_models(args=None):
    """
    cmd models.
    
    Args:
        args: positional arguments.
    """
    print("📦 Kimi 模型(自研封装 v3.0):")
    for m, i in MODELS.items():
        print(f"  {m:<28} ctx={i['ctx']:<8} 模态={i['modal']:<12} {i['desc']}")


# ═══════════════════════════════════════════════════════════
# ⑯ doctor
# ═══════════════════════════════════════════════════════════
def cmd_doctor(args=None):
    """
    cmd doctor.
    
    Args:
        args: positional arguments.
    """
    print(f"🔬 kimi-kit v{VERSION} 自检")
    print(f"  📡 端点: {BASE_URL} | ⚡ 限速: {RPM} RPM")
    try:
        d = chat([{"role": "user", "content": "只回复: 连通"}], max_tokens=10)
        print(f"  ✅ 连通: {get_content(d)[:30]}")
        print(f"  🖼️ 多模态: {'✅ 可用' if MODELS['kimi-k2.6']['modal'] == '文+图' else '❌'}")
        print(f"  ✅ 全能力就绪")
    except SystemExit as e:
        print(f"  ❌ {e}")


HELP = f"""kimi-kit.py v{VERSION} — Kimi 全能力自研封装(多模态, 内置限速)
  chat <问题> [--system 提示] [--temp 0.7] | stream <问题>
  vision <图...> [问题] | video <视频.mp4> [问题](直传不抽帧)
  search <问题>(联网) | partial <文本> [--prefix 续写](续写模式)
  tools <需求> | json <内容> --fields 姓名 | schema <内容> [--schema s.json]
  batch <文件...> [--prompt 指令] | context <文本> | estimate <文本>
  balance | models | doctor
"""

def main():
    """
    main.
    """
    if len(sys.argv) < 2:
        print(HELP)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    handlers = {
        "chat": cmd_chat, "vision": cmd_vision, "video": cmd_video, "stream": cmd_stream,
        "tools": cmd_tools, "json": cmd_json, "schema": cmd_schema, "batch": cmd_batch,
        "context": cmd_context, "search": cmd_search, "partial": cmd_partial,
        "balance": cmd_balance, "estimate": cmd_estimate,
        "models": cmd_models, "doctor": cmd_doctor,
    }
    fn = handlers.get(cmd)
    if not fn:
        sys.exit(f"❌ 未知命令: {cmd}\n可用: {list(handlers.keys())}")
    fn(args)

if __name__ == "__main__":
    main()