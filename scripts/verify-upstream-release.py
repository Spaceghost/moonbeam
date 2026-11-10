#!/usr/bin/env python3
"""CI admission: the mirrored version must actually be a published upstream tag."""
import json
from pathlib import Path
import subprocess
from release_common import upstream_release

root = Path(__file__).resolve().parents[1]
upstream = upstream_release(root)
release = json.loads(subprocess.check_output(['gh', 'api',
    'repos/moonlight-stream/moonlight-qt/releases/tags/' + upstream['tag']], text=True))
if release['draft'] or release['prerelease'] or release['tag_name'] != upstream['tag']:
    raise SystemExit('Select an actual stable Moonlight release')
refs = subprocess.check_output(['git', 'ls-remote', '--tags', upstream['repository'],
    'refs/tags/' + upstream['tag'], 'refs/tags/' + upstream['tag'] + '^{}'], text=True)
objects = dict(line.split()[::-1] for line in refs.splitlines())
commit = objects.get('refs/tags/' + upstream['tag'] + '^{}', objects.get('refs/tags/' + upstream['tag']))
if commit != upstream['commit']:
    raise SystemExit('Pinned upstream commit does not match the published release tag')
subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=root, check=True)
print(f"Verified Moonlight {upstream['tag']} at {commit}")
