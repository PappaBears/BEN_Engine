// BEN Engine — benhal — EFR32MG24 / MGM240P implementation (Simplicity SDK + OpenThread).
// Compiled only with -DBEN_TARGET_EFR32. NOT compiled on the build host: no Silicon Labs toolchain
// there (firmware/README.md "What was compiled here"). API names follow Simplicity SDK 2024.6; the first
// build in Simplicity Studio will most likely need signature fixes, as the previous target did.
#ifdef BEN_TARGET_EFR32
#include "hal_efr32.h"
#include <cstring>
#include <cstdio>

extern "C" {
#include "sl_system_init.h"
#include "sl_sleeptimer.h"
#include "sl_i2cspm_instances.h"
#include "em_gpio.h"
#include "nvm3_default.h"
#include "btl_interface.h"
#include "sl_memory_manager.h"
#include "openthread/link.h"
#include "openthread/netdata.h"
#include "mbedtls/ssl.h"
#include "mbedtls/x509_crt.h"
#include "mbedtls/sha256.h"
#include "mbedtls/pk.h"
}

namespace benhal {

// ----------------------------------------------------------------- logical pin table (BEN Pod v1 PCB)
// bencore/outputs.cpp keeps the historical logical ids 32/33 for relay1/relay2 so the core and its tests
// are untouched; relay3/relay4 (ids 14/15) are not fitted on the Pod and map to no pin.
const PinMap PIN_TABLE[] = {
    {32, gpioPortB, 0},   // RELAY1 (Pod E)      K1 coil driver
    {33, gpioPortB, 1},   // RELAY2 (Pod E)      K2 coil driver
    {36, gpioPortC, 0},   // LEAK comparator out HIGH = wet
    {39, gpioPortC, 1},   // DOOR dry contact    HIGH = open (pull-up)
    {34, gpioPortC, 2},   // PULSE S0 opto       falling edge
    {35, gpioPortC, 3},   // DI2 / EPO monitor   monitor only
    {2,  gpioPortD, 2},   // IDENT LED (blue)
    {3,  gpioPortD, 3},   // LINK LED (amber)
    {5,  gpioPortA, 5},   // DIP bit 0 .. 3 on PA5..PA8 (4-bit node id override)
    {6,  gpioPortA, 6}, {7, gpioPortA, 7}, {8, gpioPortA, 8},
    {40, gpioPortA, 0},   // RTD ADC (ADS124S08) CS
    {41, gpioPortA, 4},   // RTD ADC DRDY
    {42, gpioPortB, 2},   // Pod E: LAN8742 nRST
    {43, gpioPortB, 3},   // Pod E: RS-485 DE/RE
};
const size_t PIN_TABLE_LEN = sizeof PIN_TABLE / sizeof PIN_TABLE[0];

bool pin_lookup(uint8_t logical, uint8_t& port, uint8_t& pin) {
    for (size_t i = 0; i < PIN_TABLE_LEN; ++i)
        if (PIN_TABLE[i].logical == logical) { port = PIN_TABLE[i].port; pin = PIN_TABLE[i].pin; return true; }
    return false;
}

// ----------------------------------------------------------------- clock
uint32_t Efr32Clock::millis() {
    uint64_t ticks = sl_sleeptimer_get_tick_count64();
    uint64_t ms; sl_sleeptimer_tick64_to_ms(ticks, &ms);
    return (uint32_t)ms;    // wraps at 2^32 like every other platform; bencore is wrap-safe
}
bool Efr32Clock::sntp_valid() { return valid_; }
uint64_t Efr32Clock::sntp_unix_s() { return valid_ ? anchor_unix_ + (millis() - anchor_ms_) / 1000u : 0; }
void Efr32Clock::on_sntp(uint64_t unix_s) { anchor_unix_ = unix_s; anchor_ms_ = millis(); valid_ = unix_s > 1700000000ULL; }

// ----------------------------------------------------------------- gpio
void Efr32Gpio::pin_mode(uint8_t p, Mode m) {
    uint8_t port, pin; if (!pin_lookup(p, port, pin)) return;
    if (m == OUTPUT) GPIO_PinModeSet((GPIO_Port_TypeDef)port, pin, gpioModePushPull, 0);
    else if (m == INPUT_PULLUP) GPIO_PinModeSet((GPIO_Port_TypeDef)port, pin, gpioModeInputPull, 1);
    else GPIO_PinModeSet((GPIO_Port_TypeDef)port, pin, gpioModeInput, 0);
}
void Efr32Gpio::write(uint8_t p, bool level) {
    uint8_t port, pin; if (!pin_lookup(p, port, pin)) return;
    if (level) GPIO_PinOutSet((GPIO_Port_TypeDef)port, pin); else GPIO_PinOutClear((GPIO_Port_TypeDef)port, pin);
}
bool Efr32Gpio::read(uint8_t p) {
    uint8_t port, pin; if (!pin_lookup(p, port, pin)) return false;
    return GPIO_PinInGet((GPIO_Port_TypeDef)port, pin) != 0;
}

// ----------------------------------------------------------------- i2c (sl_i2cspm instance "sensor")
bool Efr32I2c::write(uint8_t addr, const uint8_t* data, size_t n) {
    I2C_TransferSeq_TypeDef seq; seq.addr = (uint16_t)(addr << 1); seq.flags = I2C_FLAG_WRITE;
    seq.buf[0].data = const_cast<uint8_t*>(data); seq.buf[0].len = (uint16_t)n;
    return I2CSPM_Transfer(sl_i2cspm_sensor, &seq) == i2cTransferDone;
}
bool Efr32I2c::read(uint8_t addr, uint8_t* data, size_t n) {
    I2C_TransferSeq_TypeDef seq; seq.addr = (uint16_t)(addr << 1); seq.flags = I2C_FLAG_READ;
    seq.buf[0].data = data; seq.buf[0].len = (uint16_t)n;
    return I2CSPM_Transfer(sl_i2cspm_sensor, &seq) == i2cTransferDone;
}

// ----------------------------------------------------------------- nvm3
uint32_t Efr32Nvs::object_id(const char* key) {
    uint32_t h = 0x811C9DC5u;                       // FNV-1a, folded to 16 bits, in the app key space
    for (const unsigned char* p = (const unsigned char*)key; *p; ++p) { h ^= *p; h *= 0x01000193u; }
    return 0x10000u | ((h ^ (h >> 16)) & 0xFFFFu);
}
Efr32Nvs::Efr32Nvs() { nvm3_initDefault(); }
bool Efr32Nvs::get_str(const char* k, char* out, size_t cap) {
    uint32_t type, len; if (nvm3_getObjectInfo(nvm3_defaultHandle, object_id(k), &type, &len) != ECODE_NVM3_OK || type != NVM3_OBJECTTYPE_DATA) return false;
    if (len >= cap) len = (uint32_t)cap - 1;
    if (nvm3_readData(nvm3_defaultHandle, object_id(k), out, len) != ECODE_NVM3_OK) return false;
    out[len] = 0; return true;
}
bool Efr32Nvs::set_str(const char* k, const char* v) { return nvm3_writeData(nvm3_defaultHandle, object_id(k), v, strlen(v)) == ECODE_NVM3_OK; }
bool Efr32Nvs::get_f32(const char* k, float& out) {
    uint32_t type, len; if (nvm3_getObjectInfo(nvm3_defaultHandle, object_id(k), &type, &len) != ECODE_NVM3_OK || len != sizeof out) return false;
    return nvm3_readData(nvm3_defaultHandle, object_id(k), &out, sizeof out) == ECODE_NVM3_OK;
}
bool Efr32Nvs::set_f32(const char* k, float v) { return nvm3_writeData(nvm3_defaultHandle, object_id(k), &v, sizeof v) == ECODE_NVM3_OK; }
bool Efr32Nvs::get_u32(const char* k, uint32_t& out) {
    uint32_t type, len; if (nvm3_getObjectInfo(nvm3_defaultHandle, object_id(k), &type, &len) != ECODE_NVM3_OK || len != sizeof out) return false;
    return nvm3_readData(nvm3_defaultHandle, object_id(k), &out, sizeof out) == ECODE_NVM3_OK;
}
bool Efr32Nvs::set_u32(const char* k, uint32_t v) { return nvm3_writeData(nvm3_defaultHandle, object_id(k), &v, sizeof v) == ECODE_NVM3_OK; }
bool Efr32Nvs::erase(const char* k) { Ecode_t e = nvm3_deleteObject(nvm3_defaultHandle, object_id(k)); return e == ECODE_NVM3_OK || e == ECODE_NVM3_ERR_KEY_NOT_FOUND; }
bool Efr32Nvs::commit() { if (nvm3_repackNeeded(nvm3_defaultHandle)) nvm3_repack(nvm3_defaultHandle); return true; }

// ----------------------------------------------------------------- net: MQTT / TLS / OpenThread TCP
// Minimal MQTT 3.1.1 client: CONNECT (with will, clean session), PUBLISH QoS0/1, SUBSCRIBE QoS1, PINGREQ.
// TLS: mbedTLS with PSA opaque key (device identity in Secure Vault), server cert pinned to the unit CA.
static mbedtls_ssl_context g_ssl; static mbedtls_ssl_config g_conf; static mbedtls_x509_crt g_ca, g_own;
static mbedtls_pk_context g_pk; static otTcpEndpoint g_tcp; static uint8_t g_rxbuf[1536]; static size_t g_rxlen = 0;
static uint8_t g_tcp_rx_ring[2048];

static int tls_send(void*, const unsigned char* buf, size_t len) {
    otLinkedBuffer lb; lb.mNext = nullptr; lb.mData = buf; lb.mLength = (uint16_t)len;
    return otTcpSendByReference(&g_tcp, &lb, 0) == OT_ERROR_NONE ? (int)len : MBEDTLS_ERR_SSL_WANT_WRITE;
}
static int tls_recv(void*, unsigned char* buf, size_t len) {
    const otLinkedBuffer* data; if (otTcpReceiveByReference(&g_tcp, &data) != OT_ERROR_NONE || !data) return MBEDTLS_ERR_SSL_WANT_READ;
    size_t n = data->mLength < len ? data->mLength : len; memcpy(buf, data->mData, n); otTcpCommitReceive(&g_tcp, n, 0); return (int)n;
}

Efr32Net::Efr32Net(otInstance* ot, const char* client_id, const char* broker_ip6, uint16_t port)
    : ot_(ot), client_id_(client_id), broker_(broker_ip6), port_(port) {
    otTcpEndpointInitializeArgs a{}; a.mReceiveBuffer = g_tcp_rx_ring; a.mReceiveBufferSize = sizeof g_tcp_rx_ring;
    otTcpEndpointInitialize(ot_, &g_tcp, &a);
    mbedtls_ssl_init(&g_ssl); mbedtls_ssl_config_init(&g_conf); mbedtls_x509_crt_init(&g_ca); mbedtls_x509_crt_init(&g_own); mbedtls_pk_init(&g_pk);
}
bool Efr32Net::connected() { return tcp_up_ && tls_up_ && mqtt_up_ && otThreadGetDeviceRole(ot_) >= OT_DEVICE_ROLE_CHILD; }
void Efr32Net::set_rx_handler(RxHandler h, void* ctx) { rx_ = h; rx_ctx_ = ctx; }
void Efr32Net::set_will_topic(const char* t) { snprintf(will_topic_, sizeof will_topic_, "%s", t); }

bool Efr32Net::tcp_open() {
    otSockAddr peer{}; otIp6AddressFromString(broker_, &peer.mAddress); peer.mPort = port_;
    return otTcpConnect(&g_tcp, &peer, OT_TCP_CONNECT_NO_FAST_OPEN) == OT_ERROR_NONE;
}
bool Efr32Net::tls_handshake() {
    static uint8_t ca_pem[1536], own_pem[1024]; static bool loaded = false;
    if (!loaded) {
        Efr32Nvs nvs; if (!nvs.get_str("ca_pem", (char*)ca_pem, sizeof ca_pem) || !nvs.get_str("cert_pem", (char*)own_pem, sizeof own_pem)) return false;
        mbedtls_x509_crt_parse(&g_ca, ca_pem, strlen((char*)ca_pem) + 1);
        mbedtls_x509_crt_parse(&g_own, own_pem, strlen((char*)own_pem) + 1);
        mbedtls_pk_setup_opaque(&g_pk, BEN_KEY_ID_DEVICE);             // key never leaves Secure Vault
        mbedtls_ssl_config_defaults(&g_conf, MBEDTLS_SSL_IS_CLIENT, MBEDTLS_SSL_TRANSPORT_STREAM, MBEDTLS_SSL_PRESET_DEFAULT);
        mbedtls_ssl_conf_authmode(&g_conf, MBEDTLS_SSL_VERIFY_REQUIRED);
        mbedtls_ssl_conf_ca_chain(&g_conf, &g_ca, nullptr);
        mbedtls_ssl_conf_own_cert(&g_conf, &g_own, &g_pk);
        static const int suites[] = { MBEDTLS_TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256, 0 };
        mbedtls_ssl_conf_ciphersuites(&g_conf, suites);
        mbedtls_ssl_setup(&g_ssl, &g_conf); mbedtls_ssl_set_hostname(&g_ssl, "broker.ben.local");
        mbedtls_ssl_set_bio(&g_ssl, nullptr, tls_send, tls_recv, nullptr);
        loaded = true;
    }
    int r = mbedtls_ssl_handshake(&g_ssl);
    return r == 0;   // WANT_READ/WRITE -> try again next poll
}
bool Efr32Net::mqtt_connect() {
    // Fixed header + variable header + payload, MQTT 3.1.1. Username = certificate CN (broker side
    // use_identity_as_username), so no password travels.
    static const char will_msg[] = "{\"fw\":\"" BEN_FW_VERSION "\",\"errors\":[\"offline (last will)\"]}";
    uint8_t pkt[320]; size_t n = 0;
    uint8_t flags = 0x02 | (will_topic_[0] ? 0x04 | 0x08 | 0x20 : 0);   // clean session, will QoS1 retain
    size_t id_len = strlen(client_id_), wt_len = strlen(will_topic_), wm_len = sizeof will_msg - 1;
    size_t rem = 10 + 2 + id_len + (will_topic_[0] ? 2 + wt_len + 2 + wm_len : 0);
    pkt[n++] = 0x10; pkt[n++] = (uint8_t)rem;                     // rem < 128 by construction
    const uint8_t vh[] = {0, 4, 'M', 'Q', 'T', 'T', 4, flags, 0, 30};
    memcpy(pkt + n, vh, sizeof vh); n += sizeof vh;
    pkt[n++] = (uint8_t)(id_len >> 8); pkt[n++] = (uint8_t)id_len; memcpy(pkt + n, client_id_, id_len); n += id_len;
    if (will_topic_[0]) {
        pkt[n++] = (uint8_t)(wt_len >> 8); pkt[n++] = (uint8_t)wt_len; memcpy(pkt + n, will_topic_, wt_len); n += wt_len;
        pkt[n++] = (uint8_t)(wm_len >> 8); pkt[n++] = (uint8_t)wm_len; memcpy(pkt + n, will_msg, wm_len); n += wm_len;
    }
    return mbedtls_ssl_write(&g_ssl, pkt, n) == (int)n;   // CONNACK handled in mqtt_rx()
}
bool Efr32Net::publish(const char* t, const char* p, size_t n, bool retain) {
    if (!connected()) return false;
    size_t tl = strlen(t); size_t rem = 2 + tl + n; if (rem > 1000) return false;
    uint8_t hdr[6]; size_t h = 0; hdr[h++] = (uint8_t)(0x30 | (retain ? 1 : 0));
    do { uint8_t b = rem % 128; rem /= 128; if (rem) b |= 0x80; hdr[h++] = b; } while (rem);
    uint8_t tlen[2] = {(uint8_t)(tl >> 8), (uint8_t)tl};
    return mbedtls_ssl_write(&g_ssl, hdr, h) > 0 && mbedtls_ssl_write(&g_ssl, tlen, 2) == 2 &&
           mbedtls_ssl_write(&g_ssl, (const uint8_t*)t, tl) == (int)tl && mbedtls_ssl_write(&g_ssl, (const uint8_t*)p, n) == (int)n;
}
bool Efr32Net::subscribe(const char* t) {
    snprintf(sub_, sizeof sub_, "%s", t);
    if (!connected()) return false;
    size_t tl = strlen(t); uint8_t pkt[128]; size_t n = 0;
    pkt[n++] = 0x82; pkt[n++] = (uint8_t)(2 + 2 + tl + 1);
    pkt[n++] = (uint8_t)(packet_id_ >> 8); pkt[n++] = (uint8_t)packet_id_; ++packet_id_;
    pkt[n++] = (uint8_t)(tl >> 8); pkt[n++] = (uint8_t)tl; memcpy(pkt + n, t, tl); n += tl; pkt[n++] = 1;   // QoS 1
    return mbedtls_ssl_write(&g_ssl, pkt, n) == (int)n;
}
void Efr32Net::mqtt_rx() {
    int r = mbedtls_ssl_read(&g_ssl, g_rxbuf + g_rxlen, sizeof g_rxbuf - g_rxlen);
    if (r <= 0) { if (r != MBEDTLS_ERR_SSL_WANT_READ && r != MBEDTLS_ERR_SSL_WANT_WRITE) { tls_up_ = mqtt_up_ = false; } return; }
    g_rxlen += (size_t)r;
    while (g_rxlen >= 2) {
        uint8_t type = g_rxbuf[0] >> 4; size_t rem = 0, mult = 1, i = 1;
        while (i < g_rxlen && (g_rxbuf[i] & 0x80)) { rem += (g_rxbuf[i] & 0x7F) * mult; mult *= 128; ++i; }
        if (i >= g_rxlen) return; rem += (g_rxbuf[i] & 0x7F) * mult; ++i;
        if (g_rxlen < i + rem) return;                                      // wait for the rest
        if (type == 2) { mqtt_up_ = g_rxbuf[i + 1] == 0; if (mqtt_up_ && sub_[0]) subscribe(sub_); }
        else if (type == 3) {
            size_t tl = (g_rxbuf[i] << 8) | g_rxbuf[i + 1]; char topic[96]; size_t tcopy = tl < sizeof topic - 1 ? tl : sizeof topic - 1;
            memcpy(topic, g_rxbuf + i + 2, tcopy); topic[tcopy] = 0;
            size_t off = i + 2 + tl; uint8_t qos = (g_rxbuf[0] >> 1) & 3;
            if (qos) { uint8_t ack[4] = {0x40, 2, g_rxbuf[off], g_rxbuf[off + 1]}; off += 2; mbedtls_ssl_write(&g_ssl, ack, 4); }
            size_t plen = i + rem - off; static char payload[1024]; if (plen >= sizeof payload) plen = sizeof payload - 1;
            memcpy(payload, g_rxbuf + off, plen); payload[plen] = 0;
            if (rx_) rx_(rx_ctx_, topic, payload, plen);
        }
        // 9 SUBACK, 13 PINGRESP, 4 PUBACK: nothing to do
        memmove(g_rxbuf, g_rxbuf + i + rem, g_rxlen - (i + rem)); g_rxlen -= i + rem;
    }
}
void Efr32Net::poll() {
    uint32_t now; { Efr32Clock c; now = c.millis(); }
    if (otThreadGetDeviceRole(ot_) < OT_DEVICE_ROLE_CHILD) { tcp_up_ = tls_up_ = mqtt_up_ = false; return; }
    if (!tcp_up_) { if (now - last_try_ms_ < 5000) return; last_try_ms_ = now; tcp_up_ = tcp_open(); return; }
    if (!tls_up_) { tls_up_ = tls_handshake(); if (tls_up_) mqtt_up_ = false, mqtt_connect(); return; }
    static uint32_t last_ping = 0;
    if (mqtt_up_ && now - last_ping > 15000) { uint8_t ping[2] = {0xC0, 0}; mbedtls_ssl_write(&g_ssl, ping, 2); last_ping = now; }
    mqtt_rx();
}
int Efr32Net::rssi() { otRouterInfo p; return otThreadGetParentInfo(ot_, &p) == OT_ERROR_NONE ? p.mLastRssi : 0; }
uint8_t Efr32Net::lqi() { otRouterInfo p; return otThreadGetParentInfo(ot_, &p) == OT_ERROR_NONE ? p.mLinkQualityIn : 0; }
const char* Efr32Net::parent_rloc16() {
    otDeviceRole role = otThreadGetDeviceRole(ot_);
    if (role == OT_DEVICE_ROLE_LEADER) return "leader";
    if (role == OT_DEVICE_ROLE_ROUTER) return "router";
    otRouterInfo p; if (otThreadGetParentInfo(ot_, &p) == OT_ERROR_NONE) snprintf(parent_buf_, sizeof parent_buf_, "0x%04x", p.mRloc16); else parent_buf_[0] = 0;
    return parent_buf_;
}
const char* Efr32Net::ip() {
    // Prefer the OMR (routable) address; fall back to mesh-local EID.
    const otNetifAddress* a = otIp6GetUnicastAddresses(ot_);
    const otIp6Address* pick = otThreadGetMeshLocalEid(ot_);
    for (; a; a = a->mNext) if (!a->mRloc && a->mAddressOrigin == OT_ADDRESS_ORIGIN_SLAAC) { pick = &a->mAddress; break; }
    otIp6AddressToString(pick, ip_buf_, sizeof ip_buf_); return ip_buf_;
}

// ----------------------------------------------------------------- system
uint32_t Efr32System::free_heap() { sl_memory_heap_info_t i; sl_memory_get_heap_info(&i); return (uint32_t)i.free_size; }
void Efr32System::reboot() { sl_sleeptimer_delay_millisecond(200); NVIC_SystemReset(); }
void Efr32System::identify(bool on) { ident_ = on; }
void Efr32System::log(const char* line) { printf("%s\n", line); }   // IOStream RTT/VCOM
bool Efr32System::boot_verified() {
    BootloaderInformation_t info; bootloader_getInfo(&info);
    return (info.capabilities & BOOTLOADER_CAPABILITY_ENFORCE_SECURE_BOOT) && bootloader_verifyApplication(BTL_APPLICATION_BASE) == BOOTLOADER_OK;
}
const char* Efr32System::cert_id() { if (!cert_id_[0]) { Efr32Nvs nvs; nvs.get_str("cert_id", cert_id_, sizeof cert_id_); } return cert_id_; }

size_t Efr32System::attest(const uint8_t* nonce, size_t nonce_len, uint8_t* sig_der, size_t cap, char* fw_hash_hex65) {
    // fw_hash = SHA-256 of the application image as the bootloader sees it (slot start .. image length).
    uint8_t digest[32]; mbedtls_sha256_context sha; mbedtls_sha256_init(&sha); mbedtls_sha256_starts(&sha, 0);
    ApplicationProperties_t* props = (ApplicationProperties_t*)bootloader_getApplicationProperties ? nullptr : nullptr; (void)props;
    extern const uint32_t __etext, __data_start__, __data_end__;        // linker symbols: text + initialised data
    size_t img_len = (size_t)((const uint8_t*)&__etext - (const uint8_t*)BTL_APPLICATION_BASE) + (size_t)((const uint8_t*)&__data_end__ - (const uint8_t*)&__data_start__);
    mbedtls_sha256_update(&sha, (const uint8_t*)BTL_APPLICATION_BASE, img_len); mbedtls_sha256_finish(&sha, digest); mbedtls_sha256_free(&sha);
    for (int i = 0; i < 32; ++i) snprintf(fw_hash_hex65 + 2 * i, 3, "%02x", digest[i]);
    // msg = nonce || fw_hash; signature = ECDSA(P-256, SHA-256) with the Secure Vault device key.
    uint8_t msg[96]; size_t ml = nonce_len < 64 ? nonce_len : 64; memcpy(msg, nonce, ml); memcpy(msg + ml, digest, 32);
    uint8_t raw[64]; size_t raw_len = 0;
    if (psa_sign_message(BEN_KEY_ID_DEVICE, PSA_ALG_ECDSA(PSA_ALG_SHA_256), msg, ml + 32, raw, sizeof raw, &raw_len) != PSA_SUCCESS) return 0;
    // raw r||s -> DER SEQUENCE { INTEGER r, INTEGER s }
    auto put_int = [](uint8_t* out, const uint8_t* v) { size_t n = 32; while (n > 1 && v[32 - n] == 0) --n; const uint8_t* s = v + 32 - n;
        bool pad = s[0] & 0x80; out[0] = 0x02; out[1] = (uint8_t)(n + pad); size_t o = 2; if (pad) out[o++] = 0; memcpy(out + o, s, n); return o + n; };
    uint8_t body[72]; size_t bl = put_int(body, raw); bl += put_int(body + bl, raw + 32);
    if (cap < bl + 2) return 0;
    sig_der[0] = 0x30; sig_der[1] = (uint8_t)bl; memcpy(sig_der + 2, body, bl); return bl + 2;
}

// OTA over Thread: fetch the signed GBL over CoAP block-wise (CoAP server on the edge, port 5683 over
// Thread, or HTTPS on Pod E Ethernet) into bootloader storage slot 0 while hashing; verify the SHA-256
// the edge sent; then let the Gecko Bootloader verify the ECDSA P-256 signature and the anti-rollback
// version before it swaps. An image with a correct hash but a wrong signature never runs.
bool Efr32System::ota_begin(const char* url, const char* sha256_hex) {
    extern bool ben_ota_fetch_to_slot(otInstance*, const char* url, uint32_t slot, uint8_t digest_out[32]);   // in main.cpp (CoAP client)
    if (bootloader_init() != BOOTLOADER_OK) return false;
    uint8_t digest[32];
    if (!ben_ota_fetch_to_slot(ot_, url, 0, digest)) return false;
    char hex[65]; for (int i = 0; i < 32; ++i) snprintf(hex + 2 * i, 3, "%02x", digest[i]);
    if (strncasecmp(hex, sha256_hex, 64) != 0) { bootloader_eraseStorageSlot(0); return false; }
    if (bootloader_verifyImage(0, nullptr) != BOOTLOADER_OK) { bootloader_eraseStorageSlot(0); return false; }   // signature + version
    if (bootloader_setImageToBootload(0) != BOOTLOADER_OK) return false;
    pending_restart_ = true;      // main loop reboots after the ack is on the wire; bootloader swaps
    return true;
}

} // namespace benhal
#endif // BEN_TARGET_EFR32
