#!/usr/bin/env python3
"""Create traceable source/checksum metadata for one already-built candidate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from release_common import asset_names, native_version

root = Path(__file__).resolve().parents[1]
dist = root / 'dist'
parser = argparse.ArgumentParser()
parser.add_argument('version')
parser.add_argument('--complete', action='store_true')
args = parser.parse_args()
version = args.version
base_version = (root / 'app/moonbeam-version.txt').read_text().strip()
native_version(base_version)
submodules = subprocess.check_output(['git', 'submodule', 'status', '--recursive'], cwd=root, text=True)
if any(line.startswith(('-', '+', 'U')) for line in submodules.splitlines()):
    parser.error('Initialize every submodule at its recorded commit before packaging source.')
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
prefix = f'moonbeam-{version}'
source = dist / f'{prefix}-source.tar.gz'
tracked = subprocess.check_output(['git', 'ls-files', '--recurse-submodules', '-z'], cwd=root).split(b'\0')
with tarfile.open(source, 'w:gz') as archive:
    for raw in tracked:
        if raw:
            name = raw.decode()
            path = root / name
            if path.is_file():
                archive.add(path, arcname=f'{prefix}/{name}', recursive=False)
files = [dist / name for name in asset_names(version, args.complete)]
artifacts = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
dirty = subprocess.run(['git', 'diff', '--quiet', 'HEAD'], cwd=root).returncode != 0
manifest = {'schema': 2, 'complete': args.complete, 'version': version, 'base_version': base_version, 'dirty': dirty,
            'commit': commit, 'branch': os.environ.get('GITHUB_REF_NAME',
                subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip()),
            'run_id': os.environ.get('GITHUB_RUN_ID'), 'sha256': artifacts}
(dist / 'candidate.json').write_text(json.dumps(manifest, indent=2) + '\n')
(dist / 'Moonbeam-SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name, digest in artifacts.items()))
print(json.dumps(manifest, indent=2))
