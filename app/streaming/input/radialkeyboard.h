#pragma once

#include <cmath>
#include <cstring>

// Transport-independent: normalized touch coordinates in, ASCII key taps out.
// No controller axes or buttons are used. Mobile adapters can use the same
// state machine with native touchpad events and their keyboard transport.
class RadialKeyboard
{
public:
    enum Phase { Down, Move, Up };
    static const int GroupCount = 9;

    static const char* letters(int group)
    {
        static const char* const groups[] = {
            "abcd", "efgh", "ijkl", "mnop", "qrst", "uvwx", "yz-'",
            "0123456789", ".>\b\r\x1b"
        };
        return groups[group >= 0 && group < GroupCount ? group : 0];
    }

    // Up coordinates are often zero/stale. Commit the last valid hover instead.
    // An Up without an observed Down never types (focus loss, reconnect, etc.).
    int touch(int pad, Phase phase, float x, float y)
    {
        if (pad < 0 || pad > 1) return 0;
        if (phase == Up) {
            const bool wasDown = m_Down[pad];
            m_Down[pad] = false;
            return pad == 1 && wasDown ? hovered() : 0;
        }
        if (!std::isfinite(x) || !std::isfinite(y) || x < 0 || x > 1 || y < 0 || y > 1) {
            m_Down[pad] = false;
            return 0;
        }
        if (phase == Move && !m_Down[pad]) return 0;
        m_Down[pad] = true;
        m_X[pad] = x;
        m_Y[pad] = y;
        if (pad == 0) {
            const int next = sector(x, y, 8, m_Group < 8 ? m_Group : -1);
            const int group = next < 0 ? 8 : next;
            if (group != m_Group) {
                m_Group = group;
                m_Letter = -1;
            }
        }
        if (m_Down[1]) {
            m_Letter = sector(m_X[1], m_Y[1], int(std::strlen(letters(m_Group))), m_Letter);
        }
        return 0;
    }

    void cancel() { *this = RadialKeyboard(); }
    bool visible() const { return m_Down[0] || m_Down[1]; }
    int group() const { return m_Group; }
    int letter() const { return m_Letter; }
    int hovered() const { return m_Letter < 0 ? ' ' : letters(m_Group)[m_Letter]; }

    // North is zero, clockwise. A small angular margin prevents boundary jitter.
    static int sector(float x, float y, int count, int previous)
    {
        const double dx = x - .5, dy = .5 - y;
        if (dx * dx + dy * dy < .0225) return -1;
        const double pi = 3.14159265358979323846;
        double angle = std::atan2(dx, dy);
        if (angle < 0) angle += 2 * pi;
        const double step = 2 * pi / count;
        if (previous >= 0 && previous < count) {
            const double delta = std::remainder(angle - previous * step, 2 * pi);
            if (std::abs(delta) <= step / 2 + .07) return previous;
        }
        return int(std::floor(angle / step + .5)) % count;
    }

private:
    bool m_Down[2] = {false, false};
    float m_X[2] = {.5f, .5f}, m_Y[2] = {.5f, .5f};
    int m_Group = 0, m_Letter = -1;
};
