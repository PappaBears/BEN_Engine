#include "node_app.h"
#include "telemetry.h"
#include <cstring>
#include <cstdio>

namespace bencore {

NodeApp::NodeApp(benhal::Hal& hal, TelemetryRing& ring)
    : hal_(hal), ring_(ring), out_(hal.gpio), time_(hal.clock) {}

void NodeApp::begin() {
    out_.begin();
    if (hal_.nvs) {
        char u[24], n[16];
        if (hal_.nvs->get_str("unit", u, sizeof u) && hal_.nvs->get_str("node_id", n, sizeof n)) {
            snprintf(id_.unit, sizeof id_.unit, "%s", u); snprintf(id_.node_id, sizeof id_.node_id, "%s", n);
            id_.provisioned = true;
        }
        ch_.load(*hal_.nvs);
        uint32_t per;
        if (hal_.nvs->get_u32("tel_ms", per) && per >= 100 && per <= 5000) cfg_.telemetry_period_ms = per;
    }
    if (hal_.net) {
        hal_.net->set_rx_handler(&NodeApp::rx_trampoline, this);
        build_topic(topic_, sizeof topic_, id_.unit, id_.node_id, "cmd");
        hal_.net->subscribe(topic_);
    }
    uint32_t now = hal_.clock ? hal_.clock->millis() : 0;
    last_contact_ms_ = now;          // give the gateway 60 s from boot before failsafe
    next_tel_ms_ = now; next_status_ms_ = now;
    was_connected_ = hal_.net && hal_.net->connected();
}

void NodeApp::provision(const char* unit, const char* node_id, bool persist) {
    snprintf(id_.unit, sizeof id_.unit, "%s", unit);
    snprintf(id_.node_id, sizeof id_.node_id, "%s", node_id);
    id_.provisioned = true;
    if (persist && hal_.nvs) { hal_.nvs->set_str("unit", unit); hal_.nvs->set_str("node_id", node_id); hal_.nvs->commit(); }
    if (hal_.net) { build_topic(topic_, sizeof topic_, id_.unit, id_.node_id, "cmd"); hal_.net->subscribe(topic_); }
}

void NodeApp::provision_from_dip(uint8_t dip) {
    char n[16]; snprintf(n, sizeof n, "node%u", (unsigned)(dip & 0x0F));
    // DIP only sets the node number; the unit id stays whatever serial provisioning stored.
    char unit[sizeof id_.unit]; snprintf(unit, sizeof unit, "%s", id_.unit);   // copy: provision() writes id_.unit
    provision(unit, n, false);
}

void NodeApp::add_error(const char* msg) {
    for (int i = 0; i < n_errors_; ++i) if (errors_[i] == msg) return;
    if (n_errors_ < 8) errors_[n_errors_++] = msg;
}

void NodeApp::rx_trampoline(void* ctx, const char* topic, const char* payload, size_t len) {
    static_cast<NodeApp*>(ctx)->on_message(topic, payload, len);
}

bool NodeApp::publish(const char* leaf, const char* payload, size_t len, bool retain) {
    if (!hal_.net || !hal_.net->connected()) return false;
    char t[96]; build_topic(t, sizeof t, id_.unit, id_.node_id, leaf);
    return hal_.net->publish(t, payload, len, retain);
}

void NodeApp::on_message(const char* topic, const char* payload, size_t len) {
    char expect[96]; build_topic(expect, sizeof expect, id_.unit, id_.node_id, "cmd");
    if (strcmp(topic, expect) != 0) return;           // not for us
    uint32_t now = hal_.clock ? hal_.clock->millis() : 0;
    last_contact_ms_ = now;                            // any command proves the gateway is alive
    CommandContext ctx{&ch_, &out_, hal_.nvs, hal_.sys, &reboot_req_, &identify_};
    size_t n = handle_command(payload, len, ctx, msg_, sizeof msg_);
    if (n == 0) { snprintf(msg_, sizeof msg_, "{\"id\":\"\",\"ok\":false,\"error\":\"ack overflow\"}"); n = strlen(msg_); }
    publish("ack", msg_, n, false);
}

bool NodeApp::tick() {
    uint32_t now = hal_.clock ? hal_.clock->millis() : 0;
    time_.poll();
    if (hal_.net) hal_.net->poll();
    bool connected = hal_.net && hal_.net->connected();

    // Link transitions. A connected broker session is treated as gateway contact: the
    // broker runs ON the gateway, so a live TCP/MQTT session means the gateway is up.
    if (connected) last_contact_ms_ = now;
    if (connected && !was_connected_) {
        char t[96]; build_topic(t, sizeof t, id_.unit, id_.node_id, "cmd"); hal_.net->subscribe(t);
        next_status_ms_ = now;   // announce ourselves immediately
    }
    was_connected_ = connected;

    out_.tick(now, last_contact_ms_, connected);

    Severity worst;
    alarms_.evaluate(ch_, now, &worst);

    bool emitted = false;
    if ((int32_t)(now - next_tel_ms_) >= 0) {
        publish_telemetry_now(now);
        next_tel_ms_ += cfg_.telemetry_period_ms;
        if ((int32_t)(now - next_tel_ms_) > 0) next_tel_ms_ = now + cfg_.telemetry_period_ms; // we fell behind
        emitted = true;
    }
    if (connected && !ring_.empty()) replay_some();
    if ((int32_t)(now - next_status_ms_) >= 0 || alarms_.changed_since_last()) {
        publish_status(now);
        next_status_ms_ = now + cfg_.status_period_ms;
    }
    return emitted;
}

void NodeApp::publish_telemetry_now(uint32_t now_ms) {
    (void)now_ms;
    ++seq_;
    uint64_t ts = time_.unix_s();
    bool connected = hal_.net && hal_.net->connected();
    bool sent = false;
    if (connected && ring_.empty()) {   // keep order: never publish live ahead of a backlog
        size_t n = build_telemetry(ch_, ts, seq_, msg_, sizeof msg_);
        if (n == 0) add_error("telemetry overflow");
        else sent = publish("telemetry", msg_, n, false);
    }
    if (!sent) ring_.push(pack_record(ch_, (uint32_t)ts, seq_, time_.valid()));
}

void NodeApp::replay_some() {
    ChannelTable tmp;
    tmp.set_cal_id(ch_.cal_id());
    for (uint32_t i = 0; i < cfg_.replay_per_tick && !ring_.empty(); ++i) {
        const TelemetryRecord& r = ring_.peek(0);
        unpack_record(r, tmp);
        size_t n = build_telemetry(tmp, r.ts, r.seq, msg_, sizeof msg_, true);
        if (n == 0 || !publish("telemetry", msg_, n, false)) break;   // stop; retry next tick
        TelemetryRecord discard; ring_.pop(discard);
        ++replayed_;
    }
}

void NodeApp::publish_status(uint32_t now_ms) {
    StatusInfo s{};
    s.fw = BEN_FW_VERSION;
    s.uptime_s = now_ms / 1000u;
    s.rssi = hal_.net ? hal_.net->rssi() : 0;
    s.ip = hal_.net ? hal_.net->ip() : "0.0.0.0";
    s.heap = hal_.sys ? hal_.sys->free_heap() : 0;
    for (int i = 0; i < n_errors_; ++i) s.errors[i] = errors_[i];
    s.n_errors = n_errors_;
    if (time_.stale() && s.n_errors < 8) s.errors[s.n_errors++] = "clock not synced";
    if (out_.failsafe_active() && s.n_errors < 8) s.errors[s.n_errors++] = "gateway lost: failsafe active";
    s.buffered = (uint32_t)ring_.size();
    s.clock_valid = time_.valid();
    size_t n = build_status(s, msg_, sizeof msg_);
    if (n) publish("status", msg_, n, true);
}

} // namespace bencore
