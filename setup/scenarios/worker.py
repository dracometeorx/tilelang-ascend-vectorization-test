"""One isolated frontend invocation; preserve failures and intermediate IR."""
import argparse
import ast
import difflib
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import traceback
from cases import CASES, source, fixture


def run(cmd, log):
    with log.open('w') as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True, timeout=180)


def npuir_provenance(tilelang, tvm, expected_root=None):
    root=Path(tilelang.__file__).resolve().parent.parent
    library=Path(tilelang._LIB_PATH).resolve()
    tvm_library=Path(tvm._ffi.base._LIB._name).resolve()
    data=dict(frontend_import_path=str(Path(tilelang.__file__).resolve()),
        frontend_library_path=str(library),
        frontend_library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
        tvm_import_path=str(Path(tvm.__file__).resolve()),
        tvm_library_path=str(tvm_library),
        tvm_library_sha256=hashlib.sha256(tvm_library.read_bytes()).hexdigest(),
        tilelang_enable_simt=os.environ.get('TILELANG_ENABLE_SIMT'))
    if expected_root is not None:
        expected_root=expected_root.resolve()
        assert root==expected_root, f'Unexpected frontend source: {root}'
        assert library.is_relative_to(root/'build'), f'Unexpected compiler library: {library}'
        assert tvm_library.is_relative_to(root/'build'), f'Unexpected TVM library: {tvm_library}'
        assert Path(tvm.__file__).resolve().is_relative_to(root/'3rdparty/tvm/python'), 'Unexpected TVM Python source'
        assert os.environ.get('TILELANG_ENABLE_SIMT')=='0', 'New comparison requires explicit SIMD selection'
        data['source_commit']=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        assert data['source_commit']=='013dbbf5824c3ac29e975d78c0b38e60b2410be7'
        data['tvm_source_commit']=subprocess.check_output(['git','-C',str(root/'3rdparty/tvm'),'rev-parse','HEAD'],text=True).strip()
        assert data['tvm_source_commit']=='c2921fdaf795b1103d21abc962e83a209c7258d7'
        data['source_changes']=subprocess.check_output(['git','-C',str(root),'diff','--name-only','--ignore-submodules=all','HEAD'],text=True).splitlines()
        assert not data['source_changes'], 'Pinned frontend has tracked source changes'
        adapter=importlib.import_module('tilelang.tladapter')
        data['native_adapter_loaded']=getattr(adapter,'_native',None) is not None
        helper=root/'build/libtilelangir.so'
        data['native_adapter_library_path']=str(helper)
        data['native_adapter_library_sha256']=hashlib.sha256(helper.read_bytes()).hexdigest()
    return data


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
        new_a5=metadata['abi']=='npuir_a5'
        indices=(0,1) if new_a5 else (1,2)
        for i in indices:
            assert len(re.findall(r'%arg'+str(i)+r'\b',mlir))==1, 'Workspace/lock use requires a different runner'
        if new_a5:
            assert signature.count(': i32')==6 and 'ffts_base_address' not in signature
            flags=['--target=Ascend950PR_9589','--enable-auto-multi-buffer=true',
                   '--disable-ffts','--enable-triton-kernel-compile=true',
                   '--enable-hivm-compile=true','--enable-vf-merge-level=1',
                   '--enable-hfusion-compile=true','--enable-auto-bind-sub-block=true']
        else:
            flags=['--enable-hivm-compile','--enable-simd-simt-mix-compile',
                   '--target=Ascend950PR_9589','--enable-tuning-mode']
        compiler=Path(shutil.which('bishengir-compile')).resolve()
        command=[str(compiler),str(p/'kernel.mlir')]+flags+[f'--save-temps={p}/temps','-o',str(p/'kernel.o')]
        metadata['device_compiler']=dict(path=str(compiler),sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
            version=subprocess.check_output([str(compiler),'--version'],text=True).strip(),command=command)
        (p/'device-command.json').write_text(json.dumps(metadata['device_compiler'],indent=2)+'\n')
        run(command,p/'device-compile.log')
        if new_a5:
            optimized=(p/'temps/module.hivm.opt.mlir').read_text()
            entry=optimized[optimized.index('  func.func @main('):].split('\n  }',1)[0]
            entry_signature=entry.splitlines()[0]
            assert entry_signature.count('memref<?xf32,')==3
            assert entry_signature.count('memref<?xi8,')==2
            assert entry_signature.count(': i32')==3 and 'hacc.entry' in entry_signature
            assert 'memref.memref_as_ptr' in optimized and 'func_dyn_memref_args' in entry_signature
            for i in (0,1):
                assert len(re.findall(r'%arg'+str(i)+r'\b',entry))==1, 'Optimized kernel uses workspace/lock'
            metadata['launch']=dict(api='rtKernelLaunchWithFlagV2',local_memory_bytes=221184,
                grid=[1,1,1],sync_lock=None,workspace=None,
                layout=['lock:pointer','workspace:pointer','A:pointer','B:pointer','O:pointer',
                        'grid_x:i32','grid_y:i32','grid_z:i32','padding:i32'])
            (p/'abi-signatures.txt').write_text(signature+'\n'+entry_signature+'\n')
        (p/'kernel.aibin').write_bytes((p/'kernel.o').read_bytes())
    assert (p/'kernel.aibin').read_bytes()[:4]==b'\x7fELF'
    run(['llvm-objcopy','--dump-section',f'__CCE_KernelArgSize={p}/argsize.bin',str(p/'kernel.aibin')],p/'abi.log')
    size=int.from_bytes((p/'argsize.bin').read_bytes(),'little')
    assert size == ((56 if metadata['abi']=='npuir_a5' else 232) if backend=='npuir' else 8*len(metadata['arguments'])), f'Unsupported kernel argument size {size}'
    run(['readelf','-SW','-sW',str(p/'kernel.aibin')],p/'elf.txt')
    metadata['kernel_arg_bytes']=size


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True)
    parser.add_argument('--backend',required=True,choices=['cpu','ascendc','pto','npuir'])
    parser.add_argument('--mode',default='auto_simd')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--compile-only',action='store_true')
    parser.add_argument('--expected-npuir-root',type=Path,
                        help='Verify fixed new source and freshly built frontend/TVM library locations')
    parser.add_argument('--npuir-cross-compile-a5',action='store_true',
                        help='Select Ascend950PR_9589 in the pinned frontend architecture cache without a hardware query')
    args=parser.parse_args()
    if args.npuir_cross_compile_a5 and (args.backend!='npuir' or not args.expected_npuir_root):
        parser.error('--npuir-cross-compile-a5 requires npuir and --expected-npuir-root')
    p=args.out.resolve(); p.mkdir(parents=True,exist_ok=True)
    case=next(c for c in CASES if c['name']==args.case)
    result=dict(case=case,backend=args.backend,mode=args.mode,status='failed',stage='frontend_import',
                started_at_utc=datetime.now(timezone.utc).isoformat())
    try:
        if args.compile_only:
            result=json.loads((p/'result.json').read_text())
            result.pop('error',None)
            result.update(status='failed',stage='device_compile')
            result['device_compile_at_utc']=datetime.now(timezone.utc).isoformat()
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
            result['provenance']=npuir_provenance(tilelang,tvm,args.expected_npuir_root)
            if args.npuir_cross_compile_a5:
                jit_npu=importlib.import_module('tilelang.jit.jit_npu')
                assert jit_npu._ARCH_CACHE in (None,'Ascend950PR_9589')
                jit_npu._ARCH_CACHE='Ascend950PR_9589'
                assert jit_npu._is_a5_device()
                result['provenance']['target_selection']=dict(
                    mode='explicit_cpu_cross_compile',arch=jit_npu._ARCH_CACHE,
                    mechanism='tilelang.jit.jit_npu._ARCH_CACHE',hardware_query=False)
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
        try:
            with tilelang.transform.PassContext(instruments=[capture]):
                if args.backend=='npuir': artifact=tilelang.lower(func,target=target)
                else:
                    with target:
                        artifact=tilelang.lower(func,target=target,enable_host_codegen=False,enable_device_compile=False)
        finally:
            (p/'passes.json').write_text(json.dumps(capture.passes,indent=2))
        if args.backend=='npuir':
            assert isinstance(artifact,str)
            if args.expected_npuir_root:
                assert any('NpuLoopVectorize' in entry['name'] for entry in capture.passes)
                assert not any('NpuSimtIndirectLoad' in entry['name'] for entry in capture.passes)
            (p/'kernel.mlir').write_text(artifact)
            assert 'torch_npu._C' not in sys.modules
            result.update(status='lowered',symbol='main',abi='npuir_a5' if args.expected_npuir_root else 'npuir')
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
