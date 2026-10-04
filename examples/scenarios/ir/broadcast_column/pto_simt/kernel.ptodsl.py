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
  with pto.simt(128, 1, 1):
    simtvf_tx = pto.get_tid_x()
    simtvf_ty = pto.get_tid_y()
    simtvf_tz = pto.get_tid_z()
    pto.store(pto.load(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), simtvf_tx * 2, contiguous=2) + pto.Vec(pto.f32, 2, init=pto.load(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), (simtvf_tx >> 5) + 512)), pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), (simtvf_tx * 2) + 256, contiguous=2)
  pto.set_flag("V", "MTE3", event_id=0)
  pto.wait_flag("V", "MTE3", event_id=0)
  pto.mte_ub_gm(pto.addptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), 256), O, 1024, nburst=(1, 1024, 1024), l2_cache="naci")

