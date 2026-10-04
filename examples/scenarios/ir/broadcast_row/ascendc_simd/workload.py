@T.prim_func
def main(A: T.Tensor((4, 64), "float32"), B: T.Tensor((64,), "float32"), O: T.Tensor((4, 64), "float32")):
    with T.Kernel(1):
        a = T.alloc_shared((4, 64), "float32")
        b = T.alloc_shared((64,), "float32")
        o = T.alloc_shared((4, 64), "float32")
        T.copy(A, a)
        T.copy(B, b)
        with T.SimdVF():
            for i, j in T.Parallel(4, 64):
                o[i, j] = a[i, j] + b[j]
        T.copy(o, O)
