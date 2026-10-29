# Client performance research and selected changes

Reviewed 2026-10-29. Sources below are upstream repositories, source changes, and
maintainer release notes. A feature advertised by a fork is not a measured speedup
on Moonbeam's target hardware.

| Client/source | Finding | Moonbeam decision |
| --- | --- | --- |
| [Vibemis](https://github.com/navyas321/vibemis) | Maintainers use genuine SDL2 and PulseAudio to avoid SDL3/sdl2-compat PipeWire audio problems on Linux handhelds. | Build pinned SDL 2.32.10 from source with native Wayland and PulseAudio; prefer PulseAudio when its server socket exists, preserving explicit driver choices. The previous portable SDL advertised only X11/offscreen/dummy/evdev, so Qt Wayland support alone was insufficient. |
| [Vibemis audio change 1620b807](https://github.com/navyas321/vibemis/commit/1620b807) | Bound audio buffering by duration rather than packet count, so 10 ms packets do not double latency. | Moonlight's 50 ms duration cap was already present. Tighten it to a byte budget including the incoming packet and partial packets; discard a packet if a stalled device exhausts the wait budget rather than growing latency. Test 5 ms/10 ms packets and surround. |
| [Vibemis releases](https://github.com/navyas321/vibemis/releases) | Headless smoke tests, bounded reconnect, and per-game/handheld profiles improve usability and diagnosis. | Add a graphical `selftest` using Moonbeam's actual renderer/decoder recreation path. Keep existing bounded reconnect. Battery profiles and Apollo-specific VRR negotiation are not enabled for generic Sunshine hosts. |
| [Artemis](https://github.com/wjbeckett/artemis) | Resolution scaling, renderer choices, and handheld-specific profiles can reduce client GPU cost. | Preserve 1080p output and existing upstream frame pacing/scaling. Do not silently lower resolution or force handheld settings on Alienware. |
| [Moonlight frame pacing](https://github.com/moonlight-stream/moonlight-qt/blob/master/app/streaming/video/ffmpeg-renderers/pacer/pacer.cpp) | The baseline already controls presentation timing and queued frames. | Retain the existing pacer rather than adding a second queue or delay. Prefer native Wayland so Qt and SDL do not take the problematic XWayland path. |
| [chiaki-ng FFmpeg 8/9 interoperability issue](https://github.com/chiaki-ng/chiaki-ng/issues/809) | Vulkan contexts and queue-family APIs change across FFmpeg versions; a headless decoder test does not validate shared rendering contexts. | Keep headers pinned to decoder dependencies, and validate the complete imported-device renderer path on hardware before tagging. |

The target-machine logs also exposed host-driver failures caused by a bundled
older GLib loading alongside a newer host GObject. Portable builds now leave the
GLib/GObject/GIO family to the host, as they already do for Wayland and GPU-facing
libraries. This is a compatibility fix, not a benchmark claim.

Validation must distinguish startup, full renderer/decoder tests, actual streamed
frames, audio, and recovery after disruption. Successful startup or decoding four
frames in an independent FFmpeg device does not establish end-to-end correctness.
