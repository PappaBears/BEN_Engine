// BEN Engine — bencore — fixed-size ring buffer of compact telemetry records.
// Sized for 1 h at 1 Hz (BEN_RING_SECONDS = 3600). Each record is 44 bytes, so the
// default buffer is ~155 KB and must be allocated once at boot (static or PSRAM).
#pragma once
#include <cstdint>
#include <cstddef>
#include "channels.h"

namespace bencore {

#ifndef BEN_RING_SECONDS
#define BEN_RING_SECONDS 3600
#endif

// Compact fixed-layout record. Scaled integers, no floats, no pointers.
struct __attribute__((packed)) TelemetryRecord {
    uint32_t ts;           // unix seconds (0 if the clock was not valid)
    uint32_t seq;
    int16_t  t_c100[9];    // T_in_1..4, T_out_1..4, T_ref  in 0.01 °C  (INT16_MIN = missing)
    uint16_t rh_100;       // %RH * 100 (0xFFFF = missing)
    int16_t  dp_10;        // Pa * 10
    uint16_t ai_ua[4];     // mA * 1000 (µA)
    uint8_t  flags;        // bit0 leak, bit1 door, bit2 clock_valid, bit3 leak present, bit4 door present, bit5 pulse present
    uint32_t pulse_kwh;
    uint8_t  pad;          // keeps the struct at 44 bytes
};
static_assert(sizeof(TelemetryRecord) == 44, "TelemetryRecord must stay 44 bytes");

TelemetryRecord pack_record(const ChannelTable& t, uint32_t ts, uint32_t seq, bool clock_valid);
// Restores calibrated values into a fresh table (for replay). cal is left at identity
// because the stored numbers are already calibrated.
void unpack_record(const TelemetryRecord& r, ChannelTable& out);

template <typename T, size_t N>
class RingBuffer {
public:
    static constexpr size_t capacity() { return N; }
    size_t size() const { return count_; }
    bool   empty() const { return count_ == 0; }
    bool   full() const { return count_ == N; }
    uint32_t dropped() const { return dropped_; }

    void push(const T& v) {
        buf_[head_] = v;
        head_ = (head_ + 1) % N;
        if (count_ == N) { tail_ = (tail_ + 1) % N; ++dropped_; } else ++count_;
    }
    bool pop(T& out) {
        if (count_ == 0) return false;
        out = buf_[tail_]; tail_ = (tail_ + 1) % N; --count_; return true;
    }
    const T& peek(size_t i) const { return buf_[(tail_ + i) % N]; }  // i < size()
    void clear() { head_ = tail_ = count_ = 0; }

private:
    T buf_[N];
    size_t head_ = 0, tail_ = 0, count_ = 0;
    uint32_t dropped_ = 0;
};

using TelemetryRing = RingBuffer<TelemetryRecord, BEN_RING_SECONDS>;

} // namespace bencore
