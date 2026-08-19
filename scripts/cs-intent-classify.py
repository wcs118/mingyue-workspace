#!/usr/bin/env python3
"""客服意图/情绪分类 — 调 DeepSeek API,输出 JSON。

用法:
  scripts/cs-intent-classify.py "客户消息"
  可选第二个参数为对话上下文(多轮时拼接)

环境变量:
  DEEPSEEK_API_KEY  (必填)
  DEEPSEEK_MODEL    可选,默认 deepseek-v4-flash
"""
import json
import os
import sys
import urllib.request

BASE = "https://api.deepseek.com"
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

SYSTEM = """你是客服意图分类器。把客户消息归到 咨询/售后/投诉/营销/其他 五类之一,
并给出情绪、紧急度、是否转人工。只输出一个 JSON 对象,不要任何多余文字。

JSON 字段(固定):
{
  "intent": "咨询|售后|投诉|营销|其他",
  "sub_intent": "<细分类,如 物流查询/退换货/退款纠纷>",
  "emotion": "平静|焦虑|愤怒|感激|中性",
  "urgency": "低|中|高",
  "route_to_human": true/false,
  "human_reason": "<一句理由>"
}
规则:投诉升级、情绪激烈、舆情风险、反复催促 → route_to_human=true;情绪与紧急度要一致。"""


def deepseek_chat(messages):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("❌ 缺少环境变量 DEEPSEEK_API_KEY")
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 1000,
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        content = json.load(r)["choices"][0]["message"]["content"]
    if not content:
        # 推理模型 max_tokens 太小时 content 可能被 reasoning 吃空 → 放大重试
        body = json.dumps({
            "model": MODEL,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 2000,
        }).encode()
        req = urllib.request.Request(
            BASE + "/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            content = json.load(r)["choices"][0]["message"]["content"]
    return content


def strip_json(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    return t.strip()


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    msg = sys.argv[1]
    ctx = sys.argv[2] if len(sys.argv) > 2 else ""
    user = msg if not ctx else f"对话上下文:\n{ctx}\n\n最新客户消息:{msg}"
    raw = deepseek_chat([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ])
    try:
        obj = json.loads(strip_json(raw))
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(raw)


if __name__ == "__main__":
    main()
