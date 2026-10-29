#!/usr/bin/env python3
"""Stage upstream's portable decoder ABI with matching public headers.

Only dependencies are reused; the modified Moonlight client is compiled locally.
The official 6.2.0 runtime is pinned so modern NVIDIA Vulkan decoding is retained.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1]
deps = root / 'build/deps'
deps.mkdir(parents=True, exist_ok=True)

def write_if_changed(path, text):
    if not path.exists() or path.read_text() != text:
        path.write_text(text)

def download(name, url, digest):
    dest = deps / name
    if not dest.is_file():
        urllib.request.urlretrieve(url, dest)
    if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f'Checksum mismatch: {name}')
    return dest

runtime = os.environ.get('MOONLIGHT_UPSTREAM_APPIMAGE')
if runtime:
    archive = Path(runtime)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != '787b0dcbd42ae90620e76fb8d77d7c441ba6473a91c2d7fc3a0fc2466f992437':
        raise RuntimeError('Upstream AppImage checksum mismatch')
else:
    archive = download('Moonlight-6.2.0-x86_64.AppImage',
        'https://github.com/moonlight-stream/moonlight-qt/releases/download/v6.2.0/Moonlight-6.2.0-x86_64.AppImage',
        '787b0dcbd42ae90620e76fb8d77d7c441ba6473a91c2d7fc3a0fc2466f992437')
runtime_dir = deps / 'upstream-runtime'
if not (runtime_dir / 'squashfs-root/usr/lib/libavcodec.so.63').exists():
    runtime_dir.mkdir(exist_ok=True)
    archive.chmod(0o755)
    subprocess.run([str(archive), '--appimage-extract'], cwd=runtime_dir, check=True, stdout=subprocess.DEVNULL)

inputs = [
    ('ffmpeg.tar.gz', 'https://github.com/FFmpeg/FFmpeg/archive/refs/tags/n9.0.2.tar.gz',
     '6e374ed621e48faa40639307dff48ba6fe574a509977956d2cce9669b7cc27e9'),
    ('libplacebo.tar.gz', 'https://github.com/haasn/libplacebo/archive/92b5ac6db79f4d680eb656692f7bf51e9606f42a.tar.gz',
     '367eb22a5c366ad9152e44968fcaf4deaaf08f1835649150b887b51d79444d13'),
    ('vulkan.tar.gz', 'https://github.com/KhronosGroup/Vulkan-Headers/archive/refs/tags/v1.4.313.tar.gz',
     'f3298b8dc620530493296759858a69b622f98ececa0e8c75488ad2000778148f')]
for name, url, digest in inputs:
    archive = download(name, url, digest)
    with tarfile.open(archive) as tar:
        directory = tar.getmembers()[0].name.split('/')[0]
        if not (deps / directory).is_dir():
            # Archives are pinned by SHA-256 before extraction.
            tar.extractall(deps)

sdk = deps / 'sdk'
include, lib = sdk / 'include', sdk / 'lib'
include.mkdir(parents=True, exist_ok=True)
(lib / 'pkgconfig').mkdir(parents=True, exist_ok=True)
for name in ['libavcodec', 'libavutil', 'libavformat', 'libswscale']:
    shutil.copytree(deps / 'FFmpeg-n9.0.2' / name, include / name, dirs_exist_ok=True)
shutil.copytree(deps / 'libplacebo-92b5ac6db79f4d680eb656692f7bf51e9606f42a/src/include/libplacebo',
                include / 'libplacebo', dirs_exist_ok=True)
shutil.copytree(deps / 'Vulkan-Headers-1.4.313/include', include, dirs_exist_ok=True)
write_if_changed(include / 'libavutil/avconfig.h',
    '#ifndef AVUTIL_AVCONFIG_H\n#define AVUTIL_AVCONFIG_H\n'
    '#define AV_HAVE_BIGENDIAN 0\n#define AV_HAVE_FAST_UNALIGNED 1\n#endif\n')
config = (include / 'libplacebo/config.h.in').read_text()
config = config.replace('@majorver@', '7').replace('@apiver@', '374')
config = config.replace('@extra_defs@', '#define PL_HAVE_VULKAN 1\n#define PL_HAVE_LCMS 1\n#define PL_HAVE_SHADERC 1')
write_if_changed(include / 'libplacebo/config.h', config)

versions = {'libavcodec': ('63', '63.0.100', 'avcodec'),
            'libavutil': ('61', '61.0.100', 'avutil'),
            'libswscale': ('10', '10.0.100', 'swscale'),
            'libplacebo': ('374', '7.374.0', 'placebo')}
upstream_lib = runtime_dir / 'squashfs-root/usr/lib'
for name in ['libavcodec.so.63', 'libavutil.so.61', 'libswscale.so.10',
             'libplacebo.so.374', 'libshaderc_shared.so.1', 'libvulkan.so.1',
             'libSDL2_ttf-2.0.so.0', 'liblcms2.so.2']:
    shutil.copy2(upstream_lib / name, lib / name)
fallback = runtime_dir / 'squashfs-root/opt/libva-fallback'
if not (sdk / 'opt/libva-fallback/libva-probe').exists():
    shutil.copytree(fallback, sdk / 'opt/libva-fallback', dirs_exist_ok=True, symlinks=True)
for path in fallback.glob('libva*.so*'):
    shutil.copy2(path, lib / path.name)
for name, (abi, version, linker_name) in versions.items():
    symlink = lib / (name + '.so')
    if not symlink.exists(): symlink.symlink_to(f'{name}.so.{abi}')
    write_if_changed(lib / 'pkgconfig' / (name + '.pc'),
        f'prefix={sdk}\nlibdir=${{prefix}}/lib\nincludedir=${{prefix}}/include\n'
        f'Name: {name}\nDescription: Pinned Moonlight portable dependency\nVersion: {version}\n'
        f'Libs: -L${{libdir}} -l{linker_name}\nCflags: -I${{includedir}}\n')
for name, dest in [('libSDL2.so', 'libSDL2-2.0.so.0'), ('libSDL2_ttf.so', 'libSDL2_ttf-2.0.so.0')]:
    link = lib / name
    if not link.exists(): link.symlink_to(dest)
sdl_archive = download('SDL2-2.32.10.tar.gz',
    'https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.tar.gz',
    '5f5993c530f084535c65a6879e9b26ad441169b3e25d789d83287040a9ca5165')
sdl_source = deps / 'SDL2-2.32.10'
if not sdl_source.exists():
    with tarfile.open(sdl_archive) as archive:
        archive.extractall(deps)
stamp = sdk / '.native-sdl2-2.32.10-wayland-pulse'
if not stamp.exists():
    build = deps / 'SDL2-build'
    subprocess.run(['cmake', '-S', str(sdl_source), '-B', str(build),
        '-DCMAKE_BUILD_TYPE=Release', f'-DCMAKE_INSTALL_PREFIX={sdk}',
        '-DSDL_SHARED=ON', '-DSDL_STATIC=OFF', '-DSDL_TEST=OFF', '-DSDL_TESTS=OFF',
        '-DSDL_WAYLAND=ON', '-DSDL_WAYLAND_SHARED=ON', '-DSDL_WAYLAND_LIBDECOR=ON',
        '-DSDL_PULSEAUDIO=ON', '-DSDL_PIPEWIRE=OFF', '-DSDL_VULKAN=ON'], check=True)
    subprocess.run(['cmake', '--build', str(build), '-j', os.environ.get('BUILD_JOBS', '8')], check=True)
    subprocess.run(['cmake', '--install', str(build)], check=True)
    # Check capabilities, not just the filename: sdl2-compat has the same SONAME.
    import ctypes
    runtime = ctypes.CDLL(str(lib / 'libSDL2-2.0.so.0'))
    runtime.SDL_GetVideoDriver.restype = ctypes.c_char_p
    drivers = [runtime.SDL_GetVideoDriver(i).decode() for i in range(runtime.SDL_GetNumVideoDrivers())]
    if 'wayland' not in drivers:
        raise RuntimeError(f'SDL was built without native Wayland: {drivers}')
    stamp.write_text('SDL 2.32.10; Wayland; PulseAudio; no sdl2-compat\n')
print(f'Prepared FFmpeg 9 / libplacebo 374 / native SDL2 2.32.10 in {sdk}')
