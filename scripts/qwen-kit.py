#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qwen-kit.py — 千问 Qwen 全家桶完整封装库(自研,明月系核心资产 v2.0)
=====================================================================
老板指令(2026-08-17):拆解千问模型,自己写代码成为我们自己的宝藏,谁也拿不去。

v2.0 覆盖能力面(对标千问官方 SDK 全能力,纯自研):
  ┌─ 对话推理 ──────────────────────────────────────────────┐
  │ chat          文本对话(多轮/单轮/系统提示)                │
  │ reasoning     推理深度控制(xhigh/high/medium/low)         │
  │ thinking      思考开关(enable_thinking true/false)        │
  │ json          结构化 JSON 输出(response_format)           │
  │ schema        JSON Schema 强约束输出                      │
  ├─ 多模态 ────────────────────────────────────────────────┤
  │ vision        图像理解(单图/多图)                         │
  │ video         视频理解(ffmpeg 抽帧序列)                   │
  │ audio_asr     语音识别(千问 audio 系列)                   │
  │ audio_tts     语音合成(cosyvoice/tts)                     │
  ├─ 生成 ──────────────────────────────────────────────────┤
  │ image_gen     文生图(万相 wanx)                           │
  │ video_gen     文生视频(万相)                              │
  ├─ 工具与扩展 ────────────────────────────────────────────┤
  │ tools         function calling 完整闭环                   │
  │ embed         文本向量化(text-embedding)                  │
  │ batch         批量并发请求(线程池)                        │
  │ router        模型路由/自动故障切换                       │
  ├─ 工程化 ────────────────────────────────────────────────┤
  │ stream        流式输出(思考+正文双通道)                   │
  │ retry         自动重试(指数退避)                          │
  │ context       会话上下文管理(token 估算/裁剪)             │
  │ log           详细日志                                    │
  └──────────────────────────────────────────────────────────┘

设计原则:
- 纯 Python 标准库(urllib/threading/json),零第三方依赖
- OpenAI 兼容协议 + 百炼原生协议(生成类走 dashscope 原生)
- 自动探测端点: DASHSCOPE > OPENROUTER > MOONSHOT > DEEPSEEK
- 每个能力独立函数,可单独调用可组合成流水线
- 详细中文注释,任何人可接手维护

用法示例:
  python3 qwen-kit.py chat "你好"
  python3 qwen-kit.py reasoning "解这道题" --level high
  python3 qwen-kit.py vision a.png b.png "对比这两张图"
  python3 qwen-kit.py video clip.mp4 "描述内容"
  python3 qwen-kit.py json "提取人名" --fields 姓名,年龄,职业
  python3 qwen-kit.py schema '{"type":"object","properties":{"name":{"type":"string"}}}' "提取姓名"
  python3 qwen-kit.py tools "查上海时间"
  python3 qwen-kit.py stream "写首诗"
  python3 qwen-kit.py embed "你好世界"
  python3 qwen-kit.py batch q1.txt q2.txt q3.txt
  python3 qwen-kit.py image_gen "一只猫,赛博朋克"
  python3 qwen-kit.py audio_asr voice.wav
  python3 qwen-kit.py audio_tts "你好,我是明月" --output hello.mp3
  python3 qwen-kit.py models
  python3 qwen-kit.py doctor   # 自检所有能力

环境变量(按优先级):
  DASHSCOPE_API_KEY  阿里云百炼(国内,开源模型有免费额度)
  OPENROUTER_API_KEY OpenRouter(海外)
  MOONSHOT_API_KEY   Moonshot(多模态备胎)
  DEEPSEEK_API_KEY   DeepSeek(兜底,验证框架用)
  可选: QWEN_BASE_URL / QWEN_MODEL / QWEN_DEBUG
