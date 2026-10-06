# TileLang Ascend A5 CPU lowering lab

在没有 NPU 的 x86_64 Linux 机器上，对比小型 `T.Parallel` FP32 算子的 **AscendC、PTO SIMT/SIMD、NPU-IR 自动 SIMD** lowering，并通过厂商 A5 CAModel 获取数值校验与模拟 Profiling。

本仓库收录测试代码、环境配置、版本/校验值和精简 IR 样例。CANN 安装包、虚拟环境、编译产物和大型模拟轨迹由安装/运行脚本生成，不存入 Git。

## 已验证结果

输入为 `(256,)` 和 `(4,64)`，单 block，FP32，`O=A+B`。所有模拟都用相同确定性输入，输出初始化为 NaN，逐元素精确比较。

| 路径 | 1D 模拟周期 | 2D 模拟周期 | 执行指令数 |
|---|---:|---:|---:|
| AscendC SIMT | 2636 | 2618 | 135 |
| AscendC SIMD | 2143 | 2161 | 103 |
| PTO SIMT | 2611 | 2639 | 167 |
| PTO SIMD | 2145 | 2160 | 97 |
| NPU-IR 自动 SIMD | 2799 | 2747 | 135 |

这 10 个用例均在原云环境通过数值校验和 Profiling。原始指标摘录在 [examples/metrics.json](examples/metrics.json)。周期是 CAModel 模拟结果，不是 CPU 墙钟时间，也不是物理 NPU 实测；同一后端的 1D/2D 最终二进制相同，小幅周期差异来自运行间波动。

## 扩展 Parallel 场景

新增 vector + scalar、行/列广播、copy/fill、flatten 和 reduction 共 14 个场景，分别对照 CPU、AscendC SIMT/SIMD、PTO SIMT/SIMD 和 NPU-IR 自动向量化路径。
测试语义与运行方式见 [场景说明](setup/scenarios/README.md)，实测状态、模拟周期/指令数和 IR 证据见 [扩展矩阵](examples/scenarios/README.md)，机制差异见 [lowering 解读](examples/scenarios/ANALYSIS.md)。
2026-10-06 固定新版 `tilelang-mlir-ascend@013dbbf5` 与 A5 开发依赖已从源码构建，14/14 同输入场景独立通过真实 CAModel。列广播融合、flatten 降低逐元素开销，三种 reduction 仍为标量循环；实际 ABI 为 56 字节。旧后端数据明确标为历史，详见[双语对比与证据](examples/scenarios/README.md)。
归约采用输出轴 Parallel、归约轴 serial；不能将其失败外推到显式 `T.reduce_sum`。NPU-IR 路径名称也不保证所有程序成功向量化。

## 安装

要求 x86_64 Linux，建议为 CANN 工具链、两套 Python 环境和本地编译预留至少 30 GB 磁盘、16 GB 内存；模拟按顺序执行，原云环境为 32 GB。无需 NPU 驱动。源码固定到 [versions.json](versions.json) 中的提交。

Debian/Ubuntu 系统依赖：

```bash
sudo apt-get update
sudo apt-get install -y build-essential git curl ca-certificates pkg-config \
  python3-venv python3-dev libffi-dev libssl-dev libzstd-dev zlib1g-dev \
  rpm rpm2cpio cpio
python3 -m venv "$HOME/.venvs/a5-lab-tools"
"$HOME/.venvs/a5-lab-tools/bin/pip" install uv==0.12.19
export PATH="$HOME/.venvs/a5-lab-tools/bin:$PATH"
```

在本仓库根目录运行（工作目录不要包含空格）：

```bash
python3 bootstrap.py --workspace /workspace/a5-lab --install
```

`bootstrap.py` 将已验证脚本中的工作目录替换为指定路径，下载并校验 Debian 12 编译 sysroot，克隆固定版本 TileLang，安装 CPU Python 依赖，构建 Ascend 后端，再配置 CANN、PTO 和独立 NPU-IR 前端。不会覆盖已有但未经本工具管理的脚本，也不会重置不匹配的 TileLang checkout。

仅检查/展开配置，不安装：

```bash
python3 bootstrap.py --workspace /workspace/a5-lab
# 同时验证可下载的 sysroot 包：
python3 bootstrap.py --workspace /workspace/a5-lab --fetch-sysroot
```

