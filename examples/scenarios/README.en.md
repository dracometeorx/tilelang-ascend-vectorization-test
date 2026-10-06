# Parallel scenario results

[中文](README.md)

## New A5 measurements (2026-10-06)

**All 14/14 scenarios with fixed `tile-ai/tilelang-mlir-ascend@013dbbf5` completed lowering, device compilation, and real vendor CAModel execution. Exact elementwise checks after NaN initialization, output canaries, and Profiling all passed: 14 independent simulations, no reuse, and no failed formal cases.** Only the new column contains current executions. Old NPU-IR and AscendC/PTO columns are historical evidence from 2026-10-04, not reruns in this task.

The full frontend commit is `013dbbf5824c3ac29e975d78c0b38e60b2410be7`; TVM is `c2921fdaf795b1103d21abc962e83a209c7258d7`. All workloads are byte-identical to historical sources and all fixture SHA256 values match. Reductions retain outer `T.Parallel` and inner `T.serial`, without switching to `T.reduce_sum`. `TILELANG_ENABLE_SIMT=0` is explicit; every case actually executes `tl.NpuLoopVectorize` and none executes the SIMT indirect-load pass.

Numbers are **CAModel cycles / executed instructions**, not physical A5 performance. Historical reuse relationships remain marked † in the full historical matrix below. All 14 new entries have separate simulation archives.

| Scenario | New NPU-IR (current) | Old NPU-IR (historical) | AscendC SIMD (historical) | PTO SIMD (historical) |
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

### Build, backend, and ABI

