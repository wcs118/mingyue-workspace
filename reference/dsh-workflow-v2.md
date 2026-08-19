# 明月调度器工作流程 v2 最终版(四图合并)
> 2026-08-16 依据老板提供的 DeepSeek Harness 四张调研图,学习其工作流机制后重新制作。
> 配套流程图: `reference/dsh-workflow-v2.html`(浏览器打开即看)

## 一、四张图教了我们什么(学习笔记)

### 图1+图3(完整版):4 个可移植到我们调度器的机制
1. **工具执行守卫链**: `pre-execute(允许/拒绝门) → 单调 guards(拒绝不可翻案) → execute(超时/重试包装) → post-execute → 结果终结`
   - 每个工具调用过"安检流水线";拒绝即停且**不可翻案**、超时/重试有包装、结果终结有校验
2. **作用域注册**: 全局/单-agent 三层工具可见性,重复名抛错 → **治理技能命名冲突**
3. **协作式取消**: AbortSignal 贯穿执行体,取消发生在 body 前/后区分明确 → **防跑飞**
4. **agent-loop 事务式生命周期**: create 失败自动回滚,不残留半成品 → **代码层"不死鸟"**

### 图2:技术栈与吸收策略
- **形态**: Web UI + Python SDK + CLI + headless + 插件开发
- **架构**: Node.js + Cordis 插件运行时(时空可组合);"Everything is a Plugin"
- **模型**: DeepSeek 直连 + 任意 OpenAI 兼容端点
- **状态**: ⚠️ developer preview,破坏性变更;MIT;Docker 可用
- **落地建议**: 只吸收模式不部署本体;技能→dsh-plugin 实现"我们的技能+官方引擎";试用放情报服务器不碰主服务器

### 图4(吸收成果):机制 → 真代码的落地样板
**executor.py(406 行,纯 Python 无外部依赖)把 4 机制全部落地,验证 11/11 全绿:**

| 官方机制 | 落地实现 | 验证 |
|---|---|---|
| 工具执行守卫链 | pre-execute门 → 单调守卫(拒绝不可翻案) → 执行 → post-execute → 观察 | ✅ |
| 作用域注册三层 | 全局 / agent局部shadow / allow-deny掩码交集 | ✅ |
| 协作式取消 | AbortSignal,区分 ABORTED_BEFORE_DISPATCH / ABORTED / TOOL_TIMEOUT | ✅ |
| 事务式生命周期 | create失败回滚不残留半成品 | ✅ |

**过程中抓到并修了 3 个真问题(宝贵经验):**
1. **agent 作用域 bug**: register 指定了 agent_id 却还走全局注册(语义错乱)→ 修
2. **超时机制无法真实触发**: 原始 _dispatch 读 SKILL.md 是即时的,永远不会走超时分支 → 修
3. **设计改进**: 改成可注入 handler 回调(对齐 dsh 的 ToolDefinition.execute 注入模式)——这才是真正的执行引擎该有的样子

## 二、重新制作:明月调度器工作流程 v2(插件层 + 四阶段 + 落地执行)

### 第 0 层 · 插件化架构(万物皆插件)
- 调度器 = **插件注册表**(登记技能/工具,如 skills-db)
- 运行时 = **插件运行时**(加载、调度、执行插件;OpenClaw 网关 + dsh)
- 插件协议 = **技能 → dsh-plugin 格式**,官方引擎 + 自研调度器双跑

### 阶段一 · 任务接收与作用域初始化(机制2)
1. 老板指令进来(微信/明示任务)
2. 明月解析:**目标 / 约束 / 交付物 / 风险等级**(读 rules/path-routing.md)
3. **作用域注册**:确定本任务可见的工具集(全局层 / 任务层 / agent 层)
4. 冲突检测:工具重名 → 抛错拒绝启动,防覆盖、防越权

### 阶段二 · 事务式会话启动(机制4 = 代码层不死鸟)
1. 创建会话 + agent(挂载工具、注入上下文)
2. **setup 校验**:上下文齐全?工具可挂?权限够?
3. 失败 → **自动回滚**,不残留半成品会话
4. 成功 → 会话持久化(append-only 事件日志,可回溯)

