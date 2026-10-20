"""T.Parallel 向量化工作负载用例表。

每个用例返回一个 T.prim_func，连同它的类别和**预期结果**。预期来自
output/analysis/tilelang-mlir-ascend-main-SIMD向量化问答.md 的 Q3 静态推导，
**尚未在真机验证**——跑出来和预期不符，可能是预期错了，也可能是实现有问题，
两种都要记录。

预期取值：
  full     整条语句被向量化，parallel 循环消失
  partial  外层循环保留，内层成为区域级操作
  scalar   回退为标量循环，不产生向量操作
  unmerged 产生了向量操作但 region 长度仍为 1（危险：Q3 §4 / Q6 §4）
  mixed    同一残留循环里既有标量 store 又有向量算子
  error    预期在编译期失败（本阶段只跑 NpuLoopVectorize，codegen 错误需 --mlir）

用例只用 alloc_ub（scope=shared=UB），避免 Q4/Q5 里 alloc_shared 的
scope 歧义干扰判定。
"""

import tilelang.language as T

N = 256
M = 32
K = 64
F32 = "float32"


# --------------------------------------------------------------------------
# A. 预期整体向量化
# --------------------------------------------------------------------------


def binary_add():
    @T.prim_func
    def f(A: T.Tensor((N,), F32), B: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i in T.Parallel(N):
                c[i] = a[i] + b[i]
            T.copy(c, C)

    return f


def binary_all_ops():
    """一次覆盖 + - * / min max 六种二元运算（各自独立 Parallel）。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), B: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i in T.Parallel(N):
                c[i] = a[i] + b[i]
            for i in T.Parallel(N):
                c[i] = a[i] - b[i]
            for i in T.Parallel(N):
                c[i] = a[i] * b[i]
            for i in T.Parallel(N):
                c[i] = a[i] / b[i]
            for i in T.Parallel(N):
                c[i] = T.min(a[i], b[i])
            for i in T.Parallel(N):
                c[i] = T.max(a[i], b[i])
            T.copy(c, C)

    return f


def unary_math():
    """exp / log / sqrt / rsqrt / fabs / sigmoid。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = T.exp(a[i])
            for i in T.Parallel(N):
                c[i] = T.log(a[i])
            for i in T.Parallel(N):
                c[i] = T.sqrt(a[i])
            for i in T.Parallel(N):
                c[i] = T.rsqrt(a[i])
            for i in T.Parallel(N):
                c[i] = T.fabs(a[i])
            for i in T.Parallel(N):
                c[i] = T.sigmoid(a[i])
            T.copy(c, C)

    return f


def cast_f32_to_f16():
    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), "float16")):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), "float16")
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = T.cast(a[i], "float16")
            T.copy(c, C)

    return f


def vector_scalar_imm():
    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = a[i] * T.float32(2.0) + T.float32(1.0)
            T.copy(c, C)

    return f


def vector_scalar_load():
    """循环不变的 buffer 读取作为标量操作数。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = a[i] + a[0]
            T.copy(c, C)

    return f


def scalar_on_left_sub():
    """非交换算子的左标量：按 Q3 应先 brc 成临时 buffer。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = T.float32(1.0) - a[i]
            T.copy(c, C)

    return f


