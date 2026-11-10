#!/usr/bin/env python3
"""Create traceable source/checksum metadata for one already-built candidate."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
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
if (root / '.git').exists():
    submodules = subprocess.check_output(['git', 'submodule', 'status', '--recursive'], cwd=root, text=True)
    if any(line.startswith(('-', '+', 'U')) for line in submodules.splitlines()):
        parser.error('Initialize every submodule at its recorded commit before packaging source.')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    tracked = subprocess.check_output(['git', 'ls-files', '--recurse-submodules', '-z'], cwd=root).decode().split('\0')
    tracked = [name for name in tracked if name]
    dirty = subprocess.run(['git', 'diff', '--quiet', 'HEAD'], cwd=root).returncode != 0
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip()
else:
    # Source archives contain all submodule files and need no Git checkout to build.
    snapshot = json.loads((root / 'SOURCE_MANIFEST.json').read_text())
    commit, tracked = snapshot['commit'], snapshot['files']
    dirty, branch = True, 'source-archive'  # Source rebuilds are never promotable CI candidates.
    if any(Path(name).is_absolute() or '..' in Path(name).parts for name in tracked):
        parser.error('Invalid source manifest path.')
prefix = f'moonbeam-{version}'
source = dist / f'{prefix}-source.tar.gz'
with tarfile.open(source, 'w:gz') as archive:
    for name in tracked:
        path = root / name
        if not path.is_file():
            parser.error(f'Missing tracked source file: {name}')
        archive.add(path, arcname=f'{prefix}/{name}', recursive=False)
    snapshot = json.dumps({'commit': commit, 'files': tracked}, indent=2).encode() + b'\n'
    info = tarfile.TarInfo(f'{prefix}/SOURCE_MANIFEST.json')
    info.size = len(snapshot)
    archive.addfile(info, io.BytesIO(snapshot))
files = [dist / name for name in asset_names(version, args.complete)]
artifacts = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
manifest = {'schema': 2, 'complete': args.complete, 'version': version,
            'base_version': base_version, 'dirty': dirty, 'commit': commit,
            'branch': os.environ.get('GITHUB_REF_NAME', branch),
            'run_id': os.environ.get('GITHUB_RUN_ID'), 'sha256': artifacts}
(dist / 'candidate.json').write_text(json.dumps(manifest, indent=2) + '\n')
(dist / 'Moonbeam-SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name, digest in artifacts.items()))
print(json.dumps(manifest, indent=2))
