# Parallel 场景实测矩阵

[English](README.en.md)

## 新版 A5 实测（2026-10-06）

**固定新版 `tile-ai/tilelang-mlir-ascend@013dbbf5` 的 14/14 场景均成功 lowering、设备编译和真实厂商 CAModel 模拟；NaN 预填后的逐元素精确比较、输出 canary 和 Profiling 全部通过。14 次独立模拟，0 次复用，0 个正式场景失败。** 以下“本次”列是新执行；旧 NPU-IR、AscendC/PTO 列取自 2026-10-04 历史证据，没有在本次重跑。

前端完整提交为 `013dbbf5824c3ac29e975d78c0b38e60b2410be7`，TVM 为 `c2921fdaf795b1103d21abc962e83a209c7258d7`。14 份 workload 与历史源文件逐字节一致，fixture SHA256 全部匹配；归约仍为外层 `T.Parallel`、内层 `T.serial`，没有改为 `T.reduce_sum`。显式 `TILELANG_ENABLE_SIMT=0`，所有场景实际经过 `tl.NpuLoopVectorize`，未经过 SIMT indirect-load pass。

数字为 **CAModel 周期 / 执行指令数**，不是物理 A5 性能。历史列中的共享模拟关系仍见下方完整历史矩阵的 † 标记；本次 14 条没有共享模拟。

| 场景 | 新 NPU-IR（本次） | 旧 NPU-IR（历史） | AscendC SIMD（历史） | PTO SIMD（历史） |
|---|---:|---:|---:|---:|
| scalar_const_256 | 2213/101 | 2229/106 | 2137/98 | 2111/93 |
| scalar_const_4x64 | 2186/101 | 2238/106 | 2128/98 | 2111/93 |
| scalar_buffer_256 | 2774/146 | 2767/153 | 2119/103 | 2135/100 |
| scalar_buffer_4x64 | 2774/146 | 2767/153 | 2131/103 | 2135/100 |
| copy_256 | 2117/65 | 2149/70 | 2138/91 | 2135/83 |
| copy_4x64 | 2143/65 | 2149/70 | 2143/91 | 2135/83 |
| fill_256 | 1483/75 | 1871/80 | 1430/83 | 1432/76 |
| fill_4x64 | 1471/75 | 1871/80 | 1420/83 | 1432/76 |
| broadcast_row | 2722/146 | 2781/153 | 2152/103 | 2146/100 |
| broadcast_column | 2739/148 | 2879/199 | 2145/107 | 2164/101 |
| flatten | 7280/1870 | 14012/11851 | 2149/91 | 2135/83 |
| reduce_all_256 | 7216/2126 | 7217/2131 | device_compile failed | device_compile failed |
| reduce_rows | 7208/2140 | 7518/2145 | device_compile failed | device_compile failed |
| reduce_columns | 6945/1554 | 6966/1559 | device_compile failed | device_compile failed |

### 构建、后端与 ABI

