#!/usr/bin/env bash
# Run in the Ubuntu 22.04 build container, with the repository at /src.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
version=6.2.0-moonbeam.1
mkdir -p build/native-vulkan build/tools dist
python3 scripts/prepare-moonbeam-sdk.py
export PKG_CONFIG_PATH="$root/build/deps/sdk/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export LD_LIBRARY_PATH="$root/build/deps/sdk/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd build/native-vulkan
qmake6 "$root/moonlight-qt.pro" CONFIG+=release CONFIG+=disable-libdrm PREFIX=/usr
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
    --library="$root/build/deps/sdk/lib/libSDL3.so.0" \
    --library=/usr/lib/x86_64-linux-gnu/libssl.so.3 \
    --library=/usr/lib/x86_64-linux-gnu/libQt6WaylandClient.so.6 \
    --library=/usr/lib/x86_64-linux-gnu/libQt6WaylandEglClientHwIntegration.so.6 \
    --exclude-library='libva*.so*' --exclude-library='libwayland*.so*' \
    --output appimage
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
sha256sum ./*.AppImage ./*.tar.gz > SHA256SUMS