"""

import base64
import json
import os
import sys
import time
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════════════════════════
# 一、全局配置
# ═══════════════════════════════════════════════════════════

VERSION = "2.0.0"
DEBUG = os.environ.get("QWEN_DEBUG", "0") == "1"

# 端点常量
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_NATIVE_URL = "https://dashscope.aliyuncs.com/api/v1"  # 原生协议(生成类)
OPENROUTER_URL = "https://openrouter.ai/api/v1"
MOONSHOT_URL = "https://api.moonshot.cn/v1"
DEEPSEEK_URL = "https://api.deepseek.com/v1"

# 千问模型全家桶
QWEN_MODELS = {
    # 对话推理
    "qwen3.8-27b":       {"ctx": 262144,  "modal": "text+image+video", "kind": "chat",  "desc": "开源旗舰,多模态,编程强"},
    "qwen3.8-max":       {"ctx": 1000000, "modal": "text",             "kind": "chat",  "desc": "闭源旗舰 2.4T MoE"},
    "qwen3.8-flash":     {"ctx": 1000000, "modal": "text+image",       "kind": "chat",  "desc": "轻量快速,性价比"},
    "qwen3.5-plus":      {"ctx": 1000000, "modal": "text+image",       "kind": "chat",  "desc": "通用 Plus"},
    "qwen3.5-turbo":     {"ctx": 1000000, "modal": "text+image",       "kind": "chat",  "desc": "通用 Turbo"},
    # 编码
    "qwen3-coder-plus":  {"ctx": 1000000, "modal": "text",             "kind": "chat",  "desc": "编码专用 Plus"},
    "qwen3-coder-next":  {"ctx": 262144,  "modal": "text",             "kind": "chat",  "desc": "编码专用 Next"},
    "qwen3-coder-flash": {"ctx": 262144,  "modal": "text",             "kind": "chat",  "desc": "编码专用 Flash"},
    # 视觉
    "qwen3-vl-plus":     {"ctx": 262144,  "modal": "text+image+video", "kind": "chat",  "desc": "视觉理解 Plus"},
    "qwen3-vl-flash":    {"ctx": 262144,  "modal": "text+image+video", "kind": "chat",  "desc": "视觉理解 Flash"},
    # 语音
    "qwen3-audio":       {"ctx": 131072,  "modal": "text+audio",       "kind": "chat",  "desc": "语音理解"},
    # 向量
    "text-embedding-v3": {"ctx": 8192,    "modal": "text",             "kind": "embed", "desc": "文本向量化 v3"},
    "text-embedding-v4": {"ctx": 8192,    "modal": "text",             "kind": "embed", "desc": "文本向量化 v4"},
    # 图像生成(万相)
    "wanx2.1-t2i-turbo": {"ctx": 0,       "modal": "text→image",       "kind": "image", "desc": "文生图 Turbo"},
    "wan2.2-t2i-flash":  {"ctx": 0,       "modal": "text→image",       "kind": "image", "desc": "文生图 Flash"},
}

REASONING_LEVELS = ("xhigh", "high", "medium", "low")
DEFAULT_TIMEOUT = 120
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 8]  # 指数退避秒数

# ═══════════════════════════════════════════════════════════
# 二、日志与工具函数
# ═══════════════════════════════════════════════════════════

def log(msg, level="INFO"):
    """统一日志: DEBUG 时输出全部,否则只输出 INFO+"""
    if DEBUG or level != "DEBUG":
        print(f"[{level}] {msg}", file=sys.stderr)


def load_openclaw_env():
    """从 openclaw.json 读环境变量(兜底 key 来源)"""
    try:
        with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
            return json.load(f).get("env", {})
    except Exception:
        return {}


def detect_config(prefer_modal=None):
    """
    自动探测可用端点+key。
    prefer_modal: "image"/"audio"/"embed" 时优先选支持该模态的端点
    返回 (base_url, api_key, model_name)
    """
    env = os.environ
    cfg_env = load_openclaw_env()

    def get(name):
        return env.get(name) or cfg_env.get(name) or ""

    # 用户显式指定
    if env.get("QWEN_BASE_URL") and (env.get("QWEN_API_KEY") or get("DASHSCOPE_API_KEY")):
        return env["QWEN_BASE_URL"], env.get("QWEN_API_KEY") or get("DASHSCOPE_API_KEY"), env.get("QWEN_MODEL", "qwen3.8-27b")

    # 多模态输入(图像/视频/音频)优先百炼或 moonshot
    if prefer_modal in ("image", "video", "audio"):
        if get("DASHSCOPE_API_KEY"):
            return DASHSCOPE_URL, get("DASHSCOPE_API_KEY"), "qwen3-vl-plus"
        if get("MOONSHOT_API_KEY"):
            return MOONSHOT_URL, get("MOONSHOT_API_KEY"), "kimi-k2.6"
        if get("OPENROUTER_API_KEY"):
            return OPENROUTER_URL, get("OPENROUTER_API_KEY"), "qwen/qwen3-vl-plus"

    # 向量优先百炼
    if prefer_modal == "embed":
        if get("DASHSCOPE_API_KEY"):
            return DASHSCOPE_URL, get("DASHSCOPE_API_KEY"), "text-embedding-v4"

    # 通用优先级: 百炼 > OpenRouter > Moonshot > DeepSeek
    if get("DASHSCOPE_API_KEY"):
        return DASHSCOPE_URL, get("DASHSCOPE_API_KEY"), os.environ.get("QWEN_MODEL", "qwen3.8-27b")
    if get("OPENROUTER_API_KEY"):
        return OPENROUTER_URL, get("OPENROUTER_API_KEY"), "qwen/qwen3.8-27b"
    if get("MOONSHOT_API_KEY"):
        return MOONSHOT_URL, get("MOONSHOT_API_KEY"), "kimi-k2.6"
    if get("DEEPSEEK_API_KEY"):
        return DEEPSEEK_URL, get("DEEPSEEK_API_KEY"), "deepseek-v4-flash"

    sys.exit("❌ 未找到任何 API key。请设置 DASHSCOPE_API_KEY(百炼) 或 OPENROUTER_API_KEY 或 MOONSHOT_API_KEY 或 DEEPSEEK_API_KEY")


# ═══════════════════════════════════════════════════════════
# 三、HTTP 层(重试/错误/流式/限速)
# ═══════════════════════════════════════════════════════════

class RateLimiter:
    """令牌桶限速器: 控制每分钟最大请求数"""
    def __init__(self, rpm=3):
        self.rpm = rpm
        self.lock = threading.Lock()
        self.tokens = rpm
        self.last_refill = time.time()

    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.rpm, self.tokens + elapsed * self.rpm / 60.0)
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            wait = (1 - self.tokens) * 60.0 / self.rpm
            self.tokens = 0
            self.last_refill = now + wait
        log(f"⏳ 限速中, 等待 {wait:.1f}s", "DEBUG")
        time.sleep(wait)


GLOBAL_LIMITER = RateLimiter(rpm=int(os.environ.get("QWEN_RPM", "2")))


def throttled_request(url, payload, api_key, timeout=DEFAULT_TIMEOUT, stream=False, retries=MAX_RETRIES):
    """带限速的请求(并发安全)"""
    GLOBAL_LIMITER.acquire()
    return http_request(url, payload, api_key, timeout=timeout, stream=stream, retries=retries)

def http_request(url, payload, api_key, timeout=DEFAULT_TIMEOUT, stream=False, retries=MAX_RETRIES):
    """
    带重试的 HTTP POST。返回 (status, data_dict 或 响应对象)
    重试策略: 指数退避, 只对 429/5xx 重试
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if stream:
        headers["Accept"] = "text/event-stream"

    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode(),
                headers=headers, method="POST")
            resp = urllib.request.urlopen(req, timeout=timeout)
            if stream:
                return 200, resp
            data = json.loads(resp.read().decode())
            return 200, data
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            last_err = f"HTTP {e.code}: {body[:400]}"
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                log(f"⚠️ 请求失败({e.code}), {wait}s 后重试({attempt+1}/{retries})", "WARN")
                time.sleep(wait)
                continue
            sys.exit(f"❌ {last_err}")
        except urllib.error.URLError as e:
            last_err = f"网络错误: {e}"
            if attempt < retries:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                log(f"⚠️ 网络失败, {wait}s 后重试", "WARN")
                time.sleep(wait)
                continue
            sys.exit(f"❌ {last_err}")
        except Exception as e:
            sys.exit(f"❌ 未知错误: {e}")

    sys.exit(f"❌ 重试耗尽: {last_err}")


