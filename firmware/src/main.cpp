#include <Arduino.h>
#include <M5Unified.h>
#include <esp32-hal-alloc-ble-mem.h>  // Keep the controller memory for NimBLE before Arduino startup.
#include <NimBLEDevice.h>
#include <Preferences.h>
#include <esp_sleep.h>
#include <HWCDC.h>
#include <inttypes.h>
#include "clock_time.h"
#include <mutex>
#include "dashboard.h"

namespace {
constexpr char serviceId[] = "ad7c4900-71f4-4f77-9ccd-798cf78fb040";
constexpr char packetId[]  = "ad7c4901-71f4-4f77-9ccd-798cf78fb040";
constexpr char statusId[]  = "ad7c4902-71f4-4f77-9ccd-798cf78fb040";
constexpr char clockId[] = "ad7c4903-71f4-4f77-9ccd-798cf78fb040";
Preferences store;
HWCDC clockUSB;
int zoneMinutes = 0;
int lastSecond = -2;
uint32_t pendingEpoch = 0;
int pendingZone = 0;
bool clockEnabled = false;
photo::Transfer transfer;
std::mutex guard;
NimBLEAddress owner;
bool hasOwner = false, disconnected = false, radio = false, hasPhoto = false;
uint32_t opened, activity, displayedCRC;

void tickClock() {
    const int second = paperClock::localSecond(time(nullptr), zoneMinutes);
    if (second == lastSecond) return;
    const bool erase = lastSecond < 0 || second < 0 || lastSecond / 60 != second / 60;
    dashboard::refreshClock(second, erase);
    lastSecond = second;
}

[[noreturn]] void powerOff() {
    if (radio) NimBLEDevice::deinit(true);
    M5.Display.waitDisplay();
    if (clockEnabled && time(nullptr) >= paperClock::earliest) {
        // Retain the panel framebuffer between ticks after disconnecting BLE.
        if (digitalRead(4)) esp_sleep_enable_ext0_wakeup(GPIO_NUM_4, 0);
        for (;;) {
            tickClock();
            timeval now;
            gettimeofday(&now, nullptr);
            esp_sleep_enable_timer_wakeup(1000000 - now.tv_usec);
            esp_light_sleep_start();
            if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_EXT0 || !digitalRead(4)) esp_restart();
        }
    }
    if (M5.getBoard() == m5::board_t::board_M5PaperDIY) {
        M5.Power.M5pm1.powerOff();
        delay(300);
    }
    esp_deep_sleep_start();
    for (;;) delay(1000);
}

bool authorized(const NimBLEConnInfo& peer) {
    return peer.isEncrypted() && peer.isBonded() && (!hasOwner || peer.getIdAddress() == owner);
}

class Connections : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer*, NimBLEConnInfo& peer) override {
        { std::lock_guard<std::mutex> lock(guard); activity = millis(); }
        NimBLEDevice::startSecurity(peer.getConnHandle());
    }
    void onAuthenticationComplete(NimBLEConnInfo& peer) override {
        if (!authorized(peer)) {
            NimBLEDevice::getServer()->disconnect(peer.getConnHandle());
            if (hasOwner && !(owner == peer.getIdAddress())) NimBLEDevice::deleteBond(peer.getIdAddress());
        }
    }
    void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) override {
        std::lock_guard<std::mutex> lock(guard);
        disconnected = true;
    }
} connections;

class Packets : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* c, NimBLEConnInfo& peer) override {
        if (!authorized(peer)) return;
        auto value = c->getValue();
        std::lock_guard<std::mutex> lock(guard);
        transfer.write(value.data(), value.size());
        activity = millis();
    }
    void onRead(NimBLECharacteristic* c, NimBLEConnInfo& peer) override {
        std::lock_guard<std::mutex> lock(guard);
        uint32_t crc = transfer.checksum;
        uint8_t status[] = {uint8_t(authorized(peer) ? transfer.phase : photo::failed),
                            uint8_t(crc), uint8_t(crc >> 8), uint8_t(crc >> 16), uint8_t(crc >> 24)};
        c->setValue(status, sizeof(status));
    }
} packets;

class ClockWrites : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* c, NimBLEConnInfo& peer) override {
        if (!authorized(peer)) return;
        auto value = c->getValue();
        if (value.size() != 6) return;
        auto* p = value.data();
        uint32_t epoch = photo::word(p);
        int zone = int16_t(uint16_t(p[4]) | uint16_t(p[5]) << 8);
        if (paperClock::valid(epoch, zone)) {
            std::lock_guard<std::mutex> lock(guard);
            pendingEpoch = epoch;
            pendingZone = zone;
        }
    }
} clockWrites;

bool setClock(uint32_t epoch, int zone) {
    timeval now{time_t(epoch), 0};
    if (settimeofday(&now, nullptr) != 0) return false;
    if (zoneMinutes != zone) {
        zoneMinutes = zone;
        store.putInt("tzMin", zone);
    }
    return true;
}

