#include "ringbuf.h"
#include <cmath>
#include <climits>

namespace bencore {

static int16_t clamp16(double v) {
    if (v > 32767.0) return 32767;
    if (v < -32767.0) return -32767;
    return (int16_t)std::lround(v);
}
static uint16_t clampu16(double v) {
    if (v > 65534.0) return 65534;
    if (v < 0) return 0;
    return (uint16_t)std::lround(v);
}

TelemetryRecord pack_record(const ChannelTable& t, uint32_t ts, uint32_t seq, bool clock_valid) {
    TelemetryRecord r{};
    r.ts = ts; r.seq = seq;
    for (int i = 0; i < 9; ++i) {
        ChannelId id = (ChannelId)(CH_T_IN_1 + i);
        r.t_c100[i] = t.present(id) ? clamp16(t.value(id) * 100.0) : INT16_MIN;
    }
    r.rh_100 = t.present(CH_RH) ? clampu16(t.value(CH_RH) * 100.0) : 0xFFFF;
    r.dp_10  = t.present(CH_DP_AISLE) ? clamp16(t.value(CH_DP_AISLE) * 10.0) : INT16_MIN;
    for (int i = 0; i < 4; ++i) {
        ChannelId id = (ChannelId)(CH_AI0_MA + i);
        r.ai_ua[i] = t.present(id) ? clampu16(t.value(id) * 1000.0) : 0xFFFF;
    }
    r.flags = (t.present(CH_LEAK) && t.value(CH_LEAK) != 0 ? 1 : 0)
            | (t.present(CH_DOOR) && t.value(CH_DOOR) != 0 ? 2 : 0)
            | (clock_valid ? 4 : 0)
            | (t.present(CH_LEAK) ? 8 : 0) | (t.present(CH_DOOR) ? 16 : 0) | (t.present(CH_PULSE_KWH) ? 32 : 0);
    r.pulse_kwh = t.present(CH_PULSE_KWH) ? (uint32_t)t.value(CH_PULSE_KWH) : 0;
    return r;
}

void unpack_record(const TelemetryRecord& r, ChannelTable& out) {
    for (int i = 0; i < 9; ++i) {
        ChannelId id = (ChannelId)(CH_T_IN_1 + i);
        if (r.t_c100[i] == INT16_MIN) out.mark_missing(id); else out.set_raw(id, r.t_c100[i] / 100.0, r.t_c100[i]);
    }
    if (r.rh_100 == 0xFFFF) out.mark_missing(CH_RH); else out.set_raw(CH_RH, r.rh_100 / 100.0, r.rh_100);
    if (r.dp_10 == INT16_MIN) out.mark_missing(CH_DP_AISLE); else out.set_raw(CH_DP_AISLE, r.dp_10 / 10.0, r.dp_10);
    for (int i = 0; i < 4; ++i) {
        ChannelId id = (ChannelId)(CH_AI0_MA + i);
        if (r.ai_ua[i] == 0xFFFF) out.mark_missing(id); else out.set_raw(id, r.ai_ua[i] / 1000.0, r.ai_ua[i]);
    }
    if (r.flags & 8) out.set_digital(CH_LEAK, r.flags & 1); else out.mark_missing(CH_LEAK);
    if (r.flags & 16) out.set_digital(CH_DOOR, (r.flags & 2) != 0); else out.mark_missing(CH_DOOR);
    if (r.flags & 32) out.set_counter(CH_PULSE_KWH, r.pulse_kwh); else out.mark_missing(CH_PULSE_KWH);
}

} // namespace bencore
