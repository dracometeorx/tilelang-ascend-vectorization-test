module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: i64 {hacc.arg_type = #hacc.arg_type<ffts_base_address>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg2: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: memref<?xf32>, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32, %arg11: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>, hivm.func_core_type = #hivm.func_core_type<AIV>, mix_mode = "aiv"} {
    %c64 = arith.constant 64 : index
    %c1 = arith.constant 1 : index
    hivm.hir.set_ffts_base_addr %arg0
    %reinterpret_cast = memref.reinterpret_cast %arg3 to offset: [0], sizes: [4, 64], strides: [%c64, %c1] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg5 to offset: [0], sizes: [4, 64], strides: [%c64, %c1] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_1 = memref.reinterpret_cast %arg4 to offset: [0], sizes: [4, 1], strides: [%c1, %c1] : memref<?xf32> to memref<4x1xf32, strided<[1, 1]>>
    %0 = tensor.empty() : tensor<4x1xf32>
    %1 = tensor.empty() : tensor<4x64xf32>
    %2 = tensor.empty() : tensor<4x64xf32>
    %alloc = memref.alloc() : memref<4x64xf32>
    memref.copy %reinterpret_cast, %alloc : memref<4x64xf32, strided<[64, 1]>> to memref<4x64xf32>
    %3 = bufferization.to_tensor %alloc restrict : memref<4x64xf32>
    %subview = memref.subview %reinterpret_cast_1[0, 0] [4, 1] [1, 1] : memref<4x1xf32, strided<[1, 1]>> to memref<4xf32, strided<[1]>>
    %alloc_2 = memref.alloc() : memref<4xf32>
    memref.copy %subview, %alloc_2 : memref<4xf32, strided<[1]>> to memref<4xf32>
    %4 = bufferization.to_tensor %alloc_2 restrict : memref<4xf32>
    %inserted_slice = tensor.insert_slice %4 into %0[0, 0] [4, 1] [1, 1] : tensor<4xf32> into tensor<4x1xf32>
    %5 = hivm.hir.vbrc ins(%inserted_slice : tensor<4x1xf32>) outs(%2 : tensor<4x64xf32>) broadcast_dims = [1] -> tensor<4x64xf32>
    %6 = hivm.hir.vadd ins(%3, %5 : tensor<4x64xf32>, tensor<4x64xf32>) outs(%1 : tensor<4x64xf32>) -> tensor<4x64xf32>
    bufferization.materialize_in_destination %6 in writable %reinterpret_cast_0 : (tensor<4x64xf32>, memref<4x64xf32, strided<[64, 1]>>) -> ()
    return
  }
}