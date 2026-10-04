"""Assemble a relocatable SDK view from signature-verified package components.

Ascend950 aliases and libruntime.so follow simulator's filelist.csv.
"""
from pathlib import Path

components = Path('/workspace/setup/cann/components-9.2')
prefix = Path('/workspace/Ascend/cann-9.2.0-beta.2')

def link(target, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        assert path.resolve() == target.resolve(), f'Conflicting link: {path}'
    else:
        assert not path.exists(), f'Existing file: {path}'
        path.symlink_to(target)

link(components/'bisheng-compiler/tools/bisheng_compiler', prefix/'tools/bisheng_compiler')
link(components/'npu-runtime/x86_64-linux/lib64', prefix/'lib64')
link(components/'npu-runtime/x86_64-linux/include', prefix/'include')
link(components/'asc-devkit/x86_64-linux/asc', prefix/'asc')
model = prefix/'tools/simulator/dav_3510/camodel'
for source in (components/'simulator/x86_64-linux/simulator/dav_3510/camodel').iterdir():
    link(source, model/source.name)
link(model/'libruntime_camodel.so', model/'libruntime.so')
for alias in ['Ascend950PR_9589', 'Ascend950PR_9599']:
    link(prefix/'tools/simulator/dav_3510', prefix/'tools/simulator'/alias)
link(Path('/workspace/tilelang/.venv/lib/python3.12/site-packages/cannsim'), prefix/'python/site-packages/cannsim')
print(prefix)
