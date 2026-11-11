#!/usr/bin/env python3
"""Apply Moonbeam's attributed SDL3 Triton driver backport to SDL 2.32.10."""
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1])
vendor = root / 'third_party/sdl2-triton'
hidapi = source / 'src/joystick/hidapi'
shutil.copy2(vendor / 'SDL_hidapi_steam_triton.c', hidapi)
shutil.copytree(vendor / 'steam_triton', hidapi / 'steam_triton', dirs_exist_ok=True)

def insert(path, marker, old, new):
    text = path.read_text()
    if marker in text:
        return
    if text.count(old) != 1:
        raise RuntimeError(f'SDL source changed; review Triton backport: {path}')
    path.write_text(text.replace(old, new))

insert(hidapi / 'SDL_hidapijoystick_c.h', '#define SDL_JOYSTICK_HIDAPI_STEAM_TRITON',
       '#define SDL_JOYSTICK_HIDAPI_STEAMDECK',
       '#define SDL_JOYSTICK_HIDAPI_STEAM_TRITON\n#define SDL_JOYSTICK_HIDAPI_STEAMDECK')
insert(hidapi / 'SDL_hidapijoystick_c.h', 'extern SDL_HIDAPI_DeviceDriver SDL_HIDAPI_DriverSteamTriton;',
       'extern SDL_HIDAPI_DeviceDriver SDL_HIDAPI_DriverSteamDeck;',
       'extern SDL_HIDAPI_DeviceDriver SDL_HIDAPI_DriverSteamTriton;\nextern SDL_HIDAPI_DeviceDriver SDL_HIDAPI_DriverSteamDeck;')
insert(hidapi / 'SDL_hidapijoystick.c', '&SDL_HIDAPI_DriverSteamTriton,',
       '#ifdef SDL_JOYSTICK_HIDAPI_STEAMDECK',
       '#ifdef SDL_JOYSTICK_HIDAPI_STEAM_TRITON\n    &SDL_HIDAPI_DriverSteamTriton,\n#endif\n#ifdef SDL_JOYSTICK_HIDAPI_STEAMDECK')

# SDL3 and SDL2 have different button indices and mapping generators. Keep
# physical sticks and triggers distinct from both trackpads; D-pad uses a hat.
old = '    if ((vendor == USB_VENDOR_NINTENDO && product == USB_PRODUCT_NINTENDO_GAMECUBE_ADAPTER) ||'
new = '''    /* Moonbeam: Steam Controller 2026 (Triton), including its dongles. */
    if (vendor == USB_VENDOR_VALVE && (product == 0x1302 || product == 0x1303 || product == 0x1304 || product == 0x1305)) {
        SDL_strlcat(mapping_string, "a:b0,b:b1,x:b2,y:b3,back:b4,guide:b5,start:b6,leftstick:b7,rightstick:b8,leftshoulder:b9,rightshoulder:b10,dpup:h0.1,dpright:h0.2,dpdown:h0.4,dpleft:h0.8,leftx:a0,lefty:a1,rightx:a2,righty:a3,lefttrigger:a4,righttrigger:a5,misc1:b15,paddle1:b16,paddle2:b17,paddle3:b18,paddle4:b19,touchpad:b20,", sizeof(mapping_string));
    } else if ((vendor == USB_VENDOR_NINTENDO && product == USB_PRODUCT_NINTENDO_GAMECUBE_ADAPTER) ||'''
insert(source / 'src/joystick/SDL_gamecontroller.c', 'Moonbeam: Steam Controller 2026 (Triton)', old, new)
