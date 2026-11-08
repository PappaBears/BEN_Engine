#include "telemetry.h"
#include "json_mini.h"
#include <cstdio>

namespace bencore {

size_t build_telemetry(const ChannelTable& t, uint64_t ts, uint32_t seq, char* buf, size_t cap, bool replay) {
    JsonWriter w(buf, cap);
    w.begin_object();
    w.kv("ts", (unsigned long long)ts);
    w.kv("seq", seq);
    w.key_object("ch");
    for (int i = 0; i < CH_COUNT; ++i) {
        ChannelId id = (ChannelId)i;
        if (!t.present(id)) continue;
        const ChannelInfo& ci = CHANNELS[i];
        if (ci.kind == KIND_ANALOG) w.kv_num(ci.name, t.value(id), ci.decimals);
        else w.kv(ci.name, (long long)t.value(id));
    }
    w.end_object();
    w.key_object("raw");
    if (!replay)
        for (int i = 0; i < CH_COUNT; ++i) {
            ChannelId id = (ChannelId)i;
            if (!t.present(id) || CHANNELS[i].kind != KIND_ANALOG) continue;
            w.kv(CHANNELS[i].name, (long long)t.counts(id));
        }
    w.end_object();
    w.kv("cal_id", t.cal_id());
    if (replay) w.kv("replay", true);
    w.end_object();
    return w.overflowed() ? 0 : w.length();
}

size_t build_status(const StatusInfo& s, char* buf, size_t cap) {
    JsonWriter w(buf, cap);
    w.begin_object();
    w.kv("fw", s.fw);
    w.kv("uptime_s", s.uptime_s);
    w.kv("rssi", s.rssi);
    w.kv("ip", s.ip);
    w.kv("heap", s.heap);
    w.key_array("errors");
    for (int i = 0; i < s.n_errors && i < 8; ++i) w.value_string(s.errors[i]);
    w.end_array();
    w.kv("buffered", s.buffered);
    w.kv("clock_valid", s.clock_valid);
    w.end_object();
    return w.overflowed() ? 0 : w.length();
}

size_t build_topic(char* buf, size_t cap, const char* unit, const char* node_id, const char* leaf) {
    int n = snprintf(buf, cap, "ben/%s/node/%s/%s", unit, node_id, leaf);
    return (n < 0 || (size_t)n >= cap) ? 0 : (size_t)n;
}

} // namespace bencore
