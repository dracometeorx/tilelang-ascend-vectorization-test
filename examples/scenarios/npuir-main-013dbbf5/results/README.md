# Parallel 场景实测矩阵

单 block、FP32；A 的逻辑规模为 256 个元素（fill 不读取 A），输出按场景为 256、1、4 或 64 个元素。数字为 CAModel **周期/执行指令数**，不是物理 NPU 性能。
† 表示跨组合复用 ELF、ABI、符号、fixture 和 runner 哈希均一致的已验证模拟；不代表独立再次执行。

| 场景 | NPU-IR 自动向量化路径 |
|---|---|
| scalar_const_256 | 2213/101 |
| scalar_const_4x64 | 2186/101 |
| scalar_buffer_256 | 2774/146 |
| scalar_buffer_4x64 | 2774/146 |
| copy_256 | 2117/65 |
| copy_4x64 | 2143/65 |
| fill_256 | 1483/75 |
| fill_4x64 | 1471/75 |
| broadcast_row | 2722/146 |
| broadcast_column | 2739/148 |
| flatten | 7280/1870 |
| reduce_all_256 | 7216/2126 |
| reduce_rows | 7208/2140 |
| reduce_columns | 6945/1554 |

状态统计：`{'passed': 14}`；设备通过 14/14 个组合，引用 14 份不同的成功模拟归档。

每个组合的源程序、IR 和失败日志见 `ir/`；`metrics.json` 保存失败阶段、完整诊断、校验标记、哈希和模拟报告的相对路径。完整 ELF/轨迹/HTML 留在工作目录。
未重新验证空白机器安装；未修改编译器，不将未通过的组合视为可用后端。
