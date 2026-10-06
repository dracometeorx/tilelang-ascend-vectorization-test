module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg2: memref<?xf32>, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: i32, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, global_kernel = "local", mix_mode = "aiv", parallel_mode = "simd"} {
    %c1_i32 = arith.constant 1 : i32
    %0 = arith.index_cast %c1_i32 : i32 to index
    %reinterpret_cast = memref.reinterpret_cast %arg2 to offset: [0], sizes: [256], strides: [%0] : memref<?xf32> to memref<256xf32, strided<[1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg4 to offset: [0], sizes: [256], strides: [%0] : memref<?xf32> to memref<256xf32, strided<[1]>>
    %reinterpret_cast_1 = memref.reinterpret_cast %arg3 to offset: [0], sizes: [1], strides: [%0] : memref<?xf32> to memref<1xf32, strided<[1]>>
    %1 = hivm.hir.get_block_idx -> i64
    %2 = arith.trunci %1 : i64 to i32
    %3 = tensor.empty() : tensor<256xf32>
    %4 = tensor.empty() : tensor<1xf32>
    %5 = tensor.empty() : tensor<256xf32>
    %6 = tensor.empty() : tensor<256xf32>
    %alloc = memref.alloc() : memref<256xf32>
    memref.copy %reinterpret_cast, %alloc : memref<256xf32, strided<[1]>> to memref<256xf32>
    %7 = bufferization.to_tensor %alloc restrict : memref<256xf32>
    %expanded = tensor.expand_shape %7 [[0]] output_shape [256] : tensor<256xf32> into tensor<256xf32>
    %inserted_slice = tensor.insert_slice %expanded into %3[0] [256] [1] : tensor<256xf32> into tensor<256xf32>
    %alloc_2 = memref.alloc() : memref<1xf32>
    memref.copy %reinterpret_cast_1, %alloc_2 : memref<1xf32, strided<[1]>> to memref<1xf32>
    %8 = bufferization.to_tensor %alloc_2 restrict : memref<1xf32>
    %expanded_3 = tensor.expand_shape %8 [[0]] output_shape [1] : tensor<1xf32> into tensor<1xf32>
    %inserted_slice_4 = tensor.insert_slice %expanded_3 into %4[0] [1] [1] : tensor<1xf32> into tensor<1xf32>
    %c0_i32 = arith.constant 0 : i32
    %9 = arith.index_cast %c0_i32 : i32 to index
    %extracted = tensor.extract %inserted_slice_4[%9] : tensor<1xf32>
    %10 = linalg.fill ins(%extracted : f32) outs(%6 : tensor<256xf32>) -> tensor<256xf32>
    %11 = linalg.elemwise_binary {fun = #linalg.binary_fn<add>} ins(%inserted_slice, %10 : tensor<256xf32>, tensor<256xf32>) outs(%5 : tensor<256xf32>) -> tensor<256xf32>
    bufferization.materialize_in_destination %11 in writable %reinterpret_cast_0 : (tensor<256xf32>, memref<256xf32, strided<[1]>>) -> ()
    return
  }
}
