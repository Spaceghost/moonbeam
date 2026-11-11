#include "streaming/session.h"
#include <Limelight.h>
#include <array>
#include <string>

void SdlInputHandler::sendRadialKey(int key)
{
    // Use the ordinary keyboard channel, so host key hooks and rhythm timing
    // behave just like a physical keyboard. Do not paste a completed spell.
    unsigned short vk = key;
    char modifiers = 0;
    if (key >= 'a' && key <= 'z') vk = key - 'a' + 'A';
    else if (key == '.' || key == '>') {
        vk = 0xBE;
        if (key == '>') modifiers = MODIFIER_SHIFT;
    }
    else if (key == '-') vk = 0xBD;
    else if (key == '\'') vk = 0xDE;
    LiSendKeyboardEvent2(vk | 0x8000, KEY_ACTION_DOWN, modifiers, 0);
    LiSendKeyboardEvent2(vk | 0x8000, KEY_ACTION_UP, 0, 0);
}

void SdlInputHandler::cancelRadialKeyboards()
{
    for (auto& keyboard : m_RadialKeyboards) keyboard.cancel();
    Session::get()->getOverlayManager().setOverlayState(Overlay::OverlayRadialKeyboard, false);
}

void SdlInputHandler::updateRadialOverlay(const RadialKeyboard& keyboard)
{
    auto& overlay = Session::get()->getOverlayManager();
    if (!keyboard.visible()) {
        // Another controller may still be spelling.
        for (const auto& other : m_RadialKeyboards) {
            if (other.visible()) { updateRadialOverlay(other); return; }
        }
        overlay.setOverlayState(Overlay::OverlayRadialKeyboard, false);
        return;
    }
    std::array<std::string, 13> rows;
    for (auto& row : rows) row.assign(64, ' ');
    const auto label = [&](int cx, int cy, const std::string& value, bool selected) {
        std::string text = selected ? "[" + value + "]" : value;
        int x = cx - int(text.size()) / 2;
        if (x >= 0 && x + int(text.size()) <= 64 && cy >= 0 && cy < 13)
            rows[cy].replace(x, text.size(), text);
    };
    const auto position = [&](int center, int index, int count, const std::string& value, bool selected) {
        double angle = index * 6.283185307179586 / count;
        label(center + int(std::round(11 * std::sin(angle))),
              6 - int(std::round(4 * std::cos(angle))), value, selected);
    };
    label(16, 0, "LEFT: GROUP", false);
    label(48, 0, "RIGHT: LIFT TO TYPE", false);
    for (int i = 0; i < 8; ++i)
        position(16, i, 8, i == 7 ? "0-9" : RadialKeyboard::letters(i), keyboard.group() == i);
    label(16, 6, "TOOLS", keyboard.group() == 8);
    const char* letters = RadialKeyboard::letters(keyboard.group());
    for (int i = 0; letters[i]; ++i) {
        std::string text(1, letters[i]);
        if (letters[i] == '\b') text = "UNDO";
        if (letters[i] == '\r') text = "ENTER";
        if (letters[i] == '\x1b') text = "ESC";
        position(48, i, int(std::strlen(letters)), text, keyboard.letter() == i);
    }
    label(48, 6, "SPACE", keyboard.letter() < 0);
    std::string text;
    for (const auto& row : rows) text += row + '\n';
    text += "Sticks + buttons: normal gamepad controls";
    // SDL may send hundreds of motion events per second; render only changes.
    if (text != overlay.getOverlayText(Overlay::OverlayRadialKeyboard)) {
        overlay.setRadialSelection(keyboard.group(), keyboard.letter());
        overlay.updateOverlayText(Overlay::OverlayRadialKeyboard, text.c_str());
    }
    overlay.setOverlayState(Overlay::OverlayRadialKeyboard, true);
}
