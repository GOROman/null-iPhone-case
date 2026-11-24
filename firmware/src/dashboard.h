#pragma once
#include <M5Unified.h>
#include "photo.h"
#include "muse_still.h"

namespace dashboard {
// v0.40 CAD, viewed from the back with the USB ports down.
// Active area origin in the case is approximately (+29.36,+27.30) mm.
// u grows towards -X and v towards -Y, with 0.108 mm per pixel.
constexpr int offsetY = 39;  // Positive moves toward the USB ports.
constexpr int photoX = 199, photoY = 201 + offsetY;
constexpr int statusX = 457, batteryY = 72 + offsetY, wifiY = 207 + offsetY, bleY = 336 + offsetY;
constexpr int listX = 271, listY = 527 + offsetY, clockX = 262, clockY = 769 + offsetY;
extern const uint8_t listFont[] asm("_binary_assets_null_regular_24_vlw_start");
extern const uint8_t dialFont[] asm("_binary_assets_null_regular_30_vlw_start");
extern const uint8_t titleFont[] asm("_binary_assets_null_regular_36_vlw_start");

inline void useFont(const uint8_t* font) {
    static const uint8_t* loaded = nullptr;
    if (font != loaded && M5.Display.loadFont(font)) loaded = font;
}

inline void label(const char* text, int x, int y) {
    M5.Display.drawString(text, x, y);
}

inline void muse(int x, int y, int scale) {
    // 56 x 59 source pixels, drawn in whole pixels to keep the sprite crisp.
    uint16_t row[56 * 4];
    for (int sy = 0; sy < 59; ++sy) {
        for (int sx = 0; sx < 56; ++sx) {
            const uint8_t pair = museStill[sy][sx / 2];
            const uint8_t grey = ((sx & 1) ? pair & 15 : pair >> 4) * 17;
            const auto color = M5.Display.color565(grey, grey, grey);
            for (int i = 0; i < scale; ++i) row[sx * scale + i] = color;
        }
        for (int i = 0; i < scale; ++i) {
            M5.Display.pushImage(x - 28 * scale, y - 59 * scale / 2 + sy * scale + i,
                                 56 * scale, 1, row);
        }
    }
}

inline void indicators(int batteryPercent) {
    auto& d = M5.Display;
    d.fillRoundRect(statusX - 22, batteryY - 22, 40, 24, 4, TFT_BLACK);
    d.fillRoundRect(statusX - 18, batteryY - 18, 32, 16, 2, TFT_WHITE);
    d.fillRect(statusX + 18, batteryY - 15, 4, 10, TFT_BLACK);
    char battery[8] = "--";
    if (batteryPercent >= 0 && batteryPercent <= 100) {
        d.fillRect(statusX - 16, batteryY - 16, 28 * batteryPercent / 100, 12, TFT_BLACK);
        snprintf(battery, sizeof(battery), "%d%%", batteryPercent);
    }
    useFont(dialFont);
    label(battery, statusX, batteryY + 18);
    for (int radius : {17, 29, 41}) {
        d.fillArc(statusX, wifiY + 19, radius, radius - 4, 225, 315, TFT_BLACK);
    }
    d.fillCircle(statusX, wifiY + 19, 4, TFT_BLACK);

    const int bx = statusX;
    d.drawWideLine(bx, bleY - 25, bx, bleY + 25, 2.5f, TFT_BLACK);
    d.drawWideLine(bx, bleY - 25, bx + 15, bleY - 12, 2.5f, TFT_BLACK);
    d.drawWideLine(bx + 15, bleY - 12, bx - 13, bleY + 13, 2.5f, TFT_BLACK);
    d.drawWideLine(bx, bleY + 25, bx + 15, bleY + 12, 2.5f, TFT_BLACK);
    d.drawWideLine(bx + 15, bleY + 12, bx - 13, bleY - 13, 2.5f, TFT_BLACK);
}

inline void drawClock(int secondOfDay) {
    auto& d = M5.Display;
    constexpr float turn = 6.28318530718f;
    auto radial = [&](float fraction, int inner, int outer, float weight) {
        float theta = fraction * turn;
        float x = sinf(theta), y = -cosf(theta);
        d.drawWideLine(clockX + lroundf(x * inner), clockY + lroundf(y * inner),
                       clockX + lroundf(x * outer), clockY + lroundf(y * outer), weight, TFT_BLACK);
    };
    for (int i = 0; i < 60; ++i) {
        bool hour = i % 5 == 0;
        radial(i / 60.0f, hour ? 91 : 99, 103, hour ? 2.5f : 1.0f);
    }
    useFont(dialFont);
    label("12", clockX, clockY - 72);
    label("3", clockX + 74, clockY);
    label("6", clockX, clockY + 73);
    label("9", clockX - 74, clockY);
    if (secondOfDay < 0) {
        // Park the hands at twelve until a phone or USB supplies the time.
        label("SYNC", clockX, clockY + 37);
        secondOfDay = 0;
    }
    radial((secondOfDay % 43200) / 43200.0f, -8, 51, 4);
    radial((secondOfDay % 3600) / 3600.0f, -10, 79, 2.5f);
    radial((secondOfDay % 60) / 60.0f, -17, 90, 1.0f);
    d.fillCircle(clockX, clockY, 6, TFT_BLACK);
}

inline void refreshClock(int secondOfDay, bool erase) {
    auto& d = M5.Display;
    constexpr int r = 140;  // Clear beyond the round window, including its edge.
    d.wakeup();
    d.setAutoDisplay(false);
    d.setEpdMode(erase ? m5gfx::epd_mode_t::epd_text : m5gfx::epd_mode_t::epd_fast);
    d.setTextDatum(middle_center);
    d.setTextColor(TFT_BLACK, TFT_WHITE);
    d.fillRect(clockX - r, clockY - r, r * 2, r * 2, TFT_WHITE);
    drawClock(secondOfDay);
    d.display(clockX - r, clockY - r, r * 2, r * 2);
    d.waitDisplay();
    d.sleep();
}

inline void statusList(bool saved) {
    auto& d = M5.Display;
    // Weekly percentages supplied by the case owner.
    const char* names[] = {"CODEX WEEKLY", "CLAUDE WEEKLY", "MUSE"};
    const char* values[] = {"68%", "72%", saved ? "SAVED" : "LOCAL"};
    useFont(listFont);
    for (int i = 0; i < 3; ++i) {
        int y = listY - 37 + 37 * i, x = listX - 185;
        if (i == 2) {
            muse(x, y - 1, 1);
        } else {
            d.fillRoundRect(x - 11, y - 8, 22, 17, 3, TFT_BLACK);
            d.fillRect(x - 1, y - 13, 3, 6, TFT_BLACK);
            d.fillRect(x - 6, y - 3, 3, 3, TFT_WHITE);
            d.fillRect(x + 3, y - 3, 3, 3, TFT_WHITE);
        }
        label(names[i], listX - 63, y);
        label(values[i], listX + 66, y);
    }
    d.drawFastVLine(listX + 120, listY - 45, 90, TFT_BLACK);
    for (int i = 0; i < 3; ++i) {
        int h = 9 + i * 11, x = listX + 149 + 16 * i;
        d.fillRect(x, listY + 18 - h, 10, h, TFT_BLACK);
    }
}

inline void paint(const uint8_t* pixels, int batteryPercent, int secondOfDay) {
    auto& d = M5.Display;
    d.wakeup();
    d.setAutoDisplay(false);
    d.setEpdMode(m5gfx::epd_mode_t::epd_quality);
    d.fillScreen(TFT_WHITE);
    d.setTextDatum(middle_center);
    d.setTextColor(TFT_BLACK, TFT_WHITE);
    if (pixels) {
        uint16_t row[photo::side];
        for (unsigned y = 0; y < photo::side; ++y) {
            for (unsigned x = 0; x < photo::side; ++x) {
                uint8_t b = pixels[(y * photo::side + x) / 2];
                uint8_t grey = ((x & 1) ? b & 15 : b >> 4) * 17;
                int dx = int(x) - 160, dy = int(y) - 160;
                row[x] = dx*dx + dy*dy <= 160*160 ? d.color565(grey, grey, grey) : TFT_WHITE;
            }
            d.pushImage(photoX - 160, photoY - 160 + y, photo::side, 1, row);
        }
    } else {
        muse(photoX, photoY - 37, 3);
        useFont(titleFont);
        label("NULL PAPER", photoX, photoY + 87);
    }
    indicators(batteryPercent);
    statusList(pixels != nullptr);
    drawClock(secondOfDay);
    d.display(0, 0, d.width(), d.height());
    d.waitDisplay();
    d.sleep();
}
}
