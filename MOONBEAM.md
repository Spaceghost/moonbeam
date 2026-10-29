# Moonbeam

A fork of Moonlight Qt 6.2.0 with automatic recovery from dropped streams.

Extract the Linux x86_64 tarball and run `./install.sh`. Open **Moonbeam**
from your applications menu, or run `~/.local/bin/moonbeam`.
No root access, Flatpak runtime, FUSE, or system image changes are required.
You can also run `Moonbeam.AppDir/AppRun` directly without installing.
The AppImage is a separate single-file option; on systems without FUSE, run it
with `--appimage-extract-and-run`.

The installer imports the pairing from Moonlight on the machine being installed.
Settings are separate from stock Moonlight. The distributable contains no pairing
keys or host addresses. Other machines without an existing pairing must pair normally.
First installation sets 1920×1080, 60 FPS, 30 Mbps, frame pacing, and reconnect on.
These remain editable in Settings. Automatic codec selection is retained; available
hardware and host encoders determine the codec. The host/game also needs a 1080p
display or rendering resolution for a true 1080p image. Increase bitrate only if
the network has enough spare capacity.

Network failure resumes the same running app after complete connection cleanup,
with up to 12 attempts at 1, 2, 4, 8, then 10 second intervals. A stream stable for
30 seconds resets that budget. Cancel stops retries. Intentional disconnection,
host termination, authentication failures, protected content, and fatal encoder
errors are not retried. Recovery verifies the original game is still running;
it never starts a replacement game. Failed attempts retain the final error.
You can disable automatic reconnect in Settings.

Linux x86_64 build targets glibc 2.35 or later, including Bazzite/Fedora and
Ubuntu 22.04+. GPU drivers come from the host. This binary does not run on
Windows, macOS, ARM Linux, iOS, or tvOS; those require separate native builds.

Build: run `bash scripts/build-moonbeam-container.sh` on Linux with Podman.
The modified C++/QML client compiles locally in Ubuntu 22.04. Decoder dependencies
come from the SHA-256-pinned official Moonlight 6.2.0 AppImage (FFmpeg 9,
libplacebo 374), with matching public headers. SDL 2.32.10 is compiled from pinned
source with native Wayland and PulseAudio support. Packaging uses linuxdeploy and its Qt plugin. See
`scripts/prepare-moonbeam-sdk.py` for exact versions and checksums. The GPLv3
client source is included as a separate archive alongside the binary bundle.

Uninstall: remove `~/.local/bin/moonbeam`, the
`io.github.Spaceghost.Moonbeam.desktop` application entry, and
`~/.local/share/moonbeam`. Your separate settings remain in
`~/.config/Moonlight Game Streaming Project/Moonbeam.conf`.
