# 固定新版 NPU-IR 的隔离构建

目标前端为 `tile-ai/tilelang-mlir-ascend@013dbbf5824c3ac29e975d78c0b38e60b2410be7`，不是旧发布 wheel。
本文件记录当前恢复流程；是否完成构建、模拟以 [本次证据](../../examples/scenarios/npuir-main-013dbbf5/) 为准。

## 官方公开依赖来源

原 gitlink 指向 `AscendNPU-IR-Dev@77f5b0617813c9974b56e4090bccf57d2612a301`。
2026-10-06，Dev 仓库匿名访问返回 401，认证后仍不可读；但官方公开的 `Ascend/AscendNPU-IR` 可以直接提供完全相同的提交。
公开仓库还具有 `dev/regbase`、`feature/mcf-dev`、`feature/mixed-cube-simt-simd` 和 A5 release 分支；本实验不改为这些分支的最新版本。

在已核对前端提交的隔离 checkout 中执行：

```bash
git submodule init 3rdparty/AscendNPU-IR-Dev
git config submodule.3rdparty/AscendNPU-IR-Dev.url https://gitcode.com/Ascend/AscendNPU-IR.git
GIT_TERMINAL_PROMPT=0 git submodule update --init --depth=1 3rdparty/AscendNPU-IR-Dev
git -C 3rdparty/AscendNPU-IR-Dev rev-parse HEAD
git submodule update --init --recursive 3rdparty/tvm
git -C 3rdparty/AscendNPU-IR-Dev submodule update --init --recursive --depth=1
```

这里只覆盖本地 Git 配置，`.gitmodules` 和固定 gitlink 不变。必须验证以下提交，不能仅确认目录存在：

| 组件 | 提交 |
|---|---|
| TVM | `c2921fdaf795b1103d21abc962e83a209c7258d7` |
| AscendNPU-IR | `77f5b0617813c9974b56e4090bccf57d2612a301` |
| LLVM | `98ef2bc767edafb97a99d50cd99009573c47ecee` |
| Triton | `c3c476f357f1e9768ea4e45aa5c17528449ab9ef` |

该版本的 `build-tools/apply_patches.sh` 会先 reset/clean Triton。此次没有运行它，而是在新建、干净的 Triton checkout 中，对 `../../build-tools/patches/triton/*.patch` 按顺序执行 `git apply --check` 和 `git apply`，保留完整 diff。重复执行前必须检查已应用状态，不能清理未知改动。

## 本次宿主构建配置

独立环境：`/workspace/setup/backends/npuir-main/venv`，Python 3.11.16、CPU torch 2.12.0+cpu、torch_npu 2.12.0.post2；安装固定前端自己的 Python requirements 和 CMake/Ninja。实测解析后的版本清单见证据目录的 `requirements-resolved.txt`。没有把旧 TileLang wheel 安装到该环境。

`UV_CACHE_DIR=/workspace/.cache/uv`；不修改全局 shell 配置。宿主为 Debian 13.6 / GCC 14.2.0，设备编译仍使用单独记录的 CANN/Bisheng 与 Debian 12/GCC 12 sysroot。4 核/16 GiB 配额下，依赖编译 3 个任务、链接 1 个任务；独立 TVM 构建使用 1 个任务。

AscendNPU-IR 构建沿用固定前端 `install_npuir.sh --build-a5` 的 RTTI、assertion、Triton 和 Python binding 要求。此次调用 `build-tools/build.sh`，不使用其清理/应用补丁选项：

