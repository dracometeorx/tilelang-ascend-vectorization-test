# Parallel 场景扩展

这组测试保持固定前端、CANN、A5 目标和单 block 边界，不修改编译器。
`cases.py` 生成每条路径的实际 Python 源文件，`worker.py` 在独立进程中解析、lowering 和编译；原始脚本与旧加法测试保持独立。

| 类别 | 测试语义 | 输入和输出 |
|---|---|---|
| vector + scalar | `A + 1.25`；`A + B[0]`（从 GM 输入加载） | A/O 为 `(256,)`、`(4,64)`；B 为 `(1,)` |
| broadcasting | `A[i,j] + B[j]`；`A[i,j] + B[i,0]` | A/O `(4,64)`；B `(64,)` 或 `(4,1)` |
| copy / fill | Parallel 逐元素赋值；Parallel 填 `1.25` | `(256,)`、`(4,64)` |
| flatten | `O[k] = A[k//64,k%64]` | `(4,64)` → `(256,)` |
| reduction | Parallel 遍历输出轴，serial 累加归约轴 | `(256,)` → `(1,)`；`(4,64)` → `(4,)` 或 `(64,)` |

归约测试的是嵌套循环的 lowering 能力，不是显式 `T.reduce_sum`，也不是无同步的并行 scatter 累加。copy/fill 测试计算体使用 Parallel；GM↔UB 搬运仍使用 `T.copy`。flatten 是实际逐元素重索引拷贝，不是零拷贝 view。内存标量不是 C ABI 的 by-value 标量参数。

## 执行

先按根目录 README 安装或恢复依赖，然后用 `bootstrap.py` 展开到实验工作目录。
在展开后的实验工作目录（`bootstrap.py --workspace` 指定的目录）运行：

```bash
bash setup/scenarios/run.sh --compile-only
bash setup/scenarios/run.sh --simulate-only --reuse-identical
python setup/scenarios/report.py \
  --results setup/tilelang/results/scenarios \
  --export parallel-report
```

也可不带参数一次执行所有阶段，或用 `--case broadcast_column` 选择单个场景。
`--simulate-only` 使用已经编译的结果；失败组合仍保留，不会伪造设备结果。默认每次模拟限时 300 秒，可用 `--simulation-timeout 900` 调整；超时单独保留，不能当作编译错误或数值错误。
需要允许本机进程间 socket：厂商 Profiling 使用 Python multiprocessing Manager。若沙箱禁止该操作，数值模拟可能成功而 HTML 报告失败，不能将其视为完成 Profiling。

## 数值与运行证据

- 14 个 fixture 共用于 CPU 和设备：输入为小范围二进制分数；归约中间结果可精确表示，允许逐元素 `rtol=atol=0`。
- fixture 二进制头为 3 个小端 uint32 长度，后接 A、B、reference 的小端 FP32 数组。runner 校验长度、完整性与尾随字节。
- 所有逻辑输出先填 NaN，末尾额外放 64 个 FP32 canary；同时检查精确值和保护区。
- AscendC/PTO 从 device TIR 获取 `A,B,O`、`A,O` 或 `O` 参数顺序，并核对 ELF `__CCE_KernelArgSize`；未使用参数会被删掉，不能固定传三个指针。
- NPU-IR 保留 232 字节的动态 rank-1 memref 描述符，分别传实际 A/B/O 长度。只接受 lock/workspace 未使用的单 block 入口；这不是通用 NPU-IR runtime。
- 每次 CAModel 使用独立工作目录和新日志；只有数值标记、唯一内核 Profiling、正周期/指令数、HTML 全部存在才标记通过。
- `--reuse-identical` 仅在 ELF、ABI、符号、输入/reference fixture 和 runner 全部匹配时复用既有成功证据；导出表对跨组合复用以 † 标记，不能当作独立重复测量。
- 默认完整执行保留所有失败结果，进程正常结束并不表示矩阵全部通过；以每条 `result.json` 和导出报告为准。

`auto_simd` 是 NPU-IR 路径标识，不保证每种源程序成功向量化。应查看 `kernel.mlir`、NpuLoopVectorize TIR 与后端 `module.hivm.opt.mlir`。所有数字仅为此版本 CAModel 的一次测量或明确标记的复用值，不是硬件性能或统计基准。
