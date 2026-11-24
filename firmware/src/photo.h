#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace photo {
constexpr unsigned side = 320;
constexpr size_t bytes = side * side / 2;
enum Phase : uint8_t { ready, receiving, rendering, done, failed };
inline uint32_t word(const uint8_t* p) {
    return uint32_t(p[0]) | uint32_t(p[1]) << 8 | uint32_t(p[2]) << 16 | uint32_t(p[3]) << 24;
}
inline uint32_t crc32(const uint8_t* p, size_t count) {
    uint32_t crc = 0xffffffffu;
    while (count--) {
        crc ^= *p++;
        for (int i = 0; i < 8; ++i) crc = (crc >> 1) ^ ((crc & 1) ? 0xedb88320u : 0u);
    }
    return ~crc;
}
struct Transfer {
    uint8_t* pixels = nullptr;
    Phase phase = ready;
    size_t used = 0;
    uint32_t checksum = 0;

    void write(const uint8_t* p, size_t n) {
        if (!n || phase == rendering || phase == done) return;
        if (p[0] == 1 && n == 9 && word(p + 1) == bytes) {
            checksum = word(p + 5);
            used = 0;
            phase = receiving;
        } else if (phase == receiving && p[0] == 2 && n > 5 &&
                   word(p + 1) == used && n - 5 <= bytes - used) {
            std::memcpy(pixels + used, p + 5, n - 5);
            used += n - 5;
        } else if (phase == receiving && p[0] == 3 && n == 1 && used == bytes &&
                   crc32(pixels, used) == checksum) {
            phase = rendering;
        } else {
            phase = failed;
        }
    }
};
}
