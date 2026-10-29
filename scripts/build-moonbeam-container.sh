#!/usr/bin/env bash
# Compile on an immutable Fedora/Bazzite host without modifying its OS image.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
storage="${MOONBEAM_BUILD_STORAGE:-$(dirname "$root")/.moonbeam-container-storage}"
runtime="${MOONBEAM_BUILD_RUNTIME:-$(dirname "$root")/.moonbeam-container-run}"
container=moonbeam-build
podman_cmd=(podman --storage-driver=vfs --root "$storage" --runroot "$runtime")
if ! "${podman_cmd[@]}" container exists "$container"; then
    "${podman_cmd[@]}" run -d --name "$container" --security-opt label=disable \
        -v "$root:/src" -w /src docker.io/library/ubuntu:22.04 sleep infinity
fi
"${podman_cmd[@]}" start "$container" >/dev/null
"${podman_cmd[@]}" exec -e DEBIAN_FRONTEND=noninteractive \
    -e "MOONBEAM_BUILD_VERSION=${MOONBEAM_BUILD_VERSION:-}" "$container" bash -lc '
    set -euo pipefail
    apt-get update -qq
    apt-get install -y --no-install-recommends eatmydata
    eatmydata apt-get install -y --no-install-recommends build-essential git ca-certificates curl wget file \
        python3 cmake pkg-config qt6-base-dev qt6-declarative-dev libqt6opengl6-dev libqt6svg6-dev qt6-base-dev-tools qt6-wayland \
        qml6-module-qtquick-controls qml6-module-qtquick-templates qml6-module-qtquick-layouts \
        qml6-module-qtqml-workerscript qml6-module-qtquick-window qml6-module-qtquick \
        libsdl2-dev libsdl2-ttf-dev libavcodec-dev libavutil-dev libswscale-dev libssl-dev libopus-dev \
        libva-dev libvdpau-dev libx11-dev libegl1-mesa-dev libdrm-dev libwayland-dev wayland-protocols \
        libdecor-0-dev libxkbcommon-dev patchelf desktop-file-utils \
        zsync squashfs-tools xvfb xauth
    bash scripts/package-moonbeam.sh
    mkdir -p build/reconnect-tests
    cd build/reconnect-tests
    qmake6 ../../tests/reconnect/reconnect.pro
    make -j4
    QT_QPA_PLATFORM=offscreen STREAM_SEGUE_SOURCE=/src/app/gui/StreamSegue.qml ./reconnect-test
'
