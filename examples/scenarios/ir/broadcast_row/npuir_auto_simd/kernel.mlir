module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: i64 {hacc.arg_type = #hacc.arg_type<ffts_base_address>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg2: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: memref<?xf32>, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32, %arg11: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>, hivm.func_core_type = #hivm.func_core_type<AIV>, mix_mode = "aiv"} {
    %c64 = arith.constant 64 : index
    %c1 = arith.constant 1 : index
    hivm.hir.set_ffts_base_addr %arg0
    %reinterpret_cast = memref.reinterpret_cast %arg3 to offset: [0], sizes: [4, 64], strides: [%c64, %c1] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg5 to offset: [0], sizes: [4, 64], strides: [%c64, %c1] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_1 = memref.reinterpret_cast %arg4 to offset: [0], sizes: [64], strides: [%c1] : memref<?xf32> to memref<64xf32, strided<[1]>>
    %0 = tensor.empty() : tensor<4x64xf32>
    %1 = tensor.empty() : tensor<4x64xf32>
    %alloc = memref.alloc() : memref<4x64xf32>
    memref.copy %reinterpret_cast, %alloc : memref<4x64xf32, strided<[64, 1]>> to memref<4x64xf32>
    %2 = bufferization.to_tensor %alloc restrict : memref<4x64xf32>
    %alloc_2 = memref.alloc() : memref<64xf32>
    memref.copy %reinterpret_cast_1, %alloc_2 : memref<64xf32, strided<[1]>> to memref<64xf32>
    %3 = bufferization.to_tensor %alloc_2 restrict : memref<64xf32>
    %expanded = tensor.expand_shape %3 [[0, 1]] output_shape [1, 64] : tensor<64xf32> into tensor<1x64xf32>
    %4 = hivm.hir.vbrc ins(%expanded : tensor<1x64xf32>) outs(%1 : tensor<4x64xf32>) broadcast_dims = [0] -> tensor<4x64xf32>
    %5 = hivm.hir.vadd ins(%2, %4 : tensor<4x64xf32>, tensor<4x64xf32>) outs(%0 : tensor<4x64xf32>) -> tensor<4x64xf32>
    bufferization.materialize_in_destination %5 in writable %reinterpret_cast_0 : (tensor<4x64xf32>, memref<4x64xf32, strided<[64, 1]>>) -> ()
    return
  }
}