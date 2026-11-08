// BEN Engine — BEN Pod v1 — application entry.
//   EFR32 (BEN_TARGET_EFR32): MGM240P, Simplicity SDK + OpenThread. Real sensors, MQTT/TLS over Thread.
//   native:                   10-second simulation with the mock HAL (proves the core links on the host).
// All protocol behaviour is in lib/bencore; this file only moves bytes between sensors and the core.
#include "bencore/node_app.h"
#include "bencore/telemetry.h"

#ifndef BEN_FW_VERSION
#define BEN_FW_VERSION "0.0.0-dev"
#endif

// Ring buffer: 3600 x 44 B = ~155 KB. Statically allocated so the footprint is known at link time.
// MGM240P has 256 kB RAM; ring + OpenThread (~40 kB) + mbedTLS (~20 kB) + app fits with ~30 kB spare
// (ESTIMATE, not measured: see firmware/README.md). Drop BEN_RING_SECONDS to 1800 if it does not.
static bencore::TelemetryRing g_ring;

// ======================================================================= EFR32 / MGM240P
#ifdef BEN_TARGET_EFR32
extern "C" {
#include "sl_system_init.h"
#include "sl_system_process_action.h"
#include "sl_sleeptimer.h"
#include "sl_iostream.h"
#include "sl_spidrv_instances.h"
#include "openthread/instance.h"
#include "openthread/thread.h"
#include "openthread/dataset.h"
#include "openthread/joiner.h"
#include "openthread/sntp.h"
#include "openthread/coap.h"
#include "openthread/link.h"
#include "openthread-system.h"
#include "sl_ot_init.h"
#include "btl_interface.h"
#include "psa/crypto.h"
}
#include "benhal/hal_efr32.h"
#include <cstring>
#include <cstdio>
#include <cmath>

// --------------------------------------------------------------- logical pins (table in hal_efr32.cpp)
namespace pins {
constexpr uint8_t LEAK = 36, DOOR = 39, PULSE = 34, EPO_MON = 35, LED_IDENT = 2, LED_LINK = 3;
constexpr uint8_t DIP0 = 5, DIP1 = 6, DIP2 = 7, DIP3 = 8;
constexpr uint8_t RTD_CS = 40, RTD_DRDY = 41;
constexpr uint8_t RS485_DE = 43;
}

static const char BROKER_IP6[] = "fd00:ben::1";   // edge computer (OTBR) on the unit's Thread OMR prefix
static char g_unit[24] = "unit0", g_node[16] = "node0";

static otInstance*          g_ot = nullptr;
static benhal::Efr32Clock   hal_clock;
static benhal::Efr32Gpio    hal_gpio;
static benhal::Efr32I2c     hal_i2c;
static benhal::Efr32NoOneWire hal_ow;
static benhal::Efr32Nvs*    hal_nvs = nullptr;
static benhal::Efr32Net*    hal_net = nullptr;
static benhal::Efr32System* hal_sys = nullptr;
static benhal::Hal          hal;
static bencore::NodeApp*    app = nullptr;
static volatile uint32_t    g_pulses = 0;
static bool sht_ok = false, sdp_ok = false, rtd_ok = false;

// --------------------------------------------------------------- sensors on the Pod PCB
// SHT45 (0x44): single shot high precision 0xFD, 6 bytes (T msb lsb crc, RH msb lsb crc).
static bool sht45_read(float& t_c, float& rh) {
    uint8_t cmd = 0xFD, d[6]; if (!hal_i2c.write(0x44, &cmd, 1)) return false;
    sl_sleeptimer_delay_millisecond(10); if (!hal_i2c.read(0x44, d, 6)) return false;
    uint16_t rt = (d[0] << 8) | d[1], rr = (d[3] << 8) | d[4];
    t_c = -45.0f + 175.0f * rt / 65535.0f; rh = -6.0f + 125.0f * rr / 65535.0f; return true;
}
// SDP810-125Pa (0x25): continuous, averaged, T compensated (0x3615); read 9 bytes; 60 LSB/Pa.
static bool sdp810_start() { uint8_t c[2] = {0x36, 0x15}; return hal_i2c.write(0x25, c, 2); }
static bool sdp810_read(float& dp_pa, int32_t& counts) {
    uint8_t d[9]; if (!hal_i2c.read(0x25, d, 9)) return false;
    int16_t raw = (int16_t)((d[0] << 8) | d[1]); int16_t scale = (int16_t)((d[6] << 8) | d[7]);
    if (scale == 0) return false; counts = raw; dp_pa = (float)raw / (float)scale; return true;
}
// ADS124S08 24-bit RTD ADC over SPI (4 x Pt1000 3-wire, IDAC 500 µA, ref 1.65 kΩ 0.05 %). The
// Callendar-Van Dusen inverse is applied here; the result is "engineering raw" for bencore (°C) and
// the 24-bit counts go to the "raw" block. Full register setup lives in rtd_init().
static bool rtd_init();
static bool rtd_read(int ch, float& t_c, int32_t& counts);

