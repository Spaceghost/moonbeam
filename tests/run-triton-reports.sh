#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source="$PWD/build/deps/SDL2-2.32.10"
cc -std=c99 -O1 -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -DUSING_GENERATED_CONFIG_H \
  -I"$PWD/build/deps/SDL2-build/include" -I"$PWD/build/deps/SDL2-build/include/SDL2" \
  -I"$PWD/build/deps/SDL2-build/include-config-release/SDL2" -I"$source/include" \
  -DTRITON_DRIVER="\"$source/src/joystick/hidapi/SDL_hidapi_steam_triton.c\"" \
  tests/triton_reports.c -o build/triton-reports-test
build/triton-reports-test
