from ptodsl import pto
import tilelang.contrib.ptodsl as tl

@pto.jit(name="main_kernel", kernel_kind="vector", target="a5", mode="explicit")
def main_kernel(O: pto.ptr(pto.f32, "gm")):
  pto.init_core()
  bx = pto.cast(pto.get_block_idx(), pto.i32)
  o = pto.castptr(pto.const(0, dtype=pto.i64), pto.ptr(pto.f32, "ub"))
  with pto.simt(128, 1, 1):
    simtvf_tx = pto.get_tid_x()
    simtvf_ty = pto.get_tid_y()
    simtvf_tz = pto.get_tid_z()
    broadcast_var = float.fromhex('0x1.4p+0')
    pto.store(pto.Vec(pto.f32, 2, init=broadcast_var), o, simtvf_tx * 2, contiguous=2)
  pto.set_flag("V", "MTE3", event_id=0)
  pto.wait_flag("V", "MTE3", event_id=0)
  pto.mte_ub_gm(o, O, 1024, nburst=(1, 1024, 1024), l2_cache="naci")

