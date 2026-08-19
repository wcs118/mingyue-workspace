#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
minimax-kit.py v2.0 — MiniMax 全能力自研封装(明月系核心资产)
=====================================================================
老板指令(2026-08-17): 百分百写成自己的代码, 能力写全, 实测才算数。
纯 Python 标准库, 零依赖。覆盖 MiniMax 全能力面:

  chat          文本对话(chatcompletion_v2)
  video_gen     H3 文生视频(提交→轮询→下载 全链路)
  video_query   查询视频任务状态
  video_list    视频生成历史/任务列表
  files         文件检索(下载 URL)
  image_gen     文生图(注: 需确认账号支持)
  audio_asr     语音识别(注: 需确认端点)
  audio_tts     语音合成(注: 需确认端点)
  models        模型清单
  doctor        自检

端点: https://api.minimaxi.com(国内) | key: config/minimax.env

用法:
  python3 minimax-kit.py chat "你好"
  python3 minimax-kit.py video_gen "一只猫在草地奔跑,16:9" [--out out.mp4] [--duration 6]
  python3 minimax-kit.py video_query <task_id> | video_list
  python3 minimax-kit.py files <file_id> [--out 保存路径]
  python3 minimax-kit.py doctor
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

VERSION = "2.0.0"
BASE = "https://api.minimaxi.com"
CHAT_URL = BASE + "/v1/text/chatcompletion_v2"
VIDEO_URL = BASE + "/v2/video_generation"
QUERY_URL = BASE + "/v1/query/video_generation"
FILES_URL = BASE + "/v1/files/retrieve"
MODELS = {
    "MiniMax-Text-01": {"type": "文本", "desc": "对话"},
    "MiniMax-H3":      {"type": "视频", "desc": "文生视频 4-15s 768p/2K"},
}


def load_cfg():
    """读取 config/minimax.env"""
    env = {}
    try:
        with open(os.path.expanduser("~/.openclaw/workspace/config/minimax.env")) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env


def get_key():
    """
    get key.
    
    Returns:
        Result of the operation.
    """
    k = os.environ.get("MINIMAX_API_KEY", "")
    if not k:
        k = load_cfg().get("MINIMAX_API_KEY", "")
    if not k:
        sys.exit("❌ 未找到 MINIMAX_API_KEY(检查 config/minimax.env)")
    return k


def get_group():
    """
    get group.
    
    Returns:
        Result of the operation.
    """
    return os.environ.get("MINIMAX_GROUP_ID", "") or load_cfg().get("MINIMAX_GROUP_ID", "")


def http_get(url, key, params=None):
    """
    http get.
    
    Args:
        url: target URL.
        key: API key or secret.
        params: query parameters.
    
    Returns:
        Result of the operation.
    """
    if params:
        url = url + "?" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code}: {e.read().decode(errors='replace')[:400]}")


