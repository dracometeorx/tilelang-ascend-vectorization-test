# NPU-IR lowering 测试：T.Parallel 向量化支持矩阵

本分支（`npuir-lowering-test`）是从空目录新建的孤立分支，与 `main` 无共同历史，专做一件事：**把 `T.Parallel` 的各类工作负载过一遍 `NpuLoopVectorize`，保存各阶段 IR，并判定每个用例是整体向量化、部分向量化还是回退标量。**

对象：`tile-ai/tilelang-mlir-ascend`，分析所依据的提交为 `417dae9908ad2ea5ffb74294a7075b6cb64b4f2b`。

> **当前状态：代码只做过语法检查、用例表自洽性检查，以及报告生成的冒烟测试，没有在装有 TileLang 的机器上执行过。**所有"预期结果"都来自静态源码阅读的推导。第一次真跑出来如果和预期不符，可能是推导错了，也可能是实现有问题——两种都要记录下来，不要默认哪一边对。

## 为什么需要这个

现有测试（`testing/npuir/`）只做 `assert_close` 比对数值。问题是**标量回退在数值上同样正确**：如果某个 `T.Parallel` 悄悄退回了标量循环，测试照样通过。

所以今天无法回答"这个写法到底有没有被向量化"。本分支的脚本不看数值，只看 IR 的结构事实：parallel 循环还在不在、region 的长度和 offset 是多少、生成了哪些区域级算子。

## 用法

需要一台装好 TileLang（`USE_NPUIR=ON`）的机器，`PYTHONPATH` 里要有仓库根目录与 bishengir 的 `python_packages`（`install_npuir.sh` 会写进 `~/.bashrc`）。

```bash
source ~/.bashrc
source /usr/local/Ascend/ascend-toolkit/set_env.sh

python3 run_matrix.py --out-dir ./artifacts/$(date +%Y%m%d-%H%M)
```

常用变体：

```bash
# 单个用例 + 打印变换后 TIR
python3 run_matrix.py --out-dir /tmp/one --only binary_add --verbose

# 只跑对齐/尾部那一组
python3 run_matrix.py --out-dir /tmp/pad --only \
  nondivisible_1d unaligned_offset tiny_inner_dim \
  broadcast_nonaligned_inner offset_plus_broadcast \
  pad_then_parallel full_block_partial_copy

# 额外走完整 lower 保存 codegen 出的 MLIR（需要 codegen 跑得通）
python3 run_matrix.py --out-dir ./artifacts/with-mlir --mlir

# Expert 模式（默认 Developer）
python3 run_matrix.py --out-dir ./artifacts/expert --mode Expert
```

全部与预期一致退出码 0，否则 1，可以直接接 CI。

**每个用例在独立子进程里跑。** `reduction_plus_equal` 预期会触发 C++ 的 `ICHECK`，那会让整个进程 abort，Python 的 `try/except` 拦不住。隔离之后一个用例炸掉不影响其余 31 个，abort 的 stderr 也能完整留下。

## 用例

`cases.py`，32 个，按预期结果分五组：

| 组 | 数量 | 内容 |
|---|---|---|
| A. 预期整体向量化 | 16 | 逐元素（6 种二元）、一元数学（6 种）、cast、向量+标量、单轴/双轴广播、拷贝、填充、循环变量参与、条件选择、复合表达式、偏移读取、二维 |
| B. 预期部分向量化 | 2 | 间接行读取、动态外层 + 静态内层 |
| C. 预期回退标量 | 6 | 动态 extent、多语句体、变换写入下标、转置读、flatten、变量填充 |
| D. 预期编译失败 | 1 | 归约 `a[i] += b[i,j]` |
| E. 对齐、尾部与 padding | 7 | 非整除长度、非对齐 offset、极小尾轴、广播+非对齐内轴、**offset+broadcast**、`T.pad` 组合、满块计算+尾块拷贝 |

A–D 组的形状全是 8 的倍数（FP32 下 32 字节对齐），**刻意回避了对齐问题**；E 组专门不对齐。

用例统一使用 `T.alloc_ub`（TIR scope = `shared` = UB），避开 `alloc_shared` 默认 `shared.dyn` 带来的歧义——那个 scope 在 Developer 模式下是普通 tensor，在 Expert 模式下却是 L1。

## 产物

```
<out-dir>/
├── matrix.md                      # 人读的支持矩阵 + region 明细 + 待人工确认项
├── matrix.json                    # 机读，便于跨版本 diff
└── <用例名>/
    ├── 00-frontend.tir            # TVMScript 解析后的原始 TIR
    ├── 01-before-vectorize.tir    # LowerAndLegalize 之后、向量化之前
    ├── 02-after-vectorize.tir     # NpuLoopVectorize 之后  ← 主要看这个
    ├── 03-codegen.mlir            # 仅 --mlir
    ├── verdict.json               # 结构事实、判定、regions（offset + 长度）
    ├── stdout.txt
    └── stderr.txt                 # ICHECK / abort 落在这里
```

