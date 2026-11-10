#!/usr/bin/env bash
# Compile on an immutable Fedora/Bazzite host without modifying its OS image.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
storage="${MOONBEAM_BUILD_STORAGE:-$(dirname "$root")/.moonbeam-container-storage}"
runtime="${MOONBEAM_BUILD_RUNTIME:-$(dirname "$root")/.moonbeam-container-run}"
workspace_id=$(printf '%s' "$root" | sha256sum | cut -c1-12)
container=${MOONBEAM_BUILD_CONTAINER:-moonbeam-build-$workspace_id}
extra_mounts=()
if [[ -f "$root/.git" ]]; then
    common_git=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir)
    extra_mounts+=(-v "$common_git:$common_git")
fi
podman_cmd=(podman --storage-driver=vfs --root "$storage" --runroot "$runtime")
if ! "${podman_cmd[@]}" container exists "$container"; then
    "${podman_cmd[@]}" run -d --name "$container" --security-opt label=disable \
        -v "$root:/src" -v "$root:$root" "${extra_mounts[@]}" -w "$root" \
        docker.io/library/ubuntu:22.04 sleep infinity
fi
"${podman_cmd[@]}" start "$container" >/dev/null
"${podman_cmd[@]}" exec \
    -e "MOONBEAM_BUILD_VERSION=${MOONBEAM_BUILD_VERSION:-}" "$container" \
    bash scripts/build-moonbeam-linux.sh
