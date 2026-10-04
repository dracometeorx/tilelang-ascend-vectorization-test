module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: i64 {hacc.arg_type = #hacc.arg_type<ffts_base_address>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg2: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: memref<?xf32>, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32, %arg11: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>, hivm.func_core_type = #hivm.func_core_type<AIV>, mix_mode = "aiv"} {
    %c1 = arith.constant 1 : index
    %cst = arith.constant 1.250000e+00 : f32
    hivm.hir.set_ffts_base_addr %arg0
    %reinterpret_cast = memref.reinterpret_cast %arg5 to offset: [0], sizes: [256], strides: [%c1] : memref<?xf32> to memref<256xf32, strided<[1]>>
    %0 = tensor.empty() : tensor<256xf32>
    %1 = hivm.hir.vbrc ins(%cst : f32) outs(%0 : tensor<256xf32>) -> tensor<256xf32>
    bufferization.materialize_in_destination %1 in writable %reinterpret_cast : (tensor<256xf32>, memref<256xf32, strided<[1]>>) -> ()
    return
  }
}