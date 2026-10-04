#!/usr/bin/env bash
# CPU-only TileLang NPU-IR frontend. Use a separate shell for CANN compilation.
source /workspace/setup/backends/npuir-venv/bin/activate
unset PYTHONPATH ASCEND_HOME_PATH ASCEND_TOOLKIT_HOME
export TORCH_DEVICE_BACKEND_AUTOLOAD=0
export TILELANG_ASCEND_MODE=Developer
export TILELANG_ASCEND_DEVICE_NAME=Ascend950
export TILELANG_CACHE_DIR=/workspace/.cache/tilelang-npuir
export TEST_DATA_ROOT_PATH=/workspace/.cache/tvm-test-data
export OMP_NUM_THREADS=1
