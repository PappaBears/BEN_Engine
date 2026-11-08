// BEN Engine — BEN Node v1 — application entry.
//   ESP32 (Arduino): real sensors on the Olimex ESP32-POE-ISO, MQTT to the unit gateway.
//   native:          5-second simulation with the mock HAL (proves the core links on the host).
// All protocol behaviour is in lib/bencore; this file only moves bytes between sensors and core.
#include "bencore/node_app.h"
#include "bencore/telemetry.h"

#ifndef BEN_FW_VERSION
#define BEN_FW_VERSION "0.0.0-dev"
#endif

// Ring buffer: 3600 x 44 B = ~155 KB. Statically allocated so the footprint is known at link time.
static bencore::TelemetryRing g_ring;

// ======================================================================= ESP32
#ifdef ARDUINO
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SHT4x.h>
#include <Adafruit_ADS1X15.h>
#include <SensirionI2CSdp.h>
#include <esp_sntp.h>
#include "benhal/hal_esp32.h"

// --------------------------------------------------------------- pin map (see README + wiring SVG)
// Olimex ESP32-POE-ISO. Ethernet (RMII) owns GPIO 0,12,17,18,19,21,22,23,25,26,27; UART0 owns 1,3.
// Free for the application: 2,4,5,13,14,15,16,32,33 (I/O) and 34,35,36,39 (input only).
// Relay pins (32,33,14,15) are defined once in lib/bencore/outputs.cpp so the tests see them.
namespace pins {
constexpr uint8_t ONEWIRE   = 4;   // DS18B20 strings, one 4.7 k pull-up to 3V3 at the terminal block
constexpr uint8_t I2C_SDA   = 13;  // UEXT SDA  (SHT45, SDP810, ADS1115)
constexpr uint8_t I2C_SCL   = 16;  // UEXT SCL
constexpr uint8_t LEAK      = 36;  // input only: rope sensor via 100 k / 10 k divider, HIGH = wet
constexpr uint8_t DOOR      = 39;  // input only: reed to GND, external 10 k pull-up, HIGH = open
constexpr uint8_t PULSE     = 34;  // input only: meter S0 pulse via opto (shares on-board BUT1: pressing it counts 1 pulse)
constexpr uint8_t EPO_MON   = 35;  // input only: MONITOR ONLY of the hardwired EPO/fire loop aux contact (open BAT_SENS jumper)
constexpr uint8_t LED_IDENT = 2;   // blue IDENT/status LED (strapping pin: LED to GND keeps download mode available)
constexpr uint8_t SPARE     = 5;   // reserved: 1-bit DIP on the Olimex carrier; the 4-bit DIP lives on the v1.1 custom carrier
}

// --------------------------------------------------------------- settings (NVS overrides at provisioning)
static char g_unit[24] = "unit0";
static char g_node[16] = "node0";
static char g_broker[48] = "10.20.0.1";       // gateway on the controls VLAN
static char g_mqtt_user[24] = "node0";
static char g_mqtt_pass[48] = "changeme";

static benhal::Esp32Clock   hal_clock;
static benhal::Esp32Gpio    hal_gpio;
static benhal::Esp32I2c     hal_i2c;
static benhal::Esp32OneWire* hal_ow = nullptr;
static benhal::Esp32Nvs*    hal_nvs = nullptr;
static benhal::Esp32Net*    hal_net = nullptr;
static benhal::Esp32System  hal_sys;
static benhal::Hal          hal;
static bencore::NodeApp*    app = nullptr;

static Adafruit_SHT4x  sht;  static bool sht_ok = false;
static Adafruit_ADS1115 ads; static bool ads_ok = false;
static SensirionI2CSdp sdp;  static bool sdp_ok = false;
static uint8_t  ow_roms[8][8]; static int ow_count = 0;
static volatile uint32_t g_pulses = 0;
static void IRAM_ATTR on_pulse() { ++g_pulses; }

// DS18B20 ROM -> channel assignment is stored in NVS as "ow_T_in_1" = "28ff...". Until
// provisioned, sensors are assigned in discovery order: T_in_1..4 then T_out_1..4.
static int rom_channel(int i) { return i < 8 ? (int)bencore::CH_T_IN_1 + i : -1; }

