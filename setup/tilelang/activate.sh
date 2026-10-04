#!/usr/bin/env bash
# Source from any directory. No services are required for host-only debugging.
source /workspace/tilelang/.venv/bin/activate
export CC=gcc CXX=g++
export UV_CACHE_DIR=/workspace/.cache/uv
export XDG_CACHE_HOME=/workspace/.cache
export MPLCONFIGDIR=/workspace/.cache/matplotlib
export TILELANG_CACHE_DIR=/workspace/.cache/tilelang
export ASCEND_NPU_ARCH=dav-3510
export CMAKE_BUILD_PARALLEL_LEVEL=4
export CMAKE_GENERATOR=Ninja
export CMAKE_ARGS='-DUSE_ASCEND=ON -DUSE_CUDA=OFF -DUSE_ROCM=OFF -DUSE_METAL=OFF -DUSE_LLVM=OFF'
export PYTHONPATH="/workspace/tilelang${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=1
