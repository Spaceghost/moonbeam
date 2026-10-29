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

On an NVIDIA RTX 3070 with GNOME Wayland, Moonbeam's VAAPI/EGL path decoded at
about 60 FPS but displayed colored noise. Its three-pass hardware self-test still
passed, so that result alone did not establish visual correctness. Vulkan Video
initialization failed on this driver. Retaining VAAPI decoding while transferring
frames through SDL produced a clear 1920×1080 stream and passed the same self-test.
In one 50-second run, average decoding time was 0.19 ms and rendering frame rate
was 59.43 FPS. A separate software-decoded run averaged 1.58 ms decoding and
59.30 FPS rendering. These are observations on one machine and scene, not a
controlled cross-client benchmark.

The first fix skipped NVIDIA VAAPI on Wayland and allowed software decoding.
The later VAAPI/SDL path was clear in the recorded test, but the first fix was
preferred in use and is restored as the default. Forced VAAPI remains available
with `FORCE_VAAPI=1` and still avoids EGL import. With 189 MB free on the display
GPU, a software-decoded stream using Vulkan rendering selected the other GPU,
dropped frames, and lost its window. Selecting SDL rendering for the same
software decoder rendered 59.82 FPS with no network frame drops in a follow-up
run. The portable launcher now prefers SDL on NVIDIA Wayland unless the user
sets `VULKAN_IS_SLOW` explicitly.

The exact `v6.2.0-moonbeam.2` candidate from [run 40954444687](https://github.com/Spaceghost/moonbeam/actions/runs/40954444687)
was installed and checked on the same desktop before tagging. The three-pass
hardware self-test passed. A visually inspected 1920×1080, 60 FPS stream was
clear; a controlled run measured 60.04 incoming FPS, 59.74 rendered FPS, 0.19 ms
average decode time, and no network frame drops. A separate run received stereo
audio packets through SDL PulseAudio and recorded nonzero output on the selected
sink monitor. An 8-second pause of only the Moonbeam process dropped the
connection; automatic reconnect resumed the same host app and rendered at
59.51 FPS until the planned stop. These checks used the installed candidate
binary, not a local rebuild.

Two resource-pressure observations remain useful for diagnosis. With only
272 MB free on the RTX 3070, Qt failed to create its launcher OpenGL context;
`QT_QUICK_BACKEND=software` allowed the same candidate to launch and keep
hardware video decoding. The portable launcher now selects that Qt Quick
backend automatically on NVIDIA Wayland when the user has not chosen another.
In a separate 14-second process-pause test, reconnect
started but the second window closed after 11 seconds with a Vulkan surface-lost
error. The shorter repeat above did not reproduce that close. Neither pause
simulates a normal packet-loss pattern, so these results should not be treated as
a general network-recovery benchmark.
