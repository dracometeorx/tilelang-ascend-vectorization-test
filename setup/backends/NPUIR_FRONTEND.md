# TileLang NPU-IR CPU lowering

已验证 `float32`、单个计算块、`(256,)` 和 `(4,64)` 两个 `T.Parallel` 加法的真实 NPU-IR lowering。

```bash
bash /workspace/setup/backends/install_npuir_frontend.sh
# 后续只需：
source /workspace/setup/backends/activate_npuir.sh
python /workspace/setup/backends/npuir_add_lab.py
```

输出为 `/workspace/setup/tilelang/results/npuir/{256,4x64}/kernel.mlir`，每个用例有 9 个 TIR pass 快照及 `passes.json`。`npuir_add_lab.py` 根据上游 `examples/elementwise/example_elementwise_add.py` 改为同一组 FP32 输入形状，采用 `alloc_shared` 和 Developer 模式。

实际路径：`T.Parallel` → `tl.NpuLoopVectorize` → `T.npuir_add` → 原生 NPU-IR codegen → tensor 形式的 `hivm.hir.vadd` → MLIR canonicalize / adapt_triton_kernel。1D 保留 `tensor<256xf32>`，2D 保留 `tensor<4x64xf32>`。它与主仓库 PTO 的显式 SIMT/SIMD VF 接口不同，不能解释为该版本支持 `T.SimtVF` 与 `T.SimdVF` 两条路径。

## 固定版本

- Python 3.11.16，独立环境 `/workspace/setup/backends/npuir-venv`。
- 上游发布 `v0.1.1.030-pre-release`，提交 `4e1bb3e494b0bd70a55ec0b7ddaa78a4b6a93333`。
- Wheel：`tilelang-0.1.1.30+ubuntu.22.4.npuir-cp311-cp311-linux_x86_64.whl`。
- 下载：`https://github.com/tile-ai/tilelang-ascend/releases/download/v0.1.1.030-pre-release/tilelang-0.1.1.30+ubuntu.22.4.npuir-cp311-cp311-linux_x86_64.whl`。
- 实际下载 SHA256：`4937fe4451c34603d773f4000a63df7bd0732e20f589ce8b576333c5fa9b9373`，安装脚本复核该散列。此值是本次官方 HTTPS 下载的本地固定值，未声称存在独立厂商签名。
- torch `2.12.0+cpu`，torch_npu `2.12.0.post2`，NumPy `1.26.4`。
- 原始 wheel 内的 1679 个 `.py` / `.so` 与当前安装内容逐字比较一致，未修改源码或原生编译器。

## CPU-only 适配及边界

Wheel 顶层导入的 `utils/npu_utils.py` 强制 `import torch_npu`，尽管此模块仅在构建运行时扩展时访问它。torch_npu 需要此环境未提供的旧版 `libhccl.so`；CANN 9.2 的 hcomm 组件没有声明该名字的兼容链接，因此没有伪造共享库或链接。

实验脚本先关闭 `TORCH_DEVICE_BACKEND_AUTOLOAD` 并加载真实 CPU torch，再用 Python 标准 `importlib.util.LazyLoader` 延迟真实、已安装的 torch_npu 模块。只要调用它的实际运行时功能，原模块仍会执行并进行正常依赖检查。没有替换 TileLang、TVM 或 NPU-IR 的编译功能。脚本最后断言 `torch_npu._C` 未加载。本环境中的普通 `import tilelang` 仍需要此纯 lowering 启动适配；它不代表完整 torch_npu NPU 运行时可用。

该 wheel 的 `AscendArch` 白名单漏了 `Ascend950`，会退到 `Ascend910B` 的容量信息并发出警告；在这两个 FP32 用例中该 helper 只参与 BF16 legalization 判断，原生输出是无固定 SIMD 宽度的高层 tensor MLIR。实际 A5 芯片由后续 `bishengir-compile --target=Ascend950PR_9589` 指定。这个验证范围不能外推至容量敏感调度、BF16、混合 Cube/Vector 或其他形状。

当前 frontend 输出采用 `adapt_triton_kernel` 的 12 个逻辑参数：ffts 地址、同步缓冲、workspace、A/B/O memref、6 个 i32 调度参数。本次 CANN 编译将 5 个动态一维 memref 分别展开为 allocated/aligned 指针、offset、size、stride，二进制 `__CCE_KernelArgSize` 为 232 字节，不能直接用原来 3 指针 AscendC launcher。额外入口已在 `sim_runner_ir.cc` 中适配。本次单 block 加法不使用跨核 FFTS、lock 或 workspace，传零；不能外推到需要这些资源的 kernel。设备编译、数值与 Profiling 状态以主比较实验结果为准。
