module attributes {pto.backend = "vpto", pto.target_arch = "a5"} {
  module attributes {pto.backend = "vpto", pto.kernel_kind = #pto.kernel_kind<vector>, pto.target_arch = "a5"} {
    func.func @main_kernel(%arg0: !pto.ptr<f32, gm>) attributes {pto.entry, pto.kernel_kind = #pto.kernel_kind<vector>} {
      %c1_i32 = arith.constant 1 : i32
      %c128_i32 = arith.constant 128 : i32
      %c36_i64 = arith.constant 36 : i64
      %c1152921504606846984_i64 = arith.constant 1152921504606846984 : i64
      %c281474976710656_i64 = arith.constant 281474976710656 : i64
      %c4_i64 = arith.constant 4 : i64
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
      %3 = pto.castptr %c0_i64 : i64 -> !pto.ptr<f32, ub>
      pto.store_vfsimt_info %c1_i32, %c1_i32, %c128_i32 : i32, i32, i32
      call @main_kernel_simt_0(%3) : (!pto.ptr<f32, ub>) -> ()
      pto.set_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      pto.wait_flag[<PIPE_V>, <PIPE_MTE3>, <EVENT_ID0>]
      pto.copy_ubuf_to_gm %3, %arg0, %c0_i64, %c1_i64, %c1024_i64, %c4_i64, %c1024_i64, %c1024_i64 : !pto.ptr<f32, ub>, !pto.ptr<f32, gm>, i64, i64, i64, i64, i64, i64
      return
    }
    func.func private @main_kernel_simt_0(%arg0: !pto.ptr<f32, ub>) attributes {pto.simt_entry, pto.simt_max_threads = 128 : i32} {
      %c2_i32 = arith.constant 2 : i32
      %c4 = arith.constant 4 : index
      %c0 = arith.constant 0 : index
      %cst = arith.constant dense<1.250000e+00> : vector<2xf32>
      %0 = pto.get_tid_x : i32
      %1 = arith.muli %0, %c2_i32 : i32
      %2 = arith.index_cast %1 : i32 to index
      %3 = pto.castptr %arg0 : !pto.ptr<f32, ub> -> i64
      %4 = arith.muli %2, %c4 : index
      %5 = arith.index_cast %4 : index to i64
      %6 = arith.addi %3, %5 : i64
      %7 = pto.castptr %6 : i64 -> !pto.ptr<vector<2xf32>, ub>
      pto.store %cst, %7[%c0] : !pto.ptr<vector<2xf32>, ub>, vector<2xf32>
      return
    }
  }
}

