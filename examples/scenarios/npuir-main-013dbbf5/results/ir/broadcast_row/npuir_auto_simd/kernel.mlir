module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg2: memref<?xf32>, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: i32, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, global_kernel = "local", mix_mode = "aiv", parallel_mode = "simd"} {
    %c1_i32 = arith.constant 1 : i32
    %0 = arith.index_cast %c1_i32 : i32 to index
    %c64_i32 = arith.constant 64 : i32
    %1 = arith.muli %c64_i32, %c1_i32 : i32
    %2 = arith.index_cast %1 : i32 to index
    %reinterpret_cast = memref.reinterpret_cast %arg2 to offset: [0], sizes: [4, 64], strides: [%2, %0] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg4 to offset: [0], sizes: [4, 64], strides: [%2, %0] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_1 = memref.reinterpret_cast %arg3 to offset: [0], sizes: [64], strides: [%0] : memref<?xf32> to memref<64xf32, strided<[1]>>
    %3 = hivm.hir.get_block_idx -> i64
    %4 = arith.trunci %3 : i64 to i32
    %5 = tensor.empty() : tensor<4x64xf32>
    %6 = tensor.empty() : tensor<64xf32>
    %7 = tensor.empty() : tensor<4x64xf32>
    %8 = tensor.empty() : tensor<64xf32>
    %9 = tensor.empty() : tensor<1x64xf32>
    %10 = tensor.empty() : tensor<4x64xf32>
    %alloc = memref.alloc() : memref<4x64xf32>
    memref.copy %reinterpret_cast, %alloc : memref<4x64xf32, strided<[64, 1]>> to memref<4x64xf32>
    %11 = bufferization.to_tensor %alloc restrict : memref<4x64xf32>
    %expanded = tensor.expand_shape %11 [[0], [1]] output_shape [4, 64] : tensor<4x64xf32> into tensor<4x64xf32>
    %inserted_slice = tensor.insert_slice %expanded into %5[0, 0] [4, 64] [1, 1] : tensor<4x64xf32> into tensor<4x64xf32>
    %alloc_2 = memref.alloc() : memref<64xf32>
    memref.copy %reinterpret_cast_1, %alloc_2 : memref<64xf32, strided<[1]>> to memref<64xf32>
    %12 = bufferization.to_tensor %alloc_2 restrict : memref<64xf32>
    %expanded_3 = tensor.expand_shape %12 [[0]] output_shape [64] : tensor<64xf32> into tensor<64xf32>
    %inserted_slice_4 = tensor.insert_slice %expanded_3 into %6[0] [64] [1] : tensor<64xf32> into tensor<64xf32>
    %collapsed = tensor.collapse_shape %inserted_slice_4 [[0]] : tensor<64xf32> into tensor<64xf32>
    %expanded_5 = tensor.expand_shape %collapsed [[0, 1]] output_shape [1, 64] : tensor<64xf32> into tensor<1x64xf32>
    %collapsed_6 = tensor.collapse_shape %expanded_5 [[0, 1]] : tensor<1x64xf32> into tensor<64xf32>
    %broadcasted = linalg.broadcast ins(%collapsed_6 : tensor<64xf32>) outs(%10 : tensor<4x64xf32>) dimensions = [0] 
    %13 = linalg.elemwise_binary {fun = #linalg.binary_fn<add>} ins(%inserted_slice, %broadcasted : tensor<4x64xf32>, tensor<4x64xf32>) outs(%7 : tensor<4x64xf32>) -> tensor<4x64xf32>
    bufferization.materialize_in_destination %13 in writable %reinterpret_cast_0 : (tensor<4x64xf32>, memref<4x64xf32, strided<[64, 1]>>) -> ()
    return
  }
}
