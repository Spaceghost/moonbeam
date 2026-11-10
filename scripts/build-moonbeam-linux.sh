#!/usr/bin/env bash
# Build on Ubuntu 22.04, either a CI runner or the local Podman builder.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
sudo_cmd=()
if [[ $EUID -ne 0 ]]; then
    sudo_cmd=(sudo)
fi
"${sudo_cmd[@]}" env DEBIAN_FRONTEND=noninteractive apt-get update -qq
"${sudo_cmd[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends eatmydata
"${sudo_cmd[@]}" env DEBIAN_FRONTEND=noninteractive eatmydata apt-get install -y --no-install-recommends \
    build-essential git ca-certificates curl wget file python3 cmake pkg-config \
    qt6-base-dev qt6-declarative-dev libqt6opengl6-dev libqt6svg6-dev qt6-base-dev-tools qt6-wayland \
    qml6-module-qtquick-controls qml6-module-qtquick-templates qml6-module-qtquick-layouts \
    qml6-module-qtqml-workerscript qml6-module-qtquick-window qml6-module-qtquick \
    libsdl2-dev libsdl2-ttf-dev libavcodec-dev libavutil-dev libswscale-dev libssl-dev libopus-dev \
    libva-dev libvdpau-dev libx11-dev libegl1-mesa-dev libdrm-dev libwayland-dev wayland-protocols \
    libdecor-0-dev libxkbcommon-dev patchelf desktop-file-utils zsync squashfs-tools xvfb xauth
bash scripts/package-moonbeam.sh
mkdir -p build/reconnect-tests
cd build/reconnect-tests
qmake6 ../../tests/reconnect/reconnect.pro
make -j4
QT_QPA_PLATFORM=offscreen STREAM_SEGUE_SOURCE="$root/app/gui/StreamSegue.qml" ./reconnect-test

cd "$root"
mkdir -p build/profile-tests
cd build/profile-tests
qmake6 ../../tests/profiles/profiles.pro
make -j4
QT_QPA_PLATFORM=offscreen GAME_PROFILE_SOURCE="$root/app/gui/profile-test.qml" ./profiles-test