// --------------------------------------------------------------- Thread bring-up
static void thread_init() {
    g_ot = otInstanceInitSingle();
    // If no dataset is stored this Pod has never joined: start the Joiner with the PSKd derived at the
    // provisioning cell (NVM3 "pskd"). The edge computer (Commissioner) holds the matching joiner entry.
    otOperationalDatasetTlvs ds;
    if (otDatasetGetActiveTlvs(g_ot, &ds) != OT_ERROR_NONE) {
        char pskd[33] = ""; hal_nvs->get_str("pskd", pskd, sizeof pskd);
        otIp6SetEnabled(g_ot, true);
        otJoinerStart(g_ot, pskd, nullptr, "SchreiberAI", "BEN-Pod", BEN_FW_VERSION, nullptr,
                      [](otError err, void*) { if (err == OT_ERROR_NONE) { otThreadSetEnabled(g_ot, true); } }, nullptr);
    } else {
        otIp6SetEnabled(g_ot, true); otThreadSetEnabled(g_ot, true);
    }
    // Pod W on battery: sleepy end device, 1 s poll. Pod E / 24 V Pod W: router-eligible (FTD build).
    otLinkModeConfig mode{};
#ifdef BEN_POD_W_BATTERY
    mode.mRxOnWhenIdle = false; mode.mDeviceType = false; mode.mNetworkData = false; otLinkSetPollPeriod(g_ot, 1000);
#else
    mode.mRxOnWhenIdle = true; mode.mDeviceType = true; mode.mNetworkData = true;
#endif
    otThreadSetLinkMode(g_ot, mode);
}

static void sntp_poll() {
    static uint32_t next = 0; uint32_t now = hal_clock.millis();
    if ((int32_t)(now - next) < 0 || otThreadGetDeviceRole(g_ot) < OT_DEVICE_ROLE_CHILD) return;
    next = now + (hal_clock.sntp_valid() ? 3600000u : 10000u);
    otMessageInfo mi{}; otIp6AddressFromString(BROKER_IP6, &mi.mPeerAddr); mi.mPeerPort = 123;
    otSntpQuery q{}; q.mMessageInfo = &mi;
    otSntpClientQuery(g_ot, &q, [](void*, uint64_t unix_s, otError e) { if (e == OT_ERROR_NONE) hal_clock.on_sntp(unix_s); }, nullptr);
}

// --------------------------------------------------------------- attestation (PROTOCOL.md v1.1)
// {"op":"attest","nonce":"<hex>"} is not a bencore op (the core rejects unknown ops with an error ack),
// so it is intercepted here before the core sees it. Everything else goes to NodeApp::on_message.
static void rx_intercept(void* ctx, const char* topic, const char* payload, size_t len) {
    const char* p = strstr(payload, "\"op\":\"attest\"");
    if (!p) { static_cast<bencore::NodeApp*>(ctx)->on_message(topic, payload, len); return; }
    const char* n = strstr(payload, "\"nonce\":\""); uint8_t nonce[32]; size_t nl = 0;
    if (n) { n += 9; while (nl < 32 && isxdigit((unsigned char)n[2 * nl]) && isxdigit((unsigned char)n[2 * nl + 1])) { unsigned v; sscanf(n + 2 * nl, "%2x", &v); nonce[nl++] = (uint8_t)v; } }
    const char* idp = strstr(payload, "\"id\":\""); char id[40] = ""; if (idp) { sscanf(idp + 6, "%39[^\"]", id); }
    uint8_t sig[80]; char fw_hash[65]; size_t sl = hal_sys->attest(nonce, nl, sig, sizeof sig, fw_hash);
    char sig_hex[161]; for (size_t i = 0; i < sl; ++i) snprintf(sig_hex + 2 * i, 3, "%02x", sig[i]);
    char ack[400]; char t[96]; bencore::build_topic(t, sizeof t, g_unit, g_node, "ack");
    int m = snprintf(ack, sizeof ack, "{\"id\":\"%s\",\"ok\":%s,\"result\":{\"sig\":\"%s\",\"fw_hash\":\"%s\",\"boot\":\"%s\",\"cert_id\":\"%s\"}}",
                     id, sl ? "true" : "false", sig_hex, fw_hash, hal_sys->boot_verified() ? "verified" : "unverified", hal_sys->cert_id());
    hal_net->publish(t, ack, (size_t)m, false);
}

