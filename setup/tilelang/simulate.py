"""Compile generated AscendC and execute each add kernel on vendor A5 CAModel."""
import json
import math
import subprocess
from pathlib import Path
from tilelang.contrib.bisheng import compile_ascend

root = Path('/workspace/setup/tilelang/results')
report = json.loads((root/'report.json').read_text())
records = []
for case in report['cases']:
    label = 'x'.join(map(str, case['shape']))
    for mode, entry in case['paths'].items():
        directory = root/f'{label}_{mode}'
        binary = directory/'kernel.aibin'
        binary.write_bytes(compile_ascend(
            (directory/'kernel.asc').read_text(), target_format='aibin',
            npu_arch='dav-3510', options=['-I/workspace/tilelang/src', '-g', '--sysroot=/workspace/setup/cann/sysroot', '--gcc-toolchain=/workspace/setup/cann/sysroot/usr'],
        ))
        run = directory/'simulation'
        run.mkdir(exist_ok=True)
        previous = set(run.glob('npusim_*/npusim.log'))
        # npusim executes the supplied binary directly; pass arguments with -u.
        command = [
            '/workspace/setup/cann/npusim', 'record',
            '/workspace/setup/tilelang/sim_runner',
            '-u', f'{binary} {entry["symbol"]} {math.prod(case["shape"])}',
            '-s', 'Ascend950', '-n', '0',
            '-f', str(binary), '-o', str(run),
        ]
        with (directory/'simulation.log').open('w') as log:
            subprocess.run(command, cwd=run, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        logs = list(set(run.glob('npusim_*/npusim.log')) - previous)
        assert len(logs) == 1, f'Expected one new run; found {len(logs)}'
        assert 'SIMULATOR_CORRECT' in logs[0].read_text(), f'Missing correctness evidence: {logs[0]}'
        archive = logs[0].parent
        with (archive/'report.log').open('w') as log:
            subprocess.run(['/workspace/setup/cann/npusim', 'report', '-e', str(archive), '-n', '0'],
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
        summary = archive/'report/results/kernel_0_reports/summary.json'
        profile = json.loads(summary.read_text())
        assert profile['kernel_info']['kernel_total_clocks'] > 0
        assert profile['kernel_info']['kernel_instructions_executed'] > 0
        assert (archive/'report/index.html').is_file()
        records.append({'shape': case['shape'], 'mode': mode, 'correct': True,
                        'archive': str(archive), 'profile': profile})
        print(f'SIMULATOR PASS {label} {mode}: {logs[0].parent}', flush=True)
(root/'simulation-summary.json').write_text(json.dumps(records, indent=2))
