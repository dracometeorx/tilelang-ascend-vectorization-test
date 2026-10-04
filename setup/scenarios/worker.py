"""One isolated frontend invocation; preserve failures and intermediate IR."""
import argparse
import ast
import difflib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import traceback
from cases import CASES, source, fixture


def run(cmd, log):
    with log.open('w') as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True, timeout=180)


def compile_device(backend, p, metadata):
    if backend == 'ascendc':
        from tilelang.contrib.bisheng import compile_ascend
        (p/'kernel.aibin').write_bytes(compile_ascend((p/'kernel.asc').read_text(), target_format='aibin', npu_arch='dav-3510',
            options=['-I/workspace/tilelang/src','-g','--sysroot=/workspace/setup/cann/sysroot','--gcc-toolchain=/workspace/setup/cann/sysroot/usr']))
    elif backend == 'pto':
        from tilelang.jit.adapter.pto.libgen import PTOLibraryGenerator
        src=(p/'kernel.ptodsl.py').read_text()
        uses_helpers=any(isinstance(n, ast.Name) and n.id=='tl' for n in ast.walk(ast.parse(src)))
        if uses_helpers:
            # Never strip an import whose namespace is actually referenced.
            # Test the real pinned package and retain its concrete import error.
            import tilelang.contrib.ptodsl
            standalone=src
        else:
            standalone=src.replace('import tilelang.contrib.ptodsl as tl\n','')
        (p/'source-adaptation.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),standalone.splitlines(True),fromfile='generated',tofile='standalone')))
        PTOLibraryGenerator._compile_ptodsl_source_to_pto(standalone,[metadata['source_symbol']],p/'kernel.standalone.ptodsl.py',p/'kernel.pto')
        base=['ptoas',str(p/'kernel.pto'),'--pto-arch=a5','--pto-backend=vpto']
        for flag,out in [('--emit-vpto','kernel.vpto.mlir'),('--emit-vpto-llvm-ir','kernel.ll')]:
            run(base+[flag,'-o',str(p/out)],p/(out+'.log'))
        run(base+['-o',str(p/'kernel.fatobj.o')],p/'device-compile.log')
        run(['llvm-objcopy','--dump-section',f'__aicore_rel_binary={p}/device.section',str(p/'kernel.fatobj.o')],p/'extract.log')
        assert (p/'device.section').read_bytes()[:4]==b'\x7fELF'
        run(['ld.lld','-m','aicorelinux','-Ttext','0',str(p/'device.section'),'-o',str(p/'kernel.aibin')],p/'link.log')
    elif backend == 'npuir':
        mlir=(p/'kernel.mlir').read_text()
        signature=next(line for line in mlir.splitlines() if 'func.func @main(' in line)
        assert signature.count('memref<?xf32>')==3 and signature.count('memref<?xi8>')==2
        assert len(re.findall(r'%arg1\b',mlir))==1 and len(re.findall(r'%arg2\b',mlir))==1, 'Workspace/lock use requires a different runner'
        run(['bishengir-compile',str(p/'kernel.mlir'),'--enable-hivm-compile','--enable-simd-simt-mix-compile','--target=Ascend950PR_9589','--enable-tuning-mode',f'--save-temps={p}/temps','-o',str(p/'kernel.o')],p/'device-compile.log')
        (p/'kernel.aibin').write_bytes((p/'kernel.o').read_bytes())
    assert (p/'kernel.aibin').read_bytes()[:4]==b'\x7fELF'
    run(['llvm-objcopy','--dump-section',f'__CCE_KernelArgSize={p}/argsize.bin',str(p/'kernel.aibin')],p/'abi.log')
    size=int.from_bytes((p/'argsize.bin').read_bytes(),'little')
    assert size == (232 if backend=='npuir' else 8*len(metadata['arguments'])), f'Unsupported kernel argument size {size}'
    metadata['kernel_arg_bytes']=size


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True)
    parser.add_argument('--backend',required=True,choices=['cpu','ascendc','pto','npuir'])
    parser.add_argument('--mode',default='auto_simd')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--compile-only',action='store_true')
    args=parser.parse_args()
    p=args.out.resolve(); p.mkdir(parents=True,exist_ok=True)
    case=next(c for c in CASES if c['name']==args.case)
    result=dict(case=case,backend=args.backend,mode=args.mode,status='failed',stage='frontend_import')
    try:
        if args.compile_only:
            result=json.loads((p/'result.json').read_text())
            result.pop('error',None)
            result.update(status='failed',stage='device_compile')
            compile_device(args.backend,p,result)
            result.update(status='compiled',stage='device_compile')
            return
        if args.backend=='npuir':
            os.environ['TORCH_DEVICE_BACKEND_AUTOLOAD']='0'
            import torch
            spec=importlib.util.find_spec('torch_npu')
            spec.loader=importlib.util.LazyLoader(spec.loader)
            module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
            import tilelang
            import tilelang.language as T
            import tvm
        else:
            import torch
            import tilelang
            from tilelang import tvm
            if args.backend=='cpu': import tilelang.cpu.language as T
            else: import tilelang.ascend.language as T
        result['frontend_version']=tilelang.__version__
        result['stage']='parse'
        src=source(case,args.backend,args.mode)
        file=p/'workload.py'; file.write_text(src)
        namespace={'T':T,'__name__':'scenario_workload'}
        exec(compile(src,str(file),'exec'),namespace)
        func=namespace['main']; (p/'input.tir').write_text(func.script())
        result['stage']='lowering'
        if args.backend=='cpu':
            torch.set_num_threads(1)
            kernel=tilelang.compile(func,target='c',execution_backend='cython')
            a,b,expected=fixture(case)
            out=torch.full(case['out'],float('nan'))
            kernel(torch.tensor(a).reshape(case['a']),torch.tensor(b).reshape(case['b']),out)
            torch.testing.assert_close(out,torch.tensor(expected).reshape(case['out']),rtol=0,atol=0)
            (p/'kernel.cc').write_text(kernel.get_kernel_source())
            result.update(status='passed',stage='cpu_correctness')
            return
        @tvm.ir.instrument.pass_instrument
        class Capture:
            def __init__(self): self.passes=[]
            def run_after_pass(self,mod,info):
                name=f'{len(self.passes):03d}_{info.name}.tir'
                (p/name).write_text(mod.script()); self.passes.append(dict(name=info.name,file=name))
        capture=Capture()
        target='npuir' if args.backend=='npuir' else tvm.target.Target(dict(kind='ascend',arch='dav-3510',**({'keys':['pto','ascend']} if args.backend=='pto' else {})))
        with tilelang.transform.PassContext(instruments=[capture]):
            if args.backend=='npuir': artifact=tilelang.lower(func,target=target)
            else:
                with target:
                    artifact=tilelang.lower(func,target=target,enable_host_codegen=False,enable_device_compile=False)
        (p/'passes.json').write_text(json.dumps(capture.passes,indent=2))
        if args.backend=='npuir':
            assert isinstance(artifact,str)
            (p/'kernel.mlir').write_text(artifact)
            assert 'torch_npu._C' not in sys.modules
            result.update(status='lowered',symbol='main',abi='npuir')
        else:
            (p/('kernel.asc' if args.backend=='ascendc' else 'kernel.ptodsl.py')).write_text(artifact.kernel_source)
            (p/'device.tir').write_text(artifact.device_mod.script())
            symbols=[str(f.attrs['global_symbol']) for f in artifact.device_mod.functions.values()]
            assert len(symbols)==1
            params=[str(v.name) for f in artifact.device_mod.functions.values() for v in f.params]
            assert params in [['A','B','O'],['A','O'],['O']], params
            result['arguments']=params
            result.update(source_symbol=symbols[0],symbol=symbols[0]+('_mix_aiv' if args.backend=='pto' else ''),abi='pointers')
            result['stage']='device_compile'
            compile_device(args.backend,p,result)
            result['status']='compiled'
    except Exception:
        result['error']=traceback.format_exc()
        (p/'error.txt').write_text(result['error'])
        print(result['error'],file=sys.stderr)
    finally:
        if result['status']!='failed':
            result.pop('error',None)
            (p/'error.txt').unlink(missing_ok=True)
        (p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(args.case,args.backend,args.mode,result['status'],result['stage'],flush=True)
    if result['status']=='failed': sys.exit(1)

if __name__=='__main__': main()