The official public [Ascend/AscendNPU-IR](https://gitcode.com/Ascend/AscendNPU-IR) repository supplies the exact required commit `77f5b0617813c9974b56e4090bccf57d2612a301`, resolving the original Dev repository's access problem. Only the local submodule URL was overridden; gitlinks were unchanged. Pinned LLVM/Triton, seven official Triton patches, 545 development static libraries, MLIR headers/config, and new TVM/TileLang libraries were built. The isolated Python 3.11.16 environment contains no old TileLang wheel. Each result records source commits, actual import paths, and main/helper/TVM library hashes. See the [build instructions](../../setup/backends/NPUIR_MAIN.md) and [build receipt](npuir-main-013dbbf5/frontend-build.json) for GCC/Clang compatibility and LLVM symbol isolation.

Device compilation retains **CANN 9.2.0-beta.2, BishengIR 1.2.0 / LLVM 19.1.7**; simulation retains `Ascend950PR_9589` / `dav-3510`. The newly built development toolchain supplies frontend dependencies, not a replacement device backend. However, compilation flags now follow the fixed new JIT's A5 configuration, including HFusion, Triton kernel adaptation, VF merge, and `--disable-ffts`; see each `device-command.json`. This compares the frontend together with its accompanying compilation flow. Differences cannot all be attributed to frontend IR alone.

New `tilelang.lower` returns tensor/linalg MLIR, while the old frontend returned lower-level HIVM MLIR. Initial outputs are at different stages, so comparisons also inspect `temps/module.hivm.opt.mlir` and actual device Profiling. Old flags returned exit 0 but produced an ELF without the kernel argument section; that diagnostic artifact was rejected for launch.

**The measured ABI is 56 bytes, versus 232 previously. The source-only 224-byte estimate was disproved.** Five dynamic memrefs and six i32 inputs become five bare pointers and three grid i32 values plus tail padding. Each ELF argument section, optimized signature, and symbol is checked. The runner uses `rtKernelLaunchWithFlagV2`, `localMemorySize=221184`, and one block; null sync/workspace pointers are allowed only after confirming they are unused in both input and optimized main. On the CPU host, the harness explicitly selects the fixed A5 architecture cache, without substituting computation, modifying pinned frontend source, or skipping lowering passes.

### Lowering and executed instructions

- **Column broadcast improves materially.** The [new optimized IR](npuir-main-013dbbf5/results/ir/broadcast_column/npuir_auto_simd/temps/module.hivm.opt.mlir) combines two vector functions into one and removes the full broadcast temporary, loading each row's scalar for register broadcast and addition. Total instructions fall `199→148`; Profiling vector execute/load/store categories fall `7/13/12→5/8/5`. Cycles fall `2879→2739`, still above historical AscendC/PTO SIMD `2145/2164`.
- **Flatten improves substantially but remains a scalar loop.** The [new IR](npuir-main-013dbbf5/results/ir/flatten/npuir_auto_simd/temps/module.hivm.opt.mlir) retains 256 iterations, replacing the old per-element `copy_ubuf_to_ubuf_1d_float` helper with direct `memref.load/store`. Instructions fall `11851→1870`, cycles `14012→7280`; the old helper's vector loads/stores `512/1024` become `0/0`, while new scalar loads/stores are `258/256`, including outer loads. IR and execution counts support the reduced overhead, but the result remains far slower than historical AscendC/PTO contiguous copies at roughly 2140 cycles.
- **The three reductions are still not vector reductions.** New kernels retain scalar accumulation loops, with all three vector execute/load/store categories zero. Correctness does not establish SIMD reduction, and this conclusion applies only to these Parallel/serial workloads. Historical AscendC SIMD/PTO SIMD device-compilation failures and PTO SIMT's required missing helpers remain historical failures; they were not rerun or removed here.
- **Memory-scalar addition and row broadcast were already fused previously.** New kernels retain register broadcast/addition, with vector categories unchanged at `5/5/5` and total instructions `153→146`. They are not newly eliminated full broadcast temporaries. Copy continues to connect GM→UB→GM directly with zero vector instructions and total instructions `70→65`.
- **Lower fill cycles do not prove new vectorization.** Cycles change `1871→1483/1471`, instructions `80→75`, but vector categories remain `2/0/5`; the `fill_256` vector body is identical after excluding function headers and indentation. Constant addition also retains categories `5/4/5`. ABI/FFTS, outer scalar instructions, compilation flags, and launch API changed together. Without controlled experiments and the old complete timeline, the entire fill cycle reduction cannot be assigned to one cause.

[comparison.json](npuir-main-013dbbf5/comparison.json) contains old/new per-case Profiling, static IR features, and deltas. New `instruction-events.json` files summarize actual CAModel PC instruction events (X/i phases, excluding dependency arrows and counters). All 14 counts match Profiling and contain no duplicate instruction IDs. These are executed device instructions, not IR lines; category counts do not form a complete partition of the total.

### Evidence and limits

[Compact current evidence](npuir-main-013dbbf5/results/) includes workloads, input/vectorized TIR, pass lists, initial/optimized MLIR, ELFs, ABI signatures/argument sections, compiler commands, correctness/canary markers, Profiling, and SHA256 values. [preflight.json](npuir-main-013dbbf5/preflight.json) records recovery/build/final status; `not_run` in immutable `inputs.json` describes input preparation, not the final execution status. Full pass dumps, SDKs, virtual environments, and large traces remain local.

The snapshot was not a complete migration: remote baseline was `06d764af`, local snapshot only `840972e`, and full historical traces were absent. Scripts/environments were restored, 658 historical compact evidence hashes checked, and identical inputs prepared. Separate diagnostics include old-frontend copy recovery `2172/70`, old-ELF V2 launch `2154/70`, and new-copy ABI smoke `2155/65`. **None counts toward the 14 formal entries**; see [probes](npuir-main-013dbbf5/probes/). The same old ELF shows small cycle variation, so differences of a few dozen cycles do not justify backend rankings.

No physical NPU was available. Actual A5 driver/runtime/launch behavior and a full installation on a blank machine remain unverified. The runner covers only these verified single-block FP32 kernels, not general multi-block, workspace, or cross-core synchronization cases.

## Historical baseline (2026-10-04)

Single block, FP32. A has a logical size of 256 elements (fill does not read A); the output contains 256, 1, 4, or 64 elements depending on the scenario. Numbers are CAModel **cycles / executed instruction count**, not physical NPU performance.
† denotes reuse across combinations of a validated simulation with identical ELF, ABI, symbol, fixture, and runner hashes. It does not denote another independent execution.

| Scenario | CPU | AscendC SIMT | AscendC SIMD | PTO SIMT | PTO SIMD | NPU-IR automatic vectorization path |
|---|---|---|---|---|---|---|
| scalar_const_256 | passed | 2648/124 | 2137/98 | 2618/144 | 2111/93 | 2229/106 |
| scalar_const_4x64 | passed | 2606/124 | 2128/98 | 2618/144 † | 2111/93 † | 2238/106 |
| scalar_buffer_256 | passed | 2627/139 | 2119/103 | 2597/159 | 2135/100 | 2767/153 |
| scalar_buffer_4x64 | passed | 2628/139 | 2131/103 | 2597/159 † | 2135/100 † | 2767/153 † |
| copy_256 | passed | 2627/116 | 2138/91 | 2599/136 | 2135/83 | 2149/70 |
| copy_4x64 | passed | 2627/116 | 2143/91 | 2599/136 † | 2135/83 † | 2149/70 † |
| fill_256 | passed | 1634/110 | 1430/83 | 1650/114 | 1432/76 | 1871/80 |
| fill_4x64 | passed | 1634/110 | 1420/83 | 1650/114 † | 1432/76 † | 1871/80 † |
| broadcast_row | passed | 2655/155 | 2152/103 | 2632/171 | 2146/100 | 2781/153 |
| broadcast_column | passed | 2641/147 | 2145/107 | 2612/167 | 2164/101 | 2879/199 |
| flatten | passed | 2647/116 | 2149/91 | 2599/136 † | 2135/83 † | 14012/11851 |
| reduce_all_256 | passed | 19235/2175 | failed (device_compile) | failed (device_compile) | failed (device_compile) | 7217/2131 |
| reduce_rows | passed | 6802/641 | failed (device_compile) | failed (device_compile) | failed (device_compile) | 7518/2145 |
| reduce_columns | passed | 2458/172 | failed (device_compile) | failed (device_compile) | failed (device_compile) | 6966/1559 |

Status totals: `{'passed': 75, 'failed': 9}`. Device combinations passed: 61/70, referencing 48 distinct successful simulation archives. The total of 75 passes includes 14 CPU cases.

Source programs, IR, and failure logs for each combination are under [ir/](ir/). [metrics.json](metrics.json) records failure stages, diagnostics, validation markers, hashes, and relative simulation report paths. Full ELFs, traces, and HTML reports remain in the working environment.
A complete installation on a clean machine has not been validated. The compiler was not modified, and failed combinations are not treated as usable backends.

## Interpreting the SIMD results

The conclusions below use the existing IR and Profiling archives in the matrix; they introduce no new simulation or hardware measurements. AscendC/PTO use the main frontend at `994b44ec`; NPU-IR uses wheel `0.1.1.030+4e1bb3e4…`. These are different frontend versions, so differences cannot all be attributed to IR design.

- **AscendC SIMD and PTO SIMD have similar vector bodies.** Contiguous addition, broadcasting, copy, and fill process four batches of 64 FP32 elements.
- **NPU-IR optimization depends on the scenario.** Copy eliminates the intermediate UB vector copy; memory-scalar addition and row broadcasting reuse vector registers after optimization; column broadcasting retains an intermediate buffer; flatten retains a per-element copy loop.
- **“Automatic vectorization path” names a compilation path.** The three NPU-IR reductions ultimately execute scalar accumulation, so their measurements are not SIMD reduction performance.
- **Interpret cycles and instruction counts separately.** The instruction count is the simulator's dynamic device instruction total, including control, transfer, scalar, and vector instructions. It is neither the IR line count nor the number of additions. Pipeline overlap, dependencies, and synchronization prevent cycles from scaling directly with instruction count.

The constant, memory-scalar, copy, and fill examples below use the `(256,)` variants. GM is device global memory; UB is the on-chip Unified Buffer. MTE2/MTE3 perform the input/output transfers here.

### AscendC and PTO: similar vector bodies

For constant addition, the [AscendC code](ir/scalar_const_256/ascendc_simd/kernel.asc) uses `vlds_norm → vdup → vadd → vsts_norm` in a four-iteration loop. The [PTO IR](ir/scalar_const_256/pto_simd/kernel.pto) uses `pto.vlds → pto.vdup → pto.vadd → pto.vsts`, with register type `!pto.vreg<64xf32>`. The [PTO LLVM](ir/scalar_const_256/pto_simd/kernel.ll) has already moved the constant broadcast outside the loop.

Both follow `GM → UB → vector computation → UB → GM`, with synchronization between transfers and computation. The results `2137/98` and `2111/93` reflect code-generation differences for similar device algorithms; they do not establish stronger SIMD compute capability for either backend.

In the constant-addition profiles for [AscendC](ir/scalar_const_256/ascendc_simd/profile.json) and [PTO](ir/scalar_const_256/pto_simd/profile.json), MTE2 utilization is about 60%, while SIMD utilization is only about 1.3%–1.4%. This case has just 1 KiB of input: vector computation is short, and transfer, control, and synchronization overheads occupy substantial time. Utilization does not establish saturated memory bandwidth. Pipelines can overlap, so their percentages cannot be added as an execution-time breakdown.

### Constants, memory scalars, and row broadcasting

NPU-IR lowers constant addition from `hivm.hir.vadd(tensor, scalar)` to a 64-element `vadds.s.x`: vectorization succeeds. Its `2229/106` is slightly higher than AscendC/PTO, but this does not mean the addition body itself is more complex. See the [optimized IR](ir/scalar_const_256/npuir_auto_simd/temps/module.hivm.opt.mlir).

A memory scalar `B[0]` requires an additional GM→UB load. NPU-IR initially has `tensor.extract → vbrc → vadd`, but the [optimized IR](ir/scalar_buffer_256/npuir_auto_simd/temps/module.hivm.opt.mlir) places the broadcast load and addition in the same vector function, without retaining a full 256-element broadcast buffer. [Row broadcasting](ir/broadcast_row/npuir_auto_simd/temps/module.hivm.opt.mlir) similarly obtains 64 elements of B and reuses them across four rows.

The following memory-scalar instruction categories come from the [AscendC](ir/scalar_buffer_256/ascendc_simd/profile.json), [PTO](ir/scalar_buffer_256/pto_simd/profile.json), and [NPU-IR](ir/scalar_buffer_256/npuir_auto_simd/profile.json) profiles:

| Metric | AscendC SIMD | PTO SIMD | NPU-IR |
|---|---:|---:|---:|
| Cycles / total instructions | 2119 / 103 | 2135 / 100 | 2767 / 153 |
| Scalar instructions | 68 | 69 | 110 |
| Vector execution class `RVECEX_count` | 5 | 5 | 5 |
| Vector load class `RVECLD_count` | 5 | 5 | 5 |
| Vector store class `RVECST_count` | 5 | 5 | 5 |

The vector category counts match; most additional instructions are outside the vector body. NPU-IR's optimized IR retains generic transfer-helper calls and parameter handling. This supports investigating transfer and control overhead, but aggregate data cannot assign the roughly 30% cycle increase to a particular call, nor justify claiming that broadcasting was not fused. These categories are not a complete partition of total instructions, and the vector execution count is not the number of `vadd` operations.

### Column broadcasting: NPU-IR retains an extra buffer

Column broadcasting computes `O[i,j] = A[i,j] + B[i,0]`. AscendC's [`vlds_brc_elem`](ir/broadcast_column/ascendc_simd/kernel.asc) and [PTO's broadcast load](ir/broadcast_column/pto_simd/kernel.ll) obtain a scalar for each row, broadcast it in a register, and add it directly.

