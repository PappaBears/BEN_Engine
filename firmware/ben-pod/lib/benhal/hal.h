// BEN Engine — benhal — thin hardware abstraction.
// Everything the application needs from the platform goes through these interfaces so
// lib/bencore compiles unchanged on the EFR32MG24 / MGM240P target (Simplicity SDK + OpenThread) and on
// the host (mock, for tests).
#pragma once
#include <cstdint>
#include <cstddef>

namespace benhal {

struct Clock {
    virtual ~Clock() = default;
    virtual uint32_t millis() = 0;                 // monotonic since boot, wraps at 2^32
    virtual bool     sntp_valid() = 0;             // true once SNTP has set the wall clock
    virtual uint64_t sntp_unix_s() = 0;            // wall clock (unix s) when valid
};

struct Gpio {
    enum Mode : uint8_t { INPUT_FLOAT, INPUT_PULLUP, OUTPUT };
    virtual ~Gpio() = default;
    virtual void pin_mode(uint8_t pin, Mode m) = 0;
    virtual void write(uint8_t pin, bool level) = 0;
    virtual bool read(uint8_t pin) = 0;
};

struct I2cBus {
    virtual ~I2cBus() = default;
    virtual bool write(uint8_t addr, const uint8_t* data, size_t n) = 0;
    virtual bool read(uint8_t addr, uint8_t* data, size_t n) = 0;
};

struct OneWireBus {
    virtual ~OneWireBus() = default;
    virtual int  scan(uint8_t roms[][8], int max) = 0;         // number of devices found
    virtual bool request_temperatures() = 0;                    // broadcast convert
    virtual bool read_c(const uint8_t rom[8], float& out_c) = 0;
};

// Key/value non-volatile storage (NVM3 on target, in-memory map on host).
struct Nvs {
    virtual ~Nvs() = default;
    virtual bool get_str(const char* key, char* out, size_t cap) = 0;
    virtual bool set_str(const char* key, const char* val) = 0;
    virtual bool get_f32(const char* key, float& out) = 0;
    virtual bool set_f32(const char* key, float val) = 0;
    virtual bool get_u32(const char* key, uint32_t& out) = 0;
    virtual bool set_u32(const char* key, uint32_t val) = 0;
    virtual bool erase(const char* key) = 0;
    virtual bool commit() = 0;
};

// Message transport (MQTT on target). The core never sees sockets.
struct Net {
    using RxHandler = void (*)(void* ctx, const char* topic, const char* payload, size_t len);
    virtual ~Net() = default;
    virtual bool connected() = 0;
    virtual bool publish(const char* topic, const char* payload, size_t len, bool retain) = 0;
    virtual bool subscribe(const char* topic) = 0;
    virtual void set_rx_handler(RxHandler h, void* ctx) = 0;
    virtual void poll() = 0;                       // service the transport
    virtual int  rssi() { return 0; }              // dBm to the Thread parent; 0 for wired Ethernet (Pod E)
    virtual const char* ip() { return "0.0.0.0"; }
};

struct System {
    virtual ~System() = default;
    virtual uint32_t free_heap() = 0;
    virtual void reboot() = 0;
    // OTA: start a download+verify+swap; returns false if it could not start.
    virtual bool ota_begin(const char* url, const char* sha256_hex) = 0;
    virtual void identify(bool on) = 0;           // drive the IDENT LED
    virtual void log(const char* line) = 0;
};

// Everything bundled for the application.
struct Hal {
    Clock*      clock = nullptr;
    Gpio*       gpio = nullptr;
    I2cBus*     i2c = nullptr;
    OneWireBus* onewire = nullptr;
    Nvs*        nvs = nullptr;
    Net*        net = nullptr;
    System*     sys = nullptr;
};

} // namespace benhal
