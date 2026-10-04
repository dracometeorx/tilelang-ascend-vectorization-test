"""CPU-only NPU-IR lowering, based on upstream example_elementwise_add.py.

The real torch_npu package is lazy-loaded: pure lowering does not need its
hardware runtime. No compiler module is replaced and no NPU execution is claimed.
"""
import os
os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
os.environ.setdefault("TEST_DATA_ROOT_PATH", "/workspace/.cache/tvm-test-data")
os.environ.setdefault("TILELANG_CACHE_DIR", "/workspace/.cache/tilelang-npuir")
os.environ["TILELANG_ASCEND_DEVICE_NAME"] = "Ascend950"
os.environ["TILELANG_ASCEND_MODE"] = "Developer"

import torch
import importlib.util
import sys
from pathlib import Path
import json

spec = importlib.util.find_spec("torch_npu")
spec.loader = importlib.util.LazyLoader(spec.loader)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

import tilelang
import tilelang.language as T
import tvm

RESULTS = Path("/workspace/setup/tilelang/results/npuir")

def add(shape):
    @T.prim_func
    def main(A: T.Tensor(shape, "float32"), B: T.Tensor(shape, "float32"), O: T.Tensor(shape, "float32")):
        with T.Kernel(1, is_npu=True):
            a = T.alloc_shared(shape, "float32")
            b = T.alloc_shared(shape, "float32")
            o = T.alloc_shared(shape, "float32")
            T.copy(A, a)
            T.copy(B, b)
            if len(shape) == 1:
                for i in T.Parallel(shape[0]):
                    o[i] = a[i] + b[i]
            else:
                for i, j in T.Parallel(shape[0], shape[1]):
                    o[i, j] = a[i, j] + b[i, j]
            T.copy(o, O)
    return main

@tvm.ir.instrument.pass_instrument
class Capture:
    def __init__(self, path):
        self.path = path
        self.passes = []

    def run_after_pass(self, mod, info):
        name = f"{len(self.passes):03d}_{info.name}"
        (self.path / f"{name}.tir").write_text(mod.script())
        self.passes.append(info.name)

def main():
    summary = {"tilelang": tilelang.__version__, "target": "npuir", "requested_device": "Ascend950", "mode": "Developer", "frontend_arch_note": "Release wheel AscendArch allowlist omits Ascend950 and falls back to Ascend910B; in this FP32 lowering the helper is consulted only for BF16 legalization. Device selection is performed by downstream bishengir-compile.", "torch_npu_loading": "real module deferred with importlib LazyLoader; hardware runtime not executed", "cases": []}
    for shape in [(256,), (4, 64)]:
        path = RESULTS / "x".join(map(str, shape))
        path.mkdir(parents=True, exist_ok=True)
        func = add(shape)
        (path / "input.tir").write_text(func.script())
        capture = Capture(path)
        with tilelang.transform.PassContext(instruments=[capture]):
            mlir = tilelang.lower(func, target="npuir")
        assert isinstance(mlir, str)
        assert "hivm.hir.vadd" in mlir or "hfusion.add" in mlir, mlir
        (path / "kernel.mlir").write_text(mlir)
        (path / "passes.json").write_text(json.dumps(capture.passes, indent=2))
        summary["cases"].append({"shape": shape, "pass_count": len(capture.passes), "mlir": str(path / "kernel.mlir")})
        print("LOWERED", shape, path / "kernel.mlir")
    assert "torch_npu._C" not in sys.modules, "Pure lowering unexpectedly loaded NPU runtime"
    summary["torch_npu_native_loaded"] = False
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
