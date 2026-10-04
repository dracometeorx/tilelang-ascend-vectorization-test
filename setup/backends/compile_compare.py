"""Export genuine TileLang PTO and NPU-IR lowering artifacts for small FP32 adds."""
import ast
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, '/workspace/setup/tilelang')
from add_lab import ascend_add, Capture
import tilelang
from tilelang import tvm
from tilelang.jit.adapter.pto.libgen import PTOLibraryGenerator

ROOT = Path('/workspace/setup/tilelang/results')

def run(cmd, log):
    with log.open('w') as stream:
        subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=180)

def main():
    cases = []
    for shape in [(256,), (4, 64)]:
        label = 'x'.join(map(str, shape))
        for mode in ['simt', 'simd']:
            p = ROOT/'pto_probe'/f'{label}_{mode}'
            p.mkdir(parents=True, exist_ok=True)
            target = tvm.target.Target({'kind':'ascend', 'arch':'dav-3510', 'keys':['pto','ascend']})
            capture = Capture(p)
            func = ascend_add(shape, mode)
            (p/'input.tir').write_text(func.script())
            with target, tilelang.transform.PassContext(instruments=[capture]):
                artifact = tilelang.lower(func, target=target, enable_host_codegen=False, enable_device_compile=False)
            source = artifact.kernel_source
            (p/'kernel.ptodsl.py').write_text(source)
            (p/'device.tir').write_text(artifact.device_mod.script())
            (p/'passes.json').write_text(json.dumps(capture.passes, indent=2))
            # This checkout imports private PTODSL helpers that changed upstream.
            # These four adds use none. Preserve the original source and fail if
            # any helper is referenced; only omit its unused import downstream.
            assert not any(isinstance(n, ast.Name) and n.id == 'tl' for n in ast.walk(ast.parse(source)))
            standalone = source.replace('import tilelang.contrib.ptodsl as tl\n', '')
            (p/'source-adaptation.diff').write_text(''.join(difflib.unified_diff(
                source.splitlines(True), standalone.splitlines(True), fromfile='generated', tofile='standalone')))
            PTOLibraryGenerator._compile_ptodsl_source_to_pto(standalone, ['main_kernel'], p/'kernel.standalone.ptodsl.py', p/'kernel.pto')
            base = ['ptoas', str(p/'kernel.pto'), '--pto-arch=a5', '--pto-backend=vpto']
            for flag, out in [('--emit-vpto', 'kernel.vpto.mlir'), ('--emit-vpto-llvm-ir','kernel.ll')]:
                run(base + [flag, '-o', str(p/out)], p/(out+'.log'))
            run(base + ['-o', str(p/'kernel.fatobj.o'), '--mlir-print-ir-after-all', '--mlir-print-ir-after-change'], p/'compile-passes.log')
            # PTOAS embeds the actual relocatable CCE ELF as this ELF section.
            run(['llvm-objcopy', '--dump-section', f'__aicore_rel_binary={p}/device.section', str(p/'kernel.fatobj.o')], p/'extract.log')
            assert (p/'device.section').read_bytes()[:4] == b'\x7fELF'
            run(['ld.lld','-m','aicorelinux','-Ttext','0', str(p/'device.section'), '-o', str(p/'kernel.aibin')], p/'link.log')
            cases.append({'backend':'pto','mode':mode,'shape':shape,'directory':str(p),'binary':str(p/'kernel.aibin'),'symbol':'main_kernel_mix_aiv','abi':'three_gm_pointers'})
            print('COMPILED PTO', label, mode, flush=True)

        p = ROOT/'npuir'/label
        assert (p/'kernel.mlir').is_file(), 'Run npuir_add_lab.py in the isolated frontend venv first'
        base = ['bishengir-compile', str(p/'kernel.mlir'), '--enable-hivm-compile', '--enable-simd-simt-mix-compile', '--target=Ascend950PR_9589', '--enable-tuning-mode']
        run(base + [f'--save-temps={p}/temps', '-o', str(p/'kernel.o'), '--mlir-disable-threading', '--mlir-print-ir-after-all', '--mlir-print-ir-after-change'], p/'compile-passes.log')
        assert (p/'kernel.o').read_bytes()[:4] == b'\x7fELF'
        cases.append({'backend':'npuir','mode':'auto_simd','shape':shape,'directory':str(p),'binary':str(p/'kernel.o'),'symbol':'main','abi':'npuir_232_byte_memref_descriptors'})
        print('COMPILED NPU-IR', label, flush=True)
    (ROOT/'backend-cases.json').write_text(json.dumps(cases, indent=2))

if __name__ == '__main__':
    main()
