"""Explicit Parallel workloads; fixtures are shared by CPU and CAModel."""
import json
import math
import struct
from pathlib import Path

CASES = []
for op in ('scalar_const', 'scalar_buffer', 'copy', 'fill'):
    for shape in ((256,), (4, 64)):
        CASES.append(dict(name=op+'_'+ 'x'.join(map(str, shape)), op=op,
                          a=list(shape), b=[1], out=list(shape)))
CASES += [
    dict(name='broadcast_row', op='broadcast_row', a=[4,64], b=[64], out=[4,64]),
    dict(name='broadcast_column', op='broadcast_column', a=[4,64], b=[4,1], out=[4,64]),
    dict(name='flatten', op='flatten', a=[4,64], b=[1], out=[256]),
    dict(name='reduce_all_256', op='reduce_all', a=[256], b=[1], out=[1]),
    dict(name='reduce_rows', op='reduce_rows', a=[4,64], b=[1], out=[4]),
    dict(name='reduce_columns', op='reduce_columns', a=[4,64], b=[1], out=[64]),
]


def fixture(case):
    a = [(i % 31 - 15)*0.25 for i in range(math.prod(case['a']))]
    b = [(i % 17 - 8)*0.5 for i in range(math.prod(case['b']))]
    op = case['op']
    if op == 'scalar_const': expected = [v + 1.25 for v in a]
    elif op == 'scalar_buffer': expected = [v + b[0] for v in a]
    elif op == 'broadcast_row': expected = [v + b[i % 64] for i,v in enumerate(a)]
    elif op == 'broadcast_column': expected = [v + b[i // 64] for i,v in enumerate(a)]
    elif op in ('copy', 'flatten'): expected = a[:]
    elif op == 'fill': expected = [1.25]*len(a)
    elif op == 'reduce_all': expected = [sum(a)]
    elif op == 'reduce_rows': expected = [sum(a[i*64:(i+1)*64]) for i in range(4)]
    elif op == 'reduce_columns': expected = [sum(a[i*64+j] for i in range(4)) for j in range(64)]
    else: raise ValueError(op)
    # All operands/results are small binary fractions, exactly representable in FP32.
    return a,b,expected


def write_fixture(case, path):
    arrays = fixture(case)
    path.write_bytes(struct.pack('<3I', *map(len,arrays)) + b''.join(
        struct.pack('<%df'%len(a), *a) for a in arrays))


def source(case, backend, mode):
    cpu = backend == 'cpu'
    op = case['op']
    ash, bsh, osh = map(tuple, (case['a'],case['b'],case['out']))
    lines = ['@T.prim_func', f'def main(A: T.Tensor({ash!r}, "float32"), B: T.Tensor({bsh!r}, "float32"), O: T.Tensor({osh!r}, "float32")):',
             '    with T.Kernel(1'+(', is_npu=True' if backend == 'npuir' else '')+'):']
    indent = '        '
    if not cpu:
        lines += [indent+f'a = T.alloc_shared({ash!r}, "float32")', indent+f'b = T.alloc_shared({bsh!r}, "float32")', indent+f'o = T.alloc_shared({osh!r}, "float32")']
        if op != 'fill': lines += [indent+'T.copy(A, a)']
        if op in ('scalar_buffer','broadcast_row','broadcast_column'): lines += [indent+'T.copy(B, b)']
        if backend != 'npuir':
            lines += [indent+('with T.SimtVF(threads=128):' if mode == 'simt' else 'with T.SimdVF():')]
            indent += '    '
    a,b,o = ('A','B','O') if cpu else ('a','b','o')
    if op == 'reduce_all':
        lines += [indent+'for i in T.Parallel(1):', indent+f'    {o}[i] = T.float32(0)',
                  indent+'    for k in T.serial(256):', indent+f'        {o}[i] = {o}[i] + {a}[k]']
    elif op.startswith('reduce_'):
        rows = op == 'reduce_rows'
        lines += [indent+f'for i in T.Parallel({4 if rows else 64}):', indent+f'    {o}[i] = T.float32(0)',
                  indent+f'    for k in T.serial({64 if rows else 4}):',
                  indent+f'        {o}[i] = {o}[i] + {a}[{"i, k" if rows else "k, i"}]']
    elif op == 'flatten':
        lines += [indent+'for k in T.Parallel(256):', indent+f'    {o}[k] = {a}[k // 64, k % 64]']
    else:
        idx = 'i' if len(ash)==1 else 'i, j'
        extents = ', '.join(map(str,ash))
        expr = {'scalar_const':f'{a}[{idx}] + T.float32(1.25)', 'scalar_buffer':f'{a}[{idx}] + {b}[0]',
                'copy':f'{a}[{idx}]', 'fill':'T.float32(1.25)',
                'broadcast_row':f'{a}[{idx}] + {b}[j]', 'broadcast_column':f'{a}[{idx}] + {b}[i, 0]'}[op]
        lines += [indent+f'for {idx} in T.Parallel({extents}):', indent+f'    {o}[{idx}] = {expr}']
    if not cpu: lines += ['        T.copy(o, O)']
    return '\n'.join(lines)+'\n'
