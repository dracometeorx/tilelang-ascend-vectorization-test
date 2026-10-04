#map = affine_map<(d0)[s0] -> (d0 + s0)>
module attributes {hivm.aic_bitcode = #hivm.aic_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.aic.c310.bc">, hivm.aiv_bitcode = #hivm.aiv_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.aiv.c310.bc">, hivm.host_bitcode = #hivm.host_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/host.bc">, hivm.mix_aic_bitcode = #hivm.mix_aic_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.mix.aic.c310.bc">, hivm.mix_aiv_bitcode = #hivm.mix_aiv_bitcode<"/workspace/setup/cann/components-9.2/npu-ir/bishengir/lib/meta_op.mix.aiv.c310.bc">} {
  module attributes {dlti.target_system_spec = #dlti.target_system_spec<"NPU" : #hacc.target_device_spec<#dlti.dl_entry<"AI_CORE_COUNT", 32 : i32>, #dlti.dl_entry<"CUBE_CORE_COUNT", 32 : i32>, #dlti.dl_entry<"VECTOR_CORE_COUNT", 64 : i32>, #dlti.dl_entry<"UB_SIZE", 2031616 : i32>, #dlti.dl_entry<"L1_SIZE", 4194304 : i32>, #dlti.dl_entry<"L0A_SIZE", 524288 : i32>, #dlti.dl_entry<"L0B_SIZE", 524288 : i32>, #dlti.dl_entry<"L0C_SIZE", 2097152 : i32>, #dlti.dl_entry<"UB_ALIGN_SIZE", 256 : i32>, #dlti.dl_entry<"L1_ALIGN_SIZE", 256 : i32>, #dlti.dl_entry<"L0C_ALIGN_SIZE", 4096 : i32>, #dlti.dl_entry<"MINIMAL_D_CACHE_SIZE", 262144 : i32>, #dlti.dl_entry<"MAXIMUM_D_CACHE_SIZE", 983040 : i32>, #dlti.dl_entry<"ARCH", "dav-c310">>>, hacc.target = #hacc.target<"Ascend950PR_9589">, hivm.module_core_type = #hivm.module_core_type<AIV>, memref.memref_as_ptr} {
    func.func @main_outlined_vf_0(%arg0: memref<4x64xf32, #hivm.address_space<ub>>, %arg1: memref<1xf32, #hivm.address_space<ub>>, %arg2: memref<4x64xf32, #hivm.address_space<ub>>) attributes {hivm.func_core_type = #hivm.func_core_type<AIV>, hivm.vector_function, no_inline} {
      %0 = llvm.mlir.constant(2 : i32) : i32
      %1 = llvm.mlir.constant(3 : i32) : i32
      %2 = llvm.mlir.constant(0 : i32) : i32
      %3 = llvm.mlir.constant(4 : i32) : i32
      %4 = llvm.mlir.constant(1 : i32) : i32
      %5 = builtin.unrealized_conversion_cast %arg1 : memref<1xf32, #hivm.address_space<ub>> to !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)>
      %6 = llvm.extractvalue %5[1] : !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)> 
      %7 = "hivm_regbaseintrins.intr.hivm.vldsx1.v64f32"(%6, %2, %1, %2) : (!llvm.ptr<6>, i32, i32, i32) -> vector<64xf32>
      cf.br ^bb1(%2 : i32)
    ^bb1(%8: i32):  // 2 preds: ^bb0, ^bb2
      %9 = arith.cmpi slt, %8, %3 : i32
      cf.cond_br %9, ^bb2, ^bb3
    ^bb2:  // pred: ^bb1
      %10 = llvm.sext %8 : i32 to i64
      %11 = builtin.unrealized_conversion_cast %10 : i64 to index
      %base_buffer, %offset, %sizes:2, %strides:2 = memref.extract_strided_metadata %arg0 : memref<4x64xf32, #hivm.address_space<ub>> -> memref<f32, #hivm.address_space<ub>>, index, index, index, index, index
      %c64 = arith.constant 64 : index
      %12 = arith.muli %11, %c64 : index
      %reinterpret_cast = memref.reinterpret_cast %base_buffer to offset: [%12], sizes: [64], strides: [1] : memref<f32, #hivm.address_space<ub>> to memref<64xf32, #map, #hivm.address_space<ub>>
      %13 = builtin.unrealized_conversion_cast %reinterpret_cast : memref<64xf32, #map, #hivm.address_space<ub>> to !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)>
      %14 = llvm.extractvalue %13[1] : !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)> 
      %15 = llvm.extractvalue %13[2] : !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)> 
      %16 = llvm.getelementptr %14[%15] : (!llvm.ptr<6>, i64) -> !llvm.ptr<6>, f32
      %17 = "hivm_regbaseintrins.intr.hivm.vldsx1.v64f32"(%16, %2, %2, %2) : (!llvm.ptr<6>, i32, i32, i32) -> vector<64xf32>
      %18 = "hivm_regbaseintrins.intr.hivm.pge.b32"(%2, %2) {mask_bit_width = 32 : i32} : (i32, i32) -> vector<256xi1>
      %19 = "hivm_regbaseintrins.intr.hivm.vadd.s.x"(%17, %7, %18) : (vector<64xf32>, vector<64xf32>, vector<256xi1>) -> vector<64xf32>
      %base_buffer_0, %offset_1, %sizes_2:2, %strides_3:2 = memref.extract_strided_metadata %arg2 : memref<4x64xf32, #hivm.address_space<ub>> -> memref<f32, #hivm.address_space<ub>>, index, index, index, index, index
      %c64_4 = arith.constant 64 : index
      %20 = arith.muli %11, %c64_4 : index
      %reinterpret_cast_5 = memref.reinterpret_cast %base_buffer_0 to offset: [%20], sizes: [64], strides: [1] : memref<f32, #hivm.address_space<ub>> to memref<64xf32, #map, #hivm.address_space<ub>>
      %21 = builtin.unrealized_conversion_cast %reinterpret_cast_5 : memref<64xf32, #map, #hivm.address_space<ub>> to !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)>
      %22 = "hivm_regbaseintrins.intr.hivm.pge.b32"(%2, %2) {mask_bit_width = 32 : i32} : (i32, i32) -> vector<256xi1>
      %23 = llvm.extractvalue %21[1] : !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)> 
      %24 = llvm.extractvalue %21[2] : !llvm.struct<(ptr<6>, ptr<6>, i64, array<1 x i64>, array<1 x i64>)> 
      %25 = llvm.getelementptr %23[%24] : (!llvm.ptr<6>, i64) -> !llvm.ptr<6>, f32
      "hivm_regbaseintrins.intr.hivm.vstsx1.v64f32"(%19, %25, %2, %0, %2, %22) : (vector<64xf32>, !llvm.ptr<6>, i32, i32, i32, vector<256xi1>) -> ()
      %26 = arith.addi %8, %4 overflow<nsw> : i32
      cf.br ^bb1(%26 : i32)
    ^bb3:  // pred: ^bb1
      return
    }
    func.func private @load_gm_to_ubuf_1d_float(memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, i32, f32, index, i32) attributes {hacc.function_kind = #hacc.function_kind<DEVICE>, hacc.noinline, hivm.func_core_type = #hivm.func_core_type<AIV>, hivm_regbaseintrins.target = #hivm_regbaseintrins.target<"dav-c310">, llvm.emit_c_interface}
    func.func private @store_ubuf_to_gm_1d_float(memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, i32) attributes {hacc.function_kind = #hacc.function_kind<DEVICE>, hacc.noinline, hivm.func_core_type = #hivm.func_core_type<AIV>, hivm_regbaseintrins.target = #hivm_regbaseintrins.target<"dav-c310">, llvm.emit_c_interface}
    func.func @main(%arg0: i64 {hacc.arg_type = #hacc.arg_type<ffts_base_address>}, %arg1: memref<?xi8, #hivm.address_space<gm>> {hacc.arg_type = #hacc.arg_type<sync_block_lock>}, %arg2: memref<?xi8, #hivm.address_space<gm>> {hacc.arg_type = #hacc.arg_type<workspace>}, %arg3: memref<?xf32, #hivm.address_space<gm>>, %arg4: memref<?xf32, #hivm.address_space<gm>>, %arg5: memref<?xf32, #hivm.address_space<gm>>, %arg6: i32, %arg7: i32, %arg8: i32, %arg9: i32, %arg10: i32, %arg11: i32) attributes {SyncBlockLockArgIdx = 0 : i64, WorkspaceArgIdx = 1 : i64, hacc.entry, hacc.function_kind = #hacc.function_kind<DEVICE>, hivm.func_core_type = #hivm.func_core_type<AIV>, hivm.vf_mode = #hivm.vf_mode<SIMD>, hivm_regbaseintrins.target = #hivm_regbaseintrins.target<"dav-c310">, mix_mode = "aiv"} {
      %0 = llvm.mlir.constant(0 : i64) : i64
      %1 = llvm.mlir.constant(1024 : i64) : i64
      %2 = llvm.mlir.constant(0 : i32) : i32
      %3 = llvm.mlir.constant(0.000000e+00 : f32) : f32
      %4 = llvm.mlir.constant(0 : index) : i64
      %5 = builtin.unrealized_conversion_cast %4 : i64 to index
      hivm.hir.set_ctrl false at ctrl[60]
      hivm.hir.set_ctrl true at ctrl[48]
      hivm.hir.set_ffts_base_addr %arg0
      %reinterpret_cast = memref.reinterpret_cast %arg4 to offset: [0], sizes: [1], strides: [1] : memref<?xf32, #hivm.address_space<gm>> to memref<1xf32, strided<[1]>, #hivm.address_space<gm>>
      %6 = hivm.hir.pointer_cast(%0) : memref<4x64xf32, #hivm.address_space<ub>>
      %base_buffer, %offset, %sizes, %strides = memref.extract_strided_metadata %arg3 : memref<?xf32, #hivm.address_space<gm>> -> memref<f32, #hivm.address_space<gm>>, index, index, index
      %reinterpret_cast_0 = memref.reinterpret_cast %base_buffer to offset: [0], sizes: [256], strides: [1] : memref<f32, #hivm.address_space<gm>> to memref<256xf32, strided<[1]>, #hivm.address_space<gm>>
      %base_buffer_1, %offset_2, %sizes_3:2, %strides_4:2 = memref.extract_strided_metadata %6 : memref<4x64xf32, #hivm.address_space<ub>> -> memref<f32, #hivm.address_space<ub>>, index, index, index, index, index
      %reinterpret_cast_5 = memref.reinterpret_cast %base_buffer_1 to offset: [0], sizes: [256], strides: [1] : memref<f32, #hivm.address_space<ub>> to memref<256xf32, #hivm.address_space<ub>>
      %cast = memref.cast %reinterpret_cast_0 : memref<256xf32, strided<[1]>, #hivm.address_space<gm>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>
      %cast_6 = memref.cast %reinterpret_cast_5 : memref<256xf32, #hivm.address_space<ub>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>
      call @load_gm_to_ubuf_1d_float(%cast, %cast_6, %2, %3, %5, %2) : (memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, i32, f32, index, i32) -> ()
      %7 = hivm.hir.pointer_cast(%1) : memref<1xf32, #hivm.address_space<ub>>
      %cast_7 = memref.cast %reinterpret_cast : memref<1xf32, strided<[1]>, #hivm.address_space<gm>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>
      %cast_8 = memref.cast %7 : memref<1xf32, #hivm.address_space<ub>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>
      call @load_gm_to_ubuf_1d_float(%cast_7, %cast_8, %2, %3, %5, %2) : (memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, i32, f32, index, i32) -> ()
      hivm.hir.set_flag[<PIPE_MTE2>, <PIPE_V>, <EVENT_ID0>]
      %8 = hivm.hir.pointer_cast(%0) : memref<4x64xf32, #hivm.address_space<ub>>
      hivm.hir.wait_flag[<PIPE_MTE2>, <PIPE_V>, <EVENT_ID0>]
      call @main_outlined_vf_0(%6, %7, %8) {hivm.vector_function, no_inline} : (memref<4x64xf32, #hivm.address_space<ub>>, memref<1xf32, #hivm.address_space<ub>>, memref<4x64xf32, #hivm.address_space<ub>>) -> ()
      hivm.hir.set_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      %base_buffer_9, %offset_10, %sizes_11:2, %strides_12:2 = memref.extract_strided_metadata %8 : memref<4x64xf32, #hivm.address_space<ub>> -> memref<f32, #hivm.address_space<ub>>, index, index, index, index, index
      %reinterpret_cast_13 = memref.reinterpret_cast %base_buffer_9 to offset: [0], sizes: [256], strides: [1] : memref<f32, #hivm.address_space<ub>> to memref<256xf32, #hivm.address_space<ub>>
      %base_buffer_14, %offset_15, %sizes_16, %strides_17 = memref.extract_strided_metadata %arg5 : memref<?xf32, #hivm.address_space<gm>> -> memref<f32, #hivm.address_space<gm>>, index, index, index
      %reinterpret_cast_18 = memref.reinterpret_cast %base_buffer_14 to offset: [0], sizes: [256], strides: [1] : memref<f32, #hivm.address_space<gm>> to memref<256xf32, strided<[1]>, #hivm.address_space<gm>>
      hivm.hir.wait_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      %cast_19 = memref.cast %reinterpret_cast_13 : memref<256xf32, #hivm.address_space<ub>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>
      %cast_20 = memref.cast %reinterpret_cast_18 : memref<256xf32, strided<[1]>, #hivm.address_space<gm>> to memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>
      call @store_ubuf_to_gm_1d_float(%cast_19, %cast_20, %2) : (memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<ub>>, memref<?xf32, strided<[?], offset: ?>, #hivm.address_space<gm>>, i32) -> ()
      hivm.hir.set_ctrl true at ctrl[60]
      hivm.hir.pipe_barrier[<PIPE_ALL>]
      return
    }
  }
}
