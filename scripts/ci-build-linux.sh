#!/usr/bin/env bash
set -euo pipefail
bash scripts/build-moonbeam-linux.sh
python3 tests/test_ci_runner.py
python3 tests/test_installer.py
python3 tests/test_release_promotion.py
python3 tests/test_release_artifacts.py
sudo_cmd=(); if [[ $EUID -ne 0 ]]; then sudo_cmd=(sudo); fi
"${sudo_cmd[@]}" apt-get install -y --no-install-recommends \
    libva-wayland2 libva-x11-2 libegl1 libgl1 libopengl0 libvulkan1 libx11-6 \
    libwayland-client0 libdrm2 libfontconfig1 libglib2.0-0 libharfbuzz0b libfreetype6
version=$(cat app/moonbeam-version.txt)
QT_QPA_PLATFORM=offscreen "dist/Moonbeam-$version-x86_64.AppImage" --appimage-extract-and-run --version
python3 scripts/release-artifacts.py "$version"
(cd dist; sha256sum -c Moonbeam-SHA256SUMS)