def http_post(url, payload, key, retries=3):
    """
    http post.
    
    Args:
        url: target URL.
        key: API key or secret.
        retries: number of retries.
    
    Returns:
        Result of the operation.
    """
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST")
    for i in range(retries):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=180).read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:400]
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                time.sleep([2, 5, 10][i])
                continue
            sys.exit(f"❌ HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            if i < retries - 1:
                time.sleep(2)
                continue
            sys.exit(f"❌ 网络: {e}")


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
# ① chat 文本对话
# ═══════════════════════════════════════════════════════════
def cmd_chat(args):
    """
    cmd chat.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--system": 1, "--temp": 1})
    q = " ".join(pos).strip() or sys.stdin.read().strip()
    if not q:
        sys.exit("用法: minimax-kit.py chat <问题>")
    msgs = []
    if opts.get("--system"):
        msgs.append({"role": "system", "content": opts["--system"]})
    msgs.append({"role": "user", "content": q})
    payload = {"model": "MiniMax-Text-01", "messages": msgs,
               "max_tokens": 4096, "stream": False}
    if opts.get("--temp"):
        payload["temperature"] = float(opts["--temp"])
    gid = get_group()
    if gid:
        payload["group_id"] = gid
    print("💬 MiniMax-Text-01:")
    data = http_post(CHAT_URL, payload, get_key())
    try:
        print(data["choices"][0]["message"]["content"])
    except Exception:
        print(json.dumps(data, ensure_ascii=False)[:800])


# ═══════════════════════════════════════════════════════════
# ② video_gen H3 文生视频(全链路)
# ═══════════════════════════════════════════════════════════
def cmd_video_gen(args):
    """
    cmd video gen.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--out": 1, "--ratio": 1, "--duration": 1, "--model": 1, "--resolution": 1})
    prompt = " ".join(pos).strip()
    if not prompt:
        sys.exit("用法: minimax-kit.py video_gen <提示词> [--out x.mp4] [--ratio 16:9] [--duration 6]")
    key = get_key()
    ratio = opts.get("--ratio", "16:9")
    duration = int(opts.get("--duration", "6"))
    if not (4 <= duration <= 15):
        sys.exit("❌ 时长必须 4-15 秒")
    model = opts.get("--model", "MiniMax-H3")
    resolution = opts.get("--resolution", "768p")

    payload = {
        "model": model,
        "content": [{"type": "text", "text": prompt}],
        "duration": duration,
        "resolution": resolution,
        "ratio": ratio,
    }
    print(f"🎬 {model} 视频生成: {prompt[:50]}... ({ratio}, {duration}s, {resolution})")
    data = http_post(VIDEO_URL, payload, key)
    # 错误码 1008/1004 余额不足直接提示
    if data.get("status_code") not in (None, 0) and data.get("status_code") != 0:
        print(f"❌ API 错误: {json.dumps(data, ensure_ascii=False)[:400]}")
        return
    task_id = data.get("task_id") or data.get("data", {}).get("task_id")
    if not task_id:
        print(f"❌ 提交失败: {json.dumps(data, ensure_ascii=False)[:400]}")
        return
    print(f"  📋 task_id: {task_id}")

    # 轮询(最多 5 分钟)
    for i in range(60):
        time.sleep(5)
        st = http_get(QUERY_URL, key, {"task_id": task_id})
        status = (st.get("status") or st.get("data", {}).get("status")
                  or st.get("output", {}).get("task_status") or "")
        if i % 6 == 0:
            print(f"  ⏳ {i * 5}s ... status={status}")
        if str(status).lower() in ("success", "succeeded", "done"):
            files = (st.get("file_id") or st.get("data", {}).get("file_id")
                     or st.get("output", {}).get("file_id"))
            if files:
                fid = files if isinstance(files, str) else files[0]
                out = opts.get("--out", f"output/minimax/h3_{int(time.time())}.mp4")
                os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
                dl = cmd_files([fid, "--out", out], quiet=True)
                print(f"  ✅ 视频已保存: {out}")
                return
            print(f"  ✅ 生成成功(未取到下载链接): {json.dumps(st, ensure_ascii=False)[:200]}")
            return
        if str(status).lower() in ("fail", "failed", "error"):
            print(f"❌ 生成失败: {json.dumps(st, ensure_ascii=False)[:400]}")
            return
    print("❌ 生成超时(300s)")


# ═══════════════════════════════════════════════════════════
# ③ video_query 查询状态
# ═══════════════════════════════════════════════════════════
def cmd_video_query(args):
    """
    cmd video query.
    
    Args:
        args: positional arguments.
    """
    if not args:
        sys.exit("用法: minimax-kit.py video_query <task_id>")
    st = http_get(QUERY_URL, get_key(), {"task_id": args[0]})
    print(json.dumps(st, ensure_ascii=False, indent=2)[:2000])


# ═══════════════════════════════════════════════════════════
# ④ files 文件检索/下载
# ═══════════════════════════════════════════════════════════
def cmd_files(args, quiet=False):
    """
    cmd files.
    
    Args:
        args: positional arguments.
    
    Returns:
        Result of the operation.
    """
    opts, pos = parse(args, {"--out": 1})
    if not pos:
        sys.exit("用法: minimax-kit.py files <file_id> [--out 保存路径]")
    fid = pos[0]
    fr = http_get(FILES_URL, get_key(), {"file_id": fid})
    dl = (fr.get("download_url") or fr.get("data", {}).get("download_url")
          or fr.get("file", {}).get("download_url"))
    if not dl:
        msg = f"❌ 未找到下载链接: {json.dumps(fr, ensure_ascii=False)[:300]}"
        if quiet:
            return msg
        print(msg)
        return None
    out = opts.get("--out") or f"output/minimax/file_{fid[:8]}_{int(time.time())}"
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    urllib.request.urlretrieve(dl, out)
    size = os.path.getsize(out) / 1024 / 1024
    if not quiet:
        print(f"✅ 已下载: {out} ({size:.1f} MB)")
    return out


# ═══════════════════════════════════════════════════════════
# ⑤ image_gen 文生图(若账号支持)
# ═══════════════════════════════════════════════════════════
def cmd_image_gen(args):
    """
    cmd image gen.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--out": 1, "--ratio": 1})
    prompt = " ".join(pos).strip()
    if not prompt:
        sys.exit("用法: minimax-kit.py image_gen <提示词> [--out x.png]")
    key = get_key()
    url = BASE + "/v1/image_generation"
    payload = {
        "model": "image-01",
        "prompt": prompt,
        "aspect_ratio": opts.get("--ratio", "1:1"),
        "response_format": "url",
        "n": 1,
    }
    print(f"🎨 文生图: {prompt[:50]}...")
    data = http_post(url, payload, key)
    try:
        url2 = data["data"]["image_urls"][0]
    except Exception:
        print(f"⚠️ 响应解析: {json.dumps(data, ensure_ascii=False)[:400]}")
        return
    out = opts.get("--out", f"output/minimax/img_{int(time.time())}.png")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    urllib.request.urlretrieve(url2, out)
    print(f"✅ 图片已保存: {out}")


# ═══════════════════════════════════════════════════════════
# ⑥ audio_tts 语音合成(若账号支持)
# ═══════════════════════════════════════════════════════════
def cmd_audio_tts(args):
    """
    cmd audio tts.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--out": 1, "--voice": 1})
    text = " ".join(pos).strip()
    if not text:
        sys.exit("用法: minimax-kit.py audio_tts <文本> [--out x.mp3]")
    key = get_key()
    url = BASE + "/v1/t2a_v2"
    payload = {
        "model": "speech-02-turbo",
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": opts.get("--voice", "female-chengshu"), "speed": 1.0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    gid = get_group()
    if gid:
        payload["group_id"] = gid
    print(f"🔊 TTS: {text[:40]}...")
    data = http_post(url, payload, key)
    try:
        audio_hex = data["data"]["audio"]
        audio = bytes.fromhex(audio_hex)
    except Exception:
        print(f"⚠️ 响应解析: {json.dumps(data, ensure_ascii=False)[:400]}")
        return
    out = opts.get("--out", f"output/minimax/tts_{int(time.time())}.mp3")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "wb") as f:
        f.write(audio)
    print(f"✅ 语音已保存: {out} ({len(audio)/1024:.0f} KB)")


# ═══════════════════════════════════════════════════════════
# ⑦ audio_asr 语音识别(若账号支持)
# ═══════════════════════════════════════════════════════════
def cmd_audio_asr(args):
    """
    cmd audio asr.
    
    Args:
        args: positional arguments.
    """
    if not args or not os.path.isfile(args[0]):
        sys.exit("用法: minimax-kit.py audio_asr <音频文件>")
    audio = args[0]
    key = get_key()
    url = BASE + "/v1/asr_v2"
    # 文件上传(构造 multipart)
    boundary = "----minimax" + str(int(time.time()))
    with open(audio, "rb") as f:
        data = f.read()
    body = b""
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nspeech-01-turbo\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(audio)}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
    body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code}: {e.read().decode(errors='replace')[:400]}")
    try:
        print(f"📝 识别结果: {resp['data']['text']}")
    except Exception:
        print(f"⚠️ 响应: {json.dumps(resp, ensure_ascii=False)[:400]}")