签名验证保持开启：CANN RPM 检查厂商签名，内部 `.run` 检查内置 SHA256，PTO/NPU-IR wheel 固定本次官方 HTTPS 下载的 SHA256，sysroot 包固定来自已验证 Debian 索引的 SHA256。上游移除旧版本时应更新经过验证的版本清单，不能跳过校验。

## 运行

```bash
# CPU 基线 + AscendC SIMT/SIMD，4 个模拟用例
bash /workspace/a5-lab/setup/tilelang/run.sh

# NPU-IR 与 PTO，6 个模拟用例
bash /workspace/a5-lab/setup/backends/run.sh

# 重跑 lowering/编译，仅复用二进制和 runner SHA256 匹配的正确模拟记录
bash /workspace/a5-lab/setup/backends/run.sh --reuse
```

完整模拟通常需要数分钟。结果写入工作目录的 `setup/tilelang/results/`：

- `SUMMARY.md`：AscendC 结果。
- `backend-comparison/README.md`：NPU-IR/PTO 结果及对照。
- `*_simt` / `*_simd`：AscendC TIR、源码及模拟输出。
- `pto_probe/`：PTO 的 TIR、PTODSL、PTO/VPTO/LLVM IR、设备 ELF、报告。
- `npuir/`：NPU-IR TIR、高层 MLIR、后端 pass 快照、设备 ELF、报告。

每次模拟必须同时满足 `SIMULATOR_CORRECT`、生成报告和正周期/指令数。仅 `npusim` 返回 0 不代表数值正确。

## Lowering 对比

```text
AscendC: T.Parallel → Ascend TIR pipeline → AscendC → Bisheng → A5 ELF
PTO:     T.Parallel → Ascend TIR pipeline → PTODSL → PTO → VPTO → LLVM → Bisheng
NPU-IR:  T.Parallel → NpuLoopVectorize → tensor HIVM → 后端向量化 → A5 ELF
```

PTO SIMT 使用 128 线程、每线程 2 元素；PTO SIMD 已明确 64 个 FP32 元素的向量操作。NPU-IR 保留整块 tensor 的 `hivm.hir.vadd`，后端再生成 64 元素向量函数。参见 [精简 IR 样例](examples/ir) 和 [测试代码](setup)。

## 兼容范围

- 主 TileLang 为 `dracometeorx/tilelang@994b44ec`；NPU-IR 为上游发布 wheel `0.1.1.030+npuir`，两者不是同一版本，因此不能把周期差异完全归因于 IR 设计。
- NPU-IR 前端使用独立 Python 3.11 环境。标准 LazyLoader 延迟真实 torch_npu 的运行时导入，编译器源码/二进制未修改。旧 wheel 的 Ascend950 白名单存在遗漏，本次仅验证 FP32 小加法；下游明确指定 A5。详见 [前端说明](setup/backends/NPUIR_FRONTEND.md)。
- PTOAS VMI 0.1.9 与主仓库的私有 helper API 不完全匹配。四个加法经 AST 检查不使用 helper，仅在独立编译副本中移除未使用 import；原始源码与 diff 都保留。其他算子不能直接外推。
- NPU-IR 本次为自动 SIMD，未声称验证其显式 SIMT VF 接口。
- 模拟 runner 仅适配这些单 block 加法。NPU-IR 使用 232 字节动态 memref 参数描述符，PTO/AscendC 使用 3 个指针。FFTS/锁/workspace 未使用，传零；不适用于跨核或混合 kernel。
- [setup/](setup) 内的 `/workspace` 是部署模板。应使用 `bootstrap.py` 展开后执行，不要在仓库内直接运行这些模板。

## 验证记录与第三方组件

原云环境的功能验证、重新打包验证及尚未执行的检查分别记录在 [VALIDATION.md](VALIDATION.md)。厂商 SDK 和第三方代码的来源/许可边界见 [THIRD_PARTY.md](THIRD_PARTY.md)。

两套 Python 环境的实测依赖清单见 [environment/](environment/)，用于排查版本差异；它们不是完整安装锁文件。

原云环境的 `install_script` / `start_skill` 可参考 [cloud-environment.md](cloud-environment.md)。本仓库不会保存令牌、账号信息或自动发布云环境。
