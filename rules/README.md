# rules/README.md — 行为规则层

框架系统 = 认知核心 + 路径规则 + 运行时钩子 + 技能固化 + 记忆循环。

## 规则文件

| 规则 | 触发条件 | 强制动作 |
|---|---|---|
| path-routing.md | 每个任务开始 | 先定目录归属、风险等级、完成标准 |
| risk-boundaries.md | 任务涉及外部/删除/覆盖/配置 | 先确认、先快照、不越界 |
| phoenix-triggers.md | 工具失败/状态异常 | 3 次熔断 → 快照 status → 回滚/升级 |
| memory-write-rules.md | 每次要写入经验/决策 | 走候选层 → 晋升门 → 才进长期层 |
| evolution-triggers.md | 空闲/每日/用户纠正 | 跑梦境循环，凝练晋升 |

## 执行顺序

1. 任务开始 → path-routing.md
2. 触碰边界 → risk-boundaries.md
3. 执行中失败 → phoenix-triggers.md
4. 有经验产出 → memory-write-rules.md
5. 空闲/收尾 → evolution-triggers.md

## 规则编号体系（R1-R8）

已晋升规则索引在 memory/learned-rules.md，全局编号 R1-R8；全文契约在对应行为载体：

| 编号 | 主题 | 行为载体 | 来源 |
|---|---|---|---|
| R1 | 记忆分层 | memory-write-rules.md | 0号v8 三体系 |
| R2 | 进化闭环 | evolution-triggers.md | self-improving/autoresearch/evolver/tdd |
| R3 | 任务分解与执行 | path-routing.md | brainstorming/codebase-design/wayfinder |
| R4 | 执行停止与熔断 | phoenix-triggers.md | executing-plans/diagnosing-bugs/code-review/wizard |
| R5 | 并行与子代理 | framework-ops/SKILL.md | dispatching-parallel-agents/writing-for-agents |
| R6 | 来源与信任 | risk-boundaries.md | source-driven-development |
| R7 | 技能库治理 | framework-ops/SKILL.md | writing-skills |
| R8 | 文档与产出 | framework-ops/SKILL.md | doc-coauthoring/teach/handoff |

防叠加铁律：同一主题只保留一条最优规则。索引-载体分离：learned-rules.md 只存摘要+指向。
```