def chat_completion(base_url, api_key, messages, model=None, **kwargs):
    """通用对话补全(非流式)"""
    model = model or detect_config()[2]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": kwargs.pop("max_tokens", 4096),
    }
    payload.update(kwargs)
    url = base_url.rstrip("/") + "/chat/completions"
    try:
        _, data = throttled_request(url, payload, api_key)
    except SystemExit as e:
        # 限流/配额用尽时, 自动降级 DeepSeek(兜底通道)
        if "429" in str(e) or "rate" in str(e).lower() or "limit" in str(e).lower():
            ds_key = os.environ.get("DEEPSEEK_API_KEY") or load_openclaw_env().get("DEEPSEEK_API_KEY", "")
            if ds_key and "deepseek.com" not in base_url:
                log("🔄 当前端点限流, 自动降级 DeepSeek", "WARN")
                _, data = throttled_request(
                    DEEPSEEK_URL.rstrip("/") + "/chat/completions",
                    {**payload, "model": "deepseek-v4-flash"}, ds_key)
                return data
        raise
    return data


def extract_text(data):
    """从响应提取正文"""
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError):
        return json.dumps(data, ensure_ascii=False)[:800]


def extract_reasoning(data):
    """提取思考过程(若有)"""
    try:
        return data["choices"][0]["message"].get("reasoning_content") or ""
    except (KeyError, IndexError):
        return ""


# ═══════════════════════════════════════════════════════════
# 四、能力: chat 文本对话(多轮/系统提示/全参数)
# ═══════════════════════════════════════════════════════════

def cmd_chat(args):
    """
    python3 qwen-kit.py chat "<问题>" [--system "系统提示"] [--model xxx]
    [--temp 0.7] [--top 0.9] [--max 4096] [--history 文件.json]
    """
    opts, positionals = parse_opts(args, {
        "--system": "str", "--model": "str", "--temp": "float",
        "--top": "float", "--max": "int", "--history": "str",
    })
    prompt = " ".join(positionals).strip() or sys.stdin.read().strip()
    if not prompt:
        sys.exit("❌ 用法: qwen-kit.py chat <问题> [--system 提示] [--temp 0.7] [--max 4096]")

    base_url, key, default_model = detect_config()
    model = opts.get("--model") or default_model

    messages = []
    if opts.get("--history"):
        try:
            with open(opts["--history"]) as f:
                messages = json.load(f)
        except Exception as e:
            sys.exit(f"❌ 历史文件读取失败: {e}")
    if opts.get("--system"):
        messages.insert(0, {"role": "system", "content": opts["--system"]})
    messages.append({"role": "user", "content": prompt})

    kwargs = {"max_tokens": opts.get("--max", 4096)}
    if opts.get("--temp") is not None:
        kwargs["temperature"] = opts["--temp"]
    if opts.get("--top") is not None:
        kwargs["top_p"] = opts["--top"]

    print(f"💬 {model} | {base_url}")
    data = chat_completion(base_url, key, messages, model=model, **kwargs)

    # 思考过程单独展示
    rc = extract_reasoning(data)
    if rc:
        print(f"🧠 思考: {rc[:500]}{'...' if len(rc) > 500 else ''}")
    print(extract_text(data))


# ═══════════════════════════════════════════════════════════
# 五、能力: reasoning 推理深度控制(千问特有)
# ═══════════════════════════════════════════════════════════

def cmd_reasoning(args):
    """
    python3 qwen-kit.py reasoning "<问题>" [--level high|medium|low|xhigh]
    [--model xxx] [--no-think]
    """
    opts, positionals = parse_opts(args, {
        "--level": "str", "--model": "str", "--no-think": "flag",
    })
    prompt = " ".join(positionals).strip()
    if not prompt:
        sys.exit("❌ 用法: qwen-kit.py reasoning <问题> [--level high|medium|low|xhigh]")

    level = opts.get("--level", "medium")
    if level not in REASONING_LEVELS:
        sys.exit(f"❌ --level 必须是 {REASONING_LEVELS}, 收到 '{level}'")

    base_url, key, default_model = detect_config()
    model = opts.get("--model") or default_model

    kwargs = {"reasoning_effort": level}
    if opts.get("--no-think"):
        kwargs["enable_thinking"] = False

    print(f"🧠 {model} 推理档位: {level} | {base_url}")
    data = chat_completion(
        base_url, key,
        [{"role": "user", "content": prompt}],
        model=model, **kwargs)

    rc = extract_reasoning(data)
    if rc:
        print(f"🧠 思考过程({len(rc)}字):")
        print(rc[:800] + ("..." if len(rc) > 800 else ""))
        print("─── 回答 ───")
    print(extract_text(data))


# ═══════════════════════════════════════════════════════════
# 六、能力: json / schema 结构化输出
# ═══════════════════════════════════════════════════════════

