#pragma once
#include <sys/time.h>
#include <ctime>
#include <cstdint>

namespace paperClock {
constexpr time_t earliest = 1704067200; // 2024-01-01 UTC
inline bool valid(uint32_t epoch, int zoneMinutes) {
    return epoch >= earliest && zoneMinutes >= -720 && zoneMinutes <= 840;
}
inline int localSecond(time_t epoch, int zoneMinutes) {
    if (epoch < earliest) return -1;
    return int((epoch + zoneMinutes * 60) % 86400);
}
}
