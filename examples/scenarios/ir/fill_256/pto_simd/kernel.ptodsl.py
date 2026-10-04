from ptodsl import pto
import tilelang.contrib.ptodsl as tl

@pto.jit(name="main_kernel", kernel_kind="vector", target="a5", mode="explicit")
def main_kernel(O: pto.ptr(pto.f32, "gm")):
  pto.init_core()
  bx = pto.cast(pto.get_block_idx(), pto.i32)
  o = pto.castptr(pto.const(0, dtype=pto.i64), pto.ptr(pto.f32, "ub"))
  with pto.vecscope():
    for _tl_range_vchunk in range(0, 4, 1):
      vchunk = pto.cast(_tl_range_vchunk, pto.i32)
      pto.vsts(pto.vdup(pto.const(float.fromhex('0x1.4p+0'), dtype=pto.f32), pto.pset_b32("PAT_ALL")), pto.addptr(o, vchunk * 64), pto.const(0), pto.pset_b32("PAT_ALL"), dist="NORM_B32")
  pto.set_flag("V", "MTE3", event_id=0)
  pto.wait_flag("V", "MTE3", event_id=0)
  pto.mte_ub_gm(o, O, 1024, nburst=(1, 1024, 1024), l2_cache="naci")

