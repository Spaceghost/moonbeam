# Moonbeam

[![Checks](https://github.com/Spaceghost/moonbeam/actions/workflows/moonbeam.yml/badge.svg)](https://github.com/Spaceghost/moonbeam/actions/workflows/moonbeam.yml)
[![Release candidates](https://github.com/Spaceghost/moonbeam/actions/workflows/release-candidate.yml/badge.svg)](https://github.com/Spaceghost/moonbeam/actions/workflows/release-candidate.yml)

Moonbeam is a Moonlight Qt fork that automatically resumes your running game after a network interruption. It builds on [Moonlight](https://github.com/moonlight-stream/moonlight-qt) and works with Sunshine and compatible GameStream hosts.

## Install

[Releases](https://github.com/Spaceghost/moonbeam/releases/latest) mirror
Moonlight's exact version numbers and direct-download platforms, with Moonbeam's
changes replayed on top. Moonlight v6.2.0 corresponds to Moonbeam v6.2.0.

Downloads include a Windows universal installer and x64/ARM64 portable ZIPs,
a universal macOS DMG, Linux x86_64 AppImage and installer bundle, Steam Link ZIP,
complete source, SHA-256 checksums and build provenance. See the [platform matrix
and release process](docs/RELEASES.md) and [upstream replay policy](docs/UPSTREAM.md).

Download the Linux x86_64 portable bundle from [Releases](https://github.com/Spaceghost/moonbeam/releases/latest), extract it, and run:

```sh
./install.sh
```

Launch **Moonbeam** from your applications menu, or run `~/.local/bin/moonbeam`. Installation needs no root access, FUSE, or changes to Bazzite's system image. An AppImage is available too. The installer imports this machine's existing Moonlight pairing and keeps Moonbeam settings separate. Existing settings from the earlier Moonlight Resilient build are migrated automatically.

Defaults are **1920×1080, 60 FPS, 30 Mbps**, frame pacing, and automatic reconnect. Adjust them in Settings to suit your network and hardware. The host/game must also render at 1080p for a true 1080p image.

## Steam Controller keyboard

Steam Controller 2026 users can enable the [radial trackpad keyboard](docs/STEAM-CONTROLLER.md)
while keeping normal PlayStation-style sticks, buttons, triggers and gyro.
The left pad selects a group and lifting the right thumb types one key.
This requires a client build containing the Triton driver; physical controller
validation and native Android/iOS integration are still outstanding.

## Per-game profiles

Right-click a game and choose **Stream settings…** to save its resolution, FPS,
bitrate, codec, decoder, renderer, frame pacing, and HDR. Profiles are separate
for each host/game and preserve global settings. **Use global settings** resets
a profile. CLI flags override saved values; `--no-game-profile` bypasses them.
See [profiles, NVIDIA options, and recovery](docs/PROFILES-AND-RECOVERY.md).

## Recovery

- Resume the same running app after the old connection has finished shutting down.
- Keep retrying with 1, 2, 4, 8, then 10 second delays; 30 seconds of stable streaming resets the delay.
- Cancel recovery from the reconnect screen.
- Stop when the original game has ended, another app is running, or the host reports an authentication or fatal encoding error.
- Intentional disconnects are never retried. Automatic reconnect can be disabled in Settings.

Recovery reconnects a dropped stream; it does not prevent packet loss or repair a failing network. Recovery lifecycle tests pass, and NVIDIA Vulkan decoding and Wayland startup have been checked on Bazzite. A twelve-second isolated network blackout has been checked against a live stream,
including same-app recovery and clear post-recovery pixels. See the
[validation record](docs/FEATURE-VALIDATION.md).

## Build and test

```sh
git clone --recursive https://github.com/Spaceghost/moonbeam.git
cd moonbeam
bash scripts/build-moonbeam-container.sh
```

The Podman builder compiles the client in Ubuntu 22.04 and writes portable packages to `dist/`. FFmpeg 9 and libplacebo 374 reuse a SHA-256-pinned official Moonlight runtime with matching public headers. Genuine SDL 2.32.10 is built from pinned source with Wayland and PulseAudio support. Host GPU and GLib libraries remain on the host. See [dependency preparation](scripts/prepare-moonbeam-sdk.py), [packaging details](MOONBEAM.md), and [client performance research](docs/CLIENT-RESEARCH.md).

The portable release targets **Linux x86_64 with glibc 2.35+**, including Bazzite/Fedora and Ubuntu 22.04+. Native Windows, macOS, and Steam Link packages are built by the release workflow;
see the [platform matrix](docs/RELEASES.md). Snap, Flatpak, and ARM Linux
repositories linked by Moonlight distribute upstream Moonlight. They do not install Moonbeam. Upstream platform build documentation is preserved in [UPSTREAM_README.md](UPSTREAM_README.md).

Tests exercise the real reconnect QML with simulated transport events, termination policy, cancellation, continued retries, and installer migration/idempotency. Run the installer tests with `python3 tests/test_installer.py`; the container builder runs the reconnect and profile Qt tests. Release checks also run
`python3 tests/test_release_promotion.py` and `python3 tests/test_release_artifacts.py`. No test interrupts an existing game session.

Run `moonbeam selftest` inside a graphical desktop to test the automatically selected decoder and renderer three times. This exercises the client path without connecting to a host or quitting a running game. For release validation, also check a real stream and audio.

## Releases and backports

Work uses branches and direct pushes. Push `release/**` to build and test a candidate; tagging is a separate promotion of the exact validated artifacts. Tags are immutable. Cherry-pick backports with `-x`, bump the Moonbeam patch version, and validate a new candidate before creating its tag. All platform builds must succeed before promotion. See [the release process](docs/RELEASES.md)
and [contributing](CONTRIBUTING.md).

## License and attribution

Moonbeam retains Moonlight's **GPL-3.0-or-later** licensing; see [LICENSE](LICENSE). Original copyrights and notices remain in the source. Moonlight contributors developed the streaming client, protocol integration, decoders, and original artwork. Moonbeam adds recovery and portable packaging. Bundled third-party libraries retain their own licenses and notices.
