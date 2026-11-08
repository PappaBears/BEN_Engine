// BEN Engine — bencore — local alarm thresholds evaluated in the node.
// The gateway is the system of record for alarms; the node evaluates a small table so a
// local LED/relay can react even when the gateway is gone.
#pragma once
#include <cstdint>
#include "channels.h"

namespace bencore {

enum Severity : uint8_t { SEV_NONE, SEV_WARN, SEV_ALARM, SEV_CRITICAL };
const char* severity_name(Severity s);

struct Threshold {
    ChannelId ch;
    bool  use_hi; double hi;   // active when value > hi
    bool  use_lo; double lo;   // active when value < lo
    Severity sev;
    uint16_t hold_s;           // must persist this long before raising (debounce)
    const char* msg;
};

constexpr int MAX_THRESHOLDS = 16;

struct AlarmState { bool active = false; uint32_t since_ms = 0; bool pending = false; };

class AlarmTable {
public:
    AlarmTable();                                   // loads the ASHRAE A1 defaults
    bool add(const Threshold& t);
    void clear() { n_ = 0; }
    int  count() const { return n_; }
    const Threshold& threshold(int i) const { return th_[i]; }
    // Evaluate all thresholds; returns number of active alarms. Highest severity in *worst.
    int  evaluate(const ChannelTable& ch, uint32_t now_ms, Severity* worst = nullptr);
    bool active(int i) const { return i >= 0 && i < n_ && st_[i].active; }
    bool changed_since_last() const { return changed_; }

private:
    Threshold th_[MAX_THRESHOLDS]; AlarmState st_[MAX_THRESHOLDS];
    int n_ = 0; bool changed_ = false;
};

} // namespace bencore
