#include "timesync.h"

namespace bencore {

void TimeSync::poll() {
    if (!clk_->sntp_valid()) return;
    uint64_t now_sntp = clk_->sntp_unix_s();
    if (now_sntp == last_seen_sntp_) return;      // nothing new from SNTP this second
    last_seen_sntp_ = now_sntp;
    uint32_t ms = clk_->millis();
    if (valid_) {
        uint64_t predicted = anchor_unix_ + (uint64_t)((ms - anchor_ms_) / 1000u);
        int64_t diff = (int64_t)now_sntp - (int64_t)predicted;
        if (diff > 2 || diff < -2) ++steps_;
    }
    valid_ = true; anchor_unix_ = now_sntp; anchor_ms_ = ms;
}

uint64_t TimeSync::unix_s() const {
    if (!valid_) return 0;
    return anchor_unix_ + (uint64_t)((clk_->millis() - anchor_ms_) / 1000u);
}

} // namespace bencore
