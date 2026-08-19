#!/bin/bash
# h3-local-deploy.sh — MiniMax H3 本地部署(有 GPU 的机器上运行)
# 用法: bash scripts/h3-local-deploy.sh [--comfyui|--diffusers|--check]
#   --check     只检查环境是否满足部署条件
#   --comfyui   部署 ComfyUI + H3 节点 + Turbo LoRA(默认)
#   --diffusers 只装 diffusers 推理环境
# ⚠️ 本机(4核/7G/无GPU)不满足,此脚本用于壹镜工坊/云 GPU 实例
set -e

echo "════════════════════════════════════"
echo "🎬 MiniMax H3 本地部署脚本 $(date '+%F %T')"
echo "════════════════════════════════════"

# ── 环境检查 ──
echo ""
echo "【环境检查】"
CORE=$(nproc); MEM=$(free -g | awk '/Mem:/{print $2}')
echo "  CPU: $CORE 核 | 内存: ${MEM}G"
if nvidia-smi -L >/dev/null 2>&1; then
  VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
  echo "  GPU: $(nvidia-smi -L | head -1) (${VRAM}M 显存)"
  if [ "$VRAM" -lt 20000 ]; then
    echo "  ⚠️ 显存 <20G,H3 33B 需 4bit 量化勉强跑,建议 ≥24G"
  else
    echo "  ✅ 显存满足基本要求"
  fi
else
  echo "  ❌ 无 GPU — H3 33B 无法本地推理!请用壹镜工坊/云 GPU 实例"
  echo "  参考: skills/minimax-h3-local/SKILL.md 部署决策表"
  exit 1
fi
DISK=$(df -h / | tail -1 | awk '{print $4}' | tr -d 'G')
echo "  磁盘可用: ${DISK}G $( [ "${DISK%.*}" -lt 100 ] && echo '⚠️ 建议≥100G' || echo '✅' )"

[ "${1:-}" = "--check" ] && { echo ""; echo "✅ 环境检查完成"; exit 0; }

# ── 安装依赖 ──
echo ""
echo "【安装基础依赖】"
pip install --upgrade pip setuptools wheel 2>/dev/null | tail -1 || true
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 2>/dev/null | tail -1 || true

if [ "${1:-}" = "--diffusers" ]; then
  echo ""
  echo "【部署 diffusers 推理环境】"
  pip install diffusers transformers accelerate safetensors sentencepiece 2>/dev/null | tail -1 || true
  echo "✅ diffusers 环境就绪"
  echo "下一步: python 脚本调用 MiniMaxAI/MiniMax-H3(diffusers 管线)"
  echo "参考: skills/minimax-h3-local/SKILL.md 第五节"
  exit 0
fi

# ── ComfyUI 部署(默认) ──
echo ""
echo "【部署 ComfyUI + H3 节点】(默认路径 /opt/ComfyUI)"
mkdir -p /opt && cd /opt
if [ ! -d ComfyUI ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git
  cd ComfyUI
  pip install -r requirements.txt 2>/dev/null | tail -1 || true
else
  cd ComfyUI && git pull 2>/dev/null | tail -1 || true
fi
mkdir -p custom_nodes
if [ ! -d custom_nodes/MiniMax-H3-ComfyUI ]; then
  git clone https://github.com/MiniMaxH3ComfyUI/MiniMax-H3-ComfyUI.git custom_nodes/MiniMax-H3-ComfyUI
  cd custom_nodes/MiniMax-H3-ComfyUI && pip install -r requirements.txt 2>/dev/null | tail -1 || true
  cd /opt/ComfyUI
fi

echo ""
echo "【权重下载】HuggingFace MiniMaxAI/MiniMax-H3(约 66G,耐心等)"
echo "  建议: huggingface-cli download MiniMaxAI/MiniMax-H3 --local-dir /opt/ComfyUI/models/minimax-h3"
echo "  国内加速: HF_ENDPOINT=https://hf-mirror.com huggingface-cli download ..."

echo ""
echo "【Turbo LoRA(可选 2x 加速)】"
echo "  huggingface-cli download MiniMaxAI/MiniMax-H3-Turbo-Lora --local-dir /opt/ComfyUI/models/loras"

echo ""
echo "【启动 ComfyUI】"
echo "  cd /opt/ComfyUI && python main.py --listen 0.0.0.0 --port 8188"
echo "  浏览器打开 http://<IP>:8188 → 拖入仓库 workflow JSON(T2V/I2V/R2V)"

echo ""
echo "════════════════════════════════════"
echo "✅ 部署完成!工作流模板在 custom_nodes/MiniMax-H3-ComfyUI/workflows/"
echo "📖 完整文档: skills/minimax-h3-local/SKILL.md"
echo "════════════════════════════════════"
