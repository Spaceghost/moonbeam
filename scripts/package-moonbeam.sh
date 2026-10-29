#!/usr/bin/env bash
# Run in the Ubuntu 22.04 build container, with the repository at /src.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
version=${MOONBEAM_BUILD_VERSION:-$(cat app/moonbeam-version.txt)}
mkdir -p build/native-vulkan build/tools dist
python3 scripts/prepare-moonbeam-sdk.py
export PKG_CONFIG_PATH="$root/build/deps/sdk/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export LD_LIBRARY_PATH="$root/build/deps/sdk/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd build/native-vulkan
qmake6 "$root/moonlight-qt.pro" CONFIG+=release CONFIG+=disable-libdrm PREFIX=/usr "MOONBEAM_VERSION=$version"
make qmake_all
make -j"${BUILD_JOBS:-8}" release
rm -rf "$root/build/Moonbeam.AppDir"
make INSTALL_ROOT="$root/build/Moonbeam.AppDir" install
cd "$root/build/tools"
for tool in linuxdeploy linuxdeploy-plugin-qt; do
    if [[ ! -x "$tool/AppRun" ]]; then
        curl -fL --retry 3 "https://github.com/linuxdeploy/$tool/releases/download/continuous/$tool-x86_64.AppImage" -o "$tool.AppImage"
        chmod +x "$tool.AppImage"
        mkdir -p "$tool"
        (cd "$tool"; "../$tool.AppImage" --appimage-extract >/dev/null; cp -a squashfs-root/. .; rm -rf squashfs-root)
    fi
done
export QMAKE=qmake6 QML_SOURCES_PATHS="$root/app/gui" EXTRA_QT_MODULES="waylandclient"
export PATH="$root/build/tools/bin:$PATH"
mkdir -p bin
ln -sfn "$root/build/tools/linuxdeploy-plugin-qt/AppRun" bin/linuxdeploy-plugin-qt
appdir="$root/build/Moonbeam.AppDir"
mkdir -p "$appdir/opt"
cp -a "$root/build/deps/sdk/opt/libva-fallback" "$appdir/opt/"
# The Qt deploy plugin does not discover all Qt 6 Wayland platform plugins.
qtplugins=$(qmake6 -query QT_INSTALL_PLUGINS)
mkdir -p "$appdir/usr/plugins/platforms"
cp "$qtplugins"/platforms/libqwayland*.so "$qtplugins"/platforms/libqoffscreen.so \
    "$qtplugins"/platforms/libqminimal.so "$appdir/usr/plugins/platforms/"
for directory in wayland-graphics-integration-client wayland-shell-integration wayland-decoration-client; do
    [[ ! -d "$qtplugins/$directory" ]] || cp -a "$qtplugins/$directory" "$appdir/usr/plugins/"
done
# Use the host's GPU-facing libraries so current Bazzite drivers remain usable.
cat > "$root/build/AppRun" <<'EOF'
#!/usr/bin/env bash
set -e
APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")}"
# Older bundled Qt otherwise chooses XWayland even in a native Wayland session.
# Preserve explicit user choices, including offscreen diagnostics.
if [[ -z "${QT_QPA_PLATFORM:-}" && -n "${WAYLAND_DISPLAY:-}" && -S "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/$WAYLAND_DISPLAY" ]]; then
    export QT_QPA_PLATFORM=wayland
fi
# Qt's launcher can fail to allocate an OpenGL context when the NVIDIA display
# GPU is busy. The streaming renderer and hardware decoder do not use Qt Quick.
# Keep user-selected Qt Quick backends, including graphics diagnostics.
if [[ -z "${QT_QUICK_BACKEND:-}" && "${QT_QPA_PLATFORM:-}" == wayland && -r /proc/driver/nvidia/version ]]; then
    export QT_QUICK_BACKEND=software
fi
# PulseAudio's protocol also works with PipeWire's pulse server. Prefer its
# stable SDL path when that server exists; leave ALSA/other desktops untouched.
if [[ -z "${SDL_AUDIODRIVER:-}" && -S "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/pulse/native" ]]; then
    export SDL_AUDIODRIVER=pulseaudio
fi
if ! "$APPDIR/opt/libva-fallback/libva-probe" 2>/dev/null; then
    export LD_LIBRARY_PATH="$APPDIR/opt/libva-fallback${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export VAAPI_USE_FALLBACK_PATHS=1
fi
export QT_PLUGIN_PATH="$APPDIR/usr/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
export QML2_IMPORT_PATH="$APPDIR/usr/qml${QML2_IMPORT_PATH:+:$QML2_IMPORT_PATH}"
export LD_LIBRARY_PATH="$APPDIR/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$APPDIR/usr/bin/moonbeam" "$@"
EOF
chmod +x "$root/build/AppRun"
cd "$root/dist"
export VERSION="$version" APPIMAGE_EXTRACT_AND_RUN=1
rm -f "$root/dist/Moonbeam-$version-x86_64.AppImage"
"$root/build/tools/linuxdeploy/AppRun" --appdir "$appdir" --plugin qt \
    --custom-apprun "$root/build/AppRun" \
    --library=/usr/lib/x86_64-linux-gnu/libssl.so.3 \
    --library=/usr/lib/x86_64-linux-gnu/libQt6WaylandClient.so.6 \
    --library=/usr/lib/x86_64-linux-gnu/libQt6WaylandEglClientHwIntegration.so.6 \
    --exclude-library='libva*.so*' --exclude-library='libwayland*.so*' \
    --exclude-library='libglib-2.0.so*' --exclude-library='libgobject-2.0.so*' \
    --exclude-library='libgio-2.0.so*' --exclude-library='libgmodule-2.0.so*' --exclude-library='libgthread-2.0.so*'
# The Qt plugin redeploys its own dependencies without inheriting linuxdeploy's
# exclusion list. Prune those host-library families after the plugin finishes,
# then create the image in a second pass without the Qt plugin.
python3 - "$appdir" <<'PY'
from pathlib import Path
import sys
lib = Path(sys.argv[1]) / 'usr/lib'
for pattern in ['libglib-2.0.so*', 'libgobject-2.0.so*', 'libgio-2.0.so*',
                'libgmodule-2.0.so*', 'libgthread-2.0.so*', 'libwayland*.so*']:
    for path in lib.glob(pattern):
        path.unlink()
PY
"$root/build/tools/linuxdeploy/AppRun" --appdir "$appdir" \
    --exclude-library='libva*.so*' --exclude-library='libwayland*.so*' \
    --exclude-library='libglib-2.0.so*' --exclude-library='libgobject-2.0.so*' \
    --exclude-library='libgio-2.0.so*' --exclude-library='libgmodule-2.0.so*' --exclude-library='libgthread-2.0.so*' \
    --custom-apprun "$root/build/AppRun" --output appimage
bundle="$root/dist/moonbeam-$version-linux-x86_64"
rm -rf "$bundle"
mkdir -p "$bundle"
cp -a "$appdir" "$bundle/"
cp "$root/scripts/install-moonbeam.sh" "$bundle/install.sh"
cp "$root/MOONBEAM.md" "$bundle/README.md"
cp "$root/LICENSE" "$bundle/"
printf '%s\n' "$version" > "$bundle/VERSION"
chmod +x "$bundle/install.sh"
tar -czf "moonbeam-$version-linux-x86_64.tar.gz" "$(basename "$bundle")"
python3 "$root/scripts/release-artifacts.py" "$version"
