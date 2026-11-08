#include "channels.h"
#include <cstring>
#include <cstdio>
#include <cmath>

namespace bencore {

const ChannelInfo CHANNELS[CH_COUNT] = {
    {"T_in_1",   "ti1", KIND_ANALOG, 2, false},
    {"T_in_2",   "ti2", KIND_ANALOG, 2, false},
    {"T_in_3",   "ti3", KIND_ANALOG, 2, false},
    {"T_in_4",   "ti4", KIND_ANALOG, 2, false},
    {"T_out_1",  "to1", KIND_ANALOG, 2, false},
    {"T_out_2",  "to2", KIND_ANALOG, 2, false},
    {"T_out_3",  "to3", KIND_ANALOG, 2, false},
    {"T_out_4",  "to4", KIND_ANALOG, 2, false},
    {"T_ref",    "tref", KIND_ANALOG, 2, false},
    {"RH",       "rh",  KIND_ANALOG, 1, false},
    {"dP_aisle", "dp",  KIND_ANALOG, 1, true},
    {"leak",     "leak", KIND_DIGITAL, 0, false},
    {"door",     "door", KIND_DIGITAL, 0, false},
    {"ai0_mA",   "ai0", KIND_ANALOG, 2, true},
    {"ai1_mA",   "ai1", KIND_ANALOG, 2, true},
    {"ai2_mA",   "ai2", KIND_ANALOG, 2, true},
    {"ai3_mA",   "ai3", KIND_ANALOG, 2, true},
    {"pulse_kwh","pkwh", KIND_COUNTER, 0, false},
};

int channel_by_name(const char* name) {
    if (!name) return -1;
    for (int i = 0; i < CH_COUNT; ++i) if (strcmp(CHANNELS[i].name, name) == 0) return i;
    return -1;
}

ChannelTable::ChannelTable() { strcpy(cal_id_, "uncal"); }

void ChannelTable::set_raw(ChannelId id, double raw, int32_t counts) {
    if (id >= CH_COUNT) return;
    s_[id].present = true; s_[id].raw = raw; s_[id].counts = counts;
}

double ChannelTable::value(ChannelId id) const {
    if (id >= CH_COUNT) return 0.0;
    if (CHANNELS[id].kind != KIND_ANALOG) return s_[id].raw;
    return s_[id].raw * cal_[id].gain + cal_[id].offset;
}

bool ChannelTable::set_cal(ChannelId id, float gain, float offset) {
    if (id >= CH_COUNT || CHANNELS[id].kind != KIND_ANALOG) return false;
    if (!std::isfinite(gain) || !std::isfinite(offset) || gain == 0.0f) return false;
    if (gain < 0.5f || gain > 2.0f) return false;            // sanity: a real sensor is never that far off
    cal_[id].gain = gain; cal_[id].offset = offset;
    return true;
}

bool ChannelTable::tare(ChannelId id) {
    if (id >= CH_COUNT || !CHANNELS[id].tareable || !s_[id].present) return false;
    cal_[id].offset = (float)(-s_[id].raw * cal_[id].gain);
    return true;
}

void ChannelTable::set_cal_id(const char* id) {
    if (!id || !*id) { strcpy(cal_id_, "uncal"); return; }
    snprintf(cal_id_, CAL_ID_LEN, "%s", id);
}

bool ChannelTable::load(benhal::Nvs& nvs) {
    char key[16]; bool any = false;
    for (int i = 0; i < CH_COUNT; ++i) {
        if (CHANNELS[i].kind != KIND_ANALOG) continue;
        float g, o;
        snprintf(key, sizeof key, "g_%s", CHANNELS[i].nvs_key);
        if (nvs.get_f32(key, g)) {
            snprintf(key, sizeof key, "o_%s", CHANNELS[i].nvs_key);
            if (nvs.get_f32(key, o) && set_cal((ChannelId)i, g, o)) any = true;
        }
    }
    char id[CAL_ID_LEN];
    if (nvs.get_str("cal_id", id, sizeof id)) { set_cal_id(id); any = true; }
    return any;
}

bool ChannelTable::save(benhal::Nvs& nvs) const {
    char key[16]; bool ok = true;
    for (int i = 0; i < CH_COUNT; ++i) {
        if (CHANNELS[i].kind != KIND_ANALOG) continue;
        snprintf(key, sizeof key, "g_%s", CHANNELS[i].nvs_key); ok &= nvs.set_f32(key, cal_[i].gain);
        snprintf(key, sizeof key, "o_%s", CHANNELS[i].nvs_key); ok &= nvs.set_f32(key, cal_[i].offset);
    }
    ok &= nvs.set_str("cal_id", cal_id_);
    ok &= nvs.commit();
    return ok;
}

} // namespace bencore
