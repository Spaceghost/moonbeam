# Moonbeam

Moonbeam is a Moonlight Qt fork that automatically resumes your running game after a network interruption. It builds on [Moonlight](https://github.com/moonlight-stream/moonlight-qt) and works with Sunshine and compatible GameStream hosts.

## Install

Download the Linux x86_64 portable bundle from [Releases](https://github.com/Spaceghost/moonbeam/releases/latest), extract it, and run:

```sh
./install.sh
```

Launch **Moonbeam** from your applications menu, or run `~/.local/bin/moonbeam`. Installation needs no root access, FUSE, or changes to Bazzite's system image. An AppImage is available too. The installer imports this machine's existing Moonlight pairing and keeps Moonbeam settings separate. Existing settings from the earlier Moonlight Resilient build are migrated automatically.

Defaults are **1920×1080, 60 FPS, 30 Mbps**, frame pacing, and automatic reconnect. Adjust them in Settings to suit your network and hardware. The host/game must also render at 1080p for a true 1080p image.

## Recovery

- Resume the same running app after the old connection has finished shutting down.
- Retry up to 12 times with 1, 2, 4, 8, then 10 second delays; 30 seconds of stable streaming resets the budget.
- Cancel recovery from the reconnect screen.
- Stop when the original game has ended, another app is running, or the host reports an authentication or fatal encoding error.
- Intentional disconnects are never retried. Automatic reconnect can be disabled in Settings.

Recovery reconnects a dropped stream; it does not prevent packet loss or repair a failing network. Recovery lifecycle tests pass, and NVIDIA Vulkan decoding and Wayland startup have been checked on Bazzite. A live network interruption during an active game has not yet been validated.

## Build and test

```sh
git clone --recursive https://github.com/Spaceghost/moonbeam.git
cd moonbeam
bash scripts/build-moonbeam-container.sh
```

The Podman builder compiles the client in Ubuntu 22.04 and writes portable packages to `dist/`. FFmpeg 9 and libplacebo 374 reuse a SHA-256-pinned official Moonlight runtime with matching public headers. Genuine SDL 2.32.10 is built from pinned source with Wayland and PulseAudio support. Host GPU and GLib libraries remain on the host. See [dependency preparation](scripts/prepare-moonbeam-sdk.py), [packaging details](MOONBEAM.md), and [client performance research](docs/CLIENT-RESEARCH.md).

The portable release targets **Linux x86_64 with glibc 2.35+**, including Bazzite/Fedora and Ubuntu 22.04+. Other operating systems and architectures require separate builds. Upstream platform build documentation is preserved in [UPSTREAM_README.md](UPSTREAM_README.md).

Tests exercise the real reconnect QML with simulated transport events, termination policy, cancellation, retry limits, and installer migration/idempotency. Run the installer tests with `python3 tests/test_installer.py`; the container builder runs the Qt tests. No test interrupts an existing game session.

Run `moonbeam selftest` inside a graphical desktop to test the automatically selected decoder and renderer three times. This exercises the client path without connecting to a host or quitting a running game. For release validation, also check a real stream and audio.

## Releases and backports

Work uses branches and direct pushes. Push `release/**` to build and test a candidate; tagging is a separate promotion of the exact validated artifacts. Tags are immutable. Cherry-pick backports with `-x`, bump the Moonbeam patch version, and validate a new candidate before creating its tag. See [the release process](docs/RELEASES.md).

## License and attribution

Moonbeam retains Moonlight's **GPL-3.0-or-later** licensing; see [LICENSE](LICENSE). Original copyrights and notices remain in the source. Moonlight contributors developed the streaming client, protocol integration, decoders, and original artwork. Moonbeam adds recovery and portable packaging. Bundled third-party libraries retain their own licenses and notices.
