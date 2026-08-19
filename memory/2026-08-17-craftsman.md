# 2026-08-17 大匠入职:对标 Codex 的编码智能体(阶段四深化)

## 背景
老板指令:「建一个智能体,对标 codex,一定要把它的模型完全的吸收,转化成我们自己的系统,可落地、可执行的真实的系统」

## 建设过程
1. **研究 Codex 本尊**:openai/codex (106K⭐, Apache-2.0),抓官方文档摸清六大核心机制:
   - 任务循环(plan→execute→observe→iterate)
   - AGENTS.md 项目规范
   - 沙箱执行(权限分级)
   - 技能系统(SKILL.md)
   - 并行子代理(subagents)
   - 验证前置(verification before completion)
2. **建「大匠」craftsman agent**:
   - 工作区: /root/.openclaw/workspace-craftsman(AGENTS/IDENTITY/SOUL/USER/TOOLS/HEARTBEAT 全定制)
   - 模型: deepseek-v4-pro(对标 Codex 的重活能力)
   - 注册: openclaw agents add craftsman(官方 CLI)
   - 权限: tools.agentToAgent.allow += craftsman(main 可派活)
3. **吸收落地**:
   - 12 个 superpowers 编码技能同步(brainstorming/TDD/systematic-debugging/parallel-agents/code-review/git-worktrees 等)
   - 脚本: task-loop.sh(任务循环)+ verify.sh(验证器,支持 py/js/sh/json)
   - 架构吸收笔记: reference/CODEX-ABSORPTION.md

## 入职测试(真闭环)✅
- 任务: 写服务器健康检查工具 healthcheck.py(CPU/内存/磁盘)
- 产出: work/onboarding/(PLAN.md + healthcheck.py + RESULT.md)
- 验证: 运行输出正常 + py_compile 通过 + 与 /proc/meminfo、df -h 交叉核对一致
- 输出: `CPU负载: 0.57 | 内存: 使用 1.3G/7.1G (19%) | 磁盘: 使用 11.5G/39.0G (30%)`

## 关键经验
- 注册新 agent 用 `openclaw agents add <id> --workspace <dir>`,别手改 config(agentDir/workspace 是受保护路径)
- 新 agent 要能接收消息,需改 tools.agentToAgent.allow 加 id
- 给 agent 派活用 `openclaw agent --agent <id> --message "..."`(sessions_send 对非 main agent 有限制)
- 大匠工具集: 无 memory_search,但它会如实说明,不伪造

## 深挖补全(同日 v2,老板指令"100%")
- **方法升级**:从文档级 → 源码级逆向(7095 文件全树 + 抓核心源码)
- **发现并补齐 6 大遗漏机制**(新增 6 技能,12→18 个):
  1. goal-management(持续目标:完成审计/阻塞审计/预算)
  2. memory-pipeline(两阶段记忆:提取+整合,渐进式披露)
  3. context-compaction(压缩交接四要素)
  4. exec-policy(沙箱三级+审批策略+前缀规则)
  5. code-review-rubric(P0-P3 分级审查,8 条 bug 判定)
  6. lifecycle-hooks(10 类钩子:pre/post_tool_use 安全闸门)
- AGENTS.md 升级:任务循环加入钩子标注 + 权限分级表 + 完成审计
- 吸收笔记 v2: CODEX-ABSORPTION.md(14 大机制全部落地)
- 验证: 18 技能 SKILL.md 齐全 + 脚本语法 OK

## 架构(现在)
老板(决策) → 明月🌙(调度/验收,flash) → 大掌柜🧭(总经理,pro) + 大匠🔧(编码执行,pro)
