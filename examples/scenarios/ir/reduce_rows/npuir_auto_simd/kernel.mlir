module attributes {hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
  func.func @main(%arg0: i64 {hacc.arg_type = #hacc.arg_type<ffts_base_address>}, %arg1: memref<?xi8> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg2: memref<?xi8> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg3: memref<?xf32>, %arg4: memref<?xf32>, %arg5: memref<?xf32>, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32, %arg11: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>, hivm.func_core_type = #hivm.func_core_type<AIV>, mix_mode = "aiv"} {
    %c64 = arith.constant 64 : index
    %c1 = arith.constant 1 : index
    %cst = arith.constant 0.000000e+00 : f32
    %c4_i32 = arith.constant 4 : i32
    %c0_i32 = arith.constant 0 : i32
    %c64_i32 = arith.constant 64 : i32
    %c1_i32 = arith.constant 1 : i32
    hivm.hir.set_ffts_base_addr %arg0
    %reinterpret_cast = memref.reinterpret_cast %arg3 to offset: [0], sizes: [4, 64], strides: [%c64, %c1] : memref<?xf32> to memref<4x64xf32, strided<[64, 1]>>
    %reinterpret_cast_0 = memref.reinterpret_cast %arg5 to offset: [0], sizes: [4], strides: [%c1] : memref<?xf32> to memref<4xf32, strided<[1]>>
    %0 = tensor.empty() : tensor<4xf32>
    %alloc = memref.alloc() : memref<4x64xf32>
    memref.copy %reinterpret_cast, %alloc : memref<4x64xf32, strided<[64, 1]>> to memref<4x64xf32>
    %1 = bufferization.to_tensor %alloc restrict : memref<4x64xf32>
    %2 = scf.for %arg12 = %c0_i32 to %c4_i32 step %c1_i32 iter_args(%arg13 = %0) -> (tensor<4xf32>)  : i32 {
      %4 = arith.index_cast %arg12 : i32 to index
      %inserted = tensor.insert %cst into %arg13[%4] : tensor<4xf32>
      scf.yield %inserted : tensor<4xf32>
    }
    %3 = scf.for %arg12 = %c0_i32 to %c4_i32 step %c1_i32 iter_args(%arg13 = %2) -> (tensor<4xf32>)  : i32 {
      %4 = scf.for %arg14 = %c0_i32 to %c64_i32 step %c1_i32 iter_args(%arg15 = %arg13) -> (tensor<4xf32>)  : i32 {
        %5 = arith.index_cast %arg12 : i32 to index
        %extracted = tensor.extract %arg15[%5] : tensor<4xf32>
        %6 = arith.index_cast %arg14 : i32 to index
        %extracted_1 = tensor.extract %1[%5, %6] : tensor<4x64xf32>
        %7 = arith.addf %extracted, %extracted_1 : f32
        %inserted = tensor.insert %7 into %arg15[%5] : tensor<4xf32>
        scf.yield %inserted : tensor<4xf32>
      }
      scf.yield %4 : tensor<4xf32>
    }
    bufferization.materialize_in_destination %3 in writable %reinterpret_cast_0 : (tensor<4xf32>, memref<4xf32, strided<[1]>>) -> ()
    return
  }
}