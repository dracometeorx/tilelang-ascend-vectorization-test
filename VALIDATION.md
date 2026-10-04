# 验证记录

验证日期：2026-10-02，x86_64 Linux 云环境，无物理 NPU。

## 原云环境

- 主 TileLang 源码构建成功；Ascend 宿主测试 688 passed、1 skipped（依赖真实 runtime），CPU 测试 35 passed，版本测试 3 passed。
- `(256,)`、`(4,64)` CPU 加法精确校验通过。
- AscendC SIMT/SIMD 的 4 个用例均完成 lowering、Bisheng 编译、CAModel 数值校验和 Profiling。
- PTO SIMT/SIMD 的 4 个用例及 NPU-IR 自动 SIMD 的 2 个用例均完成 lowering、编译、CAModel 数值校验和 Profiling。
- NPU-IR/PTO 的 `run.sh --reuse` 重新生成 6 个匹配的设备二进制，成功复用经二进制与 runner SHA256 核对的正确模拟记录。

精简指标见 `examples/metrics.json`。完整 HTML 报告、设备二进制和模拟轨迹保留在原云环境，未提交到 Git。

## 独立仓库打包验证

使用本仓库的 `bootstrap.py` 将脚本展开到 `/workspace/a5-lab-package-check`：

- 26 个模板成功展开，重复执行成功。
- 4 个 Debian sysroot 包重新下载并通过固定 SHA256 校验。
- Python 文件解析与全部 shell 脚本语法检查通过。
- 新路径下的 1D/2D CPU 加法及 4 个 AscendC lowering 通过。
- 新路径下的 2 个 NPU-IR lowering、4 个 PTO 设备编译及 2 个 NPU-IR 设备编译通过。
- 新路径下重新构建 runner 并实际运行 NPU-IR `(256,)`：256 个 FP32 输出精确正确，生成 HTML Profiling 报告，2749 模拟周期、135 条指令。与原记录的周期波动不构成真实硬件性能结论。

本次路径验证复用了原云环境已安装的 TileLang、虚拟环境、SDK 和 sysroot，通过符号链接接入；测试脚本、输出目录和重新编译的模拟 runner 位于新工作目录。

## 尚未验证与范围限制

- 没有在另一台完全空白机器上重新执行整个 `bootstrap.py --install`。安装脚本基于本次实际安装过程整理，新增的系统 RPM 工具选择分支尚未在干净镜像上验证。
- `environment/*.freeze.txt` 是实测依赖清单，不是跨平台锁文件；安装脚本固定关键工具链/前端版本，其他依赖仍按主仓库 requirements 解析。
- 没有真实 A5 硬件性能数据；没有验证其他 shape、dtype、多 block、跨核同步或复杂算子。
- NPU-IR 旧前端的 A5 架构识别限制及 PTO helper 兼容处理见 README，不能将本次小加法结果外推为完整后端兼容性。

## Parallel 扩展（2026-10-04）

新增 14 个场景：常量/内存标量加法的 1D/2D、行/列广播、copy/fill 的 1D/2D、flatten、1D 全量求和、2D 行/列求和。

- 14 个 CPU 基线通过逐元素精确校验。
- 70 个设备路径编译尝试：61 个完成 ELF 编译并通过 CAModel 精确数值、输出保护区及 Profiling 校验；9 个归约组合保留明确失败证据（3 个 AscendC SIMD、3 个 PTO SIMD、3 个 PTO SIMT）。
- 61 个成功组合引用 48 份不同的成功模拟归档；相同 ELF/ABI/符号/fixture/runner 的复用明确标记。最终再次校验全部成功记录、唯一内核报告及 658 份导出证据的 SHA256。
- 在 `/workspace/a5-lab-package-check` 重新展开脚本，复用已安装依赖，再次运行全部 84 个 CPU/设备组合，得到相同状态；238 个生成源码与前端 IR 文件逐字节一致。
- 场景脚本 Python/shell 语法检查通过；84 份生成 Python 程序通过语法检查。fixture 长度及 FP32 精确可表示性检查通过，runner 在启动 runtime 前拒绝空、截断和零长度 fixture。
- ABI 从设备 TIR 和 ELF 参数字节数核对，覆盖 1/2/3 指针及 NPU-IR 232 字节描述符。输出包含 64 个 FP32 canary，不能仅凭进程返回码认定数值通过。

实际 CAModel 状态、唯一执行与严格哈希复用、周期/指令数均记录在 [扩展矩阵](examples/scenarios/README.md) 与 `examples/scenarios/metrics.json`。初期 runner ABI 适配与沙箱 Profiling 问题不计为后端失败；最终证据只接受修正后完整通过的记录。

上述重新展开验证仍不是空白机器完整安装。归约使用 Parallel/serial 嵌套循环，未测试显式 `T.reduce_sum`；NPU-IR 的路径名称不代表每个场景都完成了自动向量化。