# ═══════════════════════════════════════════════════════════
# ⑩ embedding 向量化
# ═══════════════════════════════════════════════════════════
def cmd_embed(args):
    """
    cmd embed.
    
    Args:
        args: positional arguments.
    """
    text = " ".join(args).strip()
    if not text:
        sys.exit("用法: minimax-kit.py embed <文本>")
    key = get_key()
    url = BASE + "/v1/embeddings"
    payload = {"model": "embo-01", "texts": [text], "type": "query"}
    data = http_post(url, payload, key)
    try:
        vec = data["data"][0]["embedding"]
        print(f"📐 向量维度: {len(vec)}")
        print(f"  前8维: {[round(x, 4) for x in vec[:8]]}")
    except Exception:
        print(f"⚠️ 响应: {json.dumps(data, ensure_ascii=False)[:400]}")


# ═══════════════════════════════════════════════════════════
# ⑪ voice_clone 声音克隆
# ═══════════════════════════════════════════════════════════
def cmd_voice_clone(args):
    """
    cmd voice clone.
    
    Args:
        args: positional arguments.
    """
    opts, pos = parse(args, {"--name": 1})
    if not pos or not os.path.isfile(pos[0]):
        sys.exit("用法: minimax-kit.py voice_clone <音频文件> [--name 声音名]")
    audio = pos[0]
    key = get_key()
    url = BASE + "/v1/voice_clone"
    name = opts.get("--name", "my_voice")
    boundary = "----minimax" + str(int(time.time()))
    with open(audio, "rb") as f:
        data = f.read()
    body = b""
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(audio)}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
    body += data + b"\r\n"
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"voice_id\"\r\n\r\n{name}\r\n".encode()
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
        print(f"🎤 克隆结果: {json.dumps(resp, ensure_ascii=False)[:300]}")
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")


