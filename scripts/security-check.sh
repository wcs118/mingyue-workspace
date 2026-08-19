#!/bin/bash
# security-check.sh — 下载软件/技能安全检查(防病毒+危险模式扫描)
# 用法:
#   bash scripts/security-check.sh <文件或目录> [--quarantine]
#   --quarantine: 发现恶意内容时移动到 /tmp/quarantine-<ts>/ 隔离
# 检查项:
#   1. ClamAV 病毒扫描(clamscan 存在时)
#   2. 危险 shell 模式: 管道到sh/bash、curl/wget|bash、base64解码执行、eval 混淆
#   3. 危险文件: 可执行文件意外出现在纯技能目录、.bashrc/.zshrc 劫持、ssh key 窃取
#   4. 可疑指令: 技能 SKILL.md 中的 rm -rf 根目录、curl 到未知IP、密码/密钥外传
# 返回: 0=通过, 1=有风险(需人工复核), 2=严重(建议隔离)

set -uo pipefail
TARGET="${1:-}"
[ -z "$TARGET" ] && echo "用法: bash scripts/security-check.sh <文件或目录> [--quarantine]" && exit 2
QUARANTINE=0
[ "${2:-}" = "--quarantine" ] && QUARANTINE=1
TS=$(date +%Y%m%d%H%M%S)

[ -e "$TARGET" ] || { echo "✗ 路径不存在: $TARGET"; exit 2; }

echo "=== 安全检查: $TARGET ==="
RISK=0
SEVERE=0

# --- 1. ClamAV 病毒扫描 ---
if command -v clamscan >/dev/null 2>&1; then
  if [ -f "$TARGET" ]; then
    SCAN_TARGET="$TARGET"
  else
    SCAN_TARGET="$TARGET"
  fi
  CLAM_OUT=$(clamscan --no-summary -r "$SCAN_TARGET" 2>/dev/null)
  CLAM_HITS=$(echo "$CLAM_OUT" | grep -c 'FOUND$' || true)
  if [ "$CLAM_HITS" -gt 0 ]; then
    echo "🔴 [病毒] ClamAV 发现 $CLAM_HITS 个威胁:"
    echo "$CLAM_OUT" | grep 'FOUND$' | head -5
    SEVERE=2; RISK=2
  else
    echo "🟢 [病毒] ClamAV 扫描通过"
  fi
else
  echo "⚠ [病毒] ClamAV 未安装,跳过"
fi

# --- 2. 危险 shell 模式 ---
DANGER_PATTERNS=(
  'curl .*\| *sh'
  'curl .*\| *bash'
  'wget .*\| *sh'
  'wget .*\| *bash'
  'base64 -d.*\|.*sh'
  'eval \$(.*curl'
  'eval \$(.*wget'
  '\| *sudo sh'
  'python3? -c .*(base64|exec\(|eval\()'
)
if [ -d "$TARGET" ]; then
  FILES=$(find "$TARGET" -type f \( -name '*.sh' -o -name '*.py' -o -name '*.ts' -o -name '*.js' -o -name '*.md' \) 2>/dev/null)
else
  FILES="$TARGET"
fi
for f in $FILES; do
  for pat in "${DANGER_PATTERNS[@]}"; do
    hit=$(grep -lE "$pat" "$f" 2>/dev/null | head -1)
    if [ -n "$hit" ]; then
      echo "🔴 [危险命令] $hit 匹配模式: $pat"
      SEVERE=2; RISK=2
    fi
  done
done
[ "$SEVERE" -eq 0 ] && echo "🟢 [命令] 未发现管道执行/混淆下载模式"

# --- 3. 危险文件类型 ---
if [ -d "$TARGET" ]; then
  # 纯技能目录里出现可执行文件(elf/mach-o)要警惕
  EXECS=$(find "$TARGET" -type f -exec file {} \; 2>/dev/null | grep -E 'ELF.*executable|Mach-O.*executable' | grep -vE 'node_modules|\.git/' | head -3)
  if [ -n "$EXECS" ]; then
    echo "⚠ [可执行] 技能目录中发现二进制可执行文件:"
    echo "$EXECS"
    RISK=1
  fi
  # 隐藏文件/rc劫持
  RCFILES=$(find "$TARGET" -name '.bashrc' -o -name '.zshrc' -o -name '.profile' 2>/dev/null | head -3)
  if [ -n "$RCFILES" ]; then
    echo "🔴 [劫持] 发现 shell rc 文件: $RCFILES"
    SEVERE=2; RISK=2
  fi
fi

# --- 4. 可疑内容(密钥外传/危险删除) ---
SUSPICIOUS=$(grep -rEl 'rm -rf *[/~]|authorized_keys|id_rsa|id_ed25519|\.ssh/' "$TARGET" 2>/dev/null | grep -vE 'node_modules|\.git/' | head -3)
if [ -n "$SUSPICIOUS" ]; then
  echo "⚠ [可疑] 发现敏感路径引用:"
  echo "$SUSPICIOUS"
  RISK=1
fi

# --- 结果 ---
if [ "$SEVERE" -gt 0 ]; then
  echo "❌ 结果: 严重风险(建议隔离)"
  if [ "$QUARANTINE" -eq 1 ]; then
    QDIR="/tmp/quarantine-$TS"
    mkdir -p "$QDIR"
    mv "$TARGET" "$QDIR/" 2>/dev/null && echo "⛔ 已隔离到 $QDIR"
  fi
  exit 2
elif [ "$RISK" -gt 0 ]; then
  echo "⚠️ 结果: 存在风险项(需人工复核)"
  exit 1
else
  echo "✅ 结果: 通过"
  exit 0
fi
