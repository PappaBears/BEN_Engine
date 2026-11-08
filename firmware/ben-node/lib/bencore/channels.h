// BEN Engine — bencore — node channel map and calibration table (spec/PROTOCOL.md).
#pragma once
#include <cstdint>
#include <cstddef>
#include "../benhal/hal.h"

namespace bencore {

// Channel ids. Order defines the key order in telemetry JSON.
enum ChannelId : uint8_t {
    CH_T_IN_1, CH_T_IN_2, CH_T_IN_3, CH_T_IN_4,
    CH_T_OUT_1, CH_T_OUT_2, CH_T_OUT_3, CH_T_OUT_4,
    CH_T_REF, CH_RH, CH_DP_AISLE,
    CH_LEAK, CH_DOOR,
    CH_AI0_MA, CH_AI1_MA, CH_AI2_MA, CH_AI3_MA,
    CH_PULSE_KWH,
    CH_COUNT
};

enum ChannelKind : uint8_t { KIND_ANALOG, KIND_DIGITAL, KIND_COUNTER };

struct ChannelInfo {
    const char* name;       // protocol key, e.g. "T_in_1"
    const char* nvs_key;    // short NVS key prefix (NVS keys are limited to 15 chars)
    ChannelKind kind;
    uint8_t     decimals;   // decimals in telemetry JSON
    bool        tareable;   // "tare" command allowed
};

extern const ChannelInfo CHANNELS[CH_COUNT];
int channel_by_name(const char* name);   // -1 if unknown

struct Cal { float gain = 1.0f; float offset = 0.0f; };

struct Sample {
    bool   present = false;   // sensor answered this cycle
    double raw = 0.0;         // engineering raw (°C from DS18B20, Pa from SDP, mA from ADS...)
    int32_t counts = 0;       // raw ADC/sensor counts for the "raw" block
};

// Holds the latest sample per channel plus calibration. Calibrated value = raw*gain + offset.
class ChannelTable {
public:
    static constexpr size_t CAL_ID_LEN = 32;

    ChannelTable();

    void   set_raw(ChannelId id, double raw, int32_t counts);
    void   set_digital(ChannelId id, bool level) { set_raw(id, level ? 1.0 : 0.0, level ? 1 : 0); }
    void   set_counter(ChannelId id, uint32_t count) { set_raw(id, (double)count, (int32_t)count); }
    void   mark_missing(ChannelId id) { s_[id].present = false; }

    bool   present(ChannelId id) const { return s_[id].present; }
    double raw(ChannelId id) const { return s_[id].raw; }
    int32_t counts(ChannelId id) const { return s_[id].counts; }
    double value(ChannelId id) const;          // calibrated value (digital/counter pass through)

    const Cal& cal(ChannelId id) const { return cal_[id]; }
    bool   set_cal(ChannelId id, float gain, float offset);   // rejects non-finite/zero gain
    // Tare: choose offset so that the current reading becomes zero (dP channels).
    bool   tare(ChannelId id);
    const char* cal_id() const { return cal_id_; }
    void   set_cal_id(const char* id);

    // Persistence. Keys: "g_<nvs_key>", "o_<nvs_key>", "cal_id".
    bool   load(benhal::Nvs& nvs);
    bool   save(benhal::Nvs& nvs) const;

private:
    Sample s_[CH_COUNT];
    Cal    cal_[CH_COUNT];
    char   cal_id_[CAL_ID_LEN];
};

} // namespace bencore