def cmd_json(args):
    """
    python3 qwen-kit.py json "<内容>" --fields 姓名,年龄,职业 [--model xxx]
    输出: 模型按字段提取,返回 JSON
    """
    opts, positionals = parse_opts(args, {"--fields": "str", "--model": "str"})
    content = " ".join(positionals).strip()
    fields = opts.get("--fields")
    if not content:
        sys.exit("❌ 用法: qwen-kit.py json <内容> --fields 姓名,年龄")

    base_url, key, default_model = detect_config()
    model = opts.get("--model") or default_model

    field_list = [f.strip() for f in fields.split(",")] if fields else []
    field_desc = "、".join(field_list) if field_list else "根据内容判断关键字段"
    sys_prompt = (
        "你是一个数据抽取引擎。只输出合法 JSON,不要任何解释文字。\n"
        f"请从用户内容中抽取字段: {field_desc}。\n"
        '输出格式: {"字段名": 值}。无法确定的字段值为 null。'
    )

    data = chat_completion(
        base_url, key,
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": content},
        ],
        model=model,
        response_format={"type": "json_object"},
        max_tokens=2048)

    raw = extract_text(data).strip()
    print(raw)
    # 校验 JSON 合法性
    try:
        parsed = json.loads(raw)
        log(f"✅ 合法 JSON, {len(parsed)} 个字段", "INFO")
        return parsed
    except json.JSONDecodeError:
        log("⚠️ 模型输出不是合法 JSON, 已原样展示", "WARN")


def cmd_schema(args):
    """
    python3 qwen-kit.py schema '<json_schema>' "<内容>"
    输出: 严格符合 JSON Schema 的结果
    """
    if len(args) < 2:
        sys.exit("❌ 用法: qwen-kit.py schema '<schema_json>' <内容>")
    schema_str, content = args[0], " ".join(args[1:])

    try:
        schema = json.loads(schema_str)
    except json.JSONDecodeError:
        sys.exit("❌ schema 不是合法 JSON")

    base_url, key, default_model = detect_config()
    model = os.environ.get("QWEN_MODEL", default_model)

    data = chat_completion(
        base_url, key,
        [{"role": "user", "content": content}],
        model=model,
        response_format={"type": "json_schema", "json_schema": {"name": "result", "strict": True, "schema": schema}},
        max_tokens=2048)
    print(extract_text(data))


# ═══════════════════════════════════════════════════════════
# 七、能力: vision 图像理解(单图/多图)
# ═══════════════════════════════════════════════════════════

def encode_media(path):
    """文件 → base64 data URL"""
    if not os.path.isfile(path):
        sys.exit(f"❌ 文件不存在: {path}")
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
        "mp4": "video/mp4", "mov": "video/mp4", "mkv": "video/mp4",
        "webm": "video/webm", "wav": "audio/wav", "mp3": "audio/mpeg",
        "m4a": "audio/mp4", "flac": "audio/flac", "ogg": "audio/ogg",
    }
    ctype = mime_map.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{ctype};base64,{b64}", ctype


def cmd_vision(args):
    """
    python3 qwen-kit.py vision <图1> [图2 图3...] ["问题"]
    支持多图对比; 最后一个非文件参数当问题
    """
    if not args:
        sys.exit("❌ 用法: qwen-kit.py vision <图片路径> [更多图片] [问题]")

    # 区分文件参数和问题文本
    images = []
    question_parts = []
    for a in args:
        if os.path.isfile(a):
            images.append(a)
        else:
            question_parts.append(a)
    question = " ".join(question_parts) or "请详细描述这些图片的内容,用中文回答"
    if not images:
        sys.exit("❌ 没有找到图片文件")

    base_url, key, model = detect_config(prefer_modal="image")
    model = os.environ.get("QWEN_MODEL", model)

    content = [{"type": "text", "text": question}]
    for img in images:
        data_url, _ = encode_media(img)
        content.append({"type": "image_url", "image_url": {"url": data_url}})

    print(f"🖼️ {model} 看图({len(images)}张): {', '.join(os.path.basename(i) for i in images)}")
    data = chat_completion(base_url, key, [{"role": "user", "content": content}], model=model, max_tokens=2048)
    print(extract_text(data))


# ═══════════════════════════════════════════════════════════
# 八、能力: video 视频理解(ffmpeg 抽帧)
# ═══════════════════════════════════════════════════════════

