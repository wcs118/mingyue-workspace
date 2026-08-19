---
name: deepseek-harness
description: DeepSeek 官方 agent harness(dsh)—"Everything is a Plugin" 插件化编码 agent,无头模式直接跑任务(DeepSeek V4 + bash/文件系统/子代理工具链),已装于 /opt/dsh 实测可用
version: 1.0.0
source: https://github.com/deepseek-ai/deepseek-harness
license: MIT
tags: [deepseek, harness, agent, coding, cli, plugin]
---

# DeepSeek Harness (dsh) — DeepSeek 官方插件化 Agent Harness

## 情报(2026-08-16 吸收)

- **deepseek-ai/deepseek-harness**(⭐11.6万, MIT, TypeScript):DeepSeek 官方开源 agent harness
- 诞生 2026-08-13,3 天 11.6 万 star,本周 GitHub 最大热点,衍生生态起飞(desktop 版 ⭐6k、插件合集 ⭐3k、Web UI 皮肤 ⭐2.7k)
- 架构:**Everything is a Plugin** — 基于 Cordis(可组合插件运行时,论文: A Programming Paradigm for Spatiotemporal Composability)
- 定位:编码 agent harness,DeepSeek V4 + 本地 bash/文件系统工具 + 子代理委派 + 工作流 + todo_write + JSONL 持久化
- ⚠️ **开发者预览版**,快速迭代中,**有兼容性破坏变更**(当前版本 0.1.0-rc.6)

## 本机接入状态(真吸收 ✅ 2026-08-16)

- **安装位置**: `/opt/dsh/`(npm install @deepseek-ai/dsh,530 包)
- **CLI**: `/opt/dsh/node_modules/.bin/dsh`
- **封装脚本**: `bash scripts/dsh-run.sh "<任务>"`(自动注入 DEEPSEEK_API_KEY)
- **Key**: 复用 OpenClaw 配置里的 DeepSeek key(自动从 ~/.openclaw/openclaw.json 提取),零额外成本
- **实测通过**:
  - `dsh --profile headless "输出 hello"` → ✅ 返回结果
  - 文件创建 + bash 读取 + 大小确认 → ✅ 工具链全通
- **关键依赖**: 装完必须 `npm install-scripts approve` 批准 node-pty/koffi/dsh-subprocess-local 等 5 个原生脚本,否则 bash 工具不可用

## 真实落地验证(2026-08-16 ✅)

- **全局命令**: `ln -sf /opt/dsh/node_modules/.bin/dsh /usr/local/bin/dsh`, 任意目录直接 `dsh`
- **真实任务实测**: 让 dsh 审查 scripts/ 目录 → 发现 8 个问题(2 中 6 低), 含真实 bug:
  - trending-watch.sh 限流 403 时静默吞错、`fmt` 解析失败 exit 0、覆盖旧数据 → **已修**(HTTP code 检测 + 错误传播 + 失败保留旧数据)
  - daily-report.sh `$HOME` 定位在 cron 下不可靠 → **已改** BASH_SOURCE 相对定位
  - 无 systemd 环境误报服务故障 → **已加** command -v systemctl 检查
  - 两个脚本缺可执行权限 → chmod +x
- **教训**: dsh 审查能发现真实问题, 但修改必须人工复核(bash -n + 实跑验证), 不盲信 AI 结论

## 用法

### 无头跑任务(推荐)
```bash
# 封装脚本(自动带 key)
bash scripts/dsh-run.sh "修复这个目录下失败的测试"

# 或直接
cd /opt/dsh && DEEPSEEK_API_KEY=sk-... ./node_modules/.bin/dsh --profile headless "任务描述"
```

### Web UI
```bash
cd /opt/dsh && DEEPSEEK_API_KEY=sk-... ./node_modules/.bin/dsh web   # http://127.0.0.1:3080
```

### CLI 结构
- `dsh --profile <name> [args]` — 启动命名 profile($DSH_HOME/profiles/<name>)
- `dsh --profile headless "job"` — 跑一个一次性持久会话,打印最终答案后退出
- `dsh web` — `--profile web` 别名
- `dsh plugin --profile <name> <pnpm args>` — 管理 profile 插件
- `--dump-config` / `--dump-default-config` — 查看组合配置树