def broadcast_one_axis():
    @T.prim_func
    def f(A: T.Tensor((M, K), F32), W: T.Tensor((K,), F32), C: T.Tensor((M, K), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((M, K), F32), T.alloc_ub((M, K), F32)
            w = T.alloc_ub((K,), F32)
            T.copy(A, a)
            T.copy(W, w)
            for i, j in T.Parallel(M, K):
                c[i, j] = a[i, j] + w[j]
            T.copy(c, C)

    return f


def broadcast_two_axes():
    """维度错位：预期生成两个完整 [M,K] 临时 buffer（Q3 §6 第 4 条）。"""

    @T.prim_func
    def f(U: T.Tensor((M,), F32), V: T.Tensor((K,), F32), C: T.Tensor((M, K), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            u, v = T.alloc_ub((M,), F32), T.alloc_ub((K,), F32)
            c = T.alloc_ub((M, K), F32)
            T.copy(U, u)
            T.copy(V, v)
            for i, j in T.Parallel(M, K):
                c[i, j] = u[i] + v[j]
            T.copy(c, C)

    return f


def pure_copy():
    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = a[i]
            T.copy(c, C)

    return f


def const_fill():
    @T.prim_func
    def f(C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            c = T.alloc_ub((N,), F32)
            for i in T.Parallel(N):
                c[i] = T.float32(0.0)
            T.copy(c, C)

    return f


def loop_var_in_value():
    """循环变量参与计算，预期经 npuir_arange 物化。"""

    @T.prim_func
    def f(C: T.Tensor((M, K), "int32")):
        with T.Kernel(1, is_npu=True) as (cid, _):
            c = T.alloc_ub((M, K), "int32")
            for i, j in T.Parallel(M, K):
                c[i, j] = T.max(i, j)
            T.copy(c, C)

    return f


def if_then_else_select():
    @T.prim_func
    def f(A: T.Tensor((N,), F32), B: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i in T.Parallel(N):
                c[i] = T.if_then_else(a[i] > b[i], a[i], b[i])
            T.copy(c, C)

    return f


def compound_expr():
    @T.prim_func
    def f(A: T.Tensor((N,), F32), B: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i in T.Parallel(N):
                c[i] = T.exp(a[i] * b[i] + a[i] * b[0])
            T.copy(c, C)

    return f


def offset_read():
    """b[i] = a[off + i]，off 为循环不变量。"""

    @T.prim_func
    def f(A: T.Tensor((2 * N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((2 * N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = a[i + 8]
            T.copy(c, C)

    return f


def elementwise_2d():
    @T.prim_func
    def f(A: T.Tensor((M, K), F32), B: T.Tensor((M, K), F32), C: T.Tensor((M, K), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((M, K), F32)
            b = T.alloc_ub((M, K), F32)
            c = T.alloc_ub((M, K), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i, j in T.Parallel(M, K):
                c[i, j] = a[i, j] + b[i, j]
            T.copy(c, C)

    return f


# --------------------------------------------------------------------------
# B. 预期部分向量化
# --------------------------------------------------------------------------


def indirect_row_copy():
    """纯拷贝形式的间接行读取：外层保留，内层成行拷贝。"""

    @T.prim_func
    def f(
        TAB: T.Tensor((M, K), F32),
        IDX: T.Tensor((M,), "int32"),
        C: T.Tensor((M, K), F32),
    ):
        with T.Kernel(1, is_npu=True) as (cid, _):
            tab, c = T.alloc_ub((M, K), F32), T.alloc_ub((M, K), F32)
            idx = T.alloc_ub((M,), "int32")
            T.copy(TAB, tab)
            T.copy(IDX, idx)
            for i, j in T.Parallel(M, K):
                c[i, j] = tab[idx[i], j]
            T.copy(c, C)

    return f


def dynamic_outer_static_inner():
    """外层 extent 动态、内层静态：预期只向量化内层。"""
    @T.prim_func
    def f(A: T.Tensor((M, K), F32), C: T.Tensor((M, K), F32), n: T.int32):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((M, K), F32), T.alloc_ub((M, K), F32)
            T.copy(A, a)
            real = T.min(M, n)
            for i, j in T.Parallel(real, K):
                c[i, j] = a[i, j] * T.float32(2.0)
            T.copy(c, C)

    return f


# --------------------------------------------------------------------------
# C. 预期回退标量
# --------------------------------------------------------------------------


def dynamic_extent_1d():
    """唯一一层循环且 extent 动态：Q3 §1 推导为完全不向量化。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32), n: T.int32):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            real = T.min(N, n)
            for i in T.Parallel(real):
                c[i] = a[i] + T.float32(1.0)
            T.copy(c, C)

    return f


def multi_statement_body():
    """一个 Parallel 里两条赋值：循环体不是单条 BufferStore。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            t = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                t[i] = a[i] + T.float32(1.0)
                c[i] = t[i] * T.float32(2.0)
            T.copy(c, C)

    return f


def store_index_transformed():
    """写入下标做了变换：Q3 §2 的写入下标规则拒绝。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N - 8):
                c[i + 8] = a[i]
            T.copy(c, C)

    return f


def transpose_read():
    """转置读：读取预检拒绝。"""

    @T.prim_func
    def f(A: T.Tensor((M, M), F32), C: T.Tensor((M, M), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((M, M), F32), T.alloc_ub((M, M), F32)
            T.copy(A, a)
            for i, j in T.Parallel(M, M):
                c[i, j] = a[j, i]
            T.copy(c, C)

    return f


def flatten_read():
    """a[i] = b[i//K, i%K]：读取预检拒绝。"""

    @T.prim_func
    def f(A: T.Tensor((M, K), F32), C: T.Tensor((M * K,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((M, K), F32), T.alloc_ub((M * K,), F32)
            T.copy(A, a)
            for i in T.Parallel(M * K):
                c[i] = a[i // K, i % K]
            T.copy(c, C)

    return f


def var_fill():
    """用标量变量填充：Q3 表中列为不支持。"""

    @T.prim_func
    def f(C: T.Tensor((N,), F32), s: T.float32):
        with T.Kernel(1, is_npu=True) as (cid, _):
            c = T.alloc_ub((N,), F32)
            for i in T.Parallel(N):
                c[i] = s
            T.copy(c, C)

    return f


# --------------------------------------------------------------------------
# F. 控制流：T.if_then_else 与 Python if 的区别
#
# NpuLoopVectorize 只匹配表达式级的 tir.if_then_else（-> tl.npuir_select）。
# npuir 路径没有 IfStmtBinding（phase.py 的 124/157 行在其它分支），所以
# Python 的 if 语句不会被改写成 select。
# --------------------------------------------------------------------------


def python_if_in_body():
    """Parallel 体内用 Python if（无 else）：循环体不是单条 BufferStore。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                if a[i] > T.float32(0):
                    c[i] = a[i]
            T.copy(c, C)

    return f


def python_if_else_in_body():
    """同上但带 else。对照 if_then_else_select 的语义差别。"""

    @T.prim_func
    def f(A: T.Tensor((N,), F32), B: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i in T.Parallel(N):
                if a[i] > b[i]:
                    c[i] = a[i]
                else:
                    c[i] = b[i]
            T.copy(c, C)

    return f


def python_if_around_loop():
    """Python if 包住整个 Parallel 循环：条件对循环是 uniform 的。

    这是仓库里的常见写法（test_brc_dev.py、test_arange.py）。预期循环内部
    照常向量化，if 在 codegen 变成 scf.if。条件用运行时标量，避免被
    Simplify 折掉。
    """

    @T.prim_func
    def f(A: T.Tensor((N,), F32), B: T.Tensor((N,), F32), C: T.Tensor((N,), F32), n: T.int32):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            T.copy(B, b)
            if n > 0:
                for i in T.Parallel(N):
                    c[i] = a[i] + b[i]
            T.copy(c, C)

    return f


def ternary_in_body():
    """Python 三元表达式 `x if cond else y`。

    TVMScript 的求值器不特判 IfExp，会交给 Python 的三元运算，于是对
    PrimExpr 调用 bool()。固定版 TVM 的 ExprOp.__nonzero__（tir/expr.py:179）
    会抛 ValueError，**预期解析期就报错**，而不是静默丢掉条件。
    """

    @T.prim_func
    def f(A: T.Tensor((N,), F32), B: T.Tensor((N,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i in T.Parallel(N):
                c[i] = a[i] if a[i] > b[i] else b[i]
            T.copy(c, C)

    return f


# --------------------------------------------------------------------------
# E. 对齐、尾部与 padding
#
# 注意：前面的用例形状全部是 8 的倍数（f32 下 32 字节对齐），刻意回避了
# 对齐问题。这一组专门不对齐。NpuLoopVectorize 本身不生成 padding 也不
# 生成 mask（问答 Q2），所以这里主要看三件事：
#   - region 长度是逻辑长度还是被补齐过
#   - region offset 有没有被保留
#   - 未初始化的尾部元素是否参与了计算
# --------------------------------------------------------------------------

NU = 250  # f32 下 250 % 8 != 0，尾轴非对齐
TINY = 3  # 极小尾轴


def nondivisible_1d():
    """非整除长度的逐元素运算：region 长度应为 250，不应被补到 256。"""

    @T.prim_func
    def f(A: T.Tensor((NU,), F32), B: T.Tensor((NU,), F32), C: T.Tensor((NU,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((NU,), F32)
            b = T.alloc_ub((NU,), F32)
            c = T.alloc_ub((NU,), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i in T.Parallel(NU):
                c[i] = a[i] + b[i]
            T.copy(c, C)

    return f


def unaligned_offset():
    """起始偏移不是对齐边界的倍数：源 region offset 应为 3。"""

    @T.prim_func
    def f(A: T.Tensor((N + 8,), F32), C: T.Tensor((N,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((N + 8,), F32), T.alloc_ub((N,), F32)
            T.copy(A, a)
            for i in T.Parallel(N):
                c[i] = a[i + 3]
            T.copy(c, C)

    return f


def tiny_inner_dim():
    """极小尾轴 [M, 3]：开发指南 §3.1 说后端会自动填充，TIR 层应看不到。"""

    @T.prim_func
    def f(
        A: T.Tensor((M, TINY), F32),
        B: T.Tensor((M, TINY), F32),
        C: T.Tensor((M, TINY), F32),
    ):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((M, TINY), F32)
            b = T.alloc_ub((M, TINY), F32)
            c = T.alloc_ub((M, TINY), F32)
            T.copy(A, a)
            T.copy(B, b)
            for i, j in T.Parallel(M, TINY):
                c[i, j] = a[i, j] + b[i, j]
            T.copy(c, C)

    return f


def broadcast_nonaligned_inner():
    """广播 + 非对齐内轴：看外提的临时 buffer 长度是 250 还是被补齐。"""

    @T.prim_func
    def f(A: T.Tensor((M, NU), F32), W: T.Tensor((NU,), F32), C: T.Tensor((M, NU), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((M, NU), F32), T.alloc_ub((M, NU), F32)
            w = T.alloc_ub((NU,), F32)
            T.copy(A, a)
            T.copy(W, w)
            for i, j in T.Parallel(M, NU):
                c[i, j] = a[i, j] + w[j]
            T.copy(c, C)

    return f


def offset_plus_broadcast():
    """**Q3 §4 的疑点用例。**

    `c[i,j] = a[i,j] + w[j+1]` 会走广播路径（w 缺 i 轴）。按
    EmitReshapeAndBroadcast（npu_loop_vectorize.cc:585-590）的推导，映射到
    循环变量的那一维源 offset 被置 0，于是 `+1` 丢失。

    判定仍会是 full——**要看的是 verdict.json 里 w 那个源 region 的 offset
    是 1 还是 0。是 0 就复现了这个疑点。**
    """

    @T.prim_func
    def f(
        A: T.Tensor((M, K), F32),
        W: T.Tensor((K + 1,), F32),
        C: T.Tensor((M, K), F32),
    ):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a, c = T.alloc_ub((M, K), F32), T.alloc_ub((M, K), F32)
            w = T.alloc_ub((K + 1,), F32)
            T.copy(A, a)
            T.copy(W, w)
            for i, j in T.Parallel(M, K):
                c[i, j] = a[i, j] + w[j + 1]
            T.copy(c, C)

    return f


def pad_then_parallel():
    """显式 T.pad 之后再向量化：验证 Q2 待验证清单第 3 条。

    T.pad 的 pad_value 必须是带类型的常量，写 0.0 会编译失败
    （docs/Tilelang.language/shape操作/T.pad.md §2.3）。
    """

    @T.prim_func
    def f(A: T.Tensor((N,), F32), C: T.Tensor((N + 8,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            padded = T.alloc_ub((N + 8,), F32)
            c = T.alloc_ub((N + 8,), F32)
            T.copy(A, a)
            T.pad(a, padded, T.float32(0), [0], [8])
            for i in T.Parallel(N + 8):
                c[i] = padded[i] * T.float32(2.0)
            T.copy(c, C)

    return f


def full_block_partial_copy():
    """仓库 binary_simple 的形态：只拷贝 tail_size，却按满块计算。

    结构上预期 full。真正要查的是**语义**：未被拷入的那段片上元素未初始化，
    却参与了向量计算。问答 Q2 待验证清单第 1 条。
    运行时传 shape < 256 才会真正触发。
    """

    @T.prim_func
    def f(
        A: T.Tensor((N,), F32),
        B: T.Tensor((N,), F32),
        C: T.Tensor((N,), F32),
        shape: T.int32,
    ):
        with T.Kernel(1, is_npu=True) as (cid, _):
            a = T.alloc_ub((N,), F32)
            b = T.alloc_ub((N,), F32)
            c = T.alloc_ub((N,), F32)
            start = cid * N
            tail = T.min(N, shape - start)
            T.copy(A[start : start + tail], a[:tail])
            T.copy(B[start : start + tail], b[:tail])
            for i in T.Parallel(N):  # 满块，不是 tail
                c[i] = a[i] + b[i]
            T.copy(c[:tail], C[start : start + tail])

    return f


# --------------------------------------------------------------------------
# D. 预期编译失败（边界探测）
# --------------------------------------------------------------------------


def reduction_plus_equal():
    """a[i] += b[i,j]：无归约匹配，Q3 §4 推导为 codegen 形状检查失败。"""

    @T.prim_func
    def f(B: T.Tensor((M, K), F32), C: T.Tensor((M,), F32)):
        with T.Kernel(1, is_npu=True) as (cid, _):
            b, c = T.alloc_ub((M, K), F32), T.alloc_ub((M,), F32)
            T.copy(B, b)
            for i, j in T.Parallel(M, K):
                c[i] += b[i, j]
            T.copy(c, C)

    return f


# --------------------------------------------------------------------------
# 用例表
# --------------------------------------------------------------------------

CASES = [
    # (名称, 类别, 构造函数, 预期, 对应问答文档位置)
    ("binary_add", "A.逐元素", binary_add, "full", "Q3 §3"),
    ("binary_all_ops", "A.逐元素", binary_all_ops, "full", "Q3 §3"),
    ("unary_math", "A.一元", unary_math, "full", "Q3 §3"),
    ("cast_f32_f16", "A.类型转换", cast_f32_to_f16, "full", "Q3 §3"),
    ("vector_scalar_imm", "A.向量标量", vector_scalar_imm, "full", "Q3 §3"),
    ("vector_scalar_load", "A.向量标量", vector_scalar_load, "full", "Q3 §3"),
    ("scalar_on_left_sub", "A.向量标量", scalar_on_left_sub, "full", "Q3 §3"),
    ("broadcast_one_axis", "A.广播", broadcast_one_axis, "full", "Q3 §3"),
    ("broadcast_two_axes", "A.广播", broadcast_two_axes, "full", "Q3 §3"),
    ("pure_copy", "A.拷贝填充", pure_copy, "full", "Q3 §3"),
    ("const_fill", "A.拷贝填充", const_fill, "full", "Q3 §3"),
    ("loop_var_in_value", "A.循环变量", loop_var_in_value, "full", "Q3 §3"),
    ("if_then_else_select", "A.条件", if_then_else_select, "full", "Q3 §3"),
    ("compound_expr", "A.复合", compound_expr, "full", "Q3 §3"),
    ("offset_read", "A.偏移", offset_read, "full", "Q3 §3"),
    ("elementwise_2d", "A.二维", elementwise_2d, "full", "Q3 §3"),
    ("indirect_row_copy", "B.部分", indirect_row_copy, "partial", "Q3 §3"),
    (
        "dynamic_outer_static_inner",
        "B.部分",
        dynamic_outer_static_inner,
        "partial",
        "Q3 §1",
    ),
    ("dynamic_extent_1d", "C.回退", dynamic_extent_1d, "scalar", "Q3 §1"),
    ("multi_statement_body", "C.回退", multi_statement_body, "scalar", "Q3 §3"),
    ("store_index_transformed", "C.回退", store_index_transformed, "scalar", "Q3 §2"),
    ("transpose_read", "C.回退", transpose_read, "scalar", "Q3 §2"),
    ("flatten_read", "C.回退", flatten_read, "scalar", "Q3 §2"),
    ("var_fill", "C.回退", var_fill, "scalar", "Q3 §3"),
    ("nondivisible_1d", "E.对齐尾部", nondivisible_1d, "full", "Q2"),
    ("unaligned_offset", "E.对齐尾部", unaligned_offset, "full", "Q2"),
    ("tiny_inner_dim", "E.对齐尾部", tiny_inner_dim, "full", "开发指南 §3.1"),
    (
        "broadcast_nonaligned_inner",
        "E.对齐尾部",
        broadcast_nonaligned_inner,
        "full",
        "Q2",
    ),
    ("offset_plus_broadcast", "E.对齐尾部", offset_plus_broadcast, "full", "Q3 §4"),
    ("pad_then_parallel", "E.对齐尾部", pad_then_parallel, "full", "Q2 §5"),
    (
        "full_block_partial_copy",
        "E.对齐尾部",
        full_block_partial_copy,
        "full",
        "Q2 §5",
    ),
    ("python_if_in_body", "F.控制流", python_if_in_body, "scalar", "Q3 §3"),
    ("python_if_else_in_body", "F.控制流", python_if_else_in_body, "scalar", "Q3 §3"),
    ("python_if_around_loop", "F.控制流", python_if_around_loop, "full", "Q3 §1"),
    ("ternary_in_body", "F.控制流", ternary_in_body, "error", "TVM expr.py:179"),
    ("reduction_plus_equal", "D.静默接受", reduction_plus_equal, "full", "Q3 §4"),
]

BY_NAME = {name: (cat, fn, exp, ref) for name, cat, fn, exp, ref in CASES}

# verdict 判定不了的东西，要人工看 verdict.json 里的 regions 字段。
NOTES = {
    "nondivisible_1d": "region 长度应为 250。若出现 256，说明某处做了补齐。",
    "unaligned_offset": "源 region 的 offset 应为 3。",
    "offset_plus_broadcast": (
        "**重点用例。**看 w 对应的源 region offset：应为 1；若为 0，"
        "则复现了 Q3 §4 的 offset+broadcast 丢常数项疑点。"
    ),
    "broadcast_nonaligned_inner": "看外提的 reshape/brc 临时 buffer 长度是 250 还是 256。",
    "tiny_inner_dim": "TIR 层应为 [32,3]；后端的对齐填充在这一层看不到。",
    "pad_then_parallel": "先确认 T.pad 本身能编过；再看 Parallel 部分是否照常向量化。",
    "full_block_partial_copy": (
        "结构上预期 full。真正的问题是语义：未拷入的尾部元素未初始化却参与计算，"
        "需要运行时传 shape < 256 并检查输出有效段。"
    ),
    "reduction_plus_equal": (
        "**已实测（2026-10-20）**：TIR 阶段静默通过，生成 [M] + [M,N] -> [M] 的逐元素"
        "加法，不是归约。codegen 是否会在 getBroadcastDim 的同 rank 检查处拦住，"
        "需加 --mlir 复跑确认。"
    ),
    "dynamic_extent_1d": "若居然向量化了，说明 Q3 §1 对动态 extent 的判断有误。",
    "python_if_in_body": "对照 if_then_else_select：同样的条件语义，写法不同则不向量化。",
    "python_if_around_loop": "确认 if 被保留为 scf.if 的同时，循环内部仍整体向量化。",
    "ternary_in_body": (
        "预期在解析期抛 ValueError（Cannot use and / or / not operator to Expr）。"
        "若竟然编过了，务必检查条件是否被静默丢弃——那会是严重问题。"
    ),
}