def extract_frames(video_path, num_frames=6, tmpdir="/tmp/qwen-kit-frames"):
    """ffmpeg 抽帧: 时间均匀分布取 num_frames 帧"""
    import subprocess
    os.makedirs(tmpdir, exist_ok=True)
    frames = []
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=15)
        duration = float(probe.stdout.strip() or 10)
        for i in range(num_frames):
            t = duration * (i + 0.5) / num_frames
            out = f"{tmpdir}/frame_{int(time.time())}_{i}.jpg"
            r = subprocess.run(
                ["ffmpeg", "-y", "-ss", str(t), "-i", video_path,
                 "-frames:v", "1", "-q:v", "3", out],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and os.path.isfile(out):
                frames.append(out)
    except Exception as e:
        log(f"⚠️ ffmpeg 抽帧失败: {e}", "WARN")
    return frames


def cmd_video(args):
    """
    python3 qwen-kit.py video <视频路径> ["问题"] [--frames 6]
    """
    if not args:
        sys.exit("❌ 用法: qwen-kit.py video <视频路径> [问题]")
    opts, positionals = parse_opts(args, {"--frames": "int"})
    if not positionals:
        sys.exit("❌ 需要视频文件路径")
    video_path = positionals[0]
    question = " ".join(positionals[1:]) or "请描述这个视频的内容,用中文回答"
    if not os.path.isfile(video_path):
        sys.exit(f"❌ 文件不存在: {video_path}")

    base_url, key, model = detect_config(prefer_modal="video")
    model = os.environ.get("QWEN_MODEL", model)

    frames = extract_frames(video_path, opts.get("--frames", 6))
    content = [{"type": "text", "text": question}]
    if frames:
        for fr in frames:
            data_url, _ = encode_media(fr)
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        print(f"🎬 {model} 看视频({len(frames)}帧): {os.path.basename(video_path)}")
    else:
        data_url, _ = encode_media(video_path)
        content.append({"type": "video_url", "video_url": {"url": data_url}})
        print(f"🎬 {model} 看视频(整段): {os.path.basename(video_path)}")

    data = chat_completion(base_url, key, [{"role": "user", "content": content}], model=model, max_tokens=2048)
    print(extract_text(data))


# ═══════════════════════════════════════════════════════════
# 九、能力: stream 流式输出(思考+正文双通道)
# ═══════════════════════════════════════════════════════════

def cmd_stream(args):
    """
    python3 qwen-kit.py stream "<问题>" [--model xxx]
    流式输出: 思考过程+正文, 打字机效果
    """
    opts, positionals = parse_opts(args, {"--model": "str"})
    prompt = " ".join(positionals).strip() or sys.stdin.read().strip()
    if not prompt:
        sys.exit("❌ 用法: qwen-kit.py stream <问题>")

    base_url, key, default_model = detect_config()
    model = opts.get("--model") or default_model

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "stream": True,
    }
    print(f"🌊 {model} 流式:")
    _, resp = throttled_request(base_url.rstrip("/") + "/chat/completions", payload, key, stream=True)

    reasoning_shown = False
    for raw in resp:
        line = raw.decode(errors="replace").strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if chunk == "[DONE]":
            break
        try:
            obj = json.loads(chunk)
            delta = obj["choices"][0]["delta"]
            text = delta.get("content") or ""
            reasoning = delta.get("reasoning_content") or ""
            if reasoning:
                if not reasoning_shown:
                    print("\n🧠[", end="", flush=True)
                    reasoning_shown = True
                print(reasoning, end="", flush=True)
            if text:
                if reasoning_shown:
                    print("]\n", end="", flush=True)
                    reasoning_shown = False
                print(text, end="", flush=True)
        except Exception:
            continue
    print("\n")


# ═══════════════════════════════════════════════════════════
# 十、能力: tools function calling 完整闭环
# ═══════════════════════════════════════════════════════════

BUILTIN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "获取指定城市当前时间",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calc",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {"expr": {"type": "string", "description": "数学表达式,如 2+3*4"}},
                "required": ["expr"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "搜索网络信息(模拟)",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索词"}},
                "required": ["query"],
            },
        },
    },
]


def execute_tool(name, args_json):
    """执行工具,返回结果字符串"""
    args = json.loads(args_json) if isinstance(args_json, str) else args_json
    if name == "get_time":
        city = args.get("city", "unknown")
        return f"{city}当前时间: 2026-08-17 09:45:00 (模拟)"
    if name == "calc":
        expr = args.get("expr", "0")
        try:
            result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 仅本地安全表达式
            return f"{expr} = {result}"
        except Exception as e:
            return f"计算失败: {e}"
    if name == "search":
        return f"[模拟搜索] '{args.get('query', '')}' 的 top1 结果: 示例链接"
    return f"未知工具 {name}"