### 环境变量
- `DEEPSEEK_API_KEY` 必填
- `DEEPSEEK_BASE_URL` 可选,默认官方 API(可指向代理)

## 目录结构速览
- `examples/headless-agent/` — 无头编码 agent 配置示例(cordis.yml 组合层)
- `docs/` — architecture / agent-lifecycle / tool-catalog / api-gateway / capability-seams 等
- `apps/cli/` — dsh 命令实现
- `packages/` — 各插件包(boot/fs/bash/subprocess/e2b 等)

## 与现有工具链关系
- **kimi-code**(kimi provider) / **grok-build**(DeepSeek 代理) / **dsh**(DeepSeek 原生) = 三把编码 agent 并列
- dsh 与 OpenClaw 是同类平台(都是 agent harness),互补不冲突:dsh 适合跑独立编码任务,OpenClaw 是主调度
- 上游追踪已入 skills-db/upstream.json,skills-updater 每日 10:00 自动检查更新

## 阶段五落地:guard-exec.py(2026-08-16)

照 dsh executor.py 样板,把 4 大机制落地成我们自己的守卫链执行器:
- **文件**: scripts/guard-exec.py(纯 Python,无外部依赖)+ scripts/guard.sh(bash 封装)
- **机制1 守卫链**: pre-execute(熔断+作用域门) → 单调 guards(红线/需确认/沙箱,拒绝不可翻案) → execute(超时/重试) → post-execute(handler 校验) → 结果终结
- **机制2 作用域**: Scope 类,全局 allow/deny + agent 局部 shadow 掩码交集
- **机制3 协作取消**: TOOL_TIMEOUT(超时)/ ABORTED / ABORTED_BEFORE_DISPATCH 三态
- **机制4 事务**: GUARD_TMP_DIR 环境变量,失败自动清理临时产物
- **熔断**: 同一工具连续失败 3 次熔断(状态落盘 .guard-breaker.json),安全工具永远放行
- **账本**: 成功/失败自动写 memory/events.log(phoenix 三字段格式)
- **用法**:
  - `python3 scripts/guard-exec.py check --cmd "命令"` — 只检查
  - `python3 scripts/guard-exec.py run --cmd "命令" [--yes] [--timeout N]` — 执行
  - `bash scripts/guard.sh "命令" [--yes]` — bash 封装
  - `python3 scripts/guard-exec.py smoke` — 自测 10 项
- **验证**: 自测 10/10 全绿;实跑红线拦截/密钥拦截/超时/熔断/回滚全部通过

## 阶段五完整落地:工作流 v2 五件套(2026-08-16 补齐)

把 dsh 4 大机制 + 插件协议全部落成可执行代码:

| 组件 | 文件 | 机制 |
|---|---|---|
| 守卫链执行器 | scripts/guard-exec.py + guard.sh | 机制1+3(守卫链/协作取消/熔断/账本) |
| 作用域路由 | scripts/scope-router.py | 机制2(L0-L3 定级→工具集映射) |
| 会话级回滚 | scripts/session-rollback.py | 机制4(begin/check/rollback/commit) |
| 技能→插件转换 | scripts/skill-to-plugin.py | 第0层插件协议(169技能→dsh插件) |
| 一键编排 | scripts/workflow-run.sh | 五阶段串成一条命令 |
| dsh 接入守卫 | scripts/dsh-run.sh(已改造) | dsh 执行前先定级+过守卫 |

端到端验证(全部实测通过):
- workflow-run.sh 成功路径/失败回滚/L3拦截 ✅
- dsh --profile headless + 明月技能插件 真正跑通 ✅
- 169 个技能已生成 dsh 插件包(reference/dsh-plugins/)
- pnpm 已装(11.22.0),@deepseek-ai/dsh-skill-human-writing 已装入 headless profile

关键踩坑(cordis 插件协议):
- dsh 插件 = 真实 npm 包(package.json + index.js + cordis.patch.yml + dsh.bundle 声明)
- index.js 必须导出 apply(ctx) 方法,不能是 data 对象
- apply 内不能访问注入属性(ctx.config/ctx.skills),会报 "without inject"
- 插件装进 profile 后不能再 --patch 同一 id(duplicate loader entry)
- 熔断状态落盘跨进程生效(联测把 sleep 熔断后自测都受影响,清理 .guard-breaker.json 即恢复)
