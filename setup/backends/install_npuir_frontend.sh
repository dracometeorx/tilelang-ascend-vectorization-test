#!/usr/bin/env bash
set -euo pipefail
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_PYTHON_INSTALL_DIR=/workspace/setup/backends/python
export UV_PYTHON_BIN_DIR=/workspace/setup/backends/bin
backend_root=/workspace/setup/backends
wheel_name=tilelang-0.1.1.30+ubuntu.22.4.npuir-cp311-cp311-linux_x86_64.whl
mkdir -p "$backend_root/downloads"
uv python install 3.11.16
if [ ! -x "$backend_root/npuir-venv/bin/python" ]; then
  uv venv --python 3.11.16 "$backend_root/npuir-venv"
fi
if [ ! -f "$backend_root/downloads/$wheel_name" ]; then
  curl -fL --retry 2 "https://github.com/tile-ai/tilelang-ascend/releases/download/v0.1.1.030-pre-release/$wheel_name" -o "$backend_root/downloads/$wheel_name"
fi
echo "4937fe4451c34603d773f4000a63df7bd0732e20f589ce8b576333c5fa9b9373  $backend_root/downloads/$wheel_name" | sha256sum --check
uv pip install --python "$backend_root/npuir-venv/bin/python" \
  "$backend_root/downloads/$wheel_name" 'numpy==1.26.4' scipy decorator attrs
uv pip install --python "$backend_root/npuir-venv/bin/python" \
  'torch==2.12.0' --index-url https://download.pytorch.org/whl/cpu
uv pip install --python "$backend_root/npuir-venv/bin/python" 'torch-npu==2.12.0.post2'
source "$backend_root/activate_npuir.sh"
python "$backend_root/npuir_add_lab.py"
