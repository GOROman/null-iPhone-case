// Host-side protocol checks. Build with c++ -std=c++17 test/receiver.cpp.
#include "../src/photo.h"
#include <algorithm>
#include <array>
#include <cassert>
#include <vector>
int main() {
    std::array<uint8_t, photo::bytes> buffer{};
    photo::Transfer rx;
    rx.pixels = buffer.data();
    const uint8_t begin[] = {1, 0, 0xc8, 0, 0, 0xcd, 0x5e, 0x59, 0x58};
    const uint8_t end[] = {3};
    const uint8_t wrongOffset[] = {2, 1, 0, 0, 0, 0xff};
    rx.write(begin, sizeof(begin));
    rx.write(wrongOffset, sizeof(wrongOffset));
    assert(rx.phase == photo::failed);
    rx.write(begin, sizeof(begin));
    rx.write(end, 1);
    assert(rx.phase == photo::failed);
    for (bool corrupt : {true, false}) {
        rx.write(begin, sizeof(begin));
        for (size_t offset = 0; offset < photo::bytes;) {
            size_t n = std::min<size_t>(173, photo::bytes - offset);
            std::vector<uint8_t> p{2, uint8_t(offset), uint8_t(offset >> 8), 0, 0};
            for (size_t i = 0; i < n; ++i) p.push_back(offset + i < photo::bytes/2 ? 0 : 255);
            if (corrupt && offset == 0) p[5] ^= 1;
            rx.write(p.data(), p.size());
            assert(rx.phase == photo::receiving);
            offset += n;
        }
        rx.write(end, 1);
        assert(rx.phase == (corrupt ? photo::failed : photo::rendering));
    }
    rx.write(begin, sizeof(begin));
    assert(rx.phase == photo::rendering && rx.used == photo::bytes);
}