原 Dev 仓库权限问题通过官方公开 [Ascend/AscendNPU-IR](https://gitcode.com/Ascend/AscendNPU-IR) 解决：直接获取完全相同的 `77f5b0617813c9974b56e4090bccf57d2612a301`，只覆盖本地子模块 URL，没有替换 gitlink。固定 LLVM/Triton、7 份官方 Triton 补丁、545 份开发静态库、MLIR headers/config 和新 TVM/TileLang 库均实际构建完成。独立 Python 3.11.16 环境没有安装旧 TileLang wheel；每例记录源码提交、实际导入位置和新编译主库/helper/TVM SHA256。构建配置、宿主 GCC/Clang 兼容处理及 LLVM 符号隔离见 [构建说明](../../setup/backends/NPUIR_MAIN.md) 和 [构建凭据](npuir-main-013dbbf5/frontend-build.json)。

设备编译仍用原 **CANN 9.2.0-beta.2、BishengIR 1.2.0 / LLVM 19.1.7**，模拟仍为 `Ascend950PR_9589` / `dav-3510`；新构建的开发工具链提供前端依赖，不替换本次设备后端。但编译选项改为固定新版 JIT 的 A5 配置，包含 HFusion、Triton kernel adaptation、VF merge 和 `--disable-ffts`，详见逐例 `device-command.json`。因此本表比较的是前端及配套编译流程的组合变化，不能把全部差异单独归因于前端 IR。

新版 `tilelang.lower` 返回 tensor/linalg MLIR；旧版返回已较低层的 HIVM MLIR，初始 IR 不处于相同阶段。比较同时检查 `temps/module.hivm.opt.mlir` 与实际设备 Profiling。旧参数虽然能返回成功，却产生缺少内核参数段的 ELF，已作为诊断拒绝启动。

**实测 ABI 为 56 字节，旧版是 232 字节；此前 224 字节仅为源码推测，已排除。** 新版输入的五个动态 memref 和六个 i32 经适配后成为五个裸指针、三个 grid i32及尾部对齐；ELF 参数段、优化入口和符号逐例核对。runner 使用 `rtKernelLaunchWithFlagV2`、`localMemorySize=221184`、单 block；只有输入/优化 main 均确认 sync/workspace 未使用才传 null。CPU 无设备查询时由 harness 显式设置固定 A5 架构缓存，没有替换计算、修改固定前端源码或跳过 lowering pass。

### Lowering 与机器指令变化

- **列广播有实质改进。** [新版优化 IR](npuir-main-013dbbf5/results/ir/broadcast_column/npuir_auto_simd/temps/module.hivm.opt.mlir) 将旧版两个向量函数合为一个，消除完整广播临时缓冲，直接加载每行标量、广播到寄存器并相加。总指令 `199→148`；Profiling 的向量执行/加载/存储分类从 `7/13/12→5/8/5`。周期 `2879→2739`，但仍高于历史 AscendC/PTO SIMD 的 `2145/2164`。
- **flatten 明显改善，但未成为连续拷贝。** [新版 IR](npuir-main-013dbbf5/results/ir/flatten/npuir_auto_simd/temps/module.hivm.opt.mlir) 保留 256 次标量循环，消除旧版逐元素 `copy_ubuf_to_ubuf_1d_float` helper，改为直接 `memref.load/store`。总指令 `11851→1870`，周期 `14012→7280`；旧 helper 的向量加载/存储 `512/1024` 变为 `0/0`，新版标量加载/存储为 `258/256`（含外围加载）。这有 IR 与执行计数互相印证，但仍远慢于历史 AscendC/PTO 连续拷贝的约 2140 周期。
- **三种 reduction 没有实现向量归约。** 新版仍为标量累加循环，三项向量执行/加载/存储分类均为 0。正确通过不等于已 SIMD 化；这些结论仅适用于本次 Parallel/serial workload。历史 AscendC SIMD/PTO SIMD 的设备编译失败、PTO SIMT 的实际 helper 缺失仍作为历史失败保留，本次没有重测或删除所需 helper。
- **scalar_buffer 和行广播原先已有融合。** 新版仍在寄存器中完成广播加法，三项向量分类与旧版同为 `5/5/5`，总指令 `153→146`。不能把它们描述为本次首次消除完整广播缓冲。copy 继续直接连接 GM→UB→GM，向量计数均为 0，总指令 `70→65`。
- **fill 的周期下降不能直接解释为新向量化。** `1871→1483/1471`，总指令 `80→75`，但向量分类仍为 `2/0/5`；`fill_256` 的向量函数体在忽略函数头/缩进后与旧版一致。常量加法也保持向量分类 `5/4/5`。ABI/FFTS、外围标量指令、编译选项和启动 API 同时变化，缺少控制实验和旧完整时间线，不能把 fill 的全部周期变化精确分摊给某一个原因。

[comparison.json](npuir-main-013dbbf5/comparison.json) 提供每例旧/新 Profiling、静态 IR 特征和差值。新增 `instruction-events.json` 汇总 CAModel 实际 PC 指令事件（X/i，排除依赖箭头和计数器），14 例均与 Profiling 总执行数一致、无重复 instruction ID；这些是设备指令，不是 IR 行数。分类计数不是总指令数的完整分解。

### 证据与验证边界

[本次完整精简证据](npuir-main-013dbbf5/results/) 包含 workload、输入 TIR、vectorize 后 TIR、pass 清单、初始/优化 MLIR、ELF、ABI 签名/参数段、编译命令、数值/canary 标记、Profiling 和 SHA256。[preflight.json](npuir-main-013dbbf5/preflight.json) 记录恢复、构建和最终状态；`inputs.json` 的 `not_run` 是不可变的输入准备记录，不是最终结果。完整 pass dump、SDK、虚拟环境及大型轨迹留在本地。

新快照并未完整迁移旧环境：远端基线为 `06d764af`，快照本地仅 `840972e`；历史完整轨迹缺失，本次重新恢复脚本/环境、校验 658 份历史精简证据并准备相同输入。额外旧前端 copy 恢复冒烟 `2172/70`、旧 ELF 的 V2 启动探测 `2154/70`，以及新版 copy ABI 冒烟 `2155/65` 都是独立诊断，**不计入本次 14 条矩阵**，见 [probes](npuir-main-013dbbf5/probes/)。同一旧 ELF 已出现小幅周期变化，不能据几十周期差异给后端排序。

没有物理 NPU，未验证真实 A5 驱动/运行时/启动行为，也未在全新空白机器完成从零安装。runner 仅覆盖已验证的单 block FP32 小算子，不外推到多 block、workspace 或跨核同步。

## 历史基线（2026-10-04）

单 block、FP32；A 的逻辑规模为 256 个元素（fill 不读取 A），输出按场景为 256、1、4 或 64 个元素。数字为 CAModel **周期/执行指令数**，不是物理 NPU 性能。
† 表示跨组合复用 ELF、ABI、符号、fixture 和 runner 哈希均一致的已验证模拟；不代表独立再次执行。

| 场景 | CPU | AscendC SIMT | AscendC SIMD | PTO SIMT | PTO SIMD | NPU-IR 自动向量化路径 |
|---|---|---|---|---|---|---|
| scalar_const_256 | 通过 | 2648/124 | 2137/98 | 2618/144 | 2111/93 | 2229/106 |
| scalar_const_4x64 | 通过 | 2606/124 | 2128/98 | 2618/144 † | 2111/93 † | 2238/106 |
| scalar_buffer_256 | 通过 | 2627/139 | 2119/103 | 2597/159 | 2135/100 | 2767/153 |
| scalar_buffer_4x64 | 通过 | 2628/139 | 2131/103 | 2597/159 † | 2135/100 † | 2767/153 † |
| copy_256 | 通过 | 2627/116 | 2138/91 | 2599/136 | 2135/83 | 2149/70 |
| copy_4x64 | 通过 | 2627/116 | 2143/91 | 2599/136 † | 2135/83 † | 2149/70 † |
| fill_256 | 通过 | 1634/110 | 1430/83 | 1650/114 | 1432/76 | 1871/80 |
| fill_4x64 | 通过 | 1634/110 | 1420/83 | 1650/114 † | 1432/76 † | 1871/80 † |
| broadcast_row | 通过 | 2655/155 | 2152/103 | 2632/171 | 2146/100 | 2781/153 |
| broadcast_column | 通过 | 2641/147 | 2145/107 | 2612/167 | 2164/101 | 2879/199 |
| flatten | 通过 | 2647/116 | 2149/91 | 2599/136 † | 2135/83 † | 14012/11851 |
| reduce_all_256 | 通过 | 19235/2175 | failed (device_compile) | failed (device_compile) | failed (device_compile) | 7217/2131 |
| reduce_rows | 通过 | 6802/641 | failed (device_compile) | failed (device_compile) | failed (device_compile) | 7518/2145 |
| reduce_columns | 通过 | 2458/172 | failed (device_compile) | failed (device_compile) | failed (device_compile) | 6966/1559 |

状态统计：`{'passed': 75, 'failed': 9}`；设备通过 61/70 个组合，引用 48 份不同的成功模拟归档。75 个通过项包含 14 个 CPU 用例。

每个组合的源程序、IR 和失败日志见 [ir/](ir/)；[metrics.json](metrics.json) 保存失败阶段、完整诊断、校验标记、哈希和模拟报告的相对路径。完整 ELF/轨迹/HTML 留在工作目录。
未重新验证空白机器安装；未修改编译器，不将未通过的组合视为可用后端。

## 如何解读 SIMD 结果

以下结论来自上表已有的 IR 和 Profiling 归档，没有新增模拟或真机测量。AscendC/PTO 使用主前端 `994b44ec`；NPU-IR 使用 wheel `0.1.1.030+4e1bb3e4…`。两个前端版本不同，不能将全部差异归因于 IR 设计。

- **AscendC SIMD 与 PTO SIMD 的向量主体接近。** 连续加法、广播、copy 和 fill 均使用每批 64 个 FP32、共 4 批的处理方式。
- **NPU-IR 的优化效果依赖具体场景。** copy 消去了 UB 内部向量拷贝；内存标量和行广播在优化后复用向量寄存器；列广播仍保留中间缓冲；flatten 保留逐元素搬运循环。
- **“自动向量化路径”是编译路径名称。** NPU-IR 的三个归约最终使用标量累加，不能当作 SIMD reduction 性能。
- **周期与指令数需要分别解读。** 指令数是模拟器记录的动态设备指令总数，包含控制、搬运、标量和向量等指令，不是 IR 行数或加法次数。流水线重叠、依赖和同步使周期不与指令数成比例。

下文常量、内存标量、copy 和 fill 的数字取 `(256,)` 版本。GM 指设备全局内存，UB 指片上 Unified Buffer，MTE2/MTE3 分别承担这里的搬入/写回。

### AscendC 与 PTO：相近的向量主体

常量加法的 [AscendC 代码](ir/scalar_const_256/ascendc_simd/kernel.asc) 在四次循环中使用 `vlds_norm → vdup → vadd → vsts_norm`。[PTO IR](ir/scalar_const_256/pto_simd/kernel.pto) 对应 `pto.vlds → pto.vdup → pto.vadd → pto.vsts`，寄存器类型为 `!pto.vreg<64xf32>`；[PTO LLVM](ir/scalar_const_256/pto_simd/kernel.ll) 已把常量广播放到循环外。

两者都采用 `GM → UB → 向量计算 → UB → GM`，并在搬运和计算之间同步。`2137/98` 与 `2111/93` 表示相近算法下的代码生成差异，不能据此判断某一后端的 SIMD 计算能力更强。

常量加法的 [AscendC Profiling](ir/scalar_const_256/ascendc_simd/profile.json) 与 [PTO Profiling](ir/scalar_const_256/pto_simd/profile.json) 中，MTE2 利用率约为 60%，SIMD 利用率仅约 1.3%–1.4%。本例只有 1 KiB 输入，向量计算很短，搬运、控制和同步开销占据显著时间。利用率不能证明内存带宽已饱和；不同流水线可重叠，也不能把百分比直接相加当作耗时分解。

### 常量、内存标量与行广播

NPU-IR 常量路径由 `hivm.hir.vadd(tensor, scalar)` 降为 64 元素的 `vadds.s.x`，确实完成向量化。其 `2229/106` 比 AscendC/PTO 略高，不能解释成加法主体本身更复杂。见 [优化后 IR](ir/scalar_const_256/npuir_auto_simd/temps/module.hivm.opt.mlir)。

内存标量 `B[0]` 需要额外的 GM→UB 加载。NPU-IR 高层有 `tensor.extract → vbrc → vadd`，但[优化后 IR](ir/scalar_buffer_256/npuir_auto_simd/temps/module.hivm.opt.mlir) 将广播加载和加法放入同一个向量函数，没有保留完整的 256 元素广播缓冲。[行广播](ir/broadcast_row/npuir_auto_simd/temps/module.hivm.opt.mlir)同样先取得 B 的 64 个元素，再供四行计算复用。

内存标量的动态指令分类如下，来自三个后端各自的 [AscendC](ir/scalar_buffer_256/ascendc_simd/profile.json)、[PTO](ir/scalar_buffer_256/pto_simd/profile.json)、[NPU-IR](ir/scalar_buffer_256/npuir_auto_simd/profile.json) Profiling：

| 指标 | AscendC SIMD | PTO SIMD | NPU-IR |
|---|---:|---:|---:|
| 周期 / 总指令数 | 2119 / 103 | 2135 / 100 | 2767 / 153 |
| 标量指令数 | 68 | 69 | 110 |
| 向量执行类 `RVECEX_count` | 5 | 5 | 5 |
| 向量加载类 `RVECLD_count` | 5 | 5 | 5 |
| 向量存储类 `RVECST_count` | 5 | 5 | 5 |

向量分类计数相同，多出的指令主要位于外围部分。NPU-IR 的优化 IR 保留通用搬运 helper 调用及参数处理。这支持进一步检查搬运与控制开销，但不能仅凭汇总数据把约 30% 的周期增加精确归因于某个调用，也不能声称广播未融合。上述分类不是总指令数的完整分解，向量执行类计数也不等于 `vadd` 次数。

### 列广播：NPU-IR 保留额外缓冲

列广播计算 `O[i,j] = A[i,j] + B[i,0]`。AscendC 的 [`vlds_brc_elem`](ir/broadcast_column/ascendc_simd/kernel.asc) 和 [PTO 的广播加载](ir/broadcast_column/pto_simd/kernel.ll) 在每行直接取得标量、在寄存器中广播并相加。

NPU-IR 的[优化后 IR](ir/broadcast_column/npuir_auto_simd/temps/module.hivm.opt.mlir)则保留：

```text
加载 4 个 B → UB 内部拷贝
           → 向量函数 0：展开为 4×64 广播缓冲
           → 向量函数 1：读取 A 和广播缓冲并相加
```

这增加了一个 1 KiB 中间结果及其写入、读取。向量加载/存储计数在 AscendC/PTO 中为 `8/5`，在 [NPU-IR Profiling](ir/broadcast_column/npuir_auto_simd/profile.json) 中为 `13/12`。因此 `2879/199` 对比 `2145/107`、`2164/101` 有明确的结构性差异：该列广播尚未融合成直接的广播加载加法。源输入 B 仍只有 4 个元素，没有预先扩展输入来规避广播。

### copy 与 fill：更少指令不保证更少周期

AscendC/PTO 的 copy 仍经过 UB 输入区到输出区的向量 load/store。NPU-IR 的 [copy IR](ir/copy_256/npuir_auto_simd/temps/module.hivm.opt.mlir) 直接复用同一个 UB 缓冲，连接 `GM→UB` 和 `UB→GM`，并同步 MTE2 与 MTE3。其[向量执行、加载、存储计数均为零](ir/copy_256/npuir_auto_simd/profile.json)。总指令数由 AscendC 的 91、PTO 的 83 降到 70，属于成功优化；但 GM 读写规模没有减少，周期仍约为 2140。

fill 不读取 A，只生成常量并写回。三者的向量执行/加载/存储计数都是 `2/0/5`，但 NPU-IR 为 `1871/80`，AscendC 为 `1430/83`，PTO 为 `1432/76`。NPU-IR 指令少于 AscendC，周期却更多，说明不能用指令数直接解释时间差。其 [IR](ir/fill_256/npuir_auto_simd/temps/module.hivm.opt.mlir) 保留写回 helper 和末尾 barrier；需要指令时间线才能将差异分摊到延迟、依赖、同步或调度，现有汇总数据不能认定某个操作造成全部额外周期。

### flatten：连续拷贝未被识别

源程序显式执行 `O[k] = A[k // 64, k % 64]`。A 连续存储，线性地址可化简为 `(k // 64) * 64 + k % 64 = k`。

AscendC 的 flatten 与 copy 生成相同的 `kernel.asc`；PTO 生成相同的 `kernel.ll`，对应模式下 ELF 也相同。因此它们都约为 2140 周期。

NPU-IR [高层 IR](ir/flatten/npuir_auto_simd/kernel.mlir) 保留 256 次循环和单元素 slice 操作；[优化后 IR](ir/flatten/npuir_auto_simd/temps/module.hivm.opt.mlir) 仍在循环内构造单元素视图，并调用 `copy_ubuf_to_ubuf_1d_float`。与 NPU-IR 自己的 copy 相比：

| 指标 | copy | flatten | 对比 |
|---|---:|---:|---|
| 周期 | 2149 | 14012 | 约 6.52 倍 |
| 总指令数 | 70 | 11851 | 169.3 倍 |
| 向量加载 / 存储计数 | 0 / 0 | 512 / 1024 | 大量小拷贝 |

问题在于连续拷贝语义没有被识别，保留了逐元素搬运结构。不能仅凭高层 `div/rem` 就断言最终仍执行昂贵的整数除法，后续 LLVM 仍可能化简地址运算。此 flatten 有实际数据移动，不是零拷贝视图变换。

### 归约：能执行不等于已向量化

三个归约使用输出轴 `T.Parallel` 加归约轴 `T.serial`，分别计算 256 元素全量和、4 行各 64 元素和、64 列各 4 元素和，没有并行写同一输出的竞态。本轮未使用显式 `T.reduce_sum`。

AscendC 在 `__simd_vf__` 内保留标量读写、相加；PTO 在 `pto.vecscope` 内保留 `pto.load/addf/store`。当前编译器拒绝这种 SIMD 区域内的标量累加，报 `Unsupported scalar instruction in AIV loop`。见行归约的 [AscendC 代码](ir/reduce_rows/ascendc_simd/kernel.asc)、[PTO IR](ir/reduce_rows/pto_simd/kernel.pto) 和[编译诊断](ir/reduce_rows/pto_simd/device-compile.log)。这属于当前写法和版本的 lowering 边界，不代表后端或 ISA 不支持归约。

NPU-IR 可以执行，但[优化后的行归约](ir/reduce_rows/npuir_auto_simd/temps/module.hivm.opt.mlir)仍是 `memref.load → llvm.fadd f32 → memref.store` 的标量循环。三种归约的 `RVECEX_count`、`RVECLD_count`、`RVECST_count` 全部为零，标量流水线利用率约为 78%–85%。因此 `7217/2131`、`7518/2145`、`6966/1559` 是标量归约的模拟结果，`hivm.vf_mode=SIMD` 属性不能作为向量归约证据。

矩阵中的 PTO SIMT 失败原因不同：生成代码实际使用 `tl.as_logical_bool`，触发不兼容私有 helper 的 `ModuleNotFoundError: ptodsl._allreduce`，见[兼容诊断](compatibility/pto-helper-import.txt)。不能把所有归约失败归为同一个 SIMD 编译错误。

### 比较边界与后续方向

`(256,)` 和 `(4,64)` 都是连续的 256 元素，多个场景会生成相同或等价的设备代码。`†` 对应同一份已验证模拟，不是独立重复实验；不能据此计算多次运行的均值或方差，也不能根据几十周期的小差异给后端排序。

通过的设备组合均完成 NaN 初始化后的逐元素精确比较和输出末尾 64 个 FP32 canary 检查。失败组合没有可比较的模拟性能。当前 runner 仅覆盖这些单 block 用例，未验证跨核同步，也没有物理 A5 测量。

最明确的后续优化方向是 NPU-IR 的 flatten 连续拷贝识别、列广播融合，以及三条路径对嵌套 Parallel/serial 归约的处理。这些尚未实施；评估整体性能还需统一前端版本、扩大输入规模并重复测量。复现与补充解释见[场景说明](../../setup/scenarios/README.md)、[lowering 观察](ANALYSIS.md)及[验证范围](../../VALIDATION.md)。
