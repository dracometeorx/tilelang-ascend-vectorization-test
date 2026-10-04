#!/usr/bin/env python3
"""Stage the tested cloud scripts in a configurable workspace and optionally install."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import urllib.request

SOURCE = Path(__file__).resolve().parent

def run(*args, **kwargs):
    subprocess.run(args, check=True, **kwargs)

def stage(workspace):
    # Existing unrelated/user-edited helpers are never silently overwritten.
    manifest = workspace / 'setup/lab-staged-files.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    planned = []
    for src in sorted((SOURCE/'setup').rglob('*')):
        if not src.is_file() or '__pycache__' in src.parts:
            continue
        relative = src.relative_to(SOURCE)
        data = src.read_text().replace('/workspace', str(workspace)).encode()
        target = workspace/relative
        if target.exists() and target.read_bytes() != data:
            old_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if previous.get(str(relative)) != old_hash:
                raise SystemExit(f'Refusing to overwrite existing or edited helper: {target}')
        planned.append((relative, target, data))
    hashes = {}
    for relative, target, data in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if target.suffix == '.sh' or target.name == 'npusim':
            target.chmod(0o755)
        hashes[str(relative)] = hashlib.sha256(data).hexdigest()
    manifest.write_text(json.dumps(hashes, indent=2)+'\n')
    print(f'Staged {len(hashes)} files in {workspace}/setup', flush=True)

def fetch_sysroot(workspace):
    destination = workspace/'setup/cann/sysroot-debs'
    destination.mkdir(parents=True, exist_ok=True)
    for package in json.loads((SOURCE/'sysroot-packages.json').read_text()):
        path = destination/package['filename']
        if not path.exists():
            temporary = path.with_suffix('.deb.partial')
            with urllib.request.urlopen(package['url'], timeout=120) as response, temporary.open('wb') as output:
                shutil.copyfileobj(response, output)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != package['sha256']:
                raise SystemExit(f'SHA256 mismatch: {temporary}')
            temporary.replace(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != package['sha256']:
            raise SystemExit(f'SHA256 mismatch: {path}')
        print('Verified sysroot:', path.name, flush=True)

def install(workspace):
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise SystemExit('This pinned package set requires x86_64 Linux.')
    for command in ['git', 'curl', 'uv', 'g++', 'gcc', 'dpkg-deb', 'sha256sum']:
        if not shutil.which(command):
            raise SystemExit(f'Missing prerequisite: {command}; see README.md')
    for command in ['rpmkeys', 'rpm2cpio', 'cpio']:
        local = workspace/'setup/cann/tools/usr/bin'/command
        if not shutil.which(command) and not os.access(local, os.X_OK):
            raise SystemExit(f'Missing prerequisite: {command}; see README.md')
    config = json.loads((SOURCE/'versions.json').read_text())
    checkout = workspace/'tilelang'
    if not checkout.exists():
        run('git','clone','--no-checkout',config['tilelang_repository'],str(checkout))
        run('git','-C',str(checkout),'checkout','--detach',config['tilelang_commit'])
    else:
        actual = subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
        if actual != config['tilelang_commit']:
            raise SystemExit(f'Existing checkout at {actual}; expected {config["tilelang_commit"]}. Use a new workspace.')
    environment = dict(os.environ, UV_CACHE_DIR=str(workspace/'.cache/uv'),
        UV_PYTHON_INSTALL_DIR=str(workspace/'setup/backends/python'),
        UV_PYTHON_BIN_DIR=str(workspace/'setup/backends/bin'))
    run('uv','python','install',config['python_main'],env=environment)
    fetch_sysroot(workspace)
    for script in ['tilelang/install.sh','cann/install.sh','backends/install.sh']:
        run('bash',str(workspace/'setup'/script),env=environment)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=Path('/workspace/a5-lab'))
    parser.add_argument('--install',action='store_true')
    parser.add_argument('--fetch-sysroot',action='store_true')
    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()
    # Original shell helpers quote paths inconsistently; reject unsafe path forms.
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_-.' for c in str(workspace)):
        raise SystemExit('Workspace path must contain only letters, digits, /, _, -, or .')
    if workspace == SOURCE or SOURCE in workspace.parents or workspace == Path('/'):
        raise SystemExit('Choose a dedicated workspace outside this source repository.')
    stage(workspace)
    if args.install:
        install(workspace)
    elif args.fetch_sysroot:
        fetch_sysroot(workspace)

if __name__ == '__main__':
    main()
