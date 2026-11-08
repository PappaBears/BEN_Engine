// BEN Engine — bencore — SNTP-backed wall clock with monotonic fallback.
// The gateway runs chrony and serves SNTP on the controls LAN. Until the first sync the
// node reports ts=0 and marks records clock_valid=false; the gateway then re-times the
// buffered records using the (uptime, ts) pair carried in the first valid status message.
#pragma once
#include <cstdint>
#include "../benhal/hal.h"

namespace bencore {

class TimeSync {
public:
    explicit TimeSync(benhal::Clock* clk) : clk_(clk) {}
    // Call each loop. Picks up a fresh SNTP fix and re-anchors; detects large steps.
    void poll();
    bool valid() const { return valid_; }
    uint64_t unix_s() const;                 // 0 when not valid
    uint32_t uptime_s() const { return clk_->millis() / 1000u; }
    uint32_t steps() const { return steps_; } // number of >2 s clock steps seen (diagnostic)
    uint32_t last_sync_age_s() const { return valid_ ? (uint32_t)((clk_->millis() - anchor_ms_) / 1000u) : 0xFFFFFFFFu; }
    static constexpr uint32_t STALE_AFTER_S = 24u * 3600u;  // flag stale if no sync for a day
    bool stale() const { return !valid_ || last_sync_age_s() > STALE_AFTER_S; }

private:
    benhal::Clock* clk_;
    bool valid_ = false; uint64_t anchor_unix_ = 0; uint32_t anchor_ms_ = 0; uint32_t steps_ = 0;
    uint64_t last_seen_sntp_ = 0;
};

} // namespace bencore
