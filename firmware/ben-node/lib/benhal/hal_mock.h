// BEN Engine — benhal — host mock implementation used by unit tests and `pio run -e native`.
#pragma once
#include "hal.h"
#include <map>
#include <string>
#include <vector>
#include <cstring>
#include <cstdio>

namespace benhal {

struct MockClock : Clock {
    uint32_t ms = 0; bool valid = false; uint64_t unix_at_set = 0; uint32_t ms_at_set = 0;
    uint32_t millis() override { return ms; }
    bool sntp_valid() override { return valid; }
    uint64_t sntp_unix_s() override { return valid ? unix_at_set + (ms - ms_at_set) / 1000 : 0; }
    void advance(uint32_t d) { ms += d; }
    void set_sntp(uint64_t unix_s) { valid = true; unix_at_set = unix_s; ms_at_set = ms; }
};

struct MockGpio : Gpio {
    std::map<uint8_t, bool> levels; std::map<uint8_t, Mode> modes;
    void pin_mode(uint8_t pin, Mode m) override { modes[pin] = m; }
    void write(uint8_t pin, bool level) override { levels[pin] = level; }
    bool read(uint8_t pin) override { auto it = levels.find(pin); return it != levels.end() && it->second; }
};

struct MockI2c : I2cBus {
    bool write(uint8_t, const uint8_t*, size_t) override { return true; }
    bool read(uint8_t, uint8_t* d, size_t n) override { memset(d, 0, n); return true; }
};

struct MockOneWire : OneWireBus {
    std::vector<float> temps;
    int scan(uint8_t roms[][8], int max) override {
        int n = (int)temps.size() < max ? (int)temps.size() : max;
        for (int i = 0; i < n; ++i) { memset(roms[i], 0, 8); roms[i][0] = 0x28; roms[i][7] = (uint8_t)i; }
        return n;
    }
    bool request_temperatures() override { return true; }
    bool read_c(const uint8_t rom[8], float& out) override {
        size_t i = rom[7]; if (i >= temps.size()) return false; out = temps[i]; return true;
    }
};

struct MockNvs : Nvs {
    std::map<std::string, std::string> s; std::map<std::string, float> f; std::map<std::string, uint32_t> u;
    int commits = 0;
    bool get_str(const char* k, char* out, size_t cap) override {
        auto it = s.find(k); if (it == s.end()) return false; snprintf(out, cap, "%s", it->second.c_str()); return true; }
    bool set_str(const char* k, const char* v) override { s[k] = v; return true; }
    bool get_f32(const char* k, float& out) override { auto it = f.find(k); if (it == f.end()) return false; out = it->second; return true; }
    bool set_f32(const char* k, float v) override { f[k] = v; return true; }
    bool get_u32(const char* k, uint32_t& out) override { auto it = u.find(k); if (it == u.end()) return false; out = it->second; return true; }
    bool set_u32(const char* k, uint32_t v) override { u[k] = v; return true; }
    bool erase(const char* k) override { s.erase(k); f.erase(k); u.erase(k); return true; }
    bool commit() override { ++commits; return true; }
};

struct MockNet : Net {
    struct Msg { std::string topic; std::string payload; bool retain; };
    bool up = true;
    std::vector<Msg> published;
    std::vector<std::string> subscriptions;
    RxHandler handler = nullptr; void* handler_ctx = nullptr;
    bool connected() override { return up; }
    bool publish(const char* t, const char* p, size_t n, bool retain) override {
        if (!up) return false;
        published.push_back({t, std::string(p, n), retain}); return true; }
    bool subscribe(const char* t) override { subscriptions.push_back(t); return up; }
    void set_rx_handler(RxHandler h, void* ctx) override { handler = h; handler_ctx = ctx; }
    void poll() override {}
    const char* ip() override { return "10.20.0.31"; }
    // test helper: deliver an inbound message
    void inject(const char* topic, const char* payload) { if (handler) handler(handler_ctx, topic, payload, strlen(payload)); }
    const Msg* last_on(const char* suffix) const {
        for (auto it = published.rbegin(); it != published.rend(); ++it) {
            size_t sl = strlen(suffix); if (it->topic.size() >= sl && it->topic.compare(it->topic.size() - sl, sl, suffix) == 0) return &*it; }
        return nullptr;
    }
    size_t count_on(const char* suffix) const {
        size_t c = 0; size_t sl = strlen(suffix);
        for (auto& m : published) if (m.topic.size() >= sl && m.topic.compare(m.topic.size() - sl, sl, suffix) == 0) ++c;
        return c;
    }
};

struct MockSystem : System {
    uint32_t heap = 180000; int reboots = 0; int ota_calls = 0; bool ident = false; std::string last_ota_url, last_ota_sha;
    std::vector<std::string> logs;
    uint32_t free_heap() override { return heap; }
    void reboot() override { ++reboots; }
    bool ota_begin(const char* url, const char* sha) override { ++ota_calls; last_ota_url = url; last_ota_sha = sha; return true; }
    void identify(bool on) override { ident = on; }
    void log(const char* line) override { logs.push_back(line); }
};

// Convenience bundle for tests.
struct MockHal {
    MockClock clock; MockGpio gpio; MockI2c i2c; MockOneWire onewire; MockNvs nvs; MockNet net; MockSystem sys;
    Hal hal;
    MockHal() { hal.clock = &clock; hal.gpio = &gpio; hal.i2c = &i2c; hal.onewire = &onewire; hal.nvs = &nvs; hal.net = &net; hal.sys = &sys; }
};

} // namespace benhal
