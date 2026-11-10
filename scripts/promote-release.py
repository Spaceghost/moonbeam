#!/usr/bin/env python3
"""Validate a successful release-branch build and publish its exact bytes.

The tag is created only after checks, artifact hashes, and explicit video
validation are complete. Existing tags are immutable, including backport tags.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
from release_common import asset_names, native_version

parser = argparse.ArgumentParser()
parser.add_argument('--repo', default='Spaceghost/moonbeam')
parser.add_argument('--run-id', required=True, type=int)
parser.add_argument('--artifacts', required=True, type=Path)
parser.add_argument('--video-validated', action='store_true')
args = parser.parse_args()
if not args.video_validated:
    parser.error('Selected video decoder/renderer and live stream validation must finish before tagging.')

def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', f'repos/{args.repo}/{path}'], text=True))

run = api(f'actions/runs/{args.run_id}')
manifest = json.loads((args.artifacts / 'candidate.json').read_text())
if manifest.get('dirty', True):
    parser.error('Only an unmodified release-branch checkout can be promoted.')
if run['conclusion'] != 'success' or run['path'] != '.github/workflows/release-candidate.yml':
    parser.error('Select a successful Moonbeam release-candidate workflow run.')
if run['event'] not in ('push', 'workflow_dispatch'):
    parser.error('Candidate must come from a branch build, not a pull request.')
if not run['head_branch'].startswith('release/') or run['head_sha'] != manifest['commit']:
    parser.error('Candidate source must match the successful release-branch build exactly.')
if str(manifest['run_id']) != str(args.run_id):
    parser.error('Artifact run ID does not match the selected workflow run.')
if manifest.get('schema') != 3 or manifest.get('complete') is not True:
    parser.error('Promotion requires a complete multi-platform candidate (schema 3).')
if manifest.get('branch') != run['head_branch']:
    parser.error('Candidate branch does not match the selected workflow run.')
expected_version = manifest['base_version']
if manifest['version'] != expected_version:
    parser.error('Candidate version must match the stable release version.')
try:
    native_version(manifest['base_version'])
except ValueError as error:
    parser.error(str(error))
if set(manifest['sha256']) != set(asset_names(expected_version, complete=True)):
    parser.error('Candidate must contain every required platform package and source archive.')
for name, expected in manifest['sha256'].items():
    if Path(name).name != name:
        parser.error('Invalid artifact filename.')
    path = args.artifacts / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        parser.error(f'Artifact checksum mismatch: {name}')
checksums = ''.join(f'{digest}  {name}\n' for name, digest in manifest['sha256'].items())
if (args.artifacts / 'Moonbeam-SHA256SUMS').read_text() != checksums:
    parser.error('Published checksum file does not match the verified manifest.')
release_notes = (args.artifacts / 'release-notes.md').read_bytes()
if hashlib.sha256(release_notes).hexdigest() != manifest.get('release_notes_sha256'):
    parser.error('Release notes do not match the candidate manifest.')
tag = 'v' + manifest['base_version']
existing = subprocess.run(['gh', 'api', f'repos/{args.repo}/git/ref/tags/{tag}'], capture_output=True)
if existing.returncode == 0:
    parser.error(f'{tag} already exists. Bump the version on the release branch; never move a published tag.')
if '404' not in existing.stderr.decode():
    parser.error('Could not verify tag availability; refusing to tag.')
notes = args.artifacts / 'publication-notes.md'
notes.write_text(release_notes.decode() + '\n\n' +
    f"Built and tested on `{run['head_branch']}` at `{manifest['commit']}`.\n\n"
    f"Candidate build: {run['html_url']}\n\n"
    "Selected decoder/renderer recreation and live streaming were validated before promotion. "
    "These are the exact candidate binaries, with no rebuild during promotion. "
    "candidate.json and the source manifest record the exact source commit for traceability.\n\n"
    "## Downloads\n\n" + ''.join(
        f"- [{label}](https://github.com/{args.repo}/releases/download/{tag}/{name})\n"
        for label, name in zip(
            ['Linux AppImage (x86_64)', 'Linux portable bundle (run ./install.sh)', 'Source archive',
             'Windows installer (x64 and ARM64)', 'Windows portable x64', 'Windows portable ARM64',
             'macOS universal (Intel and Apple Silicon)', 'Steam Link device'],
            asset_names(manifest['version'], complete=True))) +
    "\nNative packages are unsigned unless built with separately configured signing credentials. "
    "Snap, Flatpak, and Debian repositories for Moonlight distribute upstream Moonlight, not Moonbeam.\n")
assets = [str(args.artifacts / name) for name in manifest['sha256']]
assets += [str(args.artifacts / 'Moonbeam-SHA256SUMS'), str(args.artifacts / 'candidate.json')]
subprocess.run(['gh', 'release', 'create', tag, '--repo', args.repo,
    '--target', manifest['commit'], '--title', f'Moonbeam {manifest["base_version"]}',
    '--notes-file', str(notes), '--latest', '--prerelease=false', *assets], check=True)
