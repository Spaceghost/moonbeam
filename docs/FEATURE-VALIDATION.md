# Recovery, profiles, and NVIDIA validation — 2026-11-09

The feature branch is rebased onto Moonlight `4113dd26` (2026-11-06). Upstream
renderer callback synchronization, overlay teardown locking, CUDA format checks,
and native dependency bundle v20 are retained. Published Moonbeam commits stay
reachable through a history-preserving merge after the rebase; no published ref
is rewritten. Linux keeps its pinned native SDL2/decoder SDK compatibility path.

The feature code is built as `6.2.0-moonbeam.6`. These checks do not authorize
publishing a new immutable release tag. Windows, macOS, and Steam Link still
need their own physical streaming checks before a multi-platform promotion.

## Automated coverage

- Fifteen Qt reconnect tests, including twenty consecutive recovery cycles,
  teardown ordering, duplicate callbacks, cancellation phases, backoff reset,
  initialization failure, terminal failures, and host-quit policy.
- Ten Qt profile tests in full and minimal renderer configurations covering host/app isolation, reset, invalid-value
  rejection, global inheritance, frozen reconnect settings, CLI precedence,
  self-test options, compiled renderer capabilities, corrupt-profile fallback,
  and the actual QML editor's save/reset behavior.
- Existing installer/migration checks, nineteen promotion-policy scenarios,
  complete asset checks, native versioning, and recursive source archive checks.

## Linux development A/B observations before the upstream refresh

Alienware desktop with RTX 3070 and RTX 4060 GPUs, NVIDIA driver 615.78.08,
GNOME Wayland, and the VA-API NVDEC direct backend. SDL reported its OpenGL
presentation backend. The existing host app was resumed and kept running.

Four approximately 35-second runs used software, hardware, hardware, software
order. Each used the same FFXIV launcher scene, H.264, 1920×1080, 60 FPS,
30 Mbps, SDL presentation, frame pacing, and V-sync. These are short observations
on a mostly static scene with ordinary desktop activity, not controlled game
benchmarks or measurements of input-to-display latency.

| Measurement | Software/SDL, two runs | VAAPI/SDL, two runs |
| --- | --- | --- |
| Client CPU, percent of one core | 28.08–28.61% | 21.08–21.39% |
| Average decode time | 1.59–1.92 ms | 1.31–1.35 ms |
| Average render time, including reported V-sync latency | 0.84–0.88 ms | 2.04–2.07 ms |
| Render rate | 59.12–59.70 FPS | 59.61–59.73 FPS |

CPU samples cover the client process lifetime, including startup and capture.
Both paths displayed clear pixels in inspected live-stream captures. VAAPI/SDL
used about 25% less client CPU in these runs and had higher presentation cost.
The observations support an explicit compatibility option, while the existing
Automatic default remains unchanged. Power savings and lower end-to-end latency
have not been established.

## Network recovery

The isolated harness self-test sent 60 UDP probes with 10 ms delay each way,
2 ms jitter, and 5% loss. It received 56 replies with median RTT 20.56 ms.

A live hardware/SDL stream then ran in its own namespace with 10 ms delay,
3 ms jitter, and 0.5% packet loss each way. A twelve-second complete blackout
started twenty seconds into the test. The client reported transport termination,
retried after teardown, and resumed the same app after networking returned.
Two completed stream sessions appeared in the 75-second test log, and a live
post-recovery capture showed clear pixels. The host app ID remained unchanged
before and after. Ongoing loss reduced frame rate, as expected; this test validates
recovery rather than clean-network playback performance.

No physical OS suspend was performed. No host game was quit or restarted.
Desktop captures, host addresses, pairing files, and raw private logs are not
included in this repository.

## Clean CI Linux artifact checks

The clean Linux artifact passed three hardware/SDL decoder recreation cycles.
A saved per-game profile then requested 1280×720, 30 FPS, 12 Mbps, H.264,
hardware decoding, and SDL without CLI overrides for those stream settings.
The live log confirmed the requested stream mode and VAAPI/SDL path and reported
29.66 rendered FPS. Global stream settings remained unchanged, removing the
profile restored inheritance, and the original host app remained running.

## Final rebased candidate — `1bd076c6`

[Candidate run 42759841471](https://github.com/Spaceghost/moonbeam/actions/runs/42759841471)
built every platform successfully. Downloaded assets passed all eight SHA-256
checks, Windows x64/ARM64 PE checks, macOS universal/bundle-version checks,
Steam Link ARM checks, Linux bundle checks, and recursive source-manifest checks.
The tested Linux payload is `6.2.0-moonbeam.6+g1bd076c6284b`.

On that exact Linux payload, hardware/SDL self-test passed three recreation
cycles. Automatic profile application requested 1280×720 at 30 FPS and 12 Mbps,
used VAAPI/SDL, and rendered at 30.05 FPS. Profile removal restored inheritance;
global stream settings and the running host app were preserved.

A further pair of approximately 35-second 1080p60 runs measured 28.1% of one
CPU core with software/SDL and 19.2% with VAAPI/SDL. Average decode times were
1.62 ms and 0.57 ms; average render times were 0.85 ms and 2.07 ms. Render rates
were 58.93 and 59.08 FPS. These short observations have the same limitations as
the earlier A/B runs and do not establish an end-to-end latency benefit.

The exact rebased payload also recovered from another twelve-second complete
network blackout, this time with no additional ongoing loss/delay imposed by
the harness. It resumed the original app and showed clear live frames. The
post-recovery overlay was near 60 FPS; the final session average was 58.71 FPS.
The host app remained running, and all test clients exited normally.
