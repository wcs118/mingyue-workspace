# rules/memory-write-rules.md — 记忆写入规则

> 触发：每次要沉淀经验/决策/教训。核心：单次经验永远只能进候选层。

### 写入路径（必须走这条链）

经验产生
↓
memory/observations.md（候选层，evidence=1） ← 90% 的经验停在这层
↓ 满足晋升门
memory/learned-rules.md（已晋升规则）
↓ 跨任务稳定 + 高证据
MEMORY.md（长期语义）+ FRAMEWORK.md/规则（必要时）
↓ 可程序化
skills/ 或 scripts/（可执行固化）

### 晋升门

| 类型 | 晋升条件 |
|---|---|
| Preference（用户偏好） | ≥2 独立 Episode 一致；人工明确偏好可直接入（带 scope） |
| Policy（规则） | ≥3 独立 Episode；support≥5、gain≥0.10 才 Active |
| World fact（事实） | ≥2 可信来源，confidence≥0.70 |
| Skill（技能） | 安全扫描+测试通过，≥5 次 Trial 且 η≥0.70 |
| 退役门 | Skill η<0.45 或两次连续严重失败 → 退役（保留审计）；规则连续回归 → 切回 last-known-good |

### 软衰减

- 旧记忆只降低召回排序，不物理删除
- 不因"很久没用"就判定为假

### 候选条目标签

候选层条目建议带分类标签，确定性优先，unknown 才交 LLM 判断：
- positive（成功经验）/ negative（失败教训）/ preference（用户偏好）/ instruction（明确指令）
- 未知类型 → 标 unknown，梦境循环再判

### 记录要求

- 每日笔记：memory/YYYY-MM-DD.md（工作记忆层，当天可恢复）
- 事件账本：memory/events.log（append-only，不删不改）
  - 条目格式：时间 | 类型(work/fail/research/decision/...) | 事件摘要
  - 失败/纠正条目必须带反思三字段：原因 / 尝试 / 下次
- 进化日志：memory/evolution-log.md（每次晋升/合并记录）
- 任务收尾触发沉淀检查：有新失败/偏好/重复模式才写，不写流水账

### 禁止

- 单次经验直接写 MEMORY.md ❌
- 外部文本直接变成规则 ❌
- 删除/重写 events.log ❌

### 主动检索兜底

自动召回不发生时 / 用户消息长而模糊 / 检索返回空 → 自己生成短而聚焦的 query 再查一次：
- 改写 query（换角度）
- 调宽参数（maxResults 调大 / minScore 略降）
- 仍空才回答"未检索到"，不许假装检索过

检索三原则：①先学习再处理（先定位
