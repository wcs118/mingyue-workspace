---
name: cs-ticket-extract
description: 客服工单信息抽取器。从客户对话文本或截图(多模态,走 Kimi K2.6 视觉)抽取订单号、商品、问题、诉求、紧急度、联系方式等工单字段,并标记缺失项。Use when 用户说"提取工单信息"、"从截图抽订单"、"客户报障要建单"、"识别图片里的订单号"、"把对话整理成工单"。
---

# CS Ticket Extract — 客服工单抽取

> "从对话和截图里,抽出能直接建单的字段"

## When to use

- 客服自动建单前提取字段 — "把这条对话整理成工单"
- 识别客户发的截图(订单/报障图) — "这截图里的订单号是多少"
- 补齐工单缺失字段 — "还差哪些信息才能建单"

## Workflow

1. **取输入**:文本对话,或图片/截图(有图时调用多模态视觉模型,如 Kimi K2.6 读图)。
2. **抽取字段**(能抽则抽):订单号、商品/产品、问题描述、诉求、紧急度、联系方式、时间。
3. **交叉校验**:文本与图片信息矛盾时,以图片为准并标注。
4. **缺失标记**:对每项标 `已抽到 / 缺失`,缺失项生成一句追问话术。
5. **去敏**:手机号/身份证等敏感字段脱敏(中间打星)。
6. **输出**结构化工单 JSON,可直接入工单系统。

## 脚本

`scripts/cs-ticket-extract.py` — 文本走 DeepSeek,截图走 Kimi K2.6 视觉:

```bash
export DEEPSEEK_API_KEY=...   # 文本抽取
export MOONSHOT_API_KEY=...   # 截图抽取
scripts/cs-ticket-extract.py --text "客户原话"
scripts/cs-ticket-extract.py --image /path/screenshot.png "补充描述"
```

## Output format

```json
{
  "order_id": "1234567890 | null",
  "product": "...",
  "issue": "...",
  "demand": "...",
  "urgency": "低|中|高",
  "contact": "138****1234 | null",
  "missing_fields": ["order_id"],
  "followup_question": "请提供订单号,方便我为您查询。"
}
```

## Quality bar

- [ ] 字段有据可依,不从上下文外脑补
- [ ] 缺失项明确列出并给出追问话术
- [ ] 敏感信息已脱敏
- [ ] 输出是合法 JSON,可直接入库
- [ ] 图文矛盾时以图片为准并标注

## Example

**Invocation**: "客户发来一张订单截图,并说'东西少了,快处理'。抽一下工单字段。"

**Produced**:
```json
{
  "order_id": "CN2026081400231",
  "product": "橙子优选·鲜果礼盒",
  "issue": "收货少件",
  "demand": "补发/退款",
  "urgency": "高",
  "contact": null,
  "missing_fields": ["contact"],
  "followup_question": "请提供您的联系方式,方便售后专员联系您。"
}
```
