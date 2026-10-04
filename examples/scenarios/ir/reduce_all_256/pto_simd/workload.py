@T.prim_func
def main(A: T.Tensor((256,), "float32"), B: T.Tensor((1,), "float32"), O: T.Tensor((1,), "float32")):
    with T.Kernel(1):
        a = T.alloc_shared((256,), "float32")
        b = T.alloc_shared((1,), "float32")
        o = T.alloc_shared((1,), "float32")
        T.copy(A, a)
        with T.SimdVF():
            for i in T.Parallel(1):
                o[i] = T.float32(0)
                for k in T.serial(256):
                    o[i] = o[i] + a[k]
        T.copy(o, O)