static void serial_provisioning() {
    // One-line provisioning over USB serial, e.g.:  PROV unit=ben20-0007 node=node3 broker=10.20.0.1 user=node3 pass=xxxx
    static char line[160]; static size_t n = 0;
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            line[n] = 0; n = 0;
            if (strncmp(line, "PROV ", 5) == 0) {
                char* tok = strtok(line + 5, " ");
                while (tok) {
                    char* eq = strchr(tok, '=');
                    if (eq) { *eq = 0; const char* v = eq + 1;
                        if (!strcmp(tok, "unit")) hal_nvs->set_str("unit", v);
                        else if (!strcmp(tok, "node")) hal_nvs->set_str("node_id", v);
                        else if (!strcmp(tok, "broker")) hal_nvs->set_str("broker", v);
                        else if (!strcmp(tok, "user")) hal_nvs->set_str("mqtt_user", v);
                        else if (!strcmp(tok, "pass")) hal_nvs->set_str("mqtt_pass", v);
                        else if (!strcmp(tok, "tel_ms")) hal_nvs->set_u32("tel_ms", (uint32_t)atoi(v));
                    }
                    tok = strtok(nullptr, " ");
                }
                hal_nvs->commit(); Serial.println("PROV OK, rebooting"); hal_sys.reboot();
            } else if (strcmp(line, "ID?") == 0) {
                Serial.printf("unit=%s node=%s broker=%s fw=%s\n", g_unit, g_node, g_broker, BEN_FW_VERSION);
            } else if (strcmp(line, "FACTORY") == 0) {
                for (const char* k : {"unit", "node_id", "broker", "mqtt_user", "mqtt_pass", "cal_id"}) hal_nvs->erase(k);
                hal_nvs->commit(); Serial.println("NVS identity erased"); hal_sys.reboot();
            }
        } else if (n + 1 < sizeof line) line[n++] = c;
    }
}

void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.printf("\nBEN Node fw %s (Schreiber AI)\n", BEN_FW_VERSION);

    hal_nvs = new benhal::Esp32Nvs();
    hal_nvs->get_str("unit", g_unit, sizeof g_unit);
    hal_nvs->get_str("node_id", g_node, sizeof g_node);
    hal_nvs->get_str("broker", g_broker, sizeof g_broker);
    hal_nvs->get_str("mqtt_user", g_mqtt_user, sizeof g_mqtt_user);
    hal_nvs->get_str("mqtt_pass", g_mqtt_pass, sizeof g_mqtt_pass);

    // Node id normally comes from serial provisioning (NVS). On the Olimex carrier only one spare
    // GPIO is left, so the DIP override is a single bit here (SPARE low at boot -> "node1").
    // The v1.1 custom carrier exposes a 4-bit DIP on a PCF8574; NodeApp::provision_from_dip takes 0..15.
    pinMode(pins::SPARE, INPUT_PULLUP);
    uint8_t dip = digitalRead(pins::SPARE) == LOW ? 1 : 0;

    hal_net = new benhal::Esp32Net(g_node, g_broker, 1883, g_mqtt_user, g_mqtt_pass);
    hal_ow  = new benhal::Esp32OneWire(pins::ONEWIRE);
    hal.clock = &hal_clock; hal.gpio = &hal_gpio; hal.i2c = &hal_i2c; hal.onewire = hal_ow;
    hal.nvs = hal_nvs; hal.net = hal_net; hal.sys = &hal_sys;

    app = new bencore::NodeApp(hal, g_ring);
    app->begin();
    if (dip) app->provision_from_dip(dip);
    char will[96]; bencore::build_topic(will, sizeof will, app->identity().unit, app->identity().node_id, "status");
    hal_net->set_will_topic(will);

    // SNTP from the gateway (chrony). Also the MQTT broker host.
    sntp_setoperatingmode(SNTP_OPMODE_POLL); sntp_setservername(0, g_broker); sntp_init();

    pinMode(pins::LEAK, INPUT); pinMode(pins::DOOR, INPUT); pinMode(pins::PULSE, INPUT); pinMode(pins::EPO_MON, INPUT);   // 34-39 have no internal pull-ups
    pinMode(pins::LED_IDENT, OUTPUT);
    attachInterrupt(digitalPinToInterrupt(pins::PULSE), on_pulse, FALLING);

    Wire.begin(pins::I2C_SDA, pins::I2C_SCL, 100000);
    sht_ok = sht.begin(&Wire); if (sht_ok) sht.setPrecision(SHT4X_HIGH_PRECISION); else app->add_error("SHT45 missing");
    ads_ok = ads.begin(0x48, &Wire); if (ads_ok) ads.setGain(GAIN_ONE); else app->add_error("ADS1115 missing");   // ±4.096 V, 125 µV/LSB
    sdp.begin(Wire, SDP8XX_I2C_ADDRESS_0);
    sdp_ok = sdp.startContinuousMeasurementWithDiffPressureTCompAndAveraging() == 0; if (!sdp_ok) app->add_error("SDP810 missing");
    ow_count = hal_ow->scan(ow_roms, 8); if (ow_count == 0) app->add_error("no DS18B20 found");
    Serial.printf("sensors: sht=%d ads=%d sdp=%d ds18b20=%d  unit=%s node=%s\n", sht_ok, ads_ok, sdp_ok, ow_count, app->identity().unit, app->identity().node_id);
}

