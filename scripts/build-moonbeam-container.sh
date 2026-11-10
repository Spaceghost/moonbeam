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
"${podman_cmd[@]}" exec \
    -e "MOONBEAM_BUILD_VERSION=${MOONBEAM_BUILD_VERSION:-}" "$container" \
    bash scripts/build-moonbeam-linux.sh
