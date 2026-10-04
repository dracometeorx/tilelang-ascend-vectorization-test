from ptodsl import pto
import tilelang.contrib.ptodsl as tl

@pto.jit(name="main_kernel", kernel_kind="vector", target="a5", mode="explicit")
def main_kernel(A: pto.ptr(pto.f32, "gm"), O: pto.ptr(pto.f32, "gm")):
  pto.init_core()
  bx = pto.cast(pto.get_block_idx(), pto.i32)
  buf_dyn_shmem = pto.castptr(pto.const(0, dtype=pto.i64), pto.ptr(pto.ui8, "ub"))
  pto.mte_gm_ub(pto.castptr(A, pto.ptr(pto.ui8, "gm")), pto.castptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), pto.ptr(pto.ui8, "ub")), 0, 1024, nburst=(1, 1024, 1024))
  pto.set_flag("MTE2", "V", event_id=0)
  pto.wait_flag("MTE2", "V", event_id=0)
  with pto.vecscope():
    pto.store(float.fromhex('0x0p+0'), pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), 256)
    for _tl_range_k in range(0, 256, 1):
      k = pto.cast(_tl_range_k, pto.i32)
      pto.store(pto.load(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), 256) + pto.load(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), k), pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), 256)
  pto.set_flag("V", "MTE3", event_id=0)
  pto.wait_flag("V", "MTE3", event_id=0)
  pto.mte_ub_gm(pto.addptr(pto.castptr(buf_dyn_shmem, pto.ptr(pto.f32, "ub")), 256), O, 4, nburst=(1, 4, 4), l2_cache="naci")