The NPU-IR [optimized IR](ir/broadcast_column/npuir_auto_simd/temps/module.hivm.opt.mlir) retains:

```text
Load 4 B elements → UB-to-UB copy
                  → vector function 0: expand into a 4×64 broadcast buffer
                  → vector function 1: read A and the broadcast buffer, then add
```

This adds a 1 KiB intermediate result and its writes and reads. Vector load/store counts are `8/5` for AscendC/PTO and `13/12` in the [NPU-IR profile](ir/broadcast_column/npuir_auto_simd/profile.json). Thus `2879/199`, compared with `2145/107` and `2164/101`, has a clear structural explanation: this column broadcast has not been fused into a direct broadcast-load-and-add operation. The source B still contains only four elements; the input was not expanded in advance to bypass broadcasting.

### Copy and fill: fewer instructions do not guarantee fewer cycles

AscendC/PTO copy still performs vector loads/stores between UB input and output regions. The NPU-IR [copy IR](ir/copy_256/npuir_auto_simd/temps/module.hivm.opt.mlir) reuses the same UB buffer between `GM→UB` and `UB→GM`, synchronizing MTE2 with MTE3. Its [vector execution, load, and store counts are all zero](ir/copy_256/npuir_auto_simd/profile.json). Total instructions fall from 91 for AscendC and 83 for PTO to 70: this is a successful optimization. GM read/write volume is unchanged, however, and cycles remain around 2140.

