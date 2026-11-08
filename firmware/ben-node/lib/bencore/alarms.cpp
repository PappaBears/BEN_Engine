#include "alarms.h"

namespace bencore {

const char* severity_name(Severity s) {
    switch (s) { case SEV_WARN: return "warn"; case SEV_ALARM: return "alarm"; case SEV_CRITICAL: return "critical"; default: return "none"; }
}

AlarmTable::AlarmTable() {
    // ASHRAE A1 recommended 18–27 °C inlet, allowable 15–32 °C; RH 20–80 %.
    for (int i = 0; i < 4; ++i)
        add({(ChannelId)(CH_T_IN_1 + i), true, 27.0, true, 18.0, SEV_WARN, 30, "inlet outside ASHRAE A1 recommended"});
    for (int i = 0; i < 4; ++i)
        add({(ChannelId)(CH_T_IN_1 + i), true, 32.0, true, 15.0, SEV_ALARM, 10, "inlet outside ASHRAE A1 allowable"});
    add({CH_RH, true, 80.0, true, 20.0, SEV_WARN, 60, "humidity outside A1"});
    add({CH_LEAK, true, 0.5, false, 0, SEV_CRITICAL, 2, "water leak detected"});
    add({CH_DOOR, true, 0.5, false, 0, SEV_WARN, 300, "door open > 5 min"});
    add({CH_DP_AISLE, true, 60.0, false, 0, SEV_WARN, 30, "aisle dP high (filter clog?)"});
    add({CH_DP_AISLE, false, 0, true, -5.0, SEV_ALARM, 30, "aisle dP negative (containment breach?)"});
}

bool AlarmTable::add(const Threshold& t) {
    if (n_ >= MAX_THRESHOLDS) return false;
    th_[n_] = t; st_[n_] = AlarmState{}; ++n_; return true;
}

int AlarmTable::evaluate(const ChannelTable& ch, uint32_t now_ms, Severity* worst) {
    int active = 0; Severity w = SEV_NONE; changed_ = false;
    for (int i = 0; i < n_; ++i) {
        const Threshold& t = th_[i]; AlarmState& s = st_[i];
        bool cond = false;
        if (ch.present(t.ch)) {
            double v = ch.value(t.ch);
            cond = (t.use_hi && v > t.hi) || (t.use_lo && v < t.lo);
        }
        if (cond) {
            if (!s.pending) { s.pending = true; s.since_ms = now_ms; }
            if (!s.active && (uint32_t)(now_ms - s.since_ms) >= (uint32_t)t.hold_s * 1000u) { s.active = true; changed_ = true; }
        } else {
            s.pending = false;
            if (s.active) { s.active = false; changed_ = true; }
        }
        if (s.active) { ++active; if (t.sev > w) w = t.sev; }
    }
    if (worst) *worst = w;
    return active;
}

} // namespace bencore
