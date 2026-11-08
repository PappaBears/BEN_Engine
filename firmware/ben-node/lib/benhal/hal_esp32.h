// BEN Engine — benhal — ESP32 implementation declarations (Arduino framework only).
#pragma once
#ifdef ARDUINO
#include <Arduino.h>
#include "hal.h"

#ifndef BEN_FW_VERSION
#define BEN_FW_VERSION "0.0.0-dev"
#endif

namespace benhal {

struct Esp32Clock : Clock {
    uint32_t millis() override; bool sntp_valid() override; uint64_t sntp_unix_s() override;
};
struct Esp32Gpio : Gpio {
    void pin_mode(uint8_t pin, Mode m) override; void write(uint8_t pin, bool level) override; bool read(uint8_t pin) override;
};
struct Esp32I2c : I2cBus {
    bool write(uint8_t addr, const uint8_t* data, size_t n) override; bool read(uint8_t addr, uint8_t* data, size_t n) override;
};
struct Esp32OneWire : OneWireBus {
    explicit Esp32OneWire(uint8_t pin);
    int scan(uint8_t roms[][8], int max) override; bool request_temperatures() override; bool read_c(const uint8_t rom[8], float& out_c) override;
};
struct Esp32Nvs : Nvs {
    Esp32Nvs();
    bool get_str(const char* key, char* out, size_t cap) override; bool set_str(const char* key, const char* val) override;
    bool get_f32(const char* key, float& out) override; bool set_f32(const char* key, float val) override;
    bool get_u32(const char* key, uint32_t& out) override; bool set_u32(const char* key, uint32_t val) override;
    bool erase(const char* key) override; bool commit() override;
};
struct Esp32Net : Net {
    Esp32Net(const char* client_id, const char* host, uint16_t port, const char* user, const char* pass);
    bool connected() override; bool publish(const char* topic, const char* payload, size_t len, bool retain) override;
    bool subscribe(const char* topic) override; void set_rx_handler(RxHandler h, void* ctx) override; void poll() override;
    const char* ip() override;
    void set_will_topic(const char* t);
private:
    const char* client_id_; const char* host_; uint16_t port_; const char* user_; const char* pass_;
    char sub_[96] = ""; char will_topic_[96] = ""; uint32_t last_try_ms_ = 0;
};
struct Esp32System : System {
    uint32_t free_heap() override; void reboot() override; bool ota_begin(const char* url, const char* sha256_hex) override;
    void identify(bool on) override; void log(const char* line) override;
    bool ident() const { return ident_; } bool pending_restart() const { return pending_restart_; }
private:
    bool ident_ = false; bool pending_restart_ = false;
};

} // namespace benhal
#endif
