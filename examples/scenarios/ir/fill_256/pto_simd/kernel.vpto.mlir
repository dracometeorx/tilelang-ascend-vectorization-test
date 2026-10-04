module attributes {pto.backend = "vpto", pto.target_arch = "a5"} {
  module attributes {pto.backend = "vpto", pto.kernel_kind = #pto.kernel_kind<vector>, pto.target_arch = "a5"} {
    func.func @main_kernel(%arg0: !pto.ptr<f32, gm>) attributes {pto.entry, pto.kernel_kind = #pto.kernel_kind<vector>} {
      %c1_i16 = arith.constant 1 : i16
      %c4_i16 = arith.constant 4 : i16
      %c0_i16 = arith.constant 0 : i16
      %c281474976710656_i64 = arith.constant 281474976710656 : i64
      %c1152921504606846984_i64 = arith.constant 1152921504606846984 : i64
      %c36_i64 = arith.constant 36 : i64
      %c0_i64 = arith.constant 0 : i64
      %c0 = arith.constant 0 : index
      %cst = arith.constant 1.250000e+00 : f32
      %c64_i32 = arith.constant 64 : i32
      %c1_i64 = arith.constant 1 : i64
      %c1024_i64 = arith.constant 1024 : i64
      %c4_i64 = arith.constant 4 : i64
      %0 = pto.get_ctrl : i64
      %1 = arith.andi %0, %c281474976710656_i64 : i64
      %2 = arith.ori %1, %c1152921504606846984_i64 : i64
      pto.set_ctrl %2 : i64
      pto.set_loop_size_ubtoout %c1_i64, %c1_i64 : i64, i64
      pto.set_loop_size_outtoub %c1_i64, %c1_i64 : i64, i64
      pto.set_store_atomic_cfg %c36_i64 : i64
      %3 = pto.castptr %c0_i64 : i64 -> !pto.ptr<f32, ub>
      pto.vecscope {
        %4 = pto.pset_b32 "PAT_ALL" : !pto.mask<b32>
        %5 = pto.vdup %cst, %4 : f32, !pto.mask<b32> -> !pto.vreg<64xf32>
        scf.for %arg1 = %c0_i16 to %c4_i16 step %c1_i16  : i16 {
          %6 = arith.index_cast %arg1 : i16 to index
          %7 = arith.index_cast %6 : index to i32
          %8 = arith.muli %7, %c64_i32 : i32
          %9 = arith.index_cast %8 : i32 to index
          %10 = pto.addptr %3, %9 : <f32, ub> -> <f32, ub>
          pto.vsts %5, %10[%c0], %4 {dist = "NORM_B32"} : !pto.vreg<64xf32>, !pto.ptr<f32, ub>, !pto.mask<b32>
        }
      }
      pto.set_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      pto.wait_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      pto.copy_ubuf_to_gm %3, %arg0, %c0_i64, %c1_i64, %c1024_i64, %c4_i64, %c1024_i64, %c1024_i64 : !pto.ptr<f32, ub>, !pto.ptr<f32, gm>, i64, i64, i64, i64, i64, i64
      return
    }
  }
}

