"""Compare exported new measurements with separately labeled historical evidence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from cases import CASES


def ir_features(path):
    text = path.read_text()
    bodies = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if 'func.func @' not in line or 'hivm.vector_function' not in line:
            continue
        indent = len(line) - len(line.lstrip())
        body = []
        for following in lines[i + 1:]:
            if following == ' ' * indent + '}':
                break
            body.append(following.strip())
        bodies.append(hashlib.sha256('\n'.join(body).encode()).hexdigest())
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                vector_function_count=len(bodies),
                vector_body_hashes_ignoring_header_and_indentation=bodies,
                static_vector_intrinsics=dict(sorted(Counter(
                    re.findall(r'"hivm_regbaseintrins\.intr\.hivm\.([^"\s]+)"', text)).items())),
                static_memref_loads=len(re.findall(r'\bmemref\.load\b', text)),
                static_memref_stores=len(re.findall(r'\bmemref\.store\b', text)))


def evidence(root, record):
    directory = root / 'ir' / record['case']['name'] / (record['backend'] + '_' + record['mode'])
    result = dict(status=record['status'], stage=record['stage'])
    if record['status'] == 'passed':
        profile = json.loads((directory / 'profile.json').read_text())
        result.update(cycles=record['cycles'], instructions=record['instructions'],
                      vector_instructions=profile.get('aiv_vector_instructions'),
                      scalar_instructions=profile.get('scalar_instructions'),
                      dominant_pipeline=profile.get('top_level_diagnosis'))
    ir = directory / 'temps/module.hivm.opt.mlir'
    if ir.exists():
        result['optimized_ir'] = ir_features(ir)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--new', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    old = {(r['case']['name'], r['backend'], r['mode']): r
           for r in json.loads((args.baseline / 'metrics.json').read_text())}
    current = {r['case']['name']: r for r in json.loads((args.new / 'metrics.json').read_text())}
    assert set(current) == {c['name'] for c in CASES}
    rows = []
    for case in CASES:
        name = case['name']
        r = current[name]
        assert r['backend'] == 'npuir' and r['mode'] == 'auto_simd'
        assert r['provenance']['source_commit'] == '013dbbf5824c3ac29e975d78c0b38e60b2410be7'
        row = dict(case=name, new_npuir=evidence(args.new, r))
        for backend, mode, label in [('npuir', 'auto_simd', 'historical_npuir'),
                                     ('ascendc', 'simd', 'historical_ascendc_simd'),
                                     ('pto', 'simd', 'historical_pto_simd')]:
            row[label] = evidence(args.baseline, old[name, backend, mode])
        before, after = row['historical_npuir'], row['new_npuir']
        if before['status'] == after['status'] == 'passed':
            row['delta'] = dict(cycles=after['cycles'] - before['cycles'],
                                instructions=after['instructions'] - before['instructions'])
        rows.append(row)
    args.out.write_text(json.dumps(dict(
        scope='Only new_npuir contains current executions; other columns are historical.',
        limitations='Frontend, compilation flags, ABI and launch changed. Device compiler and CAModel retained. No causal attribution from cycle delta alone.',
        ir_hash_method='Function bodies exclude headers and indentation only; differing hashes do not prove different semantics. Static intrinsic counts are not executed instruction counts.',
        cases=rows), indent=2) + '\n')


if __name__ == '__main__':
    main()
