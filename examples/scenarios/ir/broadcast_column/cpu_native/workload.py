@T.prim_func
def main(A: T.Tensor((4, 64), "float32"), B: T.Tensor((4, 1), "float32"), O: T.Tensor((4, 64), "float32")):
    with T.Kernel(1):
        for i, j in T.Parallel(4, 64):
            O[i, j] = A[i, j] + B[i, 0]