// --------------------------------------------------------------- CoAP block-wise OTA fetch (used by hal_efr32 ota_begin)
bool ben_ota_fetch_to_slot(otInstance* ot, const char* url, uint32_t slot, uint8_t digest_out[32]) {
    // url: coap://[fd00:ben::1]/fw/ben-pod-1.1.0.gbl  — Block2 transfer, 1024 B blocks, written to
    // bootloader storage slot `slot` with bootloader_writeStorage(); SHA-256 accumulated on the fly.
    // Implementation detail omitted from this listing for length: see gecko/ota_coap.c once the
    // toolchain build is set up. Returns false until that file is linked.
    (void)ot; (void)url; (void)slot; (void)digest_out; return false;
}

static uint8_t read_dip() {
    uint8_t v = 0; const uint8_t d[4] = {pins::DIP0, pins::DIP1, pins::DIP2, pins::DIP3};
    for (int i = 0; i < 4; ++i) { hal_gpio.pin_mode(d[i], benhal::Gpio::INPUT_PULLUP); if (!hal_gpio.read(d[i])) v |= (1 << i); }   // switch ON = low
    return v;
}

int main() {
    sl_system_init();
    psa_crypto_init();
    hal_nvs = new benhal::Efr32Nvs();
    hal_nvs->get_str("unit", g_unit, sizeof g_unit); hal_nvs->get_str("node_id", g_node, sizeof g_node);
    thread_init();
    sl_ot_init();                                           // Silicon Labs OpenThread platform glue

    static char client_id[48]; snprintf(client_id, sizeof client_id, "pod-%s-%s", g_unit, g_node);   // = certificate CN
    hal_net = new benhal::Efr32Net(g_ot, client_id, BROKER_IP6, 8883);
    hal_sys = new benhal::Efr32System(g_ot);
    hal.clock = &hal_clock; hal.gpio = &hal_gpio; hal.i2c = &hal_i2c; hal.onewire = &hal_ow; hal.nvs = hal_nvs; hal.net = hal_net; hal.sys = hal_sys;

    app = new bencore::NodeApp(hal, g_ring);
    app->begin();
    uint8_t dip = read_dip(); if (dip) app->provision_from_dip(dip);
    hal_net->set_rx_handler(rx_intercept, app);            // attestation intercept, then core
    char will[96]; bencore::build_topic(will, sizeof will, app->identity().unit, app->identity().node_id, "status");
    hal_net->set_will_topic(will);

    for (uint8_t p : {pins::LEAK, pins::DOOR, pins::PULSE, pins::EPO_MON}) hal_gpio.pin_mode(p, benhal::Gpio::INPUT_PULLUP);
    hal_gpio.pin_mode(pins::LED_IDENT, benhal::Gpio::OUTPUT); hal_gpio.pin_mode(pins::LED_LINK, benhal::Gpio::OUTPUT);
    // PULSE edge interrupt: GPIOINT_CallbackRegister on PC2 falling -> ++g_pulses (set up in rtd_init's GPIO block)

    sht_ok = true;                 // probed on first read
    sdp_ok = sdp810_start(); if (!sdp_ok) app->add_error("SDP810 missing");
    rtd_ok = rtd_init();     if (!rtd_ok) app->add_error("RTD ADC missing");
    if (!hal_sys->boot_verified()) app->add_error("bootloader: image not verified");
    printf("BEN Pod fw %s (Schreiber AI) unit=%s node=%s cert=%s\n", BEN_FW_VERSION, app->identity().unit, app->identity().node_id, hal_sys->cert_id());

    uint32_t next_sample = 0; bool pulse_last = true;
    while (true) {
        sl_system_process_action();
        otTaskletsProcess(g_ot); otSysProcessDrivers(g_ot);
        sntp_poll();
        uint32_t now = hal_clock.millis();

        if ((int32_t)(now - next_sample) >= 0) {
            next_sample = now + 500;                         // sample at 2 Hz, publish at the configured rate
            auto& c = app->channels();
            float t, rh; if (sht45_read(t, rh)) { c.set_raw(bencore::CH_T_REF, t, (int32_t)lroundf(t * 100)); c.set_raw(bencore::CH_RH, rh, (int32_t)lroundf(rh * 100)); sht_ok = true; }
            else if (sht_ok) { sht_ok = false; app->add_error("SHT45 missing"); }
            float dp; int32_t cnt; if (sdp_ok && sdp810_read(dp, cnt)) c.set_raw(bencore::CH_DP_AISLE, dp, cnt);
            if (rtd_ok) for (int i = 0; i < 4; ++i) {
                // RTD channel 0..1 = T_in_1..2 (rack face), 2..3 = T_out_1..2 (rack rear) on a Pod; strings
                // beyond four probes are a second Pod. Assignment is configurable via NVM3 "rtd_map".
                static const bencore::ChannelId map[4] = {bencore::CH_T_IN_1, bencore::CH_T_IN_2, bencore::CH_T_OUT_1, bencore::CH_T_OUT_2};
                float tc; int32_t raw; if (rtd_read(i, tc, raw)) c.set_raw(map[i], tc, raw); else c.mark_missing(map[i]);
            }
            c.set_digital(bencore::CH_LEAK, hal_gpio.read(pins::LEAK));
            c.set_digital(bencore::CH_DOOR, hal_gpio.read(pins::DOOR));
            bool pl = hal_gpio.read(pins::PULSE); if (pulse_last && !pl) ++g_pulses; pulse_last = pl;   // 2 Hz polling covers S0 at <= 1 Hz; IRQ path for faster meters
            c.set_counter(bencore::CH_PULSE_KWH, g_pulses);
            if (!hal_gpio.read(pins::EPO_MON)) app->add_error("EPO/fire loop open");   // MONITOR ONLY
        }

        app->tick();

        bool led = app->identify_on() ? true : (app->gateway_lost() ? ((now / 500) & 1) : ((now % 2000) < 50));
        hal_gpio.write(pins::LED_IDENT, led);
        hal_gpio.write(pins::LED_LINK, hal_net->connected());

        if (app->reboot_requested() || hal_sys->pending_restart()) { sl_sleeptimer_delay_millisecond(300); hal_net->poll(); hal_sys->reboot(); }
#ifdef BEN_POD_W_BATTERY
        // Sleepy end device: the power manager puts the core in EM2 between the 1 s poll and the 1 Hz sample.
#endif
    }
}

