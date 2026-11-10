#!/usr/bin/env python3
"""Exercise complete candidate assembly and recursive source distribution."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project / 'scripts'))
from release_common import asset_names, native_version

assert native_version('6.3.0') == '6.3.0'
assert native_version('6.3.1') == '6.3.1'
for invalid in ['6.2.0-moonbeam.5', '06.3.0', '6.3.0+g123', '6.3.0-rc1', '../invalid', '256.2.0', '6.3.65536']:
    try:
        native_version(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(invalid)

with tempfile.TemporaryDirectory(prefix='moonbeam-artifacts-') as directory:
    root = Path(directory)
    env = dict(os.environ, GITHUB_REF_NAME='release/6.2', GIT_AUTHOR_NAME='Release Test', GIT_AUTHOR_EMAIL='test@example.invalid',
               GIT_COMMITTER_NAME='Release Test', GIT_COMMITTER_EMAIL='test@example.invalid')
    def git(*args, cwd=root):
        return subprocess.check_output(['git', *args], cwd=cwd, env=env, stderr=subprocess.DEVNULL, text=True).strip()
    dependency = root / 'dependency'
    dependency.mkdir()
    git('init', cwd=dependency)
    (dependency / 'decoder.c').write_text('/* dependency source */\n')
    git('add', '.', cwd=dependency)
    git('commit', '-m', 'dependency', cwd=dependency)
    repo = root / 'repo'
    repo.mkdir()
    git('init', '-b', 'release/6.2', cwd=repo)
    (repo / 'scripts').mkdir()
    (repo / 'app').mkdir()
    (repo / 'docs/releases').mkdir(parents=True)
    (repo / 'docs/releases/6.3.0.md').write_text('# Moonbeam 6.3.0\n\nTest release notes.\n')
    (repo / 'dist').mkdir()
    (repo / '.gitignore').write_text('dist/\nprivate.conf\n__pycache__/\n')
    (repo / 'app/moonbeam-version.txt').write_text('6.3.0\n')
    for name in ['release-artifacts.py', 'release_common.py']:
        shutil.copy2(project / 'scripts' / name, repo / 'scripts' / name)
    git('-c', 'protocol.file.allow=always', 'submodule', 'add', str(dependency), 'vendor/decoder', cwd=repo)
    git('add', '.', cwd=repo)
    git('commit', '-m', 'release fixture', cwd=repo)
    commit = git('rev-parse', 'HEAD', cwd=repo)
    version = '6.3.0'
    names = asset_names(version, complete=True)
    for name in names:
        if not name.endswith('-source.tar.gz'):
            (repo / 'dist' / name).write_bytes(b'platform binary')
    (repo / 'private.conf').write_text('private pairing data')
    cmd = [sys.executable, str(repo / 'scripts/release-artifacts.py'), version, '--complete']
    result = subprocess.run(cmd, env=dict(env, GITHUB_RUN_ID='42'), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((repo / 'dist/candidate.json').read_text())
    assert manifest['complete'] and not manifest['dirty']
    assert manifest['commit'] == commit and manifest['branch'] == 'release/6.2'
    assert set(manifest['sha256']) == set(names)
    for name, digest in manifest['sha256'].items():
        assert hashlib.sha256((repo / 'dist' / name).read_bytes()).hexdigest() == digest
    source = repo / 'dist' / f'moonbeam-{version}-source.tar.gz'
    with tarfile.open(source) as archive:
        entries = archive.getnames()
        assert any(name.endswith('/vendor/decoder/decoder.c') for name in entries)
        archive.extractall(root / 'extracted', filter='data')
        assert not any('private.conf' in name or '/dist/' in name or '/.git/' in name for name in entries)
    extracted = root / 'extracted' / f'moonbeam-{version}'
    (extracted / 'dist').mkdir()
    for name in names:
        if not name.endswith('-source.tar.gz'):
            shutil.copy2(repo / 'dist' / name, extracted / 'dist' / name)
    rebuild = [sys.executable, str(extracted / 'scripts/release-artifacts.py'), version, '--complete']
    result = subprocess.run(rebuild, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads((extracted / 'dist/candidate.json').read_text())['dirty']
    (repo / 'dist' / names[-1]).unlink()
    assert subprocess.run(cmd, env=env, capture_output=True).returncode != 0
    (repo / 'dist' / names[-1]).write_bytes(b'platform binary')
    (repo / 'app/dirty-source.txt').write_text('uncommitted tracked source\n')
    git('add', 'app/dirty-source.txt', cwd=repo)
    assert subprocess.run(cmd, env=env, capture_output=True).returncode == 0
    assert json.loads((repo / 'dist/candidate.json').read_text())['dirty']
print('PASS: native versions, complete assets, checksums, submodule source, private-file exclusion, missing package, dirty source')
