// BEN Engine — bencore — relay outputs with failsafe behaviour.
// PROTOCOL.md: "A node that loses the gateway for 60 s ... leaves outputs in their last
// state unless the output is configured failsafe (then it drops)."
#pragma once
#include <cstdint>
#include "../benhal/hal.h"

namespace bencore {

constexpr int N_RELAYS = 4;
constexpr uint32_t GATEWAY_LOSS_MS = 60000;

struct RelayConfig {
    const char* name;      // "relay1".."relay4"
    const char* function;  // human label
    uint8_t     pin;
    bool        failsafe;  // drop when the gateway is lost
};
extern const RelayConfig RELAYS[N_RELAYS];
int relay_by_name(const char* name);   // -1 if unknown

class Outputs {
public:
    explicit Outputs(benhal::Gpio* gpio) : gpio_(gpio) {}
    void begin();                                       // configure pins, all off
    bool set(int idx, bool on);                         // commanded state (also applies if link is up)
    bool commanded(int idx) const { return idx >= 0 && idx < N_RELAYS && cmd_[idx]; }
    bool actual(int idx) const { return idx >= 0 && idx < N_RELAYS && act_[idx]; }
    bool failsafe_active() const { return failsafe_active_; }

    // Call every loop with the time of the last successful gateway contact.
    void tick(uint32_t now_ms, uint32_t last_gateway_contact_ms, bool link_up);
    // Test/diagnostic hook: force failsafe evaluation.
    void set_failsafe(int idx, bool fs) { if (idx >= 0 && idx < N_RELAYS) fs_[idx] = fs; }
    bool is_failsafe(int idx) const { return idx >= 0 && idx < N_RELAYS && fs_[idx]; }

private:
    void apply();
    benhal::Gpio* gpio_;
    bool cmd_[N_RELAYS] = {false, false, false, false};
    bool act_[N_RELAYS] = {false, false, false, false};
    bool fs_[N_RELAYS];
    bool failsafe_active_ = false;
};

} // namespace bencore
