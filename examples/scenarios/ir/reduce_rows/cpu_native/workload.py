@T.prim_func
def main(A: T.Tensor((4, 64), "float32"), B: T.Tensor((1,), "float32"), O: T.Tensor((4,), "float32")):
    with T.Kernel(1):
        for i in T.Parallel(4):
            O[i] = T.float32(0)
            for k in T.serial(64):
                O[i] = O[i] + A[i, k]