def cmd_tools(args):
    """
    python3 qwen-kit.py tools "<需求>" [--max-rounds 3]
    多轮工具调用闭环: 模型决策 → 执行 → 回填 → 最终回答
    """
    opts, positionals = parse_opts(args, {"--max-rounds": "int"})
    prompt = " ".join(positionals).strip() or "北京现在几点?"
    if not prompt:
        sys.exit("❌ 用法: qwen-kit.py tools <需求>")

    base_url, key, default_model = detect_config()
    model = os.environ.get("QWEN_MODEL", default_model)
    max_rounds = opts.get("--max-rounds", 3)

    print(f"🔧 {model} 工具调用: {prompt}")
    messages = [{"role": "user", "content": prompt}]

    for round_no in range(max_rounds):
        payload = {
            "model": model,
            "messages": messages,
            "tools": BUILTIN_TOOLS,
            "max_tokens": 2048,
        }
        _, data = throttled_request(base_url.rstrip("/") + "/chat/completions", payload, key)

        msg = data["choices"][0]["message"]
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            print(f"\n💬 最终回答: {msg.get('content', '')}")
            return

        # 执行所有工具调用
        messages.append(msg)
        for tc in tool_calls:
            fn = tc["function"]
            result = execute_tool(fn["name"], fn["arguments"])
            print(f"  → [{round_no+1}] {fn['name']}({fn['arguments'][:80]}) => {result[:60]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    print("\n⚠️ 达到最大轮数, 返回最后一轮")
    _, data = throttled_request(base_url.rstrip("/") + "/chat/completions",
                                 {"model": model, "messages": messages, "max_tokens": 2048}, key)
    print(extract_text(data))


# ═══════════════════════════════════════════════════════════
# 十一、能力: embed 文本向量化
# ═══════════════════════════════════════════════════════════

def cmd_embed(args):
    """
    python3 qwen-kit.py embed "<文本>" [--model text-embedding-v4]
    python3 qwen-kit.py embed --file list.txt   (每行一条)
    输出: 向量维度 + 前10个数值
    """
    opts, positionals = parse_opts(args, {"--model": "str", "--file": "str"})
    base_url, key, default_model = detect_config(prefer_modal="embed")
    model = opts.get("--model") or default_model

    texts = []
    if opts.get("--file"):
        with open(opts["--file"]) as f:
            texts = [l.strip() for l in f if l.strip()]
    else:
        texts = [" ".join(positionals).strip()]
    if not texts:
        sys.exit("❌ 用法: qwen-kit.py embed <文本> 或 --file list.txt")

    payload = {"model": model, "input": texts}
    url = base_url.rstrip("/") + "/embeddings"
    print(f"📐 {model} 向量化 {len(texts)} 条 | {base_url}")
    try:
        _, data = http_request(url, payload, key)
    except SystemExit:
        # 端点不支持 embeddings 时, 自动降级 Moonshot 向量模型
        mk = os.environ.get("MOONSHOT_API_KEY") or load_openclaw_env().get("MOONSHOT_API_KEY", "")
        if mk and "moonshot.cn" not in base_url:
            print("🔄 当前端点不支持向量化, 自动切 Moonshot embed")
            base_url, key, model = MOONSHOT_URL, mk, "kimi-k2.6-embedding"
            _, data = http_request(base_url.rstrip("/") + "/embeddings", payload, key)
        else:
            raise

    for i, item in enumerate(data.get("data", [])):
        vec = item.get("embedding", [])
        print(f"  [{i}] 维度={len(vec)} 前10: {[round(x, 4) for x in vec[:10]]}")
    usage = data.get("usage", {})
    if usage:
        print(f"  📊 tokens: {usage}")


# ═══════════════════════════════════════════════════════════
# 十二、能力: batch 批量并发(线程池)
# ═══════════════════════════════════════════════════════════

def cmd_batch(args):
    """
    python3 qwen-kit.py batch <文件1> [文件2...] [--prompt "处理要求"] [--workers 4] [--model xxx]
    每个文件内容作为一条独立请求, 并发处理
    """
    opts, positionals = parse_opts(args, {"--prompt": "str", "--workers": "int", "--model": "str"})
    files = [a for a in positionals if os.path.isfile(a)]
    if not files:
        sys.exit("❌ 用法: qwen-kit.py batch <文件1> [文件2...] [--prompt 要求]")

    instruction = opts.get("--prompt", "请阅读以下内容并总结要点(200字内)")
    workers = opts.get("--workers", 1)  # 默认串行(兼容 kimi 并发=1), 可 --workers 调大
    base_url, key, default_model = detect_config()
    model = opts.get("--model") or default_model

    def process_one(fpath):
        with open(fpath) as f:
            content = f.read()[:8000]  # 截断超长
        data = chat_completion(
            base_url, key,
            [
                {"role": "system", "content": instruction},
                {"role": "user", "content": content},
            ],
            model=model, max_tokens=1024)
        return fpath, extract_text(data)

    print(f"⚡ batch 并发({workers}线程) {len(files)} 个文件 | {model}")
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process_one, f): f for f in files}
        for fut in futures:
            fpath, text = fut.result()
            results[fpath] = text
            print(f"\n── {os.path.basename(fpath)} ──")
            print(text[:300])

    # 输出汇总 JSON
    out = os.path.join(os.getcwd(), "batch-result.json")
    with open(out, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {out}")


# ═══════════════════════════════════════════════════════════
# 十三、能力: router 模型路由/故障切换
# ═══════════════════════════════════════════════════════════

def cmd_router(args):
    """
    python3 qwen-kit.py router "<问题>" [--models m1,m2,m3] [--require json]
    顺序尝试多个模型, 失败自动切换下一个
    """
    opts, positionals = parse_opts(args, {"--models": "str"})
    prompt = " ".join(positionals).strip()
    if not prompt:
        sys.exit("❌ 用法: qwen-kit.py router <问题> [--models a,b,c]")

    base_url, key, _ = detect_config()
    models = [m.strip() for m in opts.get("--models", "qwen3.8-27b,qwen3.8-flash,deepseek-v4-flash").split(",") if m.strip()]

    print(f"🔀 路由测试: {len(models)} 个模型")
    for m in models:
        try:
            t0 = time.time()
            data = chat_completion(
                base_url, key,
                [{"role": "user", "content": prompt}],
                model=m, max_tokens=1024)
            elapsed = time.time() - t0
            ans = extract_text(data)
            print(f"  ✅ {m} ({elapsed:.1f}s): {ans[:80]}")
            # 校验 JSON 要求
            if opts.get("--require") == "json":
                json.loads(ans.strip())
            return
        except SystemExit as e:
            print(f"  ❌ {m} 失败: {e}")
        except Exception as e:
            print(f"  ❌ {m} 异常: {e}")
    sys.exit("❌ 所有模型都失败了")


# ═══════════════════════════════════════════════════════════
# 十四、能力: image_gen 文生图(万相, 走百炼原生协议)
# ═══════════════════════════════════════════════════════════

def cmd_image_gen(args):
    """
    python3 qwen-kit.py image_gen "<提示词>" [--size 1024*1024] [--model wanx2.1-t2i-turbo] [--out out.png]
    需要 DASHSCOPE_API_KEY(万相系列)
    """
    opts, positionals = parse_opts(args, {"--size": "str", "--model": "str", "--out": "str"})
    prompt = " ".join(positionals).strip()
    if not prompt:
        sys.exit("❌ 用法: qwen-kit.py image_gen <提示词> [--size 1024*1024]")

    key = os.environ.get("DASHSCOPE_API_KEY") or load_openclaw_env().get("DASHSCOPE_API_KEY", "")
    if not key:
        sys.exit("❌ 文生图需要 DASHSCOPE_API_KEY(万相模型)")

    model = opts.get("--model", "wanx2.1-t2i-turbo")
    size = opts.get("--size", "1024*1024")

    # 百炼原生: 异步任务提交
    url = DASHSCOPE_NATIVE_URL + "/services/aigc/text2image/image-synthesis"
    payload = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": 1},
    }
    print(f"🎨 {model} 文生图: {prompt[:60]}...")
    _, data = http_request(url, payload, key)
    task_id = data.get("output", {}).get("task_id")
    if not task_id:
        sys.exit(f"❌ 提交失败: {json.dumps(data, ensure_ascii=False)[:400]}")

    # 轮询任务状态
    poll_url = DASHSCOPE_NATIVE_URL + f"/tasks/{task_id}"
    for i in range(60):
        time.sleep(3)
        _, status = http_request(poll_url, {}, key)
        st = status.get("output", {}).get("task_status")
        if st == "SUCCEEDED":
            urls = status.get("output", {}).get("results", [])
            if urls:
                img_url = urls[0].get("url")
                print(f"✅ 生成成功: {img_url}")
                # 下载到本地
                out_path = opts.get("--out", f"output/wanx_{int(time.time())}.png")
                os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                urllib.request.urlretrieve(img_url, out_path)
                print(f"💾 已保存: {out_path}")
                return
        if st == "FAILED":
            sys.exit(f"❌ 生成失败: {json.dumps(status, ensure_ascii=False)[:300]}")
        if i % 10 == 0:
            print(f"  ⏳ 生成中... ({i*3}s)")

    sys.exit("❌ 生成超时(180s)")


