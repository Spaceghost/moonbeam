# Game profiles and recovery

## Per-game stream settings

Right-click a game (or open its menu with a gamepad) and choose **Stream settings…**.
Set the resolution, frame rate, bitrate, codec, decoder, renderer, frame pacing,
and HDR, then save. **Use global settings** removes the game's overrides.

Profiles belong to a host ID and app ID, so another PC's game with the same name
gets its own settings. Renaming the host or game does not change that association.
The editor starts with current global values when no profile exists. Saving stores
the displayed values as the game's profile. Global settings remain separate.

GUI launches, direct launches, and CLI streams apply the saved profile. Explicit
CLI choices take precedence. `--no-game-profile` bypasses the saved profile.
For example:

```sh
moonbeam stream HOST APP --fps 120 --bitrate 40000 --no-quit-after
```

A stream takes a snapshot of its effective settings. Reconnect uses that same
snapshot, even if the saved profile or global settings change during recovery.
Profile storage contains stream options only; pairing credentials retain their
existing storage and migration behavior.

## NVIDIA Wayland compatibility option

Automatic keeps the existing software H.264 preference on NVIDIA Wayland.
For an explicit hardware alternative, use a game profile with:

- Video codec: **H.264**
- Video decoder: **Hardware**
- Renderer: **SDL**
- HDR: **Off**

This selects VAAPI decoding with SDL presentation and avoids the NVIDIA Wayland
EGL import path that previously produced corrupted pixels. It uses CPU readback
and upload rather than claiming a zero-copy path. A forced hardware choice reports
failure when no supported hardware path initializes; it does not silently use
software decoding.

Linux CLI equivalents are `--video-decoder hardware --video-renderer sdl --no-hdr`.
Renderer choices follow the compiled backend capabilities. FFmpeg builds offer
`auto`, `sdl`, and (when compiled) `vulkan` on Linux; `auto`, `vulkan`,
`metal`, and `avsbdl` on macOS; and `auto` on Windows. Steam Link builds without
FFmpeg expose Automatic only. Unsupported saved profile
values are ignored as a whole, preserving the global fallback.

Test initialization and three decoder recreation cycles without connecting to a host:

```sh
moonbeam selftest --video-codec H.264 --video-decoder hardware --video-renderer sdl --no-hdr
```

Self-tests exercise initialization and recreation, not visual correctness of a live
stream. Inspect streamed pixels and measure the complete presentation path before
changing defaults. See [the validation record](FEATURE-VALIDATION.md).

## Recovery behavior

Recoverable failures retry at 1, 2, 4, 8, then 10 second intervals until the original
app resumes or the user cancels. Thirty seconds of stable streaming resets the
backoff. Each retry waits for the old transport to finish teardown. The host must
still report the original app as running; recovery never launches a replacement.
Authentication failures, fatal encoder errors, and intentional disconnects stop
recovery. A suspended client can use the same recovery path after the transport
reports a connection failure; physical OS suspend/resume remains a separate
hardware validation case.

**Cancel reconnect** cancels connection work, waits for cleanup, and preserves
the host app even when the normal disconnect setting would quit the app.
Duplicate or stale teardown callbacks cannot start duplicate sessions or pop an
unrelated UI page. Automated tests exercise twenty consecutive recoveries.

## Isolated network tests on Linux

`scripts/network-sandbox.py` creates a private user/network namespace and uses
slirp4netns, a TAP interface, an IFB interface, and netem to impair both directions.
Host interfaces and other processes keep their network configuration. The helper
requires `unshare`, `ip`, `tc`, and `slirp4netns`, plus kernel support for user
namespaces, IFB, and netem. It needs no root shell.

Check the harness without a game or streaming client first:

```sh
python3 scripts/network-sandbox.py --self-test --delay-ms 10 --jitter-ms 2 --loss-percent 5
```

With the current stream free, test a twelve-second outage plus ongoing delay,
jitter, and packet loss:

```sh
python3 scripts/network-sandbox.py --delay-ms 10 --jitter-ms 3 --loss-percent 0.5 \
  --outage-after 20 --outage-seconds 12 --duration 75 -- \
  moonbeam stream HOST APP --no-quit-after
```

The outage restores the selected loss/delay profile, not necessarily a clean
network. Persistent packet loss can still reduce frame rate; reconnect does not
repair network quality. The helper appends `--no-quit-after` to stream commands
and rejects positive quit-after flags. Use a separate client configuration for
diagnostics and keep desktop captures and pairing data private. Namespace teardown
removes the test interfaces and rules. This harness is for fault injection; its
NAT and queue overhead make it unsuitable as a direct performance baseline.
