"""Export compact, auditable evidence from per-case results (never infer a pass)."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
from cases import CASES, fixture

PATHS=['cpu_native','ascendc_simt','ascendc_simd','pto_simt','pto_simd','npuir_auto_simd']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--results',type=Path,default=Path('/workspace/setup/tilelang/results/scenarios'))
    ap.add_argument('--export',type=Path,required=True)
    args=ap.parse_args()
    args.results=args.results.resolve(); args.export=args.export.resolve()
    args.export.mkdir(parents=True,exist_ok=True)
    records=[]; table=[]
    for case in CASES:
        data=fixture(case)
        fixtures=args.export/'fixtures'; fixtures.mkdir(exist_ok=True)
        (fixtures/(case['name']+'.json')).write_text(json.dumps(dict(case=case,A=data[0],B=data[1],expected=data[2]),indent=2)+'\n')
        cells=[]
        for path in PATHS:
            p=args.results/case['name']/path
            r=json.loads((p/'result.json').read_text())
            r['evidence']=case['name']+'/'+path
            dest=args.export/'ir'/case['name']/path; dest.mkdir(parents=True,exist_ok=True)
            if r['status']=='failed': (dest/'failure.txt').write_text(r.get('error','No diagnostic')+'\n')
            names=['workload.py','kernel.cc','input.tir','device.tir','kernel.asc','kernel.ptodsl.py','kernel.pto','kernel.vpto.mlir','kernel.ll','kernel.mlir','passes.json','source-adaptation.diff']
            if r['status']=='failed': names+=['worker.log','compiler-worker.log','device-compile.log','error.txt']
            if r['backend']=='npuir':
                names += [str(f.relative_to(p)) for f in p.glob('*NpuLoopVectorize*.tir')]
                names += ['temps/module.hivm.opt.mlir']
            for name in names:
                if (p/name).exists():
                    target=dest/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p/name,target)
            if r['status']=='passed' and r['backend']!='cpu':
                assert r['correct'] and r['output_guard_correct'] and r['cycles']>0 and r['instructions']>0
                archive=Path(r['archive'])
                assert (archive/'report/index.html').exists()
                log=(archive/'npusim.log').read_text()
                proof=[line for line in log.splitlines() if 'SIMULATOR_CORRECT' in line]
                assert proof
                r['correctness_marker']=proof
                (dest/'correctness.txt').write_text('\n'.join(proof)+'\n')
                profiles=list((archive/'report/results').glob('kernel_*_reports/summary.json'))
                assert len(profiles)==1
                profile=json.loads(profiles[0].read_text())
                assert (r['cycles'],r['instructions'])==(profile['kernel_info']['kernel_total_clocks'],profile['kernel_info']['kernel_instructions_executed'])
                shutil.copyfile(profiles[0],dest/'profile.json')
                r['archive']=str(archive.relative_to(args.results))
                cells.append(f"{r['cycles']}/{r['instructions']}"+(' †' if r.get('reused_from') and r['reused_from']!=r['evidence'] else ''))
            elif r['backend']=='cpu' and r['status']=='passed': cells.append('通过')
            else: cells.append(r['status']+' ('+r['stage']+')')
            r['evidence_sha256']={str(f.relative_to(dest)):hashlib.sha256(f.read_bytes()).hexdigest() for f in dest.rglob('*') if f.is_file()}
            records.append(r)
        table.append('| '+case['name']+' | '+' | '.join(cells)+' |')
    (args.export/'metrics.json').write_text(json.dumps(records,indent=2)+'\n')
    counts=Counter(r['status'] for r in records)
    device_passes=[r for r in records if r['backend']!='cpu' and r['status']=='passed']
    unique_runs=len({r['archive'] for r in device_passes})
    lines=['# Parallel 场景实测矩阵','',
           '单 block、FP32；A 的逻辑规模为 256 个元素（fill 不读取 A），输出按场景为 256、1、4 或 64 个元素。数字为 CAModel **周期/执行指令数**，不是物理 NPU 性能。',
           '† 表示跨组合复用 ELF、ABI、符号、fixture 和 runner 哈希均一致的已验证模拟；不代表独立再次执行。', '',
           '| 场景 | CPU | AscendC SIMT | AscendC SIMD | PTO SIMT | PTO SIMD | NPU-IR 自动向量化路径 |',
           '|---|---|---|---|---|---|---|',*table,'',f'状态统计：`{dict(counts)}`；设备通过 {len(device_passes)}/{len(CASES)*5} 个组合，引用 {unique_runs} 份不同的成功模拟归档。', '',
           '每个组合的源程序、IR 和失败日志见 `ir/`；`metrics.json` 保存失败阶段、完整诊断、校验标记、哈希和模拟报告的相对路径。完整 ELF/轨迹/HTML 留在工作目录。',
           '未重新验证空白机器安装；未修改编译器，不将未通过的组合视为可用后端。']
    (args.export/'README.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__': main()
