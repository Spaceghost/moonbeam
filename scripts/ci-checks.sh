#!/usr/bin/env bash
set -euo pipefail
export QT_QPA_PLATFORM=offscreen
sudo_cmd=(); if [[ $EUID -ne 0 ]]; then sudo_cmd=(sudo); fi
cd "${GITHUB_WORKSPACE:-$(pwd)}"
"${sudo_cmd[@]}" apt-get update -qq
"${sudo_cmd[@]}" apt-get install -y --no-install-recommends build-essential python3 git ca-certificates qt6-base-dev \
  qt6-declarative-dev libqt6opengl6-dev qml6-module-qtquick-controls \
  qml6-module-qtquick-templates qml6-module-qtquick-window qml6-module-qtqml-workerscript \
  qml6-module-qtquick qml6-module-qtquick-layouts
cd "${GITHUB_WORKSPACE:-$(pwd)}"
python3 tests/test_ci_runner.py
python3 tests/test_installer.py
python3 tests/test_release_promotion.py
python3 tests/test_release_artifacts.py
cd "${GITHUB_WORKSPACE:-$(pwd)}"
mkdir -p build/reconnect-tests
cd build/reconnect-tests
qmake6 ../../tests/reconnect/reconnect.pro
make -j2
STREAM_SEGUE_SOURCE="$GITHUB_WORKSPACE/app/gui/StreamSegue.qml" ./reconnect-test
cd "${GITHUB_WORKSPACE:-$(pwd)}"
mkdir -p build/profile-tests
cd build/profile-tests
qmake6 ../../tests/profiles/profiles.pro
make -j2
GAME_PROFILE_SOURCE="$GITHUB_WORKSPACE/app/gui/profile-test.qml" ./profiles-test
cd "${GITHUB_WORKSPACE:-$(pwd)}"
mkdir -p build/profile-minimal-tests
cd build/profile-minimal-tests
qmake6 ../../tests/profiles/profiles.pro CONFIG+=no_ffmpeg
make -j2
GAME_PROFILE_SOURCE="$GITHUB_WORKSPACE/app/gui/profile-test.qml" ./profiles-test
