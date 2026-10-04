module attributes {hivm.aic_bitcode = #hivm.aic_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.aic.c310.bc">, hivm.aiv_bitcode = #hivm.aiv_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.aiv.c310.bc">, hivm.host_bitcode = #hivm.host_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/host.bc">, hivm.mix_aic_bitcode = #hivm.mix_aic_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.mix.aic.c310.bc">, hivm.mix_aiv_bitcode = #hivm.mix_aiv_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.mix.aiv.c310.bc">} {
  module attributes {dlti.target_system_spec = #dlti.target_system_spec<"NPU" : #hacc.target_device_spec<#dlti.dl_entry<"AI_CORE_COUNT", 32 : i32>, #dlti.dl_entry<"CUBE_CORE_COUNT", 32 : i32>, #dlti.dl_entry<"VECTOR_CORE_COUNT", 64 : i32>, #dlti.dl_entry<"UB_SIZE", 2031616 : i32>, #dlti.dl_entry<"L1_SIZE", 4194304 : i32>, #dlti.dl_entry<"L0A_SIZE", 524288 : i32>, #dlti.dl_entry<"L0B_SIZE", 524288 : i32>, #dlti.dl_entry<"L0C_SIZE", 2097152 : i32>, #dlti.dl_entry<"UB_ALIGN_SIZE", 256 : i32>, #dlti.dl_entry<"L1_ALIGN_SIZE", 256 : i32>, #dlti.dl_entry<"L0C_ALIGN_SIZE", 4096 : i32>, #dlti.dl_entry<"MINIMAL_D_CACHE_SIZE", 262144 : i32>, #dlti.dl_entry<"MAXIMUM_D_CACHE_SIZE", 983040 : i32>, #dlti.dl_entry<"ARCH", "dav-c310">>>, hacc.target = #hacc.target<"Ascend950PR_9589">, hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
    func.func private @load_gm_to_ubuf_1d_float(memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, i32, f32, index, i32) attributes {hacc.function_kind = #hacc.function_kind<DEVICE>, hacc.noinline, hivm.func_core_type = #hivm.func_core_type<AIV>, hivm_regbaseintrins.target = #hivm_regbaseintrins.target<"dav-c310">, llvm.emit_c_interface}
    func.func private @store_ubuf_to_gm_1d_float(memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, i32) attributes {hacc.function_kind = #hacc.function_kind<DEVICE>, hacc.noinline, hivm.func_core_type = #hivm.func_core_type<AIV>, hivm_regbaseintrins.target = #hivm_regbaseintrins.target<"dav-c310">, llvm.emit_c_interface}
    func.func @main(%arg0: i64 {hacc.arg_type = #hacc.arg_type<ffts_base_address>}, %arg1: memref<?xi8, #hivm.address_space<gm>> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg2: memref<?xi8, #hivm.address_space<gm>> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg3: memref<?xf32, #hivm.address_space<gm>>, %arg4: memref<?xf32, #hivm.address_space<gm>>, %arg5: memref<?xf32, #hivm.address_space<gm>>, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32, %arg11: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>, hivm.func_core_type = #hivm.func_core_type<AIV>, hivm.vf_mode = #hivm.vf_mode<SIMD>, hivm_regbaseintrins.target = #hivm_regbaseintrins.target<"dav-c310">, mix_mode = "aiv"} {
      %0 = llvm.mlir.constant(1024 : i64) : i64
      %1 = llvm.mlir.constant(0 : i64) : i64
      %2 = llvm.mlir.constant(1 : i32) : i32
      %3 = llvm.mlir.constant(0.000000e+00 : f32) : f32
      %4 = llvm.mlir.constant(0 : i32) : i32
      %5 = llvm.mlir.constant(256 : i32) : i32
      %6 = llvm.mlir.constant(0 : index) : i64
      %7 = builtin.unrealized_conversion_cast %6 : i64 to index
      hivm.hir.set_ctrl false at ctrl[60]
      hivm.hir.set_ctrl true at ctrl[48]
      hivm.hir.set_ffts_base_addr %arg0
      %reinterpret_cast = memref.reinterpret_cast %arg3 to offset: [0], sizes: [256], strides: [1] : memref<?xf32, #hivm.address_space<gm>> to memref<256xf32, strided<[1]>, #hivm.address_space<gm>>
      %reinterpret_cast_0 = memref.reinterpret_cast %arg5 to offset: [0], sizes: [1], strides: [1] : memref<?xf32, #hivm.address_space<gm>> to memref<1xf32, strided<[1]>, #hivm.address_space<gm>>
      %8 = hivm.hir.pointer_cast(%1) : memref<256xf32, #hivm.address_space<ub>>
      %cast = memref.cast %reinterpret_cast : memref<256xf32, strided<[1]>, #hivm.address_space<gm>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>
      %cast_1 = memref.cast %8 : memref<256xf32, #hivm.address_space<ub>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>
      call @load_gm_to_ubuf_1d_float(%cast, %cast_1, %4, %3, %7, %4) : (memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, i32, f32, index, i32) -> ()
      hivm.hir.set_flag[<PIPE_MTE2>, <PIPE_S>, <EVENT_ID0>]
      %9 = hivm.hir.pointer_cast(%0) : memref<1xf32, #hivm.address_space<ub>>
      memref.store %3, %9[%7] : memref<1xf32, #hivm.address_space<ub>>
      hivm.hir.wait_flag[<PIPE_MTE2>, <PIPE_S>, <EVENT_ID0>]
      cf.br ^bb1(%4 : i32)
    ^bb1(%10: i32):  // 2 preds: ^bb0, ^bb2
      %11 = arith.cmpi slt, %10, %5 : i32
      cf.cond_br %11, ^bb2, ^bb3
    ^bb2:  // pred: ^bb1
      %12 = memref.load %9[%7] {markDCacheInvalidatePatternVisited = 0 : i32} : memref<1xf32, #hivm.address_space<ub>>
      %13 = llvm.sext %10 : i32 to i64
      %14 = builtin.unrealized_conversion_cast %13 : i64 to index
      %15 = memref.load %8[%14] {markDCacheInvalidatePatternVisited = 0 : i32} : memref<256xf32, #hivm.address_space<ub>>
      %16 = llvm.fadd %12, %15  : f32
      memref.store %16, %9[%7] : memref<1xf32, #hivm.address_space<ub>>
      %17 = arith.addi %10, %2 overflow<nsw> : i32
      cf.br ^bb1(%17 : i32)
    ^bb3:  // pred: ^bb1
      hivm.hir.set_flag[<PIPE_S>, <PIPE_MTE3>, <EVENT_ID0>]
      hivm.hir.wait_flag[<PIPE_S>, <PIPE_MTE3>, <EVENT_ID0>]
      %cast_2 = memref.cast %9 : memref<1xf32, #hivm.address_space<ub>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>
      %cast_3 = memref.cast %reinterpret_cast_0 : memref<1xf32, strided<[1]>, #hivm.address_space<gm>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>
      call @store_ubuf_to_gm_1d_float(%cast_2, %cast_3, %4) : (memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, i32) -> ()
      hivm.hir.set_ctrl true at ctrl[60]
      hivm.hir.pipe_barrier[<PIPE_ALL>]
      return
    }
  }
}