void readClocks() {
    uint32_t epoch;
    int zone;
    {
        std::lock_guard<std::mutex> lock(guard);
        epoch = pendingEpoch;
        zone = pendingZone;
        pendingEpoch = 0;
    }
    if (epoch) setClock(epoch, zone);
    static char line[48];
    static size_t length = 0;
    while (clockUSB.available()) {
        int c = clockUSB.read();
        if (c == '\n') {
            line[length] = 0;
            char extra;
            if (sscanf(line, "TIME %" SCNu32 " %d %c", &epoch, &zone, &extra) == 2 &&
                paperClock::valid(epoch, zone)) {
                if (setClock(epoch, zone)) {
                    tickClock();
                    clockUSB.printf("TIME OK %02d:%02d:%02d\n", lastSecond / 3600, lastSecond / 60 % 60, lastSecond % 60);
                }
            }
            if (!strcmp(line, "CLOCK?") && lastSecond >= 0)
                clockUSB.printf("CLOCK %02d:%02d:%02d\n", lastSecond / 3600, lastSecond / 60 % 60, lastSecond % 60);
            length = 0;
        } else if (length + 1 < sizeof(line) && c != '\r') {
            line[length++] = char(c);
        }
    }
}

void paint(const uint8_t* pixels) {
    lastSecond = paperClock::localSecond(time(nullptr), zoneMinutes);
    dashboard::paint(pixels, M5.Power.getBatteryLevel(), lastSecond);
}

bool showReceived() {
    if (hasPhoto && displayedCRC == transfer.checksum) return true;
    // NVS commits the new blob atomically. An interrupted refresh is retried at boot.
    if (store.putBytes("photo", transfer.pixels, photo::bytes) != photo::bytes) return false;
    paint(transfer.pixels);
    displayedCRC = transfer.checksum;
    hasPhoto = true;
    return store.putUInt("painted", displayedCRC) == sizeof(displayedCRC);
}
}

void setup() {
    clockUSB.begin(115200);
    auto cfg = M5.config();
    cfg.clear_display = false;
    cfg.internal_imu = cfg.internal_mic = cfg.internal_spk = false;
    M5.begin(cfg);
    clockUSB.printf("PaperDIY board %d, display %dx%d\n", int(M5.getBoard()), M5.Display.width(), M5.Display.height());
    if (M5.getBoard() != m5::board_t::board_M5PaperDIY) powerOff();
    auto& d = M5.Display;
    d.setRotation(0);
    if (d.width() != 540) d.setRotation(1);
    if (d.width() != 540 || d.height() != 960) powerOff();
    if (!store.begin("case040", false, "paperdata")) powerOff();
    zoneMinutes = store.getInt("tzMin", 0);
    clockEnabled = true;
    pinMode(4, INPUT_PULLUP);
    pinMode(3, INPUT_PULLUP);
    transfer.pixels = static_cast<uint8_t*>(ps_malloc(photo::bytes));
    if (!transfer.pixels) powerOff();
    constexpr uint32_t layoutRevision = 4;
    const bool layoutChanged = store.getInt("layoutY", 0) != dashboard::offsetY ||
                               store.getUInt("layoutRev", 0) != layoutRevision;
    hasPhoto = store.getBytesLength("photo") == photo::bytes &&
               store.getBytes("photo", transfer.pixels, photo::bytes) == photo::bytes;
    if (hasPhoto) {
        displayedCRC = photo::crc32(transfer.pixels, photo::bytes);
        if (layoutChanged || !store.isKey("painted") || store.getUInt("painted") != displayedCRC) {
            paint(transfer.pixels);
            store.putUInt("painted", displayedCRC);
        }
    } else if (layoutChanged || !store.getBool("welcome", false)) {
        paint(nullptr);
        store.putBool("welcome", true);
    }

    if (layoutChanged) {
        store.putInt("layoutY", dashboard::offsetY);
        store.putUInt("layoutRev", layoutRevision);
    }
    // A cold restart may have lost RTC time while old hands remain on the panel.
    if (lastSecond == -2) tickClock();
    d.sleep();
    if (!NimBLEDevice::init("NULL PAPER")) powerOff();
    radio = true;
    if (!digitalRead(4) && !digitalRead(3)) {
        delay(700);
        if (!digitalRead(4) && !digitalRead(3)) NimBLEDevice::deleteAllBonds();
    }
    hasOwner = NimBLEDevice::getNumBonds() > 0;
    if (hasOwner) owner = NimBLEDevice::getBondedAddress(0);
    NimBLEDevice::setSecurityAuth(true, false, true);
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_NO_INPUT_OUTPUT);
    auto* server = NimBLEDevice::createServer();
    server->setCallbacks(&connections, false);
    server->advertiseOnDisconnect(false);
    auto* service = server->createService(serviceId);
    service->createCharacteristic(packetId, NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_ENC, 512)
        ->setCallbacks(&packets);
    service->createCharacteristic(statusId, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::READ_ENC, 5)
        ->setCallbacks(&packets);
    service->createCharacteristic(clockId, NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_ENC, 6)
        ->setCallbacks(&clockWrites);
    service->start();
    auto* adv = NimBLEDevice::getAdvertising();
    adv->enableScanResponse(true);
    adv->addServiceUUID(serviceId);
    adv->setName("NULL PAPER");
    adv->setMinInterval(160);
    adv->setMaxInterval(240);
    opened = activity = millis();
    if (!adv->start()) powerOff();
}

void loop() {
    readClocks();
    photo::Phase phase;
    bool expired;
    {
        std::lock_guard<std::mutex> lock(guard);
        phase = transfer.phase;
        const uint32_t idle = millis() - activity;
        expired = disconnected || millis() - opened >= 300000 ||
                  idle >= (phase == photo::done ? 10000u : phase == photo::receiving ? 20000u : 60000u);
    }
    if (phase == photo::rendering) {
        bool ok = showReceived();
        std::lock_guard<std::mutex> lock(guard);
        transfer.phase = ok ? photo::done : photo::failed;
        activity = millis();
    } else {
        if (phase != photo::receiving) tickClock();
        if (expired) powerOff();
    }
    delay(25);
}
