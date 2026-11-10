"""Shared release version and asset contract for builders and promotion."""
import re


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
