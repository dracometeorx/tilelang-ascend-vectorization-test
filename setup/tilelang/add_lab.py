"""CPU correctness and real Ascend lowering; no NPU simulation is claimed.

Run after sourcing activate.sh. Outputs IR, AscendC, and compiler cost estimates.
"""
import argparse
import difflib
import html
import json
import re
import time
from pathlib import Path

import torch
import tilelang
import tilelang.ascend.language as T
import tilelang.cpu.language as C
from tilelang import tvm
from tvm import tirx


def ascend_add(shape, mode):
    @T.prim_func
    def main(A: T.Tensor(shape, "float32"), B: T.Tensor(shape, "float32"), O: T.Tensor(shape, "float32")):
        with T.Kernel(1):
            a = T.alloc_shared(shape, "float32")
            b = T.alloc_shared(shape, "float32")
            o = T.alloc_shared(shape, "float32")
            T.copy(A, a)
            T.copy(B, b)
            if mode == "simt":
                with T.SimtVF(threads=128):
                    if len(shape) == 1:
                        for i in T.Parallel(shape[0]):
                            o[i] = a[i] + b[i]
                    else:
                        for i, j in T.Parallel(shape[0], shape[1]):
                            o[i, j] = a[i, j] + b[i, j]
            else:
                with T.SimdVF():
                    if len(shape) == 1:
                        for i in T.Parallel(shape[0]):
                            o[i] = a[i] + b[i]
                    else:
                        for i, j in T.Parallel(shape[0], shape[1]):
                            o[i, j] = a[i, j] + b[i, j]
            T.copy(o, O)
    return main


def cpu_add(shape):
    @C.prim_func
    def main(A: C.Tensor(shape, "float32"), B: C.Tensor(shape, "float32"), O: C.Tensor(shape, "float32")):
        with C.Kernel(1):
            if len(shape) == 1:
                for i in C.Parallel(shape[0]):
                    O[i] = A[i] + B[i]
            else:
                for i, j in C.Parallel(shape[0], shape[1]):
                    O[i, j] = A[i, j] + B[i, j]
    return main


@tvm.ir.instrument.pass_instrument
class Capture:
    def __init__(self, output):
        self.output = output
        self.passes = []
        self.tasks = []

    def run_after_pass(self, mod, info):
        name = str(info.name)
        filename = f"{len(self.passes):03d}_{re.sub(r'[^A-Za-z0-9_.-]', '_', name)}.tir"
        (self.output / filename).write_text(mod.script())
        self.passes.append({"pass": name, "file": filename})
        if name == "tl.EstimateLatency":
            def visit(node):
                if isinstance(node, tirx.AttrStmt) and node.attr_key == "tl.ascend_task":
                    self.tasks.append({str(k): str(v) for k, v in node.node.items()})
            for func in mod.functions.values():
                if isinstance(func, tirx.PrimFunc):
                    tirx.stmt_functor.post_order_visit(func.body, visit)


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    torch.set_num_threads(1)
    results = {
        "tilelang_version": tilelang.__version__,
        "target": {"kind": "ascend", "arch": "dav-3510"},
        "simulation_status": "This file covers host checks only. See simulation-summary.json for separate vendor A5 simulation results.",
        "timing_note": "CPU times are host wall-clock only; task latency/II are compiler estimates, not simulated profiling.",
        "cases": [],
    }
    for shape in [(256,), (4, 64)]:
        label = "x".join(map(str, shape))
        kernel = tilelang.compile(cpu_add(shape), target="c", execution_backend="cython")
        a, b = torch.randn(shape), torch.randn(shape)
        out = torch.full(shape, float("nan"))
        kernel(a, b, out)
        torch.testing.assert_close(out, a + b, rtol=0, atol=0)
        for _ in range(10):
            kernel(a, b, out)
        start = time.perf_counter_ns()
        for _ in range(100):
            kernel(a, b, out)
        cpu_us = (time.perf_counter_ns() - start) / 100 / 1000
        case = {"shape": shape, "cpu_correct": True, "cpu_call_us": cpu_us, "paths": {}}
        (output / f"cpu_{label}.cc").write_text(kernel.get_kernel_source())
        for mode in ["simt", "simd"]:
            directory = output / f"{label}_{mode}"
            directory.mkdir(exist_ok=True)
            func = ascend_add(shape, mode)
            (directory / "input.tir").write_text(func.script())
            capture = Capture(directory)
            target = tvm.target.Target({"kind": "ascend", "arch": "dav-3510"})
            with target, tilelang.transform.PassContext(instruments=[capture]):
                artifact = tilelang.lower(func, target=target, enable_host_codegen=False, enable_device_compile=False)
            (directory / "device.tir").write_text(artifact.device_mod.script())
            (directory / "kernel.asc").write_text(artifact.kernel_source)
            (directory / "passes.json").write_text(json.dumps(capture.passes, indent=2))
            assert capture.passes, "No lowering passes captured"
            assert capture.tasks, "No compiler task costs captured"
            if mode == "simd":
                assert "vadd" in artifact.kernel_source, "SIMD addition was not emitted"
            symbols = [str(f.attrs["global_symbol"]) for f in artifact.device_mod.functions.values()]
            assert len(symbols) == 1, symbols
            case["paths"][mode] = {"lowering": "passed", "symbol": symbols[0], "passes": len(capture.passes), "estimated_tasks": capture.tasks}
        for name in ["device.tir", "kernel.asc"]:
            left = (output / f"{label}_simt" / name).read_text().splitlines(True)
            right = (output / f"{label}_simd" / name).read_text().splitlines(True)
            (output / f"{label}_{name}.diff").write_text("".join(difflib.unified_diff(left, right, fromfile="SIMT", tofile="SIMD")))
            comparison = difflib.HtmlDiff(wrapcolumn=100).make_file(
                left, right, fromdesc=f"SIMT {html.escape(name)}", todesc=f"SIMD {html.escape(name)}"
            )
            (output / f"{label}_{name}.html").write_text(comparison)
        results["cases"].append(case)
    (output / "report.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("/workspace/setup/tilelang/results"))
    run(parser.parse_args().out)