`00` 和 `01` 的差别值得看一眼：npuir 路径的 `LowerAndLegalize` 只做 `BindTarget → Simplify → RemoveNoOp` 就返回，而 `Simplify` 会内联纯整数的 `let`。所以源码里写的 `bid = cid // M` 到 `01` 阶段已经变成下标里的表达式了。

## 判定规则

| 判定 | 条件 |
|---|---|
| `full` | 无 parallel 循环残留，且有向量算子 |
| `partial` | 有 parallel 循环残留，且有 region 长度 > 1 的向量算子 |
| `unmerged` | 有向量算子但所有 region 长度 ≤ 1 |
| `scalar` | 没有任何向量算子 |
| `error` | 子进程非零退出（含 ICHECK abort） |
| `timeout` | 超时，默认 600s |

`unmerged` 是专门设的一类：拆解成功但合并失败，残留单元素区域调用套在循环里。这种形态在 codegen 里可能被误降低，`src/transform/npu_loop_vectorize.cc:1110-1117` 的注释本身就在描述这个风险。**凡是判成 `unmerged` 的都要追查。**

## 怎么读 `02-after-vectorize.tir`

```python
# full：循环消失，只剩一条区域级操作
T.npuir_add(T.region(a[0], 1, 256), T.region(b[0], 1, 256), T.region(c[0], 2, 256))

# partial：外层保留，内层变成整行
for i in T.Parallel(32):
    T.copy(T.region(tab[idx[i], 0], 1, 1, 64), T.region(c[i, 0], 2, 1, 64))

# scalar：没有任何 tl.npuir_* / tl.copy
for i in T.Parallel(256):
    c[i] = a[i] + T.float32(1)
```

`T.region(buf[offset...], access, size...)` 里 `access` 是 1（读）/ 2（写），**后面的才是各维长度**，不是结束下标。

## 关于 padding 和对齐

**`NpuLoopVectorize` 本身不生成 padding，也不生成 mask。**它把循环次数直接当作 region 长度，不按硬件宽度向上取整。所以 E 组要看的不是"有没有补齐"，而是：

| 看什么 | 期望 |
|---|---|
| region 长度是逻辑长度还是被补过 | `nondivisible_1d` 应为 250，不是 256 |
| offset 有没有被保留 | `unaligned_offset` 应为 3 |
| **offset + broadcast 是否丢常数项** | **应为 1；若为 0，则复现了疑点** |
| 外提的临时 buffer 多大 | `broadcast_nonaligned_inner` 看是 250 还是 256 |

`matrix.md` 会自动把所有 region 的 offset 与长度摊平成一张表，不用逐个翻 TIR。

三件事这套脚本**测不出来**：

1. **后端的存储对齐填充**（32 字节尾轴对齐）发生在 bishengir 里，TIR 层看不见。`tiny_inner_dim` 在这一层只会显示 `[32, 3]`。
2. **未初始化尾部元素参与计算**是语义问题而非结构问题。`full_block_partial_copy` 结构上会判 `full`；要真正触发，得运行时传 `shape < 256`，再检查输出有效段与 NaN 传播。
3. **执行 mask** 在 SIMD 路径上不存在，所以没有对应用例。唯一识别尾部条件的是 A5 SIMT 路径（`NpuSimtIndirectLoad`），那是另一条链路，其 mask 操作数来自 Triton `tl.load(ptrs, mask, other)` 的 ABI。

## 第一次跑的时候，重点看这几条

| 用例 | 预期 | 不一致说明什么 |
|---|---|---|
| `dynamic_extent_1d` | `scalar` | 如果居然向量化了，说明"动态 extent 不进入匹配"的判断有误 |
| `reduction_plus_equal` | `error` | 如果"成功"了，立刻检查数值——归约可能被静默当成逐元素运算 |
| `offset_plus_broadcast` | `full` | 结构必然是 full，**要看 `w` 的源 region offset 是 1 还是 0** |
| `broadcast_two_axes` | `full` | 看外提了几个、多大的临时 buffer。这是后续优化的收益基数 |
| 任何用例 | — | 判成 `unmerged` 的都要追查 |

`matrix.md` 的"需要人工确认"一节会自动列出 verdict 判定不了的检查点，由 `cases.py` 里的 `NOTES` 驱动。

## 和 `main` 的关系

`main` 是在无 NPU 的 x86_64 机器上，用厂商 CAModel 对比 AscendC / PTO / NPU-IR 三条 lowering 路径的实验台，关注的是数值校验与模拟 Profiling。

本分支不依赖 CAModel，也不跑 kernel，只检查 TIR→region 这一段变换的结构。两者互补：本分支回答"有没有向量化、向量化成什么样"，`main` 回答"跑出来对不对、快不快"。因为关注点和依赖完全不同，故开为孤立分支而非从 `main` 分出。
