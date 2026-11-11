/* Exercise the actual vendored SDL driver with report/event sinks, without HID
 * hardware or a running SDL event loop. Unused driver functions are discarded
 * by the linker. Headers come from the same pinned SDL build as the package. */
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include TRITON_DRIVER

static Sint16 axes[6];
static Uint8 buttons[24], hat;
static struct { Uint8 down; float x, y; int events; } touches[2];
static Uint64 sensor_time;

Uint64 SDL_GetTicks64(void) { return 1000; }
int SDL_PrivateJoystickAxis(SDL_Joystick *joystick, Uint8 axis, Sint16 value)
{ (void)joystick; axes[axis] = value; return 1; }
int SDL_PrivateJoystickButton(SDL_Joystick *joystick, Uint8 button, Uint8 value)
{ (void)joystick; buttons[button] = value; return 1; }
int SDL_PrivateJoystickHat(SDL_Joystick *joystick, Uint8 index, Uint8 value)
{ (void)joystick; (void)index; hat = value; return 1; }
int SDL_PrivateJoystickTouchpad(SDL_Joystick *joystick, int pad, int finger, Uint8 down, float x, float y, float pressure)
{
    (void)joystick; (void)finger; (void)pressure;
    assert(pad == 0 || pad == 1);
    touches[pad].down = down; touches[pad].x = x; touches[pad].y = y; ++touches[pad].events;
    return 1;
}
int SDL_PrivateJoystickSensor(SDL_Joystick *joystick, SDL_SensorType type, Uint64 timestamp, const float *data, int count)
{ (void)joystick; (void)type; (void)data; assert(count == 3); sensor_time = timestamp; return 1; }

int main(void)
{
    SDL_DriverSteamTriton_Context context = {0};
    SDL_HIDAPI_Device device = {0};
    SDL_Joystick joystick = {0};
    TritonMTUNoQuat_t report = {0};
    TritonMTUNoQuat32TS_t newer = {0};
    device.context = &context;

    /* Both pads active at once while moving, looking and holding A + triggers. */
    report.buttons = TRITON_LEFT_TOUCHPAD_TOUCH | TRITON_RIGHT_TOUCHPAD_TOUCH |
                     TRITON_LBUTTON_A | TRITON_LBUTTON_DPAD_UP;
    report.sLeftStickX = 1234; report.sLeftStickY = -2345;
    report.sRightStickX = -3456; report.sRightStickY = 4567;
    report.sTriggerLeft = 10000; report.sTriggerRight = 16000;
    report.sLeftPadX = 32767; report.sRightPadY = 32767;
    HIDAPI_DriverSteamTriton_HandleState(&device, &joystick, &report);
    assert(axes[0] == 1234 && axes[1] == 2345 && axes[2] == -3456 && axes[3] == -4567);
    assert(axes[4] == -12768 && axes[5] == -768);
    assert(buttons[SDL_CONTROLLER_BUTTON_A] && hat == SDL_HAT_UP);
    assert(touches[0].down && touches[1].down);
    assert(touches[0].x > .99f && touches[0].y == .5f);
    assert(touches[1].x == .5f && touches[1].y < .01f);

    /* Moving only a pad cannot move either stick or alter the face button. */
    report.sLeftPadX = -32768; report.sRightPadY = -32768;
    HIDAPI_DriverSteamTriton_HandleState(&device, &joystick, &report);
    assert(axes[0] == 1234 && axes[1] == 2345 && axes[2] == -3456 && axes[3] == -4567);
    assert(buttons[SDL_CONTROLLER_BUTTON_A] && touches[0].x == 0 && touches[1].y == 1);

    /* Release keeps the final position even when firmware clears coordinates. */
    report.buttons = 0; report.sLeftPadX = report.sRightPadY = 0;
    HIDAPI_DriverSteamTriton_HandleState(&device, &joystick, &report);
    assert(!touches[0].down && !touches[1].down && touches[0].x == 0 && touches[1].y == 1);
    assert(!buttons[SDL_CONTROLLER_BUTTON_A]);
    HIDAPI_DriverSteamTriton_HandleState(&device, &joystick, &report);
    assert(touches[0].events == 3 && touches[1].events == 3);

    /* New firmware layout and 16-bit IMU timestamp rollover. */
    newer.buttons = TRITON_RIGHT_TOUCHPAD_TOUCH;
    newer.sLeftStickX = -9876; newer.sRightPadX = 16384;
    context.report_sensors = SDL_TRUE;
    context.last_sensor_tick16 = 65530;
    newer.imu.timestamp = 3;
    HIDAPI_DriverSteamTriton_HandleState_Timestamp(&device, &joystick, &newer);
    assert(axes[0] == -9876 && touches[1].down && touches[1].x == .75f);
    assert(sensor_time == 9 * 32);
    newer.sLeftStickY = newer.sRightStickY = SDL_MIN_SINT16;
    HIDAPI_DriverSteamTriton_HandleState_Timestamp(&device, &joystick, &newer);
    assert(axes[1] == SDL_MAX_SINT16 && axes[3] == SDL_MAX_SINT16);

    assert(HIDAPI_DriverSteamTriton_IsSupportedDevice(NULL, NULL, 0, 0x28de, 0x1302, 0, 0, 0, 0, 0));
    assert(HIDAPI_DriverSteamTriton_IsSupportedDevice(NULL, NULL, 0, 0x28de, 0x1304, 0, 2, 0, 0, 0));
    assert(!HIDAPI_DriverSteamTriton_IsSupportedDevice(NULL, NULL, 0, 0x1234, 0x1304, 0, 2, 0, 0, 0));
    assert(!HIDAPI_DriverSteamTriton_IsSupportedDevice(NULL, NULL, 0, 0x28de, 0x1304, 0, 1, 0, 0, 0));
    puts("Triton: independent pads/sticks/buttons/triggers, release, firmware layouts, IMU rollover and device matching passed");
    return 0;
}
