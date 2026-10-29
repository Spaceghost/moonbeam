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
for name, expected in manifest['sha256'].items():
    if Path(name).name != name:
        parser.error('Invalid artifact filename.')
    path = args.artifacts / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        parser.error(f'Artifact checksum mismatch: {name}')
if not re.fullmatch(r'\d+\.\d+\.\d+-moonbeam\.\d+', manifest['base_version']):
    parser.error('Invalid Moonbeam release version.')
tag = 'v' + manifest['base_version']
existing = subprocess.run(['gh', 'api', f'repos/{args.repo}/git/ref/tags/{tag}'], capture_output=True)
if existing.returncode == 0:
    parser.error(f'{tag} already exists. Bump the version on the release branch; never move a published tag.')
if '404' not in existing.stderr.decode():
    parser.error('Could not verify tag availability; refusing to tag.')
notes = args.artifacts / 'release-notes.md'
notes.write_text(f"Moonbeam {manifest['base_version']}\n\n"
    f"Built and tested on `{run['head_branch']}` at `{manifest['commit']}`.\n\n"
    f"Candidate build: {run['html_url']}\n\n"
    "Selected decoder/renderer recreation and live streaming were validated before promotion. "
    "These are the exact candidate binaries, with no rebuild during promotion. "
    "The binary version includes its source commit for traceability.\n\n"
    "Extract the Linux x86_64 tarball and run `./install.sh`, or use the AppImage. "
    "Other operating systems and architectures require separate builds.\n")
assets = [str(args.artifacts / name) for name in manifest['sha256']]
assets += [str(args.artifacts / 'Moonbeam-SHA256SUMS'), str(args.artifacts / 'candidate.json')]
subprocess.run(['gh', 'release', 'create', tag, '--repo', args.repo,
    '--target', manifest['commit'], '--title', f'Moonbeam {manifest["base_version"]}',
    '--notes-file', str(notes), '--latest', *assets], check=True)
