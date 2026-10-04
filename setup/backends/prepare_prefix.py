"""Add supported compiler executables to the local SDK bin directory."""
from pathlib import Path
prefix = Path('/workspace/Ascend/cann-9.2.0-beta.2')
sources = [prefix/'tools/bisheng_compiler/bin', Path('/workspace/setup/cann/components-9.2/npu-ir/bishengir/bin')]
(prefix/'bin').mkdir(exist_ok=True)
for directory in sources:
    for src in directory.iterdir():
        dst = prefix/'bin'/src.name
        if dst.is_symlink():
            assert dst.resolve() == src.resolve(), f'Conflicting compiler: {dst}'
        else:
            assert not dst.exists(), f'Existing compiler: {dst}'
            dst.symlink_to(src)
