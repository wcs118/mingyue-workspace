# 进化日志

- 2026-08-11 14:10 | 框架初始化 | 0号v8 三体系(长记忆/不死鸟/自进化)落地 OpenClaw，R1-R8 规则索引建立

## 2026-08-11 晋升归档（source=skill-absorption, 人工确认）
# 候选观察（未晋升）

## 2026-08-11

- [占位] 框架初始化 | evidence=1 | source=framework-bootstrap
  0号v8 三体系框架落地 OpenClaw，部署完成。

- [部署教训] 快照脚本路径解析 bug | evidence=1 | source=dreaming-narrative | label=negative
  快照格式 "hash  path"(双空格),脚本用 ${line#* } 只剥一个空格 → 路径带前导空格,status 全部误报 DELETED。
  载体: scripts/phoenix-snapshot.sh(已修复为 ${line#*  })。教训:冒烟测试必须实跑,不能只看"文件存在"。

- [阶段四经验] gm agent 配置要点 | evidence=1 | source=user-confirmed | label=positive
  sessions_send 跨agent派活需同时配置 tools.agentToAgent.enabled=true + tools.sessions.visibility=all;
  新agent用 openclaw agents add <id> --workspace <dir> --model <id> --non-interactive 创建, 会自动生成 workspace-gm 全套默认文件。

- [阶段四验证] gm实战链路可靠 | evidence=2 | source=verification | label=positive
  sessions_send 派活 → gm用TDD流程(红→绿→重构)自主完成fib.py+test_fib.py → 10/10通过 → 明月独立复核确认。
  gm 可用技能已同步(superpowers×12),工具 rg/gh 已装,Codex 能力内核就位。

- 2026-08-11 16:43 | 晋升归档 4 条候选 → evolution-log + 验证台账（待人工重构为 R 编号规则）
