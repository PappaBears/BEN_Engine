// BEN Engine — bencore — the node application, platform independent.
// main.cpp (ESP32) feeds raw sensor readings in and calls tick(); the mock HAL does the
// same under test. Everything in PROTOCOL.md that is "node behaviour" lives here.
#pragma once
#include <cstdint>
#include "../benhal/hal.h"
#include "channels.h"
#include "ringbuf.h"
#include "outputs.h"
#include "alarms.h"
#include "timesync.h"
#include "commands.h"

namespace bencore {

#ifndef BEN_FW_VERSION
#define BEN_FW_VERSION "0.0.0-dev"
#endif

struct NodeIdentity {
    char unit[24] = "unit0";
    char node_id[16] = "node0";
    bool provisioned = false;
};

struct NodeConfig {
    uint32_t telemetry_period_ms = 1000;   // 1 Hz default, 100..5000 (0.2–10 Hz)
    uint32_t status_period_ms = 10000;
    uint32_t replay_per_tick = 20;         // buffered records flushed per tick when back online
};

class NodeApp {
public:
    static constexpr size_t MSG_CAP = 768;

    NodeApp(benhal::Hal& hal, TelemetryRing& ring);

    // Load identity + calibration from NVS, configure outputs, subscribe. Call once.
    void begin();
    // Provisioning: set/store identity. DIP switch value (0..15) maps to node_id "node<N>".
    void provision(const char* unit, const char* node_id, bool persist);
    void provision_from_dip(uint8_t dip);
    const NodeIdentity& identity() const { return id_; }

    // Push fresh readings before tick().
    ChannelTable& channels() { return ch_; }
    Outputs& outputs() { return out_; }
    AlarmTable& alarms() { return alarms_; }
    TimeSync& time() { return time_; }
    NodeConfig& config() { return cfg_; }

    // Main loop entry: publishes telemetry/status on schedule, buffers when offline,
    // replays when back online, evaluates alarms and failsafe. Returns true if telemetry
    // was emitted (published or buffered) this call.
    bool tick();

    // Inbound message (wired to Net rx handler in begin()).
    void on_message(const char* topic, const char* payload, size_t len);

    uint32_t seq() const { return seq_; }
    uint32_t last_gateway_contact_ms() const { return last_contact_ms_; }
    bool gateway_lost() const { return out_.failsafe_active(); }
    bool reboot_requested() const { return reboot_req_; }
    void clear_reboot_request() { reboot_req_ = false; }
    bool identify_on() const { return identify_; }
    uint32_t replayed_total() const { return replayed_; }
    void add_error(const char* msg);

private:
    static void rx_trampoline(void* ctx, const char* topic, const char* payload, size_t len);
    void publish_telemetry_now(uint32_t now_ms);
    void publish_status(uint32_t now_ms);
    void replay_some();
    bool publish(const char* leaf, const char* payload, size_t len, bool retain);

    benhal::Hal& hal_;
    TelemetryRing& ring_;
    ChannelTable ch_;
    Outputs out_;
    AlarmTable alarms_;
    TimeSync time_;
    NodeIdentity id_;
    NodeConfig cfg_;
    uint32_t seq_ = 0;
    uint32_t next_tel_ms_ = 0, next_status_ms_ = 0, last_contact_ms_ = 0;
    bool was_connected_ = false;
    bool reboot_req_ = false, identify_ = false;
    uint32_t replayed_ = 0;
    const char* errors_[8]; int n_errors_ = 0;
    char msg_[MSG_CAP]; char topic_[96];
};

} // namespace bencore