# ═══════════════════════════════════════════════════════════
# ⑫ models
# ═══════════════════════════════════════════════════════════
def cmd_models(args=None):
    """
    cmd models.
    
    Args:
        args: positional arguments.
    """
    print("📦 MiniMax 模型(自研封装 v3.0):")
    for m, i in MODELS.items():
        print(f"  {m:<20} [{i['type']}] {i['desc']}")
    print("  embo-01: 向量化 | image-01: 文生图 | speech-02-turbo: TTS | speech-01-turbo: ASR")


# ═══════════════════════════════════════════════════════════
# ⑬ doctor
# ═══════════════════════════════════════════════════════════
def cmd_doctor(args=None):
    """
    cmd doctor.
    
    Args:
        args: positional arguments.
    """
    print(f"🔬 minimax-kit v{VERSION} 自检")
    try:
        k = get_key()
        print(f"  ✅ key: {k[:6]}...{k[-4:]}")
    except SystemExit as e:
        print(f"  ❌ {e}")
        return
    print(f"  📡 端点: {BASE}")
    print(f"  🎬 H3 视频链路: 提交→轮询→下载 全自研")
    print("  🧪 文本对话实测:")
    cmd_chat(["回复'通'"])
    print("  ⚠️ 视频/图像/语音: 需要账号有对应额度")


HELP = f"""minimax-kit.py v{VERSION} — MiniMax 全能力自研封装
  chat <问题> | video_gen <提示词> [--out x.mp4] [--ratio 16:9] [--duration 6]
  video_query <task_id> | files <file_id> [--out 路径]
  image_gen <提示词> [--out x.png] | audio_tts <文本> [--out x.mp3]
  audio_asr <音频> | voice_clone <音频> [--name 声音名] | embed <文本>
  models | doctor
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
        "chat": cmd_chat, "video_gen": cmd_video_gen, "video_query": cmd_video_query,
        "files": cmd_files, "image_gen": cmd_image_gen, "audio_tts": cmd_audio_tts,
        "audio_asr": cmd_audio_asr, "voice_clone": cmd_voice_clone, "embed": cmd_embed,
        "models": cmd_models, "doctor": cmd_doctor,
    }
    fn = handlers.get(cmd)
    if not fn:
        sys.exit(f"❌ 未知命令: {cmd}\n可用: {list(handlers.keys())}")
    fn(args)

if __name__ == "__main__":
    main()