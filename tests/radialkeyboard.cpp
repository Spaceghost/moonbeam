#include "../app/streaming/input/radialkeyboard.h"
#include <cassert>
#include <iostream>
#include <limits>
#include <string>

using R = RadialKeyboard;

static void point(R& r, int pad, int sector, int count, R::Phase phase = R::Down)
{
    const double angle = sector * 6.283185307179586 / count;
    r.touch(pad, phase, float(.5 + .45 * std::sin(angle)), float(.5 - .45 * std::cos(angle)));
}

int main()
{
    R r;
    // Every key is reachable, one emission per lift, release coordinates ignored.
    for (int group = 0; group < R::GroupCount; ++group) {
        if (group == 8) r.touch(0, R::Down, .5f, .5f);
        else point(r, 0, group, 8);
        const auto keys = R::letters(group);
        for (int letter = 0; keys[letter]; ++letter) {
            point(r, 1, letter, int(std::strlen(keys)));
            assert(r.touch(1, R::Up, 0, 0) == keys[letter]);
            assert(r.touch(1, R::Up, 0, 0) == 0);
        }
    }
    // Resting thumbs and motion alone never type. Center tap is one space.
    assert(r.touch(1, R::Down, .5f, .5f) == 0);
    assert(r.touch(1, R::Move, .51f, .51f) == 0);
    assert(r.touch(1, R::Up, 1, 1) == ' ');
    // A group change while the right thumb is down recomputes its letter.
    point(r, 0, 0, 8);
    point(r, 1, 1, 4);
    point(r, 0, 1, 8, R::Move);
    assert(r.touch(1, R::Up, 0, 0) == 'f');
    // Focus loss/disconnect discard held gestures, including later Move/Up.
    point(r, 1, 0, 4);
    r.cancel();
    assert(!r.visible());
    assert(r.touch(1, R::Move, .5f, 0) == 0);
    assert(r.touch(1, R::Up, 0, 0) == 0);
    point(r, 1, 0, 4);
    assert(r.touch(1, R::Move, std::numeric_limits<float>::quiet_NaN(), 0) == 0);
    assert(r.touch(1, R::Up, 0, 0) == 0);
    assert(R::sector(.5f, 0, 8, -1) == 0);
    assert(R::sector(1, .5f, 8, -1) == 2);
    assert(R::sector(.5f, 1, 8, -1) == 4);
    assert(R::sector(0, .5f, 8, -1) == 6);
    assert(R::sector(.70f, .04f, 8, 0) == 0); // jitter over the N/NE boundary
    assert(R::sector(.85f, .15f, 8, 0) == 1);
    std::cout << "Radial keyboard: all keys, gestures, jitter and cancellation passed\n";
}
