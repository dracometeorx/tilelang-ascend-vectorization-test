@T.prim_func
def main(A: T.Tensor((4, 64), "float32"), B: T.Tensor((1,), "float32"), O: T.Tensor((256,), "float32")):
    with T.Kernel(1):
        for k in T.Parallel(256):
            O[k] = A[k // 64, k % 64]