```bash
npui_src=/workspace/setup/backends/tilelang-mlir-ascend
npui_dep="$npui_src/3rdparty/AscendNPU-IR-Dev"
source /workspace/setup/backends/npuir-main/venv/bin/activate
export PATH=/workspace/Ascend/cann-9.2.0-beta.2/tools/bisheng_compiler/bin:$PATH
export BISHENG_INSTALL_PATH=/workspace/Ascend/cann-9.2.0-beta.2/tools/bisheng_compiler/bin
cd "$npui_dep"
bash build-tools/build.sh --c-compiler gcc --cxx-compiler g++ \
  --build-type Release -j 3 --enable-assertion \
  --disable-werror --disable-mlir-werror --disable-bishengir-werror \
  --build-triton --python-binding --build ./build \
  --install-prefix /workspace/setup/backends/npuir-main/bishengir-install \
  --add-cmake-options="-DCMAKE_LINKER=ld.lld -DLLVM_ENABLE_LLD=ON -DLLVM_ENABLE_RTTI=ON -DLLVM_PARALLEL_LINK_JOBS=1 -DLLVM_INCLUDE_TESTS=OFF -DMLIR_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_INCLUDE_BENCHMARKS=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DPython3_EXECUTABLE=/workspace/setup/backends/npuir-main/venv/bin/python -DLLVM_EXTERNAL_BISHENGIR_SOURCE_DIR=$npui_dep/bishengir -DLLVM_EXTERNAL_TRITON_SOURCE_DIR=$npui_dep/third-party/triton"
```

该固定依赖在 GCC 14.2 下有两处模板特化编译错误（`Matmul.cpp:503`、`NormalizeTypeConversion.cpp:229/231`）。单文件 `-fpermissive` 只能通过第一处，已撤下。本次通过 [npuir-main-vendor-clang.cmake](npuir-main-vendor-clang.cmake) 和 [npuir-main-vendor-clang-launcher.py](npuir-main-vendor-clang-launcher.py)，对 BiShengIR 目录中的 C++ 目标使用 SDK 自带 Bisheng/Clang 15.0.5；LLVM/Triton 保留 GCC 14.2，同用宿主 libstdc++。launcher 仅移除 Clang 不支持的三个 GCC 选项，固定上游源码保持不变。两份 GCC 失败诊断和 Clang 单文件验证保留在证据目录。

将这两个配置文件复制到 `/workspace/setup/backends/npuir-main/`，分别命名为 `vendor-clang.cmake` 和 `vendor-clang-launcher.py`，赋予 launcher 执行权限，在附加 CMake 参数中加入：

```text
-DCMAKE_PROJECT_INCLUDE=/workspace/setup/backends/npuir-main/vendor-clang.cmake
```

本次先按默认目标构建，再关闭未使用的 LLVM/MLIR 测试、示例和 benchmark 目标，并按上述宿主兼容配置增量续编。TVM 完成后，依赖构建改用 4 个编译任务；C++ 对象完成且大型 C API 库成功链接后，将 `LLVM_PARALLEL_LINK_JOBS` 从 1 调到 2，继续增量链接。

固定 TVM 另行构建到前端 checkout 的 `build/tvm-current`，供前端使用 `TVM_PREBUILD_PATH` 引入本次新编译的库；这是同一固定 TVM 源码的独立构建，不是历史二进制复用：

```bash
cmake -S "$npui_src/3rdparty/tvm" -B "$npui_src/build/tvm-current" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DUSE_LLVM=OFF -DUSE_CUDA=OFF -DUSE_ROCM=OFF \
  -DUSE_OPENCL=OFF -DUSE_VULKAN=OFF -DUSE_METAL=OFF -DUSE_RTTI=ON \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build "$npui_src/build/tvm-current" --target tvm tvm_runtime -j 1
```

前端需 `USE_NPUIR=ON`、`TILELANG_NPUIR_TARGET=A5`，以及真正包含 MLIR 头文件、静态库、CMake 包和 Python bindings 的构建依赖。恢复的 CANN BishengIR 运行工具包不满足这些开发要求；对应失败预检查日志保留作诊断，不能当作前端构建成功。

## 前端构建与实际导入

开发依赖安装完成后，本次执行以下前端配置；`build/tvm-current` 是上面独立构建的同一固定 TVM：