### 阶段三 · 执行循环(机制1 + 机制3)
每轮 agent 循环 = 模型请求 → 工具调用,工具调用过**守卫链**:
1. **pre-execute 门**:允许/拒绝(权限策略,敏感操作弹窗审批)
2. **单调 guards**:链式校验;**拒绝不可翻案**
3. **execute**:执行工具(**超时/重试包装**,可注入 handler 回调)
4. **post-execute**:结果校验,异常留痕 → **结果终结**
- 全程 **AbortSignal 协作式取消**:区分 ABORTED_BEFORE_DISPATCH(dispatch前取消,无副作用)/ ABORTED(执行中取消)/ TOOL_TIMEOUT(超时)
- 支持**委派子任务**,各子代理有自己作用域

### 阶段四 · 事务式收尾与交付(机制4)
1. 验证台账:目标达成?
2. ✅ 达成 → 交付汇报老板 + 写记忆(events.log / MEMORY.md)
3. ❌ 未达成 → 回滚清理 → 修复重试(最多 3 次)→ 仍失败升级老板拍板

### 阶段五 · 机制落地为代码(✅ 已落地 2026-08-16)
**执行管道不是文档,是代码。** 照图4 executor.py 样板,已落地到工作区:

| 机制 | 落地文件 | 验证 |
|---|---|---|
| 工具守卫链 | `scripts/guard-exec.py`(pre-execute→guards→execute→post-execute) | ✅ 自测10/10 |
| 三层作用域 | Scope 类:全局allow/deny + agent局部shadow + 掩码交集 | ✅ |
| 协作取消 | TOOL_TIMEOUT / ABORTED / ABORTED_BEFORE_DISPATCH 三态 | ✅ |
| 事务回滚 | GUARD_TMP_DIR 失败自动清理 | ✅ |
| 熔断 | 连败3次熔断,状态落盘;安全工具永放行 | ✅ |
| 账本 | 自动写 events.log(三字段) | ✅ |

- 入口: `python3 scripts/guard-exec.py check|run|smoke` 或 `bash scripts/guard.sh "命令"`
- 红线/需确认/沙箱规则直接从 rules/risk-boundaries.md 提取编码

## 三、与现有体系的映射

| dsh 概念 | 我们已有的对应物 | 差距/落地动作 |
|---|---|---|
| 插件注册表 | skills-db(技能索引 167+ 技能) | 已有索引,缺"技能→dsh-plugin 格式"转换器 |
| 插件运行时 | OpenClaw 网关 + dsh 本体(/opt/dsh) | dsh 已装可跑,待把我们的技能接入 |
| 工具守卫链 | rules/risk-boundaries.md(红线)、phoenix-triggers.md(熔断) | 已有原则,缺"执行前校验流水线"脚本 |
| 作用域注册 | path-routing.md(任务路由) | 缺"任务→工具集"自动映射 |
| 协作式取消 | 无 | **缺** → 工具调用加超时/中断信号 |
| 事务式生命周期 | phoenix-snapshot.sh(文件级快照) | 已有文件级,缺"会话级回滚" |
| 机制→代码落地 | ✅ 已落地: scripts/guard-exec.py + guard.sh(照图4样板) | 可继续扩展:技能→dsh-plugin 转换器 |

## 四、结论

四张图拼出完整答案:**dsh 的价值在"万物皆插件"架构 + 4 个防跑飞/防残留机制,而且这些机制可以(也应该)落成真代码**。
- **本体**:只吸收模式,不部署本体;试用放情报服务器
- **架构**:已重制为「明月调度器工作流程 v2」(插件层 + 四阶段 + 落地执行层)
- **下一步**: ① 把 guard 接入常用脚本(如 dsh-run.sh 执行前过守卫) ② 技能→dsh-plugin 转换器

---
*配套文件: reference/dsh-workflow-v2.html(流程图) · reference/dsh-workflow-v2.png(截图) · skills/deepseek-harness/SKILL.md(dsh 技能包) · scripts/dsh-run.sh(调用封装)*
