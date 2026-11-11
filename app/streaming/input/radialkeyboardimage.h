#pragma once
#include "radialkeyboard.h"
#include <QImage>
#include <QPainter>
#include <QFont>

inline QImage radialKeyboardImage(int group, int letter)
{
    QImage image(620, 280, QImage::Format_ARGB32);
    image.fill(Qt::transparent);
    QPainter p(&image);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(QPen(QColor(95, 162, 190, 180), 1));
    p.setBrush(QColor(12, 20, 32, 230));
    p.drawRoundedRect(QRectF(2, 2, 616, 276), 18, 18);
    QFont font;
    font.setPixelSize(17);
    p.setFont(font);
    p.setPen(QColor(200, 230, 245));
    p.drawText(QRectF(0, 12, 310, 25), Qt::AlignCenter, "LEFT: LETTER GROUP");
    p.drawText(QRectF(310, 12, 310, 25), Qt::AlignCenter, "RIGHT: LIFT TO TYPE");
    const auto wheel = [&](int cx, int count, int selected, bool groups) {
        QRectF bounds(cx - 96, 44, 192, 192);
        const double step = 360.0 / count;
        for (int i = 0; i < count; ++i) {
            p.setPen(QPen(QColor(73, 112, 141), 1));
            p.setBrush(i == selected ? QColor(38, 126, 171, 240) : QColor(23, 39, 57, 235));
            p.drawPie(bounds, int((90 + step / 2 - i * step) * 16), int(-step * 16));
            const double angle = i * 6.283185307179586 / count;
            const double x = cx + 68 * std::sin(angle), y = 140 - 68 * std::cos(angle);
            QString label;
            if (groups) label = i == 7 ? "0-9" : QString::fromLatin1(RadialKeyboard::letters(i)).toUpper();
            else {
                const char ch = RadialKeyboard::letters(group)[i];
                label = ch == '\b' ? "UNDO" : ch == '\r' ? "ENTER" : ch == '\x1b' ? "ESC" : QString(QChar(ch));
            }
            p.setPen(i == selected ? Qt::white : QColor(192, 212, 226));
            p.drawText(QRectF(x - 38, y - 12, 76, 24), Qt::AlignCenter, label);
        }
        p.setPen(QPen(QColor(95, 162, 190), 1));
        p.setBrush(selected < 0 ? QColor(38, 126, 171) : QColor(16, 29, 45));
        p.drawEllipse(QPointF(cx, 140), 29, 29);
        p.setPen(Qt::white);
        p.drawText(QRectF(cx - 29, 126, 58, 28), Qt::AlignCenter, groups ? "TOOLS" : "SPACE");
    };
    wheel(155, 8, group == 8 ? -1 : group, true);
    wheel(465, int(std::strlen(RadialKeyboard::letters(group))), letter, false);
    font.setPixelSize(14);
    p.setFont(font);
    p.setPen(QColor(164, 195, 215));
    p.drawText(QRectF(10, 246, 600, 24), Qt::AlignCenter, "Sticks, buttons and triggers keep their normal game controls");
    return image;
}