Fill does not read A; it generates constants and writes them back. All three paths have vector execution/load/store counts of `2/0/5`, but NPU-IR reports `1871/80`, AscendC `1430/83`, and PTO `1432/76`. NPU-IR executes fewer instructions than AscendC yet takes more cycles, so instruction count alone cannot explain the timing difference. Its [IR](ir/fill_256/npuir_auto_simd/temps/module.hivm.opt.mlir) retains a store helper and a final barrier. An instruction timeline is needed to attribute the difference to latency, dependencies, synchronization, or scheduling; the existing aggregate data cannot assign all extra cycles to any one operation.

### Flatten: a contiguous copy was not recognized

The source explicitly computes `O[k] = A[k // 64, k % 64]`. A is contiguous, so the linear address simplifies to `(k // 64) * 64 + k % 64 = k`.

AscendC generates identical `kernel.asc` files for flatten and copy. PTO generates identical `kernel.ll` files, and the ELFs are also identical within each corresponding mode. Both therefore remain around 2140 cycles.

NPU-IR's [high-level IR](ir/flatten/npuir_auto_simd/kernel.mlir) retains a 256-iteration loop and single-element slice operations. Its [optimized IR](ir/flatten/npuir_auto_simd/temps/module.hivm.opt.mlir) still constructs single-element views and calls `copy_ubuf_to_ubuf_1d_float` inside the loop. Compared with NPU-IR's own copy:

