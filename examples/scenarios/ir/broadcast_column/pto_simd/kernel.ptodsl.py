from ptodsl import pto
import tilelang.contrib.ptodsl as tl

@pto.jit(name="main_kernel", kernel_kind="vector", target="a5", mode="explicit")
def main_kernel(A: pto.ptr(pto.f32, "gm"), B: pto.ptr(pto.f32, "gm"), O: pto.ptr(pto.f32, "gm")):
  pto.init_core()
  bx = pto.cast(pto.get_block_idx(), pto.i32)
  buf_dyn_shmem = pto.castptr(pto.const(0, dtype=pto.i64), pto.ptr(pto.ui8, "ub"))
  pto.mte_gm_ub(pto.castptr(A, pto.ptr(pto.ui8, "gm")), pto.castptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), pto.ptr(pto.ui8, "ub")), 0, 1024, nburst=(1, 1024, 1024))
  pto.mte_gm_ub(pto.castptr(B, pto.ptr(pto.ui8, "gm")), pto.castptr(pto.addptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), 512), pto.ptr(pto.ui8, "ub")), 0, 16, nburst=(1, 16, 16))
  pto.set_flag("MTE2", "V", event_id=0)
  pto.wait_flag("MTE2", "V", event_id=0)
  with pto.vecscope():
    for _tl_range_vserial in range(0, 4, 1):
      vserial = pto.cast(_tl_range_vserial, pto.i32)
      vreg_1 = pto.vlds(pto.addptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), vserial + 512), pto.const(0), pto.vreg_type(64, pto.f32), dist="BRC_B32")
      vreg_0 = pto.vlds(pto.addptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), vserial * 64), pto.const(0), pto.vreg_type(64, pto.f32))
      vreg_2 = pto.vadd(vreg_0, vreg_1, pto.pset_b32("PAT_ALL"))
      pto.vsts(vreg_2, pto.addptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), (vserial * 64) + 256), pto.const(0), pto.pset_b32("PAT_ALL"), dist="NORM_B32")
  pto.set_flag("V", "MTE3", event_id=0)
  pto.wait_flag("V", "MTE3", event_id=0)
  pto.mte_ub_gm(pto.addptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), 256), O, 1024, nburst=(1, 1024, 1024), l2_cache="naci")

