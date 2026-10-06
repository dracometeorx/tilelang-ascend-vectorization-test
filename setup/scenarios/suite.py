"""Run isolated frontend/device compiles and vendor simulation, retaining failures."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile
from cases import CASES, source, write_fixture

HERE=Path(__file__).resolve().parent
PATHS={'cpu_native':('cpu','native'), 'ascendc_simt':('ascendc','simt'),
       'ascendc_simd':('ascendc','simd'), 'pto_simt':('pto','simt'),
       'pto_simd':('pto','simd'), 'npuir_auto_simd':('npuir','auto_simd')}

def execute(cmd,log,timeout=240,cwd=None):
    with log.open('w') as f:
        proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=cwd)
        try: return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            return 124

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def simulate(p,fixture,runner,result,timeout=300):
    binary=p/'kernel.aibin'
    runs=p/'simulation'; runs.mkdir(exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='attempt_',dir=runs))
    before=set(run.glob('npusim_*/npusim.log'))
    abi=result['abi'] if result['abi'] in ('npuir','npuir_a5') else ''.join(result['arguments'])
    args=f'{binary} {result["symbol"]} {fixture} {abi}'
    cmd=['/workspace/setup/cann/npusim','record',str(runner),'-u',args,'-s','Ascend950','-n','0','-f',str(binary),'-o',str(run)]
    code=execute(cmd,p/'simulation.log',timeout,cwd=run)
    assert code==0, f'npusim record exit {code}; see simulation.log'
    logs=set(run.glob('npusim_*/npusim.log'))-before
    assert len(logs)==1, f'Expected one fresh simulator log, got {len(logs)}'
    log=logs.pop()
    marker=f'SIMULATOR_CORRECT elements={math.prod(result["case"]["out"])} symbol={result["symbol"]}'
    assert marker in log.read_text(), f'Numerical/guard validation failed: {log}'
    archive=log.parent
    code=execute(['/workspace/setup/cann/npusim','report','-e',str(archive),'-n','0'],archive/'report.log',120,cwd=archive)
    assert code==0, 'npusim report failed'
    profiles=list((archive/'report/results').glob('kernel_*_reports/summary.json'))
    assert len(profiles)==1, f'Expected a single kernel profile, got {len(profiles)}'
    info=json.loads(profiles[0].read_text())['kernel_info']
    assert info['kernel_total_clocks']>0 and info['kernel_instructions_executed']>0
    assert (archive/'report/index.html').is_file()
    return dict(status='passed',stage='simulation',correct=True,output_guard_correct=True,
        binary_sha256=digest(binary),runner_sha256=digest(runner),fixture_sha256=digest(fixture),
        cycles=info['kernel_total_clocks'],instructions=info['kernel_instructions_executed'],archive=str(archive))

def build_runner():
    runner=HERE/'sim_runner'
    handle,tempname=tempfile.mkstemp(prefix='.sim_runner.',dir=HERE)
    os.close(handle)
    temporary=Path(tempname)
    root='/workspace/setup/cann/components-9.2/npu-runtime/x86_64-linux/pkg_inc'
    cmd=['g++','-std=c++17','-O2','-Wno-deprecated-declarations',str(HERE/'sim_runner.cc'),'-I'+root+'/runtime','-I'+root,
         '-L/workspace/Ascend/cann-9.2.0-beta.2/tools/simulator/Ascend950PR_9589/camodel',
         '-Wl,-rpath-link,/workspace/Ascend/cann-9.2.0-beta.2/lib64','-lruntime_camodel','-o',str(temporary)]
    try:
        subprocess.run(cmd,check=True)
        if not runner.exists() or runner.read_bytes()!=temporary.read_bytes(): temporary.replace(runner)
    finally:
        temporary.unlink(missing_ok=True)
    return runner

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('/workspace/setup/tilelang/results/scenarios'))
    parser.add_argument('--case',choices=[c['name'] for c in CASES])
    parser.add_argument('--paths',nargs='+',choices=PATHS,default=list(PATHS))
    parser.add_argument('--npuir-activate',type=Path,default=Path('/workspace/setup/backends/activate_npuir.sh'))
    parser.add_argument('--expected-npuir-root',type=Path,
                        help='Require prepared identical inputs and verify the fixed new frontend')
    parser.add_argument('--npuir-cross-compile-a5',action='store_true')
    phases=parser.add_mutually_exclusive_group()
    phases.add_argument('--compile-only',action='store_true')
    phases.add_argument('--simulate-only',action='store_true')
    parser.add_argument('--reuse-identical',action='store_true',help='Reuse verified simulation only for identical ELF, ABI, symbol, fixture and runner hashes')
    parser.add_argument('--simulation-timeout',type=int,default=300,help='Seconds allowed per CAModel invocation')
    args=parser.parse_args()
    if len(set(args.paths))!=len(args.paths): parser.error('--paths must not contain duplicates')
    if args.expected_npuir_root and args.paths!=['npuir_auto_simd']:
        parser.error('--expected-npuir-root requires --paths npuir_auto_simd')
    if args.npuir_cross_compile_a5 and not args.expected_npuir_root:
        parser.error('--npuir-cross-compile-a5 requires --expected-npuir-root')
    if args.simulation_timeout<=0: parser.error('--simulation-timeout must be positive')
    out=args.out.resolve()
    if any(c.isspace() for c in str(out)):
        parser.error('--out must not contain whitespace (npusim user arguments)')
    out.mkdir(parents=True,exist_ok=True)
    if args.expected_npuir_root:
        inputs=json.loads((out/'inputs.json').read_text())
        assert inputs['frontend_commit']=='013dbbf5824c3ac29e975d78c0b38e60b2410be7'
        manifests={entry['case']['name']:entry for entry in inputs['cases']}
        # Verify existing prepared inputs before any worker or simulator runs.
        for case in CASES:
            manifest=manifests[case['name']]
            prepared=out/case['name']/'npuir_auto_simd'/'workload.py'
            assert manifest['case']==case
            assert digest(prepared)==manifest['workload_sha256']
            assert digest(out/(case['name']+'.bin'))==manifest['fixture_sha256']
            assert prepared.read_text()==source(case,'npuir','auto_simd')
            with tempfile.TemporaryDirectory() as tmp:
                generated=Path(tmp)/'fixture.bin'; write_fixture(case,generated)
                assert generated.read_bytes()==(out/(case['name']+'.bin')).read_bytes()
    runner=None if args.compile_only else build_runner()
    records=[]
    cache={}
    if args.reuse_identical and runner:
        for prior in out.glob('*/*/result.json'):
            old=json.loads(prior.read_text())
            binary=prior.parent/'kernel.aibin'
            fixture_path=out/(old['case']['name']+'.bin')
            if old.get('correct') and old.get('status')=='passed' and binary.exists() and fixture_path.exists() and Path(old.get('archive',''),'report/index.html').is_file():
                key=(digest(binary),digest(fixture_path),digest(runner),old['symbol'],old['abi'],tuple(old.get('arguments',[])))
                archive=Path(old['archive'])
                profiles=list((archive/'report/results').glob('kernel_*_reports/summary.json'))
                marker=f'SIMULATOR_CORRECT elements={math.prod(old["case"]["out"])} symbol={old["symbol"]}'
                if len(profiles)==1 and (archive/'npusim.log').exists() and marker in (archive/'npusim.log').read_text():
                    info=json.loads(profiles[0].read_text())['kernel_info']
                    if key[:3]==(old.get('binary_sha256'),old.get('fixture_sha256'),old.get('runner_sha256')) and (old['cycles'],old['instructions'])==(info['kernel_total_clocks'],info['kernel_instructions_executed']): cache[key]=old
    for case in CASES:
        if args.case and case['name']!=args.case: continue
        fixture=out/(case['name']+'.bin')
        if not args.expected_npuir_root: write_fixture(case,fixture)
        for backend,mode in [PATHS[path] for path in args.paths]:
            p=out/case['name']/(backend+'_'+mode); p.mkdir(parents=True,exist_ok=True)
            worker=[str(HERE/'worker.py'),'--case',case['name'],'--backend',backend,'--mode',mode,'--out',str(p)]
            if args.expected_npuir_root:
                worker+=['--expected-npuir-root',str(args.expected_npuir_root.resolve())]
            if args.npuir_cross_compile_a5: worker+=['--npuir-cross-compile-a5']
            if not args.simulate_only:
                (p/'result.json').unlink(missing_ok=True)
                cmd=[sys.executable]+worker
                if backend=='npuir':
                    cmd=['bash','-c','source '+shlex.quote(str(args.npuir_activate.resolve()))+' && python '+shlex.join(worker)]
                code=execute(cmd,p/'worker.log',cwd=args.expected_npuir_root)
                if not (p/'result.json').exists() or code in (124,-6,-11):
                    (p/'result.json').write_text(json.dumps(dict(case=case,backend=backend,mode=mode,status='failed',stage='worker',error=f'Worker exit {code}; see worker.log')))
                result=json.loads((p/'result.json').read_text())
                if backend=='npuir' and result['status']=='lowered':
                    code=execute([sys.executable]+worker+['--compile-only'],p/'compiler-worker.log')
                    compiled=json.loads((p/'result.json').read_text())
                    if code and compiled['status']!='failed':
                        compiled.update(status='failed',stage='device_compile',error=f'Compiler worker exit {code}; see compiler-worker.log')
                        (p/'result.json').write_text(json.dumps(compiled,indent=2)+'\n')
            result=json.loads((p/'result.json').read_text())
            if not args.compile_only and backend!='cpu' and (result['status']=='compiled' or result['stage']=='simulation'):
                try:
                    key=(digest(p/'kernel.aibin'),digest(fixture),digest(runner),result['symbol'],result['abi'],tuple(result.get('arguments',[])))
                    if args.reuse_identical and key in cache:
                        old=cache[key]
                        for field in ['status','stage','correct','output_guard_correct','binary_sha256','runner_sha256','fixture_sha256','cycles','instructions','archive']: result[field]=old[field]
                        result['reused_from']=old.get('reused_from') or old['case']['name']+'/'+old['backend']+'_'+old['mode']
                    else:
                        for field in ['reused_from','correct','output_guard_correct','cycles','instructions','archive','binary_sha256','fixture_sha256','runner_sha256']: result.pop(field,None)
                        result.update(simulate(p,fixture,runner,result,args.simulation_timeout))
                        cache[key]=dict(result)
                    result.pop('error',None)
                except Exception as exc: result.update(status='failed',stage='simulation',error=str(exc))
                (p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            records.append(result)
            print(case['name'],backend,mode,result['status'],result['stage'],result.get('cycles',''),flush=True)
            (out/('summary.json' if not args.case else 'summary-'+args.case+'.json')).write_text(json.dumps(records,indent=2)+'\n')

if __name__=='__main__': main()
