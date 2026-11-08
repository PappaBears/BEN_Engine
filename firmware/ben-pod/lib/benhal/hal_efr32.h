// BEN Engine — benhal — Silicon Labs EFR32MG24 / MGM240P implementation (Gecko SDK = Simplicity SDK
// + OpenThread). Compiled only when BEN_TARGET_EFR32 is defined (gecko/ CMake flow, the .slcp project,
// or the platformio `mgm240p` env). The host build (make test / native) never sees this file's body.
//
// Mapping of the abstract HAL onto the platform:
//   Clock     sl_sleeptimer (monotonic ms) + SNTP over Thread (otSntpClient) for the wall clock
//   Gpio      em_gpio / sl_gpio through a logical-pin table (bencore keeps its small integer pin ids)
//   I2cBus    sl_i2cspm (SHT45, SDP810, RTD ADC on I²C/SPI bridge)
//   OneWire   not fitted on the Pod (Pt1000 replaces DS18B20); the interface returns 0 sensors
//   Nvs       NVM3 default instance, keys hashed from the string key (NVM3 objects are 20-bit ids)
//   Net       MQTT 3.1.1 over mbedTLS/PSA (mutual X.509) over OpenThread UDP/TCP (otTcp) to the broker
//   System    Gecko Bootloader API (btl_interface) for signed OTA, PSA Crypto for attestation, sl_system
//
// STATUS: written against Simplicity SDK 2024.6 / OpenThread 2024-Q2 APIs. NOT compiled on the build
// host (no Silicon Labs toolchain there); see firmware/README.md.
#pragma once
#ifdef BEN_TARGET_EFR32
#include <cstdint>
#include <cstddef>
#include "hal.h"

extern "C" {
#include "openthread/instance.h"
#include "openthread/thread.h"
#include "openthread/ip6.h"
#include "openthread/tcp.h"
#include "openthread/sntp.h"
#include "openthread/joiner.h"
#include "psa/crypto.h"
}

#ifndef BEN_FW_VERSION
#define BEN_FW_VERSION "0.0.0-dev"
#endif

namespace benhal {

// ---- logical pin ids used by bencore (outputs.cpp RELAYS[] and main.cpp) -> EFR32 port/pin.
struct PinMap { uint8_t logical; uint8_t port; uint8_t pin; };
extern const PinMap PIN_TABLE[];
extern const size_t PIN_TABLE_LEN;
bool pin_lookup(uint8_t logical, uint8_t& port, uint8_t& pin);

struct Efr32Clock : Clock {
    uint32_t millis() override;
    bool     sntp_valid() override;
    uint64_t sntp_unix_s() override;
    // Called from the SNTP response callback.
    void on_sntp(uint64_t unix_s);
private:
    bool valid_ = false; uint64_t anchor_unix_ = 0; uint32_t anchor_ms_ = 0;
};

struct Efr32Gpio : Gpio {
    void pin_mode(uint8_t pin, Mode m) override;
    void write(uint8_t pin, bool level) override;
    bool read(uint8_t pin) override;
};

struct Efr32I2c : I2cBus {
    bool write(uint8_t addr, const uint8_t* data, size_t n) override;
    bool read(uint8_t addr, uint8_t* data, size_t n) override;
};

// No 1-Wire on the Pod: Pt1000 strings go to the RTD ADC. Kept so the Hal struct is complete.
struct Efr32NoOneWire : OneWireBus {
    int  scan(uint8_t[][8], int) override { return 0; }
    bool request_temperatures() override { return false; }
    bool read_c(const uint8_t[8], float&) override { return false; }
};

// NVM3-backed key/value store. Object id = 0x10000 | fnv1a16(key); collisions are detected at
// provisioning time by the host tool (keys are a fixed, small set: unit, node_id, g_*/o_*, cal_id, tel_ms).
struct Efr32Nvs : Nvs {
    Efr32Nvs();
    bool get_str(const char* key, char* out, size_t cap) override;
    bool set_str(const char* key, const char* val) override;
    bool get_f32(const char* key, float& out) override;
    bool set_f32(const char* key, float val) override;
    bool get_u32(const char* key, uint32_t& out) override;
    bool set_u32(const char* key, uint32_t val) override;
    bool erase(const char* key) override;
    bool commit() override;
    static uint32_t object_id(const char* key);
};

// MQTT over TLS over OpenThread TCP. The TLS client key is a PSA opaque key living in Secure Vault
// (BEN_KEY_ID_DEVICE); the device certificate and CA chain are read from NVM3 at connect time.
struct Efr32Net : Net {
    Efr32Net(otInstance* ot, const char* client_id, const char* broker_ip6, uint16_t port);
    bool connected() override;
    bool publish(const char* topic, const char* payload, size_t len, bool retain) override;
    bool subscribe(const char* topic) override;
    void set_rx_handler(RxHandler h, void* ctx) override;
    void poll() override;
    int  rssi() override;
    const char* ip() override;
    void set_will_topic(const char* t);
    // Mesh diagnostics for the status message (PROTOCOL.md v1.1 fields).
    const char* parent_rloc16();   // "0x5400", "leader", "router"
    uint8_t     lqi();
    const char* path() const { return path_; }   // "thread" | "eth" | "rs485" (Pod E)
private:
    bool tcp_open();
    bool tls_handshake();
    bool mqtt_connect();
    void mqtt_rx();
    otInstance* ot_; const char* client_id_; const char* broker_; uint16_t port_;
    char sub_[96] = ""; char will_topic_[96] = ""; char path_[8] = "thread";
    uint32_t last_try_ms_ = 0; bool tcp_up_ = false, tls_up_ = false, mqtt_up_ = false;
    RxHandler rx_ = nullptr; void* rx_ctx_ = nullptr;
    char ip_buf_[46] = "::"; char parent_buf_[12] = "";
    uint16_t packet_id_ = 1;
};

struct Efr32System : System {
    explicit Efr32System(otInstance* ot) : ot_(ot) {}
    uint32_t free_heap() override;
    void reboot() override;
    bool ota_begin(const char* url, const char* sha256_hex) override;   // Gecko Bootloader slot 0 + signed GBL
    void identify(bool on) override;
    void log(const char* line) override;
    bool ident() const { return ident_; }
    bool pending_restart() const { return pending_restart_; }
    // Attestation: ECDSA P-256 over nonce||fw_hash with the Secure Vault device key; DER signature.
    size_t attest(const uint8_t* nonce, size_t nonce_len, uint8_t* sig_der, size_t cap, char* fw_hash_hex65);
    bool   boot_verified() const;      // Gecko Bootloader reported a verified image
    const char* cert_id();             // hex serial of the device certificate stored in NVM3
private:
    otInstance* ot_; bool ident_ = false; bool pending_restart_ = false; char cert_id_[41] = "";
};

// PSA key ids reserved for the Pod (persistent, Secure Vault wrapped).
constexpr psa_key_id_t BEN_KEY_ID_DEVICE = 0x00010001;   // ECDSA P-256 device identity / TLS client key
constexpr psa_key_id_t BEN_KEY_ID_THREAD = 0x00010002;   // wrapping key for the Thread dataset in NVM3

} // namespace benhal
#endif // BEN_TARGET_EFR32
