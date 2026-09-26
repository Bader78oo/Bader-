#!/bin/bash
# Installs the bviro-video pipeline (ffmpeg, Whisper, depth model, face tools, HyperFrames)
# at the start of every Claude Code on the web session. Idempotent: skips what is already there.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# 1. system packages: ffmpeg/sox for audio+video, EGL/GL libs for MediaPipe
need_apt=""
for p in ffmpeg sox libegl1 libgles2 libgl1; do
  dpkg -s "$p" >/dev/null 2>&1 || need_apt="$need_apt $p"
done
if [ -n "$need_apt" ]; then
  apt-get update -qq >/dev/null 2>&1 || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $need_apt >/dev/null
fi

# 2. python libraries
pip install -q --disable-pip-version-check faster-whisper mediapipe opencv-python-headless \
  onnxruntime pymupdf pillow numpy huggingface_hub 2>&1 | grep -v -i "warning" || true

# 3. models (cached in ~/.cache/huggingface): Whisper medium (Arabic captions), Depth Anything V2 Small (parallax)
python3 - <<'PY'
from huggingface_hub import hf_hub_download, snapshot_download
snapshot_download("Systran/faster-whisper-medium")
hf_hub_download("onnx-community/depth-anything-v2-small", "onnx/model.onnx")
PY

# 4. HyperFrames (HTML -> MP4 motion graphics, Apache-2.0); Playwright + Chromium are preinstalled
if ! command -v hyperframes >/dev/null 2>&1; then
  npm install -g --silent hyperframes >/dev/null 2>&1 || echo "hyperframes install failed (optional)" >&2
fi

# render with the preinstalled Playwright headless shell (HyperFrames' own Chrome download is not needed)
HS=$(ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell 2>/dev/null | head -1 || true)
if command -v hyperframes >/dev/null 2>&1; then
  hyperframes telemetry disable >/dev/null 2>&1 || true
  # agent skills live in ~/.claude/skills (outside the repo), so reinstall them when missing
  [ -d "$HOME/.claude/skills/hyperframes" ] || timeout 300 hyperframes skills >/dev/null 2>&1 || echo "hyperframes skills install failed (optional)" >&2
fi

{
  echo "export NODE_PATH=$(npm root -g)"
  [ -n "$HS" ] && echo "export HYPERFRAMES_BROWSER_PATH=$HS"
} >> "${CLAUDE_ENV_FILE:-/dev/null}"
echo "bviro-video deps ready"
