#!/usr/bin/env bash
# Keep release ABI at Ubuntu 22.04 even when the isolated worker runs 24.04.
# PRoot is a userspace compatibility environment, not a security boundary;
# security comes from the existing disposable, unprivileged Incus worker.
set -euo pipefail
# shellcheck source=/dev/null
source /etc/os-release
if [[ $ID == ubuntu && $VERSION_ID == 22.04 ]]; then
    exec "$@"
fi
[[ $(uname -m) == x86_64 ]] || { echo 'Requires an x86_64 worker'; exit 1; }
# The admitted pool permits HTTPS archive access. Keep suites and signing keys;
# change only official Ubuntu archive transport, including deb822 source files.
sudo python3 - <<'PY'
from pathlib import Path
import re
paths = [Path('/etc/apt/sources.list'), *Path('/etc/apt/sources.list.d').glob('*.list'),
         *Path('/etc/apt/sources.list.d').glob('*.sources')]
for path in paths:
    if path.is_file():
        before = path.read_text()
        after = re.sub(r'http://((?:[a-z]{2}\.)?archive\.ubuntu\.com|security\.ubuntu\.com|ports\.ubuntu\.com)/',
                       r'https://\1/', before)
        if before != after:
            path.write_text(after)
PY
sudo apt-get -o Acquire::Retries=3 -o Acquire::https::Timeout=30 update -qq
sudo apt-get install -y --no-install-recommends proot ca-certificates curl
task_tmp=${RUNNER_TEMP:?RUNNER_TEMP is required}
rootfs="$task_tmp/moonbeam-jammy"
if [[ ! -f $rootfs/.moonbeam-ready ]]; then
    archive="$task_tmp/ubuntu-base-22.04.5-base-amd64.tar.gz"
    curl -fL --retry 3 --connect-timeout 30 \
        https://cdimage.ubuntu.com/ubuntu-base/releases/22.04/release/ubuntu-base-22.04.5-base-amd64.tar.gz -o "$archive"
    echo "242cd8898b33ea806ef5f13b1076ed7c76f9f989d18384452f7166692438ff1a  $archive" | sha256sum -c -
    mkdir -p "$rootfs"
    tar --extract --gzip --file "$archive" --directory "$rootfs" --no-same-owner --exclude='dev/*'
    sed -i 's|http://|https://|g' "$rootfs/etc/apt/sources.list"
    printf '%s\n' 'APT::Sandbox::User "root";' 'Acquire::Retries "3";' \
        'Acquire::https::Timeout "30";' > "$rootfs/etc/apt/apt.conf.d/99moonbeam"
    # Seed the guest-owned bundle for HTTPS bootstrap. Bind-mounting the host
    # certificate directory breaks ca-certificates postinst under fake root.
    mkdir -p "$rootfs/etc/ssl/certs"
    cp /etc/ssl/certs/ca-certificates.crt "$rootfs/etc/ssl/certs/ca-certificates.crt"
    touch "$rootfs/.moonbeam-ready"
fi
# Bind the checkout and runner scratch only; no host credentials or sockets.
exec proot -0 -R "$rootfs" -b "$PWD:/workspace" -b "$task_tmp:/ci-tmp" \
    -w /workspace /usr/bin/env \
    HOME=/root TMPDIR=/ci-tmp TMP=/ci-tmp TEMP=/ci-tmp \
    GITHUB_WORKSPACE=/workspace BUILD_JOBS=2 QT_QPA_PLATFORM=offscreen "$@"
