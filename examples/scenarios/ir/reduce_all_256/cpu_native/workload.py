@T.prim_func
def main(A: T.Tensor((256,), "float32"), B: T.Tensor((1,), "float32"), O: T.Tensor((1,), "float32")):
    with T.Kernel(1):
        for i in T.Parallel(1):
            O[i] = T.float32(0)
            for k in T.serial(256):
                O[i] = O[i] + A[k]
