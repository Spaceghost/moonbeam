# Steam Controller radial keyboard

Moonbeam can send normal PlayStation-style controller input and a radial
trackpad keyboard together. Enable **Settings → Gamepad → Use Steam Controller
trackpads as a radial keyboard**, then start a new stream. It defaults on for
Steam controllers with two native touchpads; other controllers are unaffected.

Connect the 2026 Steam Controller to the client by USB cable or its wireless
dongle. For a direct launch, exit Steam on the streaming client first, or remove
the controller's Steam Desktop Layout bindings. Launching Moonbeam outside Steam
does not disable that desktop layout. If launching through Steam, disable Steam
Input for the Moonbeam shortcut as well.
Moonbeam needs the native controller, not a Steam virtual Xbox controller.
Remove old trackpad-to-stick mappings. Linux also requires access to the
controller's hidraw devices (current Steam device udev rules normally provide
this). Logs report whether two touchpads were found; no physical device is
available to automated tests.

The sticks, D-pad, face buttons, triggers, back buttons, gyro and rumble keep
using the normal controller path. Touchpads do not generate camera/movement
axes or virtual touchpad clicks in keyboard mode. The host receives a
PlayStation controller arrival and individual key-down/key-up events over the
existing encrypted stream connection. No separate keyboard service is exposed.
This gives ordinary PS5-style controls; Steam Controller hardware does not gain
DualSense adaptive triggers.

| Control | Input |
| --- | --- |
| Left pad outer ring | ABCD / EFGH / IJKL / MNOP / QRST / UVWX / YZ-' / 0–9 |
| Left pad center | Tools: `.`, `>`, Backspace, Enter, Escape |
| Right pad outer ring | Select a key; lift to type it once |
| Right pad center | Lift for Space |

The group stays selected after lifting the left thumb. The guide shows only
while a pad is touched. Hovering never types. Focus loss, reconnect and device
removal cancel unfinished gestures, even with background gamepad input enabled.

In XivSpell 0.1.0.13+, type `i` to enter weaving, then rhythm-type `tank physick`.
Typing `physick` afterward retains the tank target. R2+A repeats and R2+B
continues the weave. Do not open XivSpell's old F8 modal stick wheel for this
layout. Normal L3/R3 controls are preserved.

## Left stick also tilts the camera

Steam's desktop layout can send arrow keys while Moonbeam sends the native
joystick axes. In FFXIV, this makes forward/backward movement also tilt the
camera. The default `desktop_neptune.vdf` layout used by the 2026 Steam
Controller binds its left stick to Up/Down/Left/Right arrow keys.

Exit Steam on the **streaming client**, leaving Moonbeam and the game running,
then try the left stick again. Alternatively, remove the controller's Steam
Desktop Layout bindings before using Moonbeam. Reopening Steam with that layout
still enabled can restore the duplicate input. Changing FFXIV's stick calibration
or swapping camera axes does not remove those extra keyboard events.

## Platform and validation status

Linux, Windows x64/ARM64 and macOS builds use the same portable gesture engine.
Their packaging builds an attributed SDL3 Triton driver backport against native
SDL 2.32.10, preserving Moonbeam's existing SDL2 audio/video path. See
[the driver notes](../third_party/sdl2-triton/README.md).

The pure C++ gesture engine has no Qt, SDL or OS dependency and can be called
from Android JNI or iOS Objective-C++. That is **not a shipped mobile client**.
This repository currently contains Moonbeam's desktop client, not Android/iOS
streaming apps. Native mobile input adapters and device access still require
implementation and platform validation. Stock Moonlight mobile apps do not gain
this feature by updating the desktop Moonbeam package. Bluetooth is not claimed
as tested by this change.

Automated tests cover every character/control, one tap per lift, stale release
coordinates, group changes, center/dead-zone behavior, boundary jitter and
focus/disconnect cancellation. Physical USB/dongle routing still requires a
client test: move and rotate the camera while spelling, press ordinary buttons,
check gyro and rumble, then alt-tab or disconnect with a thumb held and verify
that returning/reconnecting cannot type a stale character. A successful build
is not hardware attestation or release promotion.
