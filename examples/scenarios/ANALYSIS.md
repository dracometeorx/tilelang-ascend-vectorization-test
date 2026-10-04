# Parallel lowering 观察

本轮固定主前端 `994b44ec` 和 NPU-IR wheel `0.1.1.030+4e1bb3e4…`，使用相同数学输入，但两个前端版本不同。以下是产物证据，不是对 IR 设计或真实硬件性能的普遍结论。完整状态以 [实测矩阵](README.md) 为准。

## 标量与广播

常量 `1.25` 和内存标量 `B[0]` 分开测试，后者需要 GM→UB 加载。AscendC SIMD 使用向量加法和 scalar/broadcast load；NPU-IR 常量路径是 `hivm.hir.vadd(tensor, scalar)`，内存标量经加载、提取、广播后相加。

行广播复用 64 个元素的一行，列广播从 4 个行标量中为每行选一个。AscendC SIMD 列广播明确生成 `vlds_brc_elem`，而行广播是普通 `vlds_norm`；两者都与 `vadd` 配合。NPU-IR 明确生成 `hivm.hir.vbrc` 和 `hivm.hir.vadd`。小输入形状 `(1,)`、`(4,1)` 按真实大小分配，没有偷偷扩展为 256 元素的预广播输入。

## copy、fill 与 flatten

copy 的计算体是 Parallel 逐元素赋值；fill 的计算体是 Parallel 常量赋值。NPU-IR 可以消去 copy 的元素循环，fill 表现为常量广播。AscendC/PTO 的未使用 A/B 参数会被移除，fill 仅剩输出指针；runner 按实际签名传参，不能套用旧三指针加法 ABI。

flatten 明确写成 `O[k] = A[k // 64, k % 64]`，具有实际数据移动。主前端能把连续地址中的除法/取模消去；PTO flatten 的 SIMT/SIMD ELF 分别与同模式 copy 完全一致。NPU-IR 此版本的高层产物仍保留 `scf.for`、`tensor.extract` 和 `tensor.insert`，后端产物可见循环中的 `copy_ubuf_to_ubuf_1d_float`。因此不能把这条路径标注为已折叠成一次连续向量拷贝。本次 NPU-IR flatten 模拟为 14,012 周期、11,851 条指令；copy 为 2,149 周期、70 条指令。两者数值及保护区均通过，这个差异应结合循环 IR 解读，不能当作真实 NPU 测速。

## reduction 的边界

归约测试输出轴 `T.Parallel` + 归约轴 `T.serial`，分别做 256 元素全量和、4 行各 64 元素和、64 列各 4 元素和。它没有并行写相同输出的竞态；输入和所有部分和都是可精确表示的小范围二进制分数。

- AscendC SIMT 的三种归约均通过编译、精确数值和输出保护区校验。
- AscendC SIMD 和 PTO SIMD 的嵌套累加未变成向量归约，Bisheng 拒绝 VF 内的 scalar 指令，诊断为 `Unsupported scalar instruction in AIV loop`。
- PTO SIMT 生成谓词 `tl.as_logical_bool`，实际依赖当前不兼容的私有 helper。AST 检查发现实际使用后保留原 import，真实导入报 `ModuleNotFoundError: ptodsl._allreduce`；这属于当前前端/PTOAS 组合的兼容边界，不能解释成 PTO ISA 不支持求和。
- NPU-IR 的三种归约也均通过编译、精确数值和输出保护区校验，但高层 IR 保留 `scf.for` 和 tensor extract/insert，没有生成 `hivm.hir.vreduce`。`hivm.vf_mode=SIMD` 属性不能作为整个求和已向量化的证据。

本轮未替换为 `T.reduce_sum`，未调整 SIMT 线程数（固定 128），未展开或重写归约算法，也未修改编译器。因此结果只回答“同一嵌套 Parallel/serial 写法在这些固定路径上发生什么”，不代表各后端最佳归约实现。

## 证据与计时

CPU 逐元素参考校验、设备编译、CAModel 数值校验、Profiling 分阶段记录。模拟输出先填 NaN，末尾保护区也必须保持不变。唯一内核报告、正周期和指令数、HTML 与正确性标记缺一不可。

相同 ELF、ABI、符号、fixture 和 runner 才允许复用一次模拟，表中以 † 表示。未做多次运行统计，几十周期的小差异不能排序真实硬件性能。失败组合无模拟性能数字。
