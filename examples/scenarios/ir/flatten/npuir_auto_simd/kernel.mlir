module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: i64 {hacc.arg_type = #hacc.arg_type<ffts_base_address>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg2: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: memref<?xf32>, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32, %arg11: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>, hivm.func_core_type = #hivm.func_core_type<AIV>, mix_mode = "aiv"} {
    %c64 = arith.constant 64 : index
    %c1 = arith.constant 1 : index
    %c256_i32 = arith.constant 256 : i32
    %c0_i32 = arith.constant 0 : i32
    %c64_i32 = arith.constant 64 : i32
    %c1_i32 = arith.constant 1 : i32
    hivm.hir.set_ffts_base_addr %arg0
    %reinterpret_cast = memref.reinterpret_cast %arg3 to offset: [0], sizes: [4, 64], strides: [%c64, %c1] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg5 to offset: [0], sizes: [256], strides: [%c1] : memref<?xf32> to memref<256xf32, strided<[1]>>
    %0 = tensor.empty() : tensor<256xf32>
    %alloc = memref.alloc() : memref<4x64xf32>
    memref.copy %reinterpret_cast, %alloc : memref<4x64xf32, strided<[64, 1]>> to memref<4x64xf32>
    %1 = bufferization.to_tensor %alloc restrict : memref<4x64xf32>
    %2 = scf.for %arg12 = %c0_i32 to %c256_i32 step %c1_i32 iter_args(%arg13 = %0) -> (tensor<256xf32>)  : i32 {
      %3 = arith.divsi %arg12, %c64_i32 : i32
      %4 = arith.index_cast %3 : i32 to index
      %5 = arith.remsi %arg12, %c64_i32 : i32
      %6 = arith.index_cast %5 : i32 to index
      %7 = arith.index_cast %arg12 : i32 to index
      %extracted_slice = tensor.extract_slice %1[%4, %6] [1, 1] [1, 1] : tensor<4x64xf32> to tensor<1xf32>
      %inserted_slice = tensor.insert_slice %extracted_slice into %arg13[%7] [1] [1] : tensor<1xf32> into tensor<256xf32>
      scf.yield %inserted_slice : tensor<256xf32>
    }
    bufferization.materialize_in_destination %2 in writable %reinterpret_cast_0 : (tensor<256xf32>, memref<256xf32, strided<[1]>>) -> ()
    return
  }
}