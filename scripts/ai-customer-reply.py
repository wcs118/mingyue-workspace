#!/usr/bin/env python3
"""AI 客服应答话术生成 — 调 DeepSeek API。

用法:
  scripts/ai-customer-reply.py "客户消息" ["企业背景"]

环境变量:
  DEEPSEEK_API_KEY  (必填,不硬编码)
  DEEPSEEK_MODEL    可选,默认 deepseek-v4-flash
"""
import json
import os
import sys
import urllib.request

BASE = "https://api.deepseek.com"
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

SYSTEM = """你是资深电商客服话术专家。根据「企业背景」和客户消息,产出专业、共情、合规的客服回复。
规则:
1. 先判断情绪(平静/焦虑/愤怒/感激)与意图(咨询/售后/投诉/营销/闲聊)。
2. 出现投诉升级、舆情风险、超知识范围、情绪激烈 → 转人工=是,并给一句转接话术。
3. 回复结构:共情开场(一句)→ 直接给答案 → 下一步动作 → 收尾;语气匹配品牌。
4. 不编造事实;退款金额/时效等承诺一律加「以实际为准」。
5. 只输出下面格式的纯文本,不要多余解释:
情绪: <...>
意图: <...>
转人工: <是|否> — <原因,一句>
参考: <知识库id或"无">
回复:
<可直接发送的话术,多轮分行>"""


def deepseek_chat(messages):
    """
    deepseek chat.
    
    Returns:
        Result of the operation.
    """
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("❌ 缺少环境变量 DEEPSEEK_API_KEY")
    # 注意: deepseek-v4 是推理模型, max_tokens 太小会被 reasoning 吃光导致 content 为空
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1500,
    }).encode()
    req = urllib.request.Request(
        BASE + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        content = json.load(r)["choices"][0]["message"]["content"]
    if not content:
        # 推理吃光预算导致空内容 → 放大 max_tokens 重试一次
        body = json.dumps({
            "model": MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 3000,
        }).encode()
        req = urllib.request.Request(
            BASE + "/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            content = json.load(r)["choices"][0]["message"]["content"]
    return content


def main():
    """
    main.
    """
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    question = sys.argv[1]
    background = sys.argv[2] if len(sys.argv) > 2 else "通用电商客服(未提供背景,按通用政策拟答)"
    user = f"企业背景:\n{background}\n\n客户消息:{question}"
    print(deepseek_chat([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]))


if __name__ == "__main__":
    main()