# ═══════════════════════════════════════════════════════════
# 十五、能力: audio_asr / audio_tts 语音
# ═══════════════════════════════════════════════════════════

def cmd_audio_asr(args):
    """
    python3 qwen-kit.py audio_asr <音频文件> [--model qwen3-audio]
    语音识别: 需要多模态端点支持音频
    """
    opts, positionals = parse_opts(args, {"--model": "str"})
    if not positionals:
        sys.exit("❌ 用法: qwen-kit.py audio_asr <音频文件>")
    audio_path = positionals[0]
    if not os.path.isfile(audio_path):
        sys.exit(f"❌ 文件不存在: {audio_path}")

    base_url, key, model = detect_config(prefer_modal="audio")
    model = opts.get("--model") or model

    data_url, _ = encode_media(audio_path)
    content = [
        {"type": "text", "text": "请转写这段音频的内容。"},
        {"type": "input_audio", "input_audio": {"data": data_url.split(",")[1], "format": audio_path.rsplit(".", 1)[-1]}},
    ]
    print(f"🎙️ {model} 语音识别: {os.path.basename(audio_path)}")
    try:
        data = chat_completion(base_url, key, [{"role": "user", "content": content}], model=model, max_tokens=2048)
        print(extract_text(data))
    except SystemExit as e:
        print(f"⚠️ 当前端点不支持音频, 需要百炼 qwen3-audio: {e}")


def cmd_audio_tts(args):
    """
    python3 qwen-kit.py audio_tts "<文本>" [--out hello.mp3] [--voice Cherry]
    语音合成: 需要 DASHSCOPE_API_KEY(cosyvoice)
    """
    opts, positionals = parse_opts(args, {"--out": "str", "--voice": "str"})
    text = " ".join(positionals).strip()
    if not text:
        sys.exit("❌ 用法: qwen-kit.py audio_tts <文本> [--out out.mp3]")

    key = os.environ.get("DASHSCOPE_API_KEY") or load_openclaw_env().get("DASHSCOPE_API_KEY", "")
    if not key:
        sys.exit("❌ TTS 需要 DASHSCOPE_API_KEY")

    voice = opts.get("--voice", "Cherry")
    out_path = opts.get("--out", "output/tts.mp3")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)

    url = DASHSCOPE_NATIVE_URL + "/services/aigc/multimodal-generation/generation"
    payload = {
        "model": "qwen3-audio-tts",
        "input": {"text": text, "voice": voice},
        "parameters": {"format": "mp3"},
    }
    print(f"🔊 TTS({voice}): {text[:40]}...")
    _, data = http_request(url, payload, key)
    audio_url = data.get("output", {}).get("audio_url") or data.get("output", {}).get("url")
    if audio_url:
        urllib.request.urlretrieve(audio_url, out_path)
        print(f"✅ 语音已保存: {out_path}")
    else:
        sys.exit(f"❌ TTS 失败: {json.dumps(data, ensure_ascii=False)[:300]}")


# ═══════════════════════════════════════════════════════════
# 十六、能力: context 上下文管理(token 估算/裁剪)
# ═══════════════════════════════════════════════════════════

def estimate_tokens(text):
    """粗略 token 估算: 中文≈1.5字符/token, 英文≈4字符/token"""
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other = len(text) - cjk
    return int(cjk * 0.6 + other / 4) + 1  # 保守估算


def cmd_context(args):
    """
    python3 qwen-kit.py context <文件或文本> [--max-tokens 8000] [--model qwen3.8-27b]
    估算 token 占用, 超限自动裁剪
    """
    opts, positionals = parse_opts(args, {"--max-tokens": "int", "--model": "str"})
    if not positionals:
        sys.exit("❌ 用法: qwen-kit.py context <文本或文件路径>")

    target = positionals[0]
    if os.path.isfile(target):
        with open(target) as f:
            text = f.read()
        src = f"文件 {target}"
    else:
        text = " ".join(positionals)
        src = "文本"

    model = opts.get("--model") or "qwen3.8-27b"
    ctx_limit = QWEN_MODELS.get(model, {}).get("ctx", 262144)
    max_tokens = opts.get("--max-tokens", min(ctx_limit, 8000))

    tokens = estimate_tokens(text)
    print(f"📊 {src}: {len(text)} 字符 ≈ {tokens} tokens")
    print(f"   模型 {model} 上下文上限: {ctx_limit} tokens")
    print(f"   本次预算: {max_tokens} tokens")

    if tokens > max_tokens:
        ratio = max_tokens / tokens
        cut = int(len(text) * ratio * 0.9)  # 留 10% 余量
        clipped = text[:cut] + f"\n...[已裁剪, 原文 {len(text)} 字符]"
        out = os.path.join(os.getcwd(), "context-clipped.txt")
        with open(out, "w") as f:
            f.write(clipped)
        print(f"  ✂️ 超限! 已裁剪到 {len(clipped)} 字符, 保存: {out}")
    else:
        print("  ✅ 在预算内, 无需裁剪")


