#!/usr/bin/env python3
"""Replace only the native Windows/macOS SDL2 dependency with our pinned backport."""
import argparse
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--arch', choices=['x64', 'arm64', 'universal'], required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
deps = root / 'build/deps'
deps.mkdir(parents=True, exist_ok=True)
archive = deps / 'SDL2-2.32.10.tar.gz'
if not archive.exists():
    urllib.request.urlretrieve('https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.tar.gz', archive)
if hashlib.sha256(archive.read_bytes()).hexdigest() != '5f5993c530f084535c65a6879e9b26ad441169b3e25d789d83287040a9ca5165':
    raise RuntimeError('SDL2 archive checksum mismatch')
source = deps / 'SDL2-2.32.10'
if not source.exists():
    with tarfile.open(archive) as tar:
        tar.extractall(deps)
subprocess.run([sys.executable, str(root / 'scripts/patch-sdl2-triton.py'), str(source)], check=True)
build = deps / ('SDL2-triton-' + args.arch)
install = build / 'install'
configure = ['cmake', '-S', str(source), '-B', str(build),
             '-DCMAKE_BUILD_TYPE=Release', '-DSDL_SHARED=ON', '-DSDL_STATIC=OFF',
             '-DSDL_TEST=OFF', '-DSDL_TESTS=OFF', '-DSDL2_DISABLE_INSTALL=OFF',
             '-DCMAKE_INSTALL_PREFIX=' + str(install)]
if platform.system() == 'Windows':
    if args.arch == 'universal': raise RuntimeError('Use x64 or arm64 on Windows')
    configure += ['-A', 'ARM64' if args.arch == 'arm64' else 'x64']
elif platform.system() == 'Darwin':
    if args.arch != 'universal': raise RuntimeError('macOS builds must be universal')
    configure += ['-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64', '-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0',
                  '-DCMAKE_INSTALL_NAME_DIR=@rpath']
else:
    raise RuntimeError('Linux uses prepare-moonbeam-sdk.py')
subprocess.run(configure, check=True)
subprocess.run(['cmake', '--build', str(build), '--config', 'Release', '--parallel', '4'], check=True)
subprocess.run(['cmake', '--install', str(build), '--config', 'Release'], check=True)
if platform.system() == 'Windows':
    target = root / 'libs/windows'
    shutil.copytree(install / 'include/SDL2', target / 'include' / args.arch / 'SDL2', dirs_exist_ok=True)
    for file in (install / 'lib').glob('SDL2*.lib'):
        shutil.copy2(file, target / 'lib' / args.arch / file.name)
    dll = install / 'bin/SDL2.dll'
    if not dll.exists(): raise RuntimeError('Patched SDL2 DLL missing')
    shutil.copy2(dll, target / 'lib' / args.arch / dll.name)
else:
    target = root / 'libs/mac'
    shutil.copytree(install / 'include/SDL2', target / 'include/SDL2', dirs_exist_ok=True)
    for file in (install / 'lib').glob('libSDL2*.dylib'):
        destination = target / 'lib' / file.name
        if destination.is_symlink(): destination.unlink()
        shutil.copy2(file, destination)
