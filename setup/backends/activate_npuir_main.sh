#!/usr/bin/env bash
# Pinned source build; device compilation/simulation use the separate CANN shell.
source /workspace/setup/backends/npuir-main/venv/bin/activate
unset ASCEND_HOME_PATH ASCEND_TOOLKIT_HOME
export UV_CACHE_DIR=/workspace/.cache/uv
export TORCH_DEVICE_BACKEND_AUTOLOAD=0
export TILELANG_ASCEND_MODE=Developer
export TILELANG_ASCEND_DEVICE_NAME=Ascend950
export TILELANG_ENABLE_SIMT=0
export TILELANG_CACHE_DIR=/workspace/.cache/tilelang-npuir-main-013dbbf5
export TEST_DATA_ROOT_PATH=/workspace/.cache/tvm-test-data
export OMP_NUM_THREADS=1
export PYTHONPATH=/workspace/setup/backends/tilelang-mlir-ascend:/workspace/setup/backends/tilelang-mlir-ascend/build
export TVM_IMPORT_PYTHON_PATH=/workspace/setup/backends/tilelang-mlir-ascend/3rdparty/tvm/python
export TVM_LIBRARY_PATH=/workspace/setup/backends/tilelang-mlir-ascend/build/tvm-current
export TILELANG_LIBRARY_PATH=/workspace/setup/backends/tilelang-mlir-ascend/build
