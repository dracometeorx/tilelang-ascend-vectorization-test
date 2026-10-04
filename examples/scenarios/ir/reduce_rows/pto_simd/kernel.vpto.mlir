module attributes {pto.backend = "vpto", pto.target_arch = "a5"} {
  module attributes {pto.backend = "vpto", pto.kernel_kind = #pto.kernel_kind<vector>, pto.target_arch = "a5"} {
    func.func @main_kernel(%arg0: !pto.ptr<f32, gm>, %arg1: !pto.ptr<f32, gm>) attributes {pto.entry, pto.kernel_kind = #pto.kernel_kind<vector>} {
      %c64_i16 = arith.constant 64 : i16
      %c1_i16 = arith.constant 1 : i16
      %c4_i16 = arith.constant 4 : i16
      %c0_i16 = arith.constant 0 : i16
      %false = arith.constant false
      %c36_i64 = arith.constant 36 : i64
      %c1152921504606846984_i64 = arith.constant 1152921504606846984 : i64
      %c281474976710656_i64 = arith.constant 281474976710656 : i64
      %c4_i64 = arith.constant 4 : i64
      %c16_i64 = arith.constant 16 : i64
      %c256 = arith.constant 256 : index
      %c64_i32 = arith.constant 64 : i32
      %cst = arith.constant 0.000000e+00 : f32
      %c256_i32 = arith.constant 256 : i32
      %c1024_i64 = arith.constant 1024 : i64
      %c1_i64 = arith.constant 1 : i64
      %c0_i64 = arith.constant 0 : i64
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
        scf.for %arg2 = %c0_i16 to %c4_i16 step %c1_i16  : i16 {
          %8 = arith.index_cast %arg2 : i16 to index
          %9 = arith.index_cast %8 : index to i32
          %10 = arith.addi %9, %c256_i32 : i32
          %11 = arith.index_castui %10 : i32 to index
          pto.store %cst, %5[%11] : !pto.ptr<f32, ub>, f32
          %12 = arith.muli %9, %c64_i32 : i32
          scf.for %arg3 = %c0_i16 to %c64_i16 step %c1_i16  : i16 {
            %13 = arith.index_cast %arg3 : i16 to index
            %14 = arith.index_cast %13 : index to i32
            %15 = pto.load %5[%11] : !pto.ptr<f32, ub> -> f32
            %16 = arith.addi %12, %14 : i32
            %17 = arith.index_castui %16 : i32 to index
            %18 = pto.load %5[%17] : !pto.ptr<f32, ub> -> f32
            %19 = arith.addf %15, %18 : f32
            pto.store %19, %5[%11] : !pto.ptr<f32, ub>, f32
          }
        }
      }
      pto.set_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      pto.wait_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      %7 = pto.addptr %5, %c256 : <f32, ub> -> <f32, ub>
      pto.copy_ubuf_to_gm %7, %arg1, %c0_i64, %c1_i64, %c16_i64, %c4_i64, %c16_i64, %c16_i64 : !pto.ptr<f32, ub>, !pto.ptr<f32, gm>, i64, i64, i64, i64, i64, i64
      return
    }
  }
}

