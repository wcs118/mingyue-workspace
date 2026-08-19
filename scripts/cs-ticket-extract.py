#!/usr/bin/env python3
"""客服工单信息抽取 — 文本走 DeepSeek,截图/图片走 Kimi K2.6 视觉。

用法:
  # 文本抽取(DeepSeek)
  scripts/cs-ticket-extract.py --text "客户原话或对话"
  # 截图抽取(Kimi K2.6 多模态)
  scripts/cs-ticket-extract.py --image /path/to/screenshot.png "补充描述"

环境变量:
  DEEPSEEK_API_KEY  (文本抽取必填)
  MOONSHOT_API_KEY  (截图抽取必填)
  DEEPSEEK_MODEL / KIMI_MODEL  可选,默认 deepseek-v4-flash / kimi-k2.6
"""
import base64
import json
import os
import sys
import urllib.request

DEEPSEEK_BASE = "https://api.deepseek.com"
MOONSHOT_BASE = "https://api.moonshot.cn/v1"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
KIMI_MODEL = os.environ.get("KIMI_MODEL", "kimi-k2.6")

SYSTEM = """你是客服工单抽取器。从客户消息/截图抽取工单字段,只输出一个 JSON 对象,不要多余文字。
JSON 字段(固定):
{
  "order_id": "订单号或 null",
  "product": "商品/产品",
  "issue": "问题描述",
  "demand": "客户诉求",
  "urgency": "低|中|高",
  "contact": "联系方式或 null",
  "missing_fields": ["缺失字段"],
  "followup_question": "对缺失字段的一句追问"
}
规则:字段有据可依,不脑补;手机号/身份证等敏感字段脱敏(中间打星);缺失项必须列进 missing_fields。"""


def _post(url, payload, key, timeout=120):
    """
    post.
    
    Args:
        url: target URL.
        key: API key or secret.
        timeout: timeout in seconds.
    
    Returns:
        Result of the operation.
    """
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def deepseek_extract(text):
    """
    deepseek extract.
    
    Args:
        text: input text.
    
    Returns:
        Result of the operation.
    """
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("❌ 缺少环境变量 DEEPSEEK_API_KEY")
    d = _post(DEEPSEEK_BASE + "/chat/completions", {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"客户消息:\n{text}"},
        ],
        "temperature": 0.0, "max_tokens": 3000,
    }, key, 60)
    content = d["choices"][0]["message"]["content"]
    if not content:
        # 推理模型 max_tokens 太小时 content 被 reasoning 吃空(实测 500 时出现) → 放大重试
        d = _post(DEEPSEEK_BASE + "/chat/completions", {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"客户消息:\n{text}"},
            ],
            "temperature": 0.0, "max_tokens": 6000,
        }, key, 90)
        content = d["choices"][0]["message"]["content"]
    return content


def kimi_extract(image_path, note):
    """
    kimi extract.
    
    Returns:
        Result of the operation.
    """
    key = os.environ.get("MOONSHOT_API_KEY")
    if not key:
        raise SystemExit("❌ 缺少环境变量 MOONSHOT_API_KEY")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = image_path.rsplit(".", 1)[-1].lower()
    ctype = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    prompt = SYSTEM + f"\n\n{note}" if note else SYSTEM
    d = _post(MOONSHOT_BASE + "/chat/completions", {
        "model": KIMI_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{ctype};base64,{b64}"}},
        ]}],
        "max_tokens": 8000,
    }, key, 180)
    return d["choices"][0]["message"]["content"]


def strip_json(text):
    """
    strip json.
    
    Args:
        text: input text.
    
    Returns:
        Result of the operation.
    """
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    return t.strip()


def main():
    """
    main.
    """
    args = sys.argv[1:]
    if not args or args[0] not in ("--text", "--image"):
        raise SystemExit(__doc__)
    mode = args[0]
    if mode == "--text":
        if len(args) < 2:
            raise SystemExit("用法: cs-ticket-extract.py --text \"客户原话\"")
        raw = deepseek_extract(args[1])
    else:
        if len(args) < 2:
            raise SystemExit("用法: cs-ticket-extract.py --image <图片路径> [补充描述]")
        note = args[2] if len(args) > 2 else ""
        raw = kimi_extract(args[1], note)
    try:
        print(json.dumps(json.loads(strip_json(raw)), ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(raw)


if __name__ == "__main__":
    main()