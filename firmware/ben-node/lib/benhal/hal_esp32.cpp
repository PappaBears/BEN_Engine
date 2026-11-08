// BEN Engine — benhal — ESP32 (Arduino framework) implementation for the Olimex ESP32-POE-ISO.
// Compiled only in the ESP32 environment. NOT yet verified on hardware: the espressif32
// platform could not be downloaded on the build host (see firmware/README.md).
#ifdef ARDUINO
#include "hal_esp32.h"
#include <ETH.h>
#include <WiFiClient.h>
#include <PubSubClient.h>
#include <Preferences.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <HTTPClient.h>
#include <Update.h>
#include <mbedtls/sha256.h>
#include <esp_sntp.h>
#include <time.h>

namespace benhal {

// ------------------------------------------------------------------ clock
uint32_t Esp32Clock::millis() { return ::millis(); }
bool Esp32Clock::sntp_valid() { return sntp_get_sync_status() != SNTP_SYNC_STATUS_RESET && time(nullptr) > 1700000000; }
uint64_t Esp32Clock::sntp_unix_s() { return (uint64_t)time(nullptr); }

// ------------------------------------------------------------------ gpio
void Esp32Gpio::pin_mode(uint8_t pin, Mode m) {
    pinMode(pin, m == OUTPUT ? ::OUTPUT : (m == INPUT_PULLUP ? ::INPUT_PULLUP : ::INPUT));
}
void Esp32Gpio::write(uint8_t pin, bool level) { digitalWrite(pin, level ? HIGH : LOW); }
bool Esp32Gpio::read(uint8_t pin) { return digitalRead(pin) == HIGH; }

// ------------------------------------------------------------------ i2c
bool Esp32I2c::write(uint8_t addr, const uint8_t* data, size_t n) {
    Wire.beginTransmission(addr); Wire.write(data, n); return Wire.endTransmission() == 0;
}
bool Esp32I2c::read(uint8_t addr, uint8_t* data, size_t n) {
    size_t got = Wire.requestFrom((int)addr, (int)n);
    for (size_t i = 0; i < got && i < n; ++i) data[i] = Wire.read();
    return got == n;
}

// ------------------------------------------------------------------ 1-wire
static OneWire* g_ow = nullptr; static DallasTemperature* g_dt = nullptr;
Esp32OneWire::Esp32OneWire(uint8_t pin) {
    g_ow = new OneWire(pin); g_dt = new DallasTemperature(g_ow);
    g_dt->begin(); g_dt->setResolution(12); g_dt->setWaitForConversion(false);
}
int Esp32OneWire::scan(uint8_t roms[][8], int max) {
    int n = 0; g_ow->reset_search();
    while (n < max && g_ow->search(roms[n])) if (roms[n][0] == 0x28) ++n;   // DS18B20 family only
    return n;
}
bool Esp32OneWire::request_temperatures() { g_dt->requestTemperatures(); return true; }
bool Esp32OneWire::read_c(const uint8_t rom[8], float& out_c) {
    float t = g_dt->getTempC(rom);
    if (t == DEVICE_DISCONNECTED_C || t < -55.0f || t > 125.0f) return false;
    out_c = t; return true;
}

// ------------------------------------------------------------------ nvs
static Preferences g_prefs;
Esp32Nvs::Esp32Nvs() { g_prefs.begin("ben", false); }
bool Esp32Nvs::get_str(const char* k, char* out, size_t cap) { if (!g_prefs.isKey(k)) return false; g_prefs.getString(k, out, cap); return true; }
bool Esp32Nvs::set_str(const char* k, const char* v) { return g_prefs.putString(k, v) > 0; }
bool Esp32Nvs::get_f32(const char* k, float& out) { if (!g_prefs.isKey(k)) return false; out = g_prefs.getFloat(k); return true; }
bool Esp32Nvs::set_f32(const char* k, float v) { return g_prefs.putFloat(k, v) > 0; }
bool Esp32Nvs::get_u32(const char* k, uint32_t& out) { if (!g_prefs.isKey(k)) return false; out = g_prefs.getUInt(k); return true; }
bool Esp32Nvs::set_u32(const char* k, uint32_t v) { return g_prefs.putUInt(k, v) > 0; }
bool Esp32Nvs::erase(const char* k) { return g_prefs.remove(k); }
bool Esp32Nvs::commit() { return true; }   // Preferences commits on each put

// ------------------------------------------------------------------ net (MQTT over Ethernet)
static WiFiClient g_tcp; static PubSubClient g_mqtt(g_tcp);
static Net::RxHandler g_rx = nullptr; static void* g_rx_ctx = nullptr;
static char g_rx_buf[1024];
static void mqtt_cb(char* topic, uint8_t* payload, unsigned int len) {
    if (!g_rx) return;
    if (len >= sizeof g_rx_buf) len = sizeof g_rx_buf - 1;
    memcpy(g_rx_buf, payload, len); g_rx_buf[len] = 0;
    g_rx(g_rx_ctx, topic, g_rx_buf, len);
}
static bool g_eth_up = false;
static void eth_event(WiFiEvent_t ev) {
    if (ev == ARDUINO_EVENT_ETH_GOT_IP) g_eth_up = true;
    else if (ev == ARDUINO_EVENT_ETH_DISCONNECTED || ev == ARDUINO_EVENT_ETH_STOP) g_eth_up = false;
}
Esp32Net::Esp32Net(const char* client_id, const char* host, uint16_t port, const char* user, const char* pass)
    : client_id_(client_id), host_(host), port_(port), user_(user), pass_(pass) {
    WiFi.onEvent(eth_event);
    // Olimex ESP32-POE-ISO: LAN8720, PHY addr 0, power pin 12, MDC 23, MDIO 18, clock out GPIO17
    ETH.begin(0, 12, 23, 18, ETH_PHY_LAN8720, ETH_CLOCK_GPIO17_OUT);
    g_mqtt.setServer(host_, port_); g_mqtt.setCallback(mqtt_cb); g_mqtt.setBufferSize(1024); g_mqtt.setKeepAlive(15);
}
bool Esp32Net::connected() { return g_eth_up && g_mqtt.connected(); }
bool Esp32Net::publish(const char* t, const char* p, size_t n, bool retain) { return g_mqtt.publish(t, (const uint8_t*)p, n, retain); }
bool Esp32Net::subscribe(const char* t) { snprintf(sub_, sizeof sub_, "%s", t); return g_mqtt.connected() ? g_mqtt.subscribe(t, 1) : false; }
void Esp32Net::set_rx_handler(RxHandler h, void* ctx) { g_rx = h; g_rx_ctx = ctx; }
void Esp32Net::poll() {
    if (!g_eth_up) return;
    if (!g_mqtt.connected()) {
        uint32_t now = ::millis();
        if (now - last_try_ms_ < 5000) return;                     // back off 5 s between attempts
        last_try_ms_ = now;
        // Last-will: the gateway sees an offline status immediately if the node drops.
        char will_topic[96]; snprintf(will_topic, sizeof will_topic, "%s", will_topic_);
        if (g_mqtt.connect(client_id_, user_, pass_, will_topic_[0] ? will_topic : nullptr, 1, true,
                           will_topic_[0] ? "{\"fw\":\"" BEN_FW_VERSION "\",\"errors\":[\"offline (last will)\"]}" : nullptr)) {
            if (sub_[0]) g_mqtt.subscribe(sub_, 1);
        }
        return;
    }
    g_mqtt.loop();
}
const char* Esp32Net::ip() { static char b[20]; snprintf(b, sizeof b, "%s", ETH.localIP().toString().c_str()); return b; }
void Esp32Net::set_will_topic(const char* t) { snprintf(will_topic_, sizeof will_topic_, "%s", t); }

// ------------------------------------------------------------------ system
uint32_t Esp32System::free_heap() { return ESP.getFreeHeap(); }
void Esp32System::reboot() { delay(200); ESP.restart(); }
void Esp32System::identify(bool on) { ident_ = on; }
void Esp32System::log(const char* line) { Serial.println(line); }

// OTA: stream the image into the inactive OTA partition while hashing it; abort unless the
// SHA-256 matches the one the gateway sent. With Secure Boot v2 enabled the bootloader
// additionally refuses an image whose signature does not verify (see firmware/README.md).
bool Esp32System::ota_begin(const char* url, const char* sha256_hex) {
    HTTPClient http; http.begin(url); http.setTimeout(15000);
    int code = http.GET();
    if (code != HTTP_CODE_OK) { http.end(); return false; }
    int len = http.getSize();
    if (len <= 0 || !Update.begin(len)) { http.end(); return false; }
    mbedtls_sha256_context sha; mbedtls_sha256_init(&sha); mbedtls_sha256_starts(&sha, 0);
    WiFiClient* s = http.getStreamPtr(); uint8_t buf[1024]; int remaining = len;
    while (remaining > 0 && http.connected()) {
        int n = s->readBytes(buf, min((int)sizeof buf, remaining));
        if (n <= 0) break;
        mbedtls_sha256_update(&sha, buf, n);
        if (Update.write(buf, n) != (size_t)n) { Update.abort(); http.end(); return false; }
        remaining -= n;
    }
    http.end();
    uint8_t digest[32]; mbedtls_sha256_finish(&sha, digest); mbedtls_sha256_free(&sha);
    char hex[65]; for (int i = 0; i < 32; ++i) snprintf(hex + 2 * i, 3, "%02x", digest[i]);
    bool match = remaining == 0 && strcasecmp(hex, sha256_hex) == 0;
    if (!match || !Update.end(true)) { Update.abort(); return false; }
    pending_restart_ = true;      // main loop restarts after the ack has been published
    return true;
}

} // namespace benhal
#endif // ARDUINO
