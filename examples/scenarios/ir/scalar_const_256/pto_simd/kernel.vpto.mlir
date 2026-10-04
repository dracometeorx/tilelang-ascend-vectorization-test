module attributes {pto.backend = "vpto", pto.target_arch = "a5"} {
  module attributes {pto.backend = "vpto", pto.kernel_kind = #pto.kernel_kind<vector>, pto.target_arch = "a5"} {
    func.func @main_kernel(%arg0: !pto.ptr<f32, gm>, %arg1: !pto.ptr<f32, gm>) attributes {pto.entry, pto.kernel_kind = #pto.kernel_kind<vector>} {
      %c1_i16 = arith.constant 1 : i16
      %c4_i16 = arith.constant 4 : i16
      %c0_i16 = arith.constant 0 : i16
      %false = arith.constant false
      %c281474976710656_i64 = arith.constant 281474976710656 : i64
      %c1152921504606846984_i64 = arith.constant 1152921504606846984 : i64
      %c36_i64 = arith.constant 36 : i64
      %c0_i64 = arith.constant 0 : i64
      %c1_i64 = arith.constant 1 : i64
      %c1024_i64 = arith.constant 1024 : i64
      %c0 = arith.constant 0 : index
      %c64_i32 = arith.constant 64 : i32
      %cst = arith.constant 1.250000e+00 : f32
      %c256_i32 = arith.constant 256 : i32
      %c256 = arith.constant 256 : index
      %c4_i64 = arith.constant 4 : i64
      %0 = pto.get_ctrl : i64
      %1 = arith.andi %0, %c281474976710656_i64 : i64
      %2 = arith.ori %1, %c1152921504606846984_i64 : i64
      pto.set_ctrl %2 : i64
      pto.set_loop_size_ubtoout %c1_i64, %c1_i64 : i64, i64
      pto.set_loop_size_outtoub %c1_i64, %c1_i64 : i64, i64
      pto.set_store_atomic_cfg %c36_i64 : i64
      %3 = pto.castptr %c0_i64 : i64 -> !pto.ptr<ui8, ub>
      %4 = pto.castptr %arg0 : !pto.ptr<f32, gm> -> !pto.ptr<ui8, gm>
      %5 = pto.castptr %3 : !pto.ptr<ui8, ub> -> !pto.ptr<f32, ub>
      %6 = pto.castptr %5 : !pto.ptr<f32, ub> -> !pto.ptr<ui8, ub>
      pto.copy_gm_to_ubuf %4, %6, %c0_i64, %c1_i64, %c1024_i64, %c0_i64, %c0_i64, %false, %c0_i64, %c1024_i64, %c1024_i64 : !pto.ptr<ui8, gm>, !pto.ptr<ui8, ub>, i64, i64, i64, i64, i64, i1, i64, i64, i64
      pto.set_flag[<PIPE_MTE2>, <PIPE_V>, <EVENT_ID0>]
      pto.wait_flag[<PIPE_MTE2>, <PIPE_V>, <EVENT_ID0>]
      pto.vecscope {
        %8 = pto.pset_b32 "PAT_ALL" : !pto.mask<b32>
        %9 = pto.vdup %cst, %8 : f32, !pto.mask<b32> -> !pto.vreg<64xf32>
        scf.for %arg2 = %c0_i16 to %c4_i16 step %c1_i16  : i16 {
          %10 = arith.index_cast %arg2 : i16 to index
          %11 = arith.index_cast %10 : index to i32
          %12 = arith.muli %11, %c64_i32 : i32
          %13 = arith.index_cast %12 : i32 to index
          %14 = pto.addptr %5, %13 : <f32, ub> -> <f32, ub>
          %result = pto.vlds %14[%c0] : !pto.ptr<f32, ub> -> !pto.vreg<64xf32>
          %15 = arith.addi %12, %c256_i32 : i32
          %16 = arith.index_cast %15 : i32 to index
          %17 = pto.addptr %5, %16 : <f32, ub> -> <f32, ub>
          %18 = pto.vadd %result, %9, %8 : !pto.vreg<64xf32>, !pto.vreg<64xf32>, !pto.mask<b32> -> !pto.vreg<64xf32>
          pto.vsts %18, %17[%c0], %8 {dist = "NORM_B32"} : !pto.vreg<64xf32>, !pto.ptr<f32, ub>, !pto.mask<b32>
        }
      }
      pto.set_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      pto.wait_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      %7 = pto.addptr %5, %c256 : <f32, ub> -> <f32, ub>
      pto.copy_ubuf_to_gm %7, %arg1, %c0_i64, %c1_i64, %c1024_i64, %c4_i64, %c1024_i64, %c1024_i64 : !pto.ptr<f32, ub>, !pto.ptr<f32, gm>, i64, i64, i64, i64, i64, i64
      return
    }
  }
}

