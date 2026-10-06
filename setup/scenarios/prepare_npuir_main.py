#!/usr/bin/env python3
"""Prepare identical inputs for a new frontend; never compile or claim a run."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from cases import CASES, source, write_fixture


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True,
                        help='Exported historical examples/scenarios directory')
    parser.add_argument('--out', type=Path, required=True,
                        help='New, nonexistent results directory')
    args = parser.parse_args()
    baseline = args.baseline.resolve()
    out = args.out.resolve()
    if out.exists():
        parser.error('--out must not exist; preserve prior results')
    metrics = json.loads((baseline / 'metrics.json').read_text())
    prepared = []
    # Verify every case before creating the requested output directory.
    with tempfile.TemporaryDirectory() as temporary:
        for case in CASES:
            name = case['name']
            records = [r for r in metrics if r['case']['name'] == name
                       and r['backend'] == 'npuir' and r['mode'] == 'auto_simd']
            if len(records) != 1:
                raise ValueError(f'{name}: expected one historical NPU-IR record')
            old = records[0]
            if old['case'] != case:
                raise ValueError(f'{name}: workload definition changed')
            workload = source(case, 'npuir', 'auto_simd').encode()
            historical = (baseline / 'ir' / old['evidence'] / 'workload.py').read_bytes()
            if workload != historical or digest(workload) != old['evidence_sha256']['workload.py']:
                raise ValueError(f'{name}: workload differs from historical evidence')
            fixture_path = Path(temporary) / (name + '.bin')
            write_fixture(case, fixture_path)
            fixture = fixture_path.read_bytes()
            if digest(fixture) != old['fixture_sha256']:
                raise ValueError(f'{name}: fixture differs from historical SHA256')
            prepared.append((case, workload, fixture))
    out.mkdir(parents=True)
    records = []
    for case, workload, fixture in prepared:
        directory = out / case['name'] / 'npuir_auto_simd'
        directory.mkdir(parents=True)
        (directory / 'workload.py').write_bytes(workload)
        (out / (case['name'] + '.bin')).write_bytes(fixture)
        records.append(dict(
            case=case, status='not_run', stage='prepared_inputs',
            workload_sha256=digest(workload), fixture_sha256=digest(fixture),
            workload_byte_equal_to_historical=True,
            fixture_hash_equal_to_historical=True,
        ))
    manifest = dict(
        schema_version=1, status='prepared_inputs_only',
        frontend_commit='013dbbf5824c3ac29e975d78c0b38e60b2410be7',
        required_environment={'TILELANG_ENABLE_SIMT': '0'},
        historical_metrics_sha256=digest((baseline / 'metrics.json').read_bytes()),
        frontend_import_verified=False, compiled=False, simulated=False,
        cases=records,
    )
    (out / 'inputs.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Prepared and verified {len(records)} inputs; compiled=0, simulated=0')


if __name__ == '__main__':
    main()
