"""Run each compiled backend on the same vendor A5 model; validate and report."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

ROOT = Path('/workspace/setup/tilelang/results')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', help='Optional backend:shape[:mode] selector')
    parser.add_argument('--reuse', action='store_true', help='Reuse only successful reports with matching binary and runner SHA256')
    args = parser.parse_args()
    records = []
    cases = json.loads((ROOT/'backend-cases.json').read_text())
    cases.sort(key=lambda c: (c['backend'] != 'npuir', c['shape'], c['mode']))
    runner = Path('/workspace/setup/backends/sim_runner_ir')
    runner_hash = hashlib.sha256(runner.read_bytes()).hexdigest()
    for case in cases:
        name = ':'.join([case['backend'], 'x'.join(map(str, case['shape'])), case['mode']])
        if args.case and not name.startswith(args.case):
            continue
        directory = Path(case['directory'])
        binary = Path(case['binary'])
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        summary_file = directory/'verified-simulation.json'
        if args.reuse and summary_file.exists():
            old = json.loads(summary_file.read_text())
            if old.get('binary_sha256') == digest and old.get('runner_sha256') == runner_hash and Path(old['archive'], 'report/index.html').exists():
                records.append(old)
                print('REUSED', name, flush=True)
                continue
        run = directory/'simulation'
        run.mkdir(exist_ok=True)
        previous = set(run.glob('npusim_*/npusim.log'))
        argv = f'{binary} {case["symbol"]} 256'
        if case['backend'] == 'npuir':
            argv += ' npuir'
        print('SIMULATING', name, flush=True)
        with (directory/'simulation.log').open('w') as log:
            cmd = ['/workspace/setup/cann/npusim','record',str(runner),'-u',argv,'-s','Ascend950','-n','0','-f',str(binary),'-o',str(run)]
            process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=15)
                raise
            if code:
                raise subprocess.CalledProcessError(code, cmd)
        logs = list(set(run.glob('npusim_*/npusim.log')) - previous)
        assert len(logs) == 1
        assert 'SIMULATOR_CORRECT' in logs[0].read_text(), f'Numerical validation failed: {logs[0]}'
        archive = logs[0].parent
        with (archive/'report.log').open('w') as log:
            subprocess.run(['/workspace/setup/cann/npusim','report','-e',str(archive),'-n','0'], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        profile = json.loads((archive/'report/results/kernel_0_reports/summary.json').read_text())
        assert profile['kernel_info']['kernel_total_clocks'] > 0
        assert profile['kernel_info']['kernel_instructions_executed'] > 0
        assert (archive/'report/index.html').exists()
        record = dict(case, binary_sha256=digest, runner_sha256=runner_hash, correct=True, archive=str(archive), profile=profile)
        summary_file.write_text(json.dumps(record, indent=2))
        records.append(record)
        print('SIMULATOR PASS', name, profile['kernel_info'], flush=True)
    output = ROOT/('backend-simulation-summary.json' if not args.case else 'backend-simulation-partial.json')
    output.write_text(json.dumps(records, indent=2))

if __name__ == '__main__':
    main()
