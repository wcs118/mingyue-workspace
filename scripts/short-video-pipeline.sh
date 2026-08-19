#!/bin/bash
# 短视频流水线: 分镜提示词文件 → H3 逐段出片 → 成片清单 + 剪映导入说明
# 用法: bash scripts/short-video-pipeline.sh <分镜文件> [比例] [时长]
# 分镜文件: 每行一个镜头的画面提示词(建议 2-6 段, 每段 4-6 秒)
# 例:   bash scripts/short-video-pipeline.sh clips.txt 9:16 5
set -euo pipefail

CLIPS="${1:?用法: short-video-pipeline.sh <分镜文件> [比例] [时长]}"
RATIO="${2:-9:16}"      # 短视频默认竖屏
DURATION="${3:-5}"      # 单段秒数 (H3 支持 4-15)
H3_SCRIPT=~/.openclaw/workspace/scripts/minimax-h3.sh
OUT_DIR=~/.openclaw/workspace/output/short-video

# 参数校验(防止把 --help 之类当参数, 误触发真实生成)
case "$RATIO" in
  16:9|4:3|1:1|3:4|9:16|21:9) ;;
  *) echo "❌ ratio 必须是 16:9/4:3/1:1/3:4/9:16/21:9, 收到 '$RATIO'"; exit 1 ;;
esac
if ! [[ "$DURATION" =~ ^[0-9]+$ ]] || [ "$DURATION" -lt 4 ] || [ "$DURATION" -gt 15 ]; then
  echo "❌ 时长须为 4-15 的整数, 收到 '$DURATION'"; exit 1
fi

[ -f "$CLIPS" ] || { echo "❌ 找不到分镜文件: $CLIPS"; exit 1; }
[ -f "$H3_SCRIPT" ] || { echo "❌ 缺少 $H3_SCRIPT"; exit 1; }

# 读分镜(过滤空行/注释)
mapfile -t PROMPTS < <(grep -vE '^\s*$|^\s*#' "$CLIPS")
N=${#PROMPTS[@]}
if [ "$N" -lt 1 ] || [ "$N" -gt 8 ]; then
  echo "❌ 分镜段数需 1-8 条, 当前 $N 条"; exit 1
fi
mkdir -p "$OUT_DIR"
TS=$(date +%Y%m%d-%H%M%S)
MANIFEST="$OUT_DIR/manifest_${TS}.txt"

echo "🎬 短视频流水线启动: $N 段 × ${DURATION}s @ $RATIO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━"

declare -a FILES=()
for i in "${!PROMPTS[@]}"; do
  NO=$((i+1))
  echo "[$NO/$N] 生成第 $NO 段..."
  echo "  提示词: ${PROMPTS[$i]:0:60}..."
  OUT=$(bash "$H3_SCRIPT" "${PROMPTS[$i]}" "$DURATION" 768p "$RATIO" 2>&1 | tail -1)
  MP4=$(echo "$OUT" | grep -oE '/[^ ]+\.mp4' || true)
  if [ -z "$MP4" ]; then
    echo "  ❌ 第 $NO 段生成失败, 跳过: $OUT"
    continue
  fi
  echo "  ✅ 第 $NO 段: $MP4"
  FILES+=("$MP4")
done

# 写清单
{
  echo "# 短视频成片清单 $TS (${#FILES[@]}/${N} 段成功)"
  echo "# 比例: $RATIO | 单段: ${DURATION}s"
  echo "# 导入剪映: 按顺序拖入轨道 → 加字幕/BGM → 导出"
  for f in "${FILES[@]}"; do echo "$f"; done
} > "$MANIFEST"

echo "━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "${#FILES[@]}" -gt 0 ]; then
  echo "🎉 完成: ${#FILES[@]}/${N} 段, 清单见 $MANIFEST"
  echo "下一步: 剪映按清单顺序拼接 → 加字幕/BGM → 导出发布"
else
  echo "❌ 全部失败, 请检查 H3 额度/网络"
  exit 1
fi