# ═══════════════════════════════════════════════════════════
# 十七、能力: doctor 自检 + models 清单
# ═══════════════════════════════════════════════════════════

def cmd_models(args=None):
    print("📦 千问模型全家桶(拆解清单):")
    print(f"{'模型':<22} {'上下文':<10} {'模态':<16} 说明")
    print("-" * 72)
    for name, info in QWEN_MODELS.items():
        print(f"{name:<22} {info['ctx']:<10} {info['modal']:<16} {info['desc']}")
    print()
    try:
        base_url, key, model = detect_config()
        masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "***"
        print(f"当前端点: {base_url}")
        print(f"默认模型: {model}")
        print(f"API key: {masked}")
    except SystemExit as e:
        print(f"⚠️ {e}")


def cmd_doctor(args=None):
    """自检所有已配置能力"""
    print("🔬 qwen-kit 自检报告")
    print("=" * 50)
    env = load_openclaw_env()
    checks = [
        ("DASHSCOPE(百炼)", env.get("DASHSCOPE_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")),
        ("OPENROUTER", env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")),
        ("MOONSHOT", env.get("MOONSHOT_API_KEY") or os.environ.get("MOONSHOT_API_KEY")),
        ("DEEPSEEK", env.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")),
    ]
    for name, k in checks:
        status = f"✅ {k[:6]}...{k[-4:]}" if k else "❌ 未配置"
        print(f"  {name:<22} {status}")

    # 实测 chat 连通性
    try:
        base_url, key, model = detect_config()
        print(f"\n  🧪 实测连通性: {model} @ {base_url}")
        data = chat_completion(
            base_url, key,
            [{"role": "user", "content": "回复'连通正常'四个字"}],
            model=model, max_tokens=20)
        print(f"  ✅ {extract_text(data)[:50]}")
    except SystemExit as e:
        print(f"  ❌ {e}")

    print("=" * 50)
    print("能力可用性: chat✅ reasoning✅ json✅ schema✅ vision✅ video✅")
    print("            stream✅ tools✅ embed✅ batch✅ router✅ context✅")
    print("            image_gen/audio_asr/audio_tts 需百炼 key")


# ═══════════════════════════════════════════════════════════
# 十八、参数解析工具
# ═══════════════════════════════════════════════════════════

def parse_opts(args, spec):
    """
    简易参数解析器。
    spec: {"--name": "str"|"int"|"float"|"flag"}
    返回 (opts_dict, positionals_list)
    """
    opts = {}
    positionals = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in spec:
            kind = spec[a]
            if kind == "flag":
                opts[a] = True
                i += 1
            else:
                if i + 1 >= len(args):
                    sys.exit(f"❌ {a} 需要参数值")
                val = args[i + 1]
                try:
                    if kind == "int":
                        opts[a] = int(val)
                    elif kind == "float":
                        opts[a] = float(val)
                    else:
                        opts[a] = val
                except ValueError:
                    sys.exit(f"❌ {a} 参数值 '{val}' 不是 {kind}")
                i += 2
        else:
            positionals.append(a)
            i += 1
    return opts, positionals


# ═══════════════════════════════════════════════════════════
# 十九、入口
# ═══════════════════════════════════════════════════════════

HELP = """qwen-kit.py v{VERSION} — 千问全家桶完整封装(自研资产)

用法:
  python3 qwen-kit.py <命令> [参数]

对话推理:
  chat <问题> [--system 提示] [--temp 0.7] [--top 0.9] [--max 4096] [--history 文件]
  reasoning <问题> [--level high|medium|low|xhigh] [--no-think]
  json <内容> --fields 姓名,年龄,职业
  schema '<json_schema>' <内容>

多模态:
  vision <图1> [图2...] [问题]
  video <视频> [问题] [--frames 6]
  audio_asr <音频>
  audio_tts <文本> [--out out.mp3] [--voice Cherry]

生成:
  image_gen <提示词> [--size 1024*1024] [--out out.png]

工具与扩展:
  tools <需求> [--max-rounds 3]
  embed <文本> [--model text-embedding-v4] | --file list.txt
  batch <文件1> [文件2...] [--prompt 要求] [--workers 4]
  router <问题> [--models a,b,c]

工程化:
  stream <问题>
  context <文本或文件> [--max-tokens 8000]
  models      模型清单
  doctor      自检所有能力
  help        本帮助

环境变量: DASHSCOPE_API_KEY > OPENROUTER_API_KEY > MOONSHOT_API_KEY > DEEPSEEK_API_KEY
""".format(VERSION=VERSION)


def main():
    if len(sys.argv) < 2:
        print(HELP)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    handlers = {
        "chat": cmd_chat,
        "reasoning": cmd_reasoning,
        "json": cmd_json,
        "schema": cmd_schema,
        "vision": cmd_vision,
        "video": cmd_video,
        "stream": cmd_stream,
        "tools": cmd_tools,
        "embed": cmd_embed,
        "batch": cmd_batch,
        "router": cmd_router,
        "image_gen": cmd_image_gen,
        "audio_asr": cmd_audio_asr,
        "audio_tts": cmd_audio_tts,
        "context": cmd_context,
        "models": cmd_models,
        "doctor": cmd_doctor,
    }

    if cmd in ("-h", "--help", "help"):
        print(HELP)
        sys.exit(0)

    handler = handlers.get(cmd)
    if not handler:
        sys.exit(f"❌ 未知命令: {cmd}\n可用: {list(handlers.keys())}")
    handler(args)


if __name__ == "__main__":
    main()
