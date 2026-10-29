#!/usr/bin/env bash
set -euo pipefail
umask 077
bundle=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(uname -m) == x86_64 ]] || { echo 'This build requires x86_64 Linux.' >&2; exit 1; }
[[ -x "$bundle/Moonlight-Resilient.AppDir/AppRun" ]] || { echo 'Extract the complete portable bundle before installing.' >&2; exit 1; }
version=$(cat "$bundle/VERSION")
install_root="${XDG_DATA_HOME:-$HOME/.local/share}/moonlight-resilient"
destination="$install_root/$version"
mkdir -p "$install_root" "$HOME/.local/bin" "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
if [[ ! -e "$destination" ]]; then
    stage=$(mktemp -d "$install_root/.install.XXXXXX")
    trap 'rm -rf -- "$stage"' EXIT
    cp -a "$bundle/Moonlight-Resilient.AppDir/." "$stage/"
    mv -- "$stage" "$destination"
    trap - EXIT
fi
ln -sfn "$destination" "$install_root/current"
ln -sfn "$install_root/current/AppRun" "$HOME/.local/bin/moonlight-resilient"

# Import only this machine's pairing. Never ship credentials in the bundle.
python3 - <<'PY'
import os, pathlib, re
home = pathlib.Path.home()
config = pathlib.Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config')))
target = config / 'Moonlight Game Streaming Project' / 'Moonlight Resilient.conf'
if not target.exists():
    sources = [home / '.var/app/com.moonlight_stream.Moonlight/config/Moonlight Game Streaming Project/Moonlight.conf',
               config / 'Moonlight Game Streaming Project/Moonlight.conf']
    source = next((p for p in sources if p.is_file()), None)
    text = source.read_text() if source else '[General]\n'
    settings = {'width': '1920', 'height': '1080', 'fps': '60', 'bitrate': '30000',
                'autoreconnect': 'true', 'framepacing': 'true', 'quitAppAfter': 'false'}
    for key, value in settings.items():
        pattern = rf'(?m)^{re.escape(key)}=.*$'
        if re.search(pattern, text):
            text = re.sub(pattern, f'{key}={value}', text)
        else:
            text = text.replace('[General]\n', f'[General]\n{key}={value}\n', 1)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(text)
    print('Imported local Moonlight pairing.' if source else 'Created 1080p/60 settings; pair your host in the app.')
else:
    print('Kept existing Moonlight Resilient settings.')
PY
desktop="${XDG_DATA_HOME:-$HOME/.local/share}/applications/com.moonlight_stream.Moonlight.Resilient.desktop"
cat > "$desktop" <<EOF
[Desktop Entry]
Name=Moonlight Resilient
Comment=1080p game streaming with automatic reconnect
Exec="$HOME/.local/bin/moonlight-resilient"
Icon=$install_root/current/usr/share/icons/hicolor/scalable/apps/moonlight.svg
Terminal=false
Type=Application
Categories=Game;Network;RemoteAccess;
StartupWMClass=com.moonlight_stream.Moonlight.Resilient
EOF
command -v update-desktop-database >/dev/null && update-desktop-database "$(dirname "$desktop")" || true
printf 'Installed %s. Launch Moonlight Resilient from your applications menu.\n' "$version"
