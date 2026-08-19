#!/bin/bash
# 连接小服务器 121.41.227.191 的测试脚本
# 用法: bash connect-miniserver.sh [密码]
# 老板重置密码后,传新密码即可;不传则尝试已知组合

IP="121.41.227.191"
PW="${1:-}"

echo "=== $(date +%H:%M:%S) 测试 $IP ==="

try() {
  local user="$1" pass="$2"
  local out
  out=$(timeout 10 sshpass -p "$pass" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 \
        -o PreferredAuthentications=password -o PubkeyAuthentication=no \
        "$user@$IP" 'echo "✅ CONNECTED"; hostname; whoami; sudo -n whoami 2>&1 | head -1' 2>&1)
  local rc=$?
  if echo "$out" | grep -q "CONNECTED"; then
    echo "✅ 成功: $user / $pass"
    echo "$out"
    return 0
  fi
  echo "❌ $user: $(echo "$out" | grep -iE 'denied|refused|timed' | head -1)"
  return 1
}

if [ -n "$PW" ]; then
  try admin "$PW" || try root "$PW"
else
  try admin "W123456@" || try admin "Wang518518-"
fi