| Metric | Copy | Flatten | Comparison |
|---|---:|---:|---|
| Cycles | 2149 | 14012 | About 6.52× |
| Total instructions | 70 | 11851 | 169.3× |
| Vector loads / stores | 0 / 0 | 512 / 1024 | Many small copies |

The contiguous-copy semantics were not recognized, leaving a per-element transfer structure. High-level `div/rem` alone does not prove that expensive integer division survives in the final instructions: later LLVM optimization may still simplify address arithmetic. This flatten performs actual data movement; it is not a zero-copy view transformation.

### Reductions: successful execution does not imply vectorization

The three reductions use `T.Parallel` on output axes and `T.serial` on reduction axes: a sum over 256 elements, four row sums of 64 elements each, and 64 column sums of four elements each. There are no concurrent writes to the same output. Explicit `T.reduce_sum` was not tested.

AscendC retains scalar loads, additions, and stores inside `__simd_vf__`; PTO retains `pto.load/addf/store` inside `pto.vecscope`. The current compiler rejects this scalar accumulation inside a SIMD region with `Unsupported scalar instruction in AIV loop`. See the row-reduction [AscendC code](ir/reduce_rows/ascendc_simd/kernel.asc), [PTO IR](ir/reduce_rows/pto_simd/kernel.pto), and [compiler diagnostics](ir/reduce_rows/pto_simd/device-compile.log). This is a lowering limitation of the current source pattern and versions, not evidence that the backend or ISA cannot support reductions.

NPU-IR executes successfully, but its [optimized row reduction](ir/reduce_rows/npuir_auto_simd/temps/module.hivm.opt.mlir) remains a scalar loop using `memref.load → llvm.fadd f32 → memref.store`. All three reductions have zero `RVECEX_count`, `RVECLD_count`, and `RVECST_count`, with scalar pipeline utilization around 78%–85%. Consequently, `7217/2131`, `7518/2145`, and `6966/1559` are simulated scalar-reduction results. The `hivm.vf_mode=SIMD` attribute is not evidence of vector reduction.

PTO SIMT failures in the matrix have a different cause: generated code actually uses `tl.as_logical_bool`, triggering an incompatible private helper import, `ModuleNotFoundError: ptodsl._allreduce`. See the [compatibility diagnostic](compatibility/pto-helper-import.txt). Not all reduction failures are the same SIMD compilation error.

### Comparison limits and next steps

Both `(256,)` and `(4,64)` describe 256 contiguous elements; several scenarios generate identical or equivalent device code. A `†` references the same validated simulation, not an independent repetition. Such rows cannot establish repeated-run means or variance, and differences of a few dozen cycles do not rank backend performance.

Every passing device combination passed elementwise exact comparison after NaN output initialization and checks on 64 trailing FP32 canaries. Failed combinations have no comparable simulated performance. The runner covers only these single-block cases; cross-core synchronization and physical A5 execution have not been validated.

The clearest optimization targets are NPU-IR contiguous-copy recognition for flatten, column-broadcast fusion, and nested Parallel/serial reduction handling across the three paths. These improvements have not been implemented. Broader performance evaluation requires aligned frontend versions, larger inputs, and repeated measurements. See the [scenario guide](../../setup/scenarios/README.md), [additional lowering observations](ANALYSIS.md), and [validation scope](../../VALIDATION.md) for reproduction details and further context.
