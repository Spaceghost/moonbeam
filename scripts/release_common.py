"""Shared release version and asset contract for builders and promotion."""
import re
import json

UPSTREAM_REPOSITORY = 'https://github.com/moonlight-stream/moonlight-qt.git'


def validate_upstream_release(upstream, version):
    """Public Moonbeam versions are exact counterparts of a Moonlight tag."""
    native_version(version)
    if upstream.get('repository') != UPSTREAM_REPOSITORY:
        raise ValueError('Release must mirror the official Moonlight repository')
    if upstream.get('tag') != 'v' + version or upstream.get('version') != version:
        raise ValueError('Moonbeam version must exactly match its published Moonlight release tag')
    if not re.fullmatch(r'[0-9a-f]{40}', upstream.get('commit', '')):
        raise ValueError('Pin the exact upstream release commit')
    return upstream


def upstream_release(root):
    record = json.loads((root / 'upstream.json').read_text())
    version = (root / 'app/moonbeam-version.txt').read_text().strip()
    if (root / 'app/version.txt').read_text().strip() != version:
        raise ValueError('Moonbeam and upstream application versions must match')
    return validate_upstream_release(dict(repository=record['repository'],
        tag=record['release_tag'], version=record['base_version'],
        commit=record['release_commit']), version)


def native_version(base):
    match = re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', base)
    if not match:
        raise ValueError('Expected stable MAJOR.MINOR.PATCH without suffixes')
    major, minor, patch = map(int, match.groups())
    if not (major <= 255 and minor <= 255 and patch <= 65535):
        raise ValueError('Release version exceeds native installer limits')
    return base



def asset_names(version, complete=False):
    names = [f'Moonbeam-{version}-x86_64.AppImage',
             f'moonbeam-{version}-linux-x86_64.tar.gz',
             f'moonbeam-{version}-source.tar.gz']
    if complete:
        names += [f'MoonbeamSetup-{version}.exe',
                  f'MoonbeamPortable-x64-{version}.zip',
                  f'MoonbeamPortable-arm64-{version}.zip',
                  f'Moonbeam-{version}.dmg', f'Moonbeam-SteamLink-{version}.zip']
    return names
