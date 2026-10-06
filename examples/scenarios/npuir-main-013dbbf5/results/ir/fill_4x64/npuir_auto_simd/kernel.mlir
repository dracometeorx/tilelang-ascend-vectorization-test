module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg2: memref<?xf32>, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: i32, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, global_kernel = "local", mix_mode = "aiv", parallel_mode = "simd"} {
    %c1_i32 = arith.constant 1 : i32
    %0 = arith.index_cast %c1_i32 : i32 to index
    %c64_i32 = arith.constant 64 : i32
    %1 = arith.muli %c64_i32, %c1_i32 : i32
    %2 = arith.index_cast %1 : i32 to index
    %reinterpret_cast = memref.reinterpret_cast %arg2 to offset: [0], sizes: [4, 64], strides: [%2, %0] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg4 to offset: [0], sizes: [4, 64], strides: [%2, %0] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_1 = memref.reinterpret_cast %arg3 to offset: [0], sizes: [1], strides: [%0] : memref<?xf32> to memref<1xf32, strided<[1]>>
    %3 = hivm.hir.get_block_idx -> i64
    %4 = arith.trunci %3 : i64 to i32
    %5 = tensor.empty() : tensor<4x64xf32>
    %cst = arith.constant 1.250000e+00 : f32
    %6 = linalg.fill ins(%cst : f32) outs(%5 : tensor<4x64xf32>) -> tensor<4x64xf32>
    bufferization.materialize_in_destination %6 in writable %reinterpret_cast_0 : (tensor<4x64xf32>, memref<4x64xf32, strided<[64, 1]>>) -> ()
    return
  }
}
