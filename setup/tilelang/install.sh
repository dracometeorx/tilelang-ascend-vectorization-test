#!/usr/bin/env bash
set -euo pipefail
cd /workspace/tilelang
export UV_CACHE_DIR=/workspace/.cache/uv
mkdir -p "$UV_CACHE_DIR"
if [ ! -x .venv/bin/python ]; then
  uv venv .venv --python 3.12.14
fi
source /workspace/setup/tilelang/activate.sh
git submodule update --init --recursive --jobs 4
uv pip install --python .venv/bin/python 'torch==2.14.1+cpu' --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -r requirements-dev.txt -r requirements.txt -r requirements-lint.txt pytest pytest-xdist pytest-timeout pytest-durations scipy einops pyyaml numpy matplotlib cffi
uv pip install --python .venv/bin/python --no-build-isolation --no-deps -e .
python -c 'import tilelang, torch; import tilelang.testing; print(tilelang.__version__); assert tilelang.testing.ascend_backend_compiled(); assert not torch.cuda.is_available()'
python /workspace/setup/tilelang/add_lab.py
