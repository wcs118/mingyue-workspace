#!/bin/bash
# guard.sh — 守卫链执行器 bash 封装
# 用法: bash scripts/guard.sh "<命令>" [--yes] [--timeout N] [--scope agent:xxx]
# 返回: 0=成功 2=守卫拒绝 3=超时 1=其他失败
set -u
cd "$(dirname "$0")/.." || exit 1

CMD="${1:-}"
if [ -z "$CMD" ]; then
  echo "用法: bash scripts/guard.sh \"<命令>\" [--yes] [--timeout N] [--scope agent:xxx]"
  exit 2
fi
shift

python3 scripts/guard-exec.py run --cmd "$CMD" "$@"
exit $?
