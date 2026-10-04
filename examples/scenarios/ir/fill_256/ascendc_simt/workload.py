@T.prim_func
def main(A: T.Tensor((256,), "float32"), B: T.Tensor((1,), "float32"), O: T.Tensor((256,), "float32")):
    with T.Kernel(1):
        a = T.alloc_shared((256,), "float32")
        b = T.alloc_shared((1,), "float32")
        o = T.alloc_shared((256,), "float32")
        with T.SimtVF(threads=128):
            for i in T.Parallel(256):
                o[i] = T.float32(1.25)
        T.copy(o, O)
