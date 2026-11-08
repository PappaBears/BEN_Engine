#include "outputs.h"
#include <cstring>

namespace bencore {

// Pin numbers match firmware/README.md and design/specs/wiring/02_node_wiring.svg.
// relay1 (cooling enable) is failsafe: when the gateway is gone, cooling falls back to the
// cooling unit's own local control, which is the safe direction. Lights/fan boost/spare hold.
const RelayConfig RELAYS[N_RELAYS] = {
    {"relay1", "cooling enable", 32, true},
    {"relay2", "lights",         33, false},
    {"relay3", "fan boost",      14, false},
    {"relay4", "spare",          15, false},
};

int relay_by_name(const char* name) {
    if (!name) return -1;
    for (int i = 0; i < N_RELAYS; ++i) if (strcmp(RELAYS[i].name, name) == 0) return i;
    return -1;
}

void Outputs::begin() {
    for (int i = 0; i < N_RELAYS; ++i) {
        fs_[i] = RELAYS[i].failsafe;
        if (gpio_) { gpio_->pin_mode(RELAYS[i].pin, benhal::Gpio::OUTPUT); gpio_->write(RELAYS[i].pin, false); }
        cmd_[i] = act_[i] = false;
    }
}

bool Outputs::set(int idx, bool on) {
    if (idx < 0 || idx >= N_RELAYS) return false;
    cmd_[idx] = on;
    apply();
    return true;
}

void Outputs::tick(uint32_t now_ms, uint32_t last_contact_ms, bool link_up) {
    uint32_t silent = now_ms - last_contact_ms;    // wrap-safe unsigned subtraction
    bool lost = !link_up || silent >= GATEWAY_LOSS_MS;
    if (lost != failsafe_active_) { failsafe_active_ = lost; apply(); }
}

void Outputs::apply() {
    for (int i = 0; i < N_RELAYS; ++i) {
        bool want = cmd_[i];
        if (failsafe_active_ && fs_[i]) want = false;        // failsafe outputs drop
        if (failsafe_active_ && !fs_[i]) want = act_[i];     // others hold last state
        if (want != act_[i]) { act_[i] = want; if (gpio_) gpio_->write(RELAYS[i].pin, want); }
    }
}

} // namespace bencore
