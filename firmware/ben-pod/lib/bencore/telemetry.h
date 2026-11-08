// BEN Engine — bencore — telemetry / status JSON builders (spec/PROTOCOL.md).
#pragma once
#include <cstddef>
#include <cstdint>
#include "channels.h"

namespace bencore {

// {"ts":…,"seq":…,"ch":{…},"raw":{…},"cal_id":"…"}  — channels that are not present are omitted.
// replay=true marks a record flushed from the ring buffer: the compact record keeps only the
// calibrated values, so "raw" is emitted empty and "replay":true is appended so the gateway
// never mistakes scaled integers for ADC counts.
// Returns bytes written (0 on overflow).
size_t build_telemetry(const ChannelTable& t, uint64_t ts, uint32_t seq, char* buf, size_t cap, bool replay = false);

struct StatusInfo {
    const char* fw;
    uint32_t uptime_s;
    int rssi;
    const char* ip;
    uint32_t heap;
    const char* errors[8];
    int n_errors;
    // extras the gateway can use but PROTOCOL.md does not require
    uint32_t buffered;       // records waiting in the ring buffer
    bool clock_valid;
};
// {"fw":"1.0.0","uptime_s":…,"rssi":…,"ip":"…","heap":…,"errors":[]} (+ "buffered","clock_valid")
size_t build_status(const StatusInfo& s, char* buf, size_t cap);

// Topic helpers: ben/<unit>/node/<node_id>/<leaf>
size_t build_topic(char* buf, size_t cap, const char* unit, const char* node_id, const char* leaf);

} // namespace bencore
