# Steam Controller 2026 driver

Backported from SDL commit `4ca1b1c2d084b59ca72c87f36a18fc1a3898f424`:
[driver and protocol headers](https://github.com/libsdl-org/SDL/tree/4ca1b1c2d084b59ca72c87f36a18fc1a3898f424/src/joystick/hidapi).
The original zlib license and copyright notices remain in every source file.

Moonbeam retains native SDL2 for its audio/video path. This backport adds the
new controller's USB and wireless dongle reports, independent touchpads, analog
sticks/triggers, buttons, motion sensors, battery state and rumble. It does not
turn the trackpads into sticks. The SDL3 capacitive stick/grip API has no SDL2
equivalent and is omitted. Adaptive trigger resistance is not a capability of
this controller.

Changes adapt SDL3 event APIs, sensor timestamps, controller mappings and SDL2
return conventions. Dongle matching additionally checks Valve's vendor ID;
16-bit IMU timestamps wrap before conversion to microseconds, and stick Y
inversion saturates at full deflection instead of wrapping to the other side. No proprietary
firmware or Steam client components are distributed.

`scripts/patch-sdl2-triton.py` installs this into the pinned SDL 2.32.10 source.
It rejects unexpected patch locations and is safe to run again. Both the driver
and application require hardware validation; compilation is not a substitute.
Bluetooth and native mobile BLE adapters are outside this backport's validated
transport scope.