```bash
cmake -S "$npui_src" -B "$npui_src/build" -G Ninja \
  -DUSE_NPUIR=ON -DTILELANG_NPUIR_TARGET=A5 \
  -DBISHENGIR_ROOT_PATH=/workspace/setup/backends/npuir-main/bishengir-install \
  -DTVM_PREBUILD_PATH="$npui_src/build/tvm-current" \
  -DTVM_SOURCE_DIR="$npui_src/3rdparty/tvm" \
  -DUSE_CUDA=OFF -DUSE_ROCM=OFF -DUSE_LLVM=OFF -DMLIR_INCLUDE_TESTS=OFF \
  -DPython3_EXECUTABLE=/workspace/setup/backends/npuir-main/venv/bin/python \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_JOB_POOLS=frontend_link=1 -DCMAKE_JOB_POOL_LINK=frontend_link \
  -DCMAKE_MODULE_LINKER_FLAGS=-Wl,--exclude-libs,ALL
cmake --build "$npui_src/build" -j 3
```

原默认链接能构建，但真实导入第二份库 `libtilelangir.so` 时因 LLVM option 重复注册而 abort。最后一个链接选项隐藏 helper module 静态库符号，解决了两份 native library 的 LLVM 符号相互干扰；没有修改固定前端源码、关闭 assertion 或跳过 lowering pass。实际导入主库和 native adapter 均成功，路径与 SHA256 见 [frontend-build.json](../../examples/scenarios/npuir-main-013dbbf5/frontend-build.json)。详细最终配置见同目录 `selected-build-config.json`。

使用 [activate_npuir_main.sh](activate_npuir_main.sh) 进行 source-tree 导入，没有安装旧 wheel，也没有把旧 wheel 的二进制与新 Python 源码拼接。正式 worker 的 cwd 固定为前端根目录，避免该版本的版本字符串从调用目录错误获取 Git 后缀。

## 输入、CPU 目标选择与设备 ABI

先运行 [prepare_npuir_main.py](../scenarios/prepare_npuir_main.py) 校验 workload 和 fixture。新版 worker 使用 `--expected-npuir-root "$npui_src"` 检查实际导入目录、固定源码提交、未修改的前端文件，以及位于该 checkout `build/` 下的 TileLang/TVM 编译库；记录主库、helper 与 TVM SHA256，并要求 `TILELANG_ENABLE_SIMT=0`。

`--npuir-cross-compile-a5` 显式把该固定前端 `tilelang.jit.jit_npu._ARCH_CACHE` 设为 `Ascend950PR_9589`。这是无硬件环境中的目标选择：其 `phase.py` 在判断 SIMT 开关前先查询设备。该适配不替换算子、不生成假计算，也不跳过 pass；每条成功 lowering 必须实际经过 `NpuLoopVectorize`，且不得出现 `NpuSimtIndirectLoad`。保留原查询失败诊断。

设备编译保留 CANN 9.2.0-beta.2 的 BishengIR 1.2.0 / LLVM 19.1.7，使用固定新版 `jit_npu.py` 的 A5 参数：

```text
--target=Ascend950PR_9589 --enable-auto-multi-buffer=true --disable-ffts
--enable-triton-kernel-compile=true --enable-hivm-compile=true
--enable-vf-merge-level=1 --enable-hfusion-compile=true --enable-auto-bind-sub-block=true
```

附加 `--save-temps=<case>/temps` 保留优化 MLIR。沿用旧参数得到的 ELF 缺少内核参数段，已拒绝启动。新版输入为两个动态 i8 memref、三个动态 f32 memref 和六个 i32；Triton kernel adaptation 去掉 PID 参数并把 memref 变为裸指针。实测优化入口为 5 指针 + 3 个 i32，ELF `__CCE_KernelArgSize` 为 **56 字节**（含尾部对齐）；232 和 224 均不是本次 ABI。

`npuir_a5` runner 使用 V2 launch、单 block、grid=(1,1,1)、`localMemorySize=221184`（固定前端 A5 默认值）。worker 对输入及优化后的 main 函数检查 lock/workspace 未使用，才允许传 null；核对签名、符号/ELF 参数段并保留证据。该 runner 不支持一般 workspace、跨核同步或其他 ABI。

只有真实 CAModel 执行、NaN 预填输出的逐元素精确比较、64 个 FP32 canary 和 Profiling 全部通过，才能记为成功。新版通过 `report.py --paths npuir_auto_simd` 单独导出；SDK、虚拟环境、完整构建目录和大型模拟轨迹不上传。不能复制历史其他后端结果充当本次执行。
