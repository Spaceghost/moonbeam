#!/usr/bin/env bash
# Native checks/Steam Link on the admitted Ubuntu pool; portable Linux uses
# GitHub Ubuntu 22.04 explicitly to preserve its glibc 2.35 release baseline.
set -euo pipefail
# shellcheck source=/dev/null
source /etc/os-release
[[ $ID == ubuntu && ( $VERSION_ID == 22.04 || $VERSION_ID == 24.04 ) ]] || {
    echo 'Requires an admitted Ubuntu 22.04 or 24.04 worker'; exit 1;
}
sudo_cmd=(); if [[ $EUID -ne 0 ]]; then sudo_cmd=(sudo); fi
# The admitted pool permits HTTPS archive access. Keep suites and signing keys;
# change only official Ubuntu archive transport, including deb822 source files.
"${sudo_cmd[@]}" python3 - <<'PY'
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
export BUILD_JOBS=${BUILD_JOBS:-2}
exec "$@"
