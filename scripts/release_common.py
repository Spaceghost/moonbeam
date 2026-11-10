"""Shared release version and asset contract for builders and promotion."""
import re


def native_version(base):
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)-moonbeam\.(\d+)', base)
    if not match:
        raise ValueError('Expected MAJOR.MINOR.PATCH-moonbeam.REVISION')
    major, minor, patch, revision = map(int, match.groups())
    # MSI ignores a fourth component. Reserve 1000 fork revisions per upstream patch.
    if not (major <= 255 and minor <= 255 and revision < 1000 and patch * 1000 + revision <= 65535):
        raise ValueError('Release version exceeds native installer limits')
    return f'{major}.{minor}.{patch * 1000 + revision}'


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