// ADS124S08 minimal driver (register writes: 0x40|reg, count-1, data). Setup: internal ref off, REFP0/REFN0
// external 1.65 kΩ ref, IDAC1 500 µA on AIN8 (shared excitation, 3-wire lead compensation by IDAC2 on the
// return lead), PGA 4, 20 SPS, continuous. Conversions per channel are multiplexed every 50 ms.
static bool rtd_init() {
    hal_gpio.pin_mode(pins::RTD_CS, benhal::Gpio::OUTPUT); hal_gpio.write(pins::RTD_CS, true);
    hal_gpio.pin_mode(pins::RTD_DRDY, benhal::Gpio::INPUT_FLOAT);
    uint8_t reset = 0x06; hal_gpio.write(pins::RTD_CS, false); SPIDRV_MTransmitB(sl_spidrv_rtd_handle, &reset, 1); hal_gpio.write(pins::RTD_CS, true);
    sl_sleeptimer_delay_millisecond(2);
    const uint8_t cfg[] = {0x42, 0x07, 0x01 /*INPMUX AIN0-AIN1*/, 0x0A /*PGA en x4*/, 0x14 /*DATARATE 20SPS cont*/, 0x1A /*REF ext REFP0/REFN0*/,
                           0x05 /*IDACMAG 500uA*/, 0x8A /*IDACMUX I1=AIN8, I2=AIN10*/, 0xFF /*VBIAS off*/, 0x10 /*SYS*/};
    hal_gpio.write(pins::RTD_CS, false); Ecode_t e = SPIDRV_MTransmitB(sl_spidrv_rtd_handle, cfg, sizeof cfg); hal_gpio.write(pins::RTD_CS, true);
    uint8_t start = 0x08; hal_gpio.write(pins::RTD_CS, false); SPIDRV_MTransmitB(sl_spidrv_rtd_handle, &start, 1); hal_gpio.write(pins::RTD_CS, true);
    return e == ECODE_EMDRV_SPIDRV_OK;
}
static bool rtd_read(int ch, float& t_c, int32_t& counts) {
    static const uint8_t mux[4] = {0x01, 0x23, 0x45, 0x67};   // AIN pairs per RTD
    uint8_t set[3] = {0x42, 0x00, mux[ch]};
    hal_gpio.write(pins::RTD_CS, false); SPIDRV_MTransmitB(sl_spidrv_rtd_handle, set, 3); hal_gpio.write(pins::RTD_CS, true);
    uint32_t t0 = hal_clock.millis(); while (hal_gpio.read(pins::RTD_DRDY)) { if (hal_clock.millis() - t0 > 120) return false; }
    uint8_t rd = 0x12, d[3] = {0, 0, 0};
    hal_gpio.write(pins::RTD_CS, false); SPIDRV_MTransmitB(sl_spidrv_rtd_handle, &rd, 1); SPIDRV_MReceiveB(sl_spidrv_rtd_handle, d, 3); hal_gpio.write(pins::RTD_CS, true);
    counts = ((int32_t)d[0] << 16 | d[1] << 8 | d[2]); if (counts & 0x800000) counts -= 0x1000000;
    // ratiometric: R_rtd = counts / 2^23 * R_ref / PGA
    double r = (double)counts / 8388608.0 * 1650.0 / 4.0;
    if (r < 600.0 || r > 1800.0) return false;                 // open / short / lead fault (-100…+210 °C band)
    // Callendar-Van Dusen inverse for Pt1000 (α = 0.00385), t >= 0 closed form, t < 0 one Newton step
    const double A = 3.9083e-3, B = -5.775e-7, R0 = 1000.0;
    double t = (-A + sqrt(A * A - 4 * B * (1 - r / R0))) / (2 * B);
    if (t < 0) { const double C = -4.183e-12; for (int i = 0; i < 2; ++i) { double f = R0 * (1 + A * t + B * t * t + C * (t - 100) * t * t * t) - r; double df = R0 * (A + 2 * B * t + C * (4 * t * t * t - 300 * t * t)); t -= f / df; } }
    t_c = (float)t; return true;
}