void loop() {
    static uint32_t next_sample = 0, next_ow_request = 0; static bool ow_pending = false;
    uint32_t now = millis();
    serial_provisioning();

    // DS18B20: request conversion, read 800 ms later (12-bit = 750 ms).
    if ((int32_t)(now - next_ow_request) >= 0) { hal_ow->request_temperatures(); ow_pending = true; next_ow_request = now + 1000; }
    if (ow_pending && (int32_t)(now - (next_ow_request - 200)) >= 0) {
        ow_pending = false;
        for (int i = 0; i < ow_count; ++i) {
            float t; int ch = rom_channel(i); if (ch < 0) continue;
            if (hal_ow->read_c(ow_roms[i], t)) app->channels().set_raw((bencore::ChannelId)ch, t, (int32_t)lroundf(t * 16.0f));
            else app->channels().mark_missing((bencore::ChannelId)ch);
        }
    }

    if ((int32_t)(now - next_sample) >= 0) {
        next_sample = now + 500;    // sample at 2 Hz, publish at the configured rate
        auto& c = app->channels();
        if (sht_ok) { sensors_event_t h, t; if (sht.getEvent(&h, &t)) {
            c.set_raw(bencore::CH_T_REF, t.temperature, (int32_t)lroundf(t.temperature * 100)); c.set_raw(bencore::CH_RH, h.relative_humidity, (int32_t)lroundf(h.relative_humidity * 100)); } }
        if (sdp_ok) { float dp, tc; if (sdp.readMeasurement(dp, tc) == 0) c.set_raw(bencore::CH_DP_AISLE, dp, (int32_t)lroundf(dp * 60.0f)); }  // SDP810-125: 60 LSB/Pa
        if (ads_ok) for (int i = 0; i < 4; ++i) {
            int16_t counts = ads.readADC_SingleEnded(i);
            double volts = counts * 0.000125;                  // GAIN_ONE
            c.set_raw((bencore::ChannelId)(bencore::CH_AI0_MA + i), volts / 165.0 * 1000.0, counts);   // 165 Ω shunt -> mA
        }
        c.set_digital(bencore::CH_LEAK, digitalRead(pins::LEAK) == HIGH);
        c.set_digital(bencore::CH_DOOR, digitalRead(pins::DOOR) == HIGH);     // reed open (door open) = HIGH via pull-up
        c.set_counter(bencore::CH_PULSE_KWH, g_pulses);
        // EPO/fire loop aux contact: monitor only (life-safety is hardwired, never commanded from here).
        if (digitalRead(pins::EPO_MON) == LOW) app->add_error("EPO/fire loop open"); 
    }

    app->tick();

    // IDENT LED: solid when identify, 1 Hz blink when gateway lost, short blip otherwise.
    bool led = app->identify_on() ? true : (app->gateway_lost() ? ((now / 500) & 1) : ((now % 2000) < 50));
    digitalWrite(pins::LED_IDENT, led);

    if (app->reboot_requested() || hal_sys.pending_restart()) { delay(300); hal_net->poll(); hal_sys.reboot(); }
    delay(5);
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
    printf("BEN Node %s native simulation: 5 s online, 3 s offline, 2 s online\n", BEN_FW_VERSION);
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
