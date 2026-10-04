@T.prim_func
def main(A: T.Tensor((4, 64), "float32"), B: T.Tensor((1,), "float32"), O: T.Tensor((256,), "float32")):
    with T.Kernel(1):
        a = T.alloc_shared((4, 64), "float32")
        b = T.alloc_shared((1,), "float32")
        o = T.alloc_shared((256,), "float32")
        T.copy(A, a)
        with T.SimtVF(threads=128):
            for k in T.Parallel(256):
                o[k] = a[k // 64, k % 64]
        T.copy(o, O)