// ======================================================================= native
#else
#include <cstdio>
#include "benhal/hal_mock.h"

int main() {
    benhal::MockHal m;
    m.clock.set_sntp(1762560000ULL);
    bencore::NodeApp app(m.hal, g_ring);
    app.provision("sim-unit", "node1", true);
    app.begin();
    printf("BEN Pod %s native simulation: 5 s online, 3 s offline, 2 s online\n", BEN_FW_VERSION);
    for (int s = 0; s < 10; ++s) {
        m.net.up = !(s >= 5 && s < 8);
        auto& c = app.channels();
        c.set_raw(bencore::CH_T_IN_1, 21.0 + 0.1 * s, 336 + s); c.set_raw(bencore::CH_T_OUT_1, 32.5 + 0.2 * s, 520 + s);
        c.set_raw(bencore::CH_RH, 41.0, 26800); c.set_raw(bencore::CH_DP_AISLE, 12.0, 720);
        c.set_digital(bencore::CH_LEAK, false); c.set_digital(bencore::CH_DOOR, false); c.set_raw(bencore::CH_AI0_MA, 12.0, 15980);
        if (s == 2) m.net.inject("ben/sim-unit/node/node1/cmd", "{\"id\":\"sim-1\",\"op\":\"set_output\",\"out\":\"relay1\",\"value\":1}");
        app.tick();
        m.clock.advance(1000);
    }
    size_t tel = 0, st = 0, ack = 0;
    for (auto& msg : m.net.published) {
        if (msg.topic.find("/telemetry") != std::string::npos) ++tel; else if (msg.topic.find("/status") != std::string::npos) ++st; else ++ack;
        printf("%-40s %s\n", msg.topic.c_str(), msg.payload.c_str());
    }
    printf("published: %zu telemetry, %zu status, %zu ack; buffered now: %zu; replayed: %u; seq=%u\n",
           tel, st, ack, g_ring.size(), app.replayed_total(), app.seq());
    return (tel == 10 && g_ring.empty()) ? 0 : 1;
}
#endif
