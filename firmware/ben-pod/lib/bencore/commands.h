// BEN Engine — bencore — command parser and executor (topic .../cmd -> .../ack).
// Ops: set_output | get_cal | set_cal | tare | identify | reboot | ota
#pragma once
#include <cstddef>
#include <cstdint>
#include "channels.h"
#include "outputs.h"
#include "../benhal/hal.h"

namespace bencore {

enum CmdOp : uint8_t { OP_UNKNOWN, OP_SET_OUTPUT, OP_GET_CAL, OP_SET_CAL, OP_TARE, OP_IDENTIFY, OP_REBOOT, OP_OTA };

struct Command {
    char   id[40] = "";        // echoed in the ack ("" if the gateway sent none)
    CmdOp  op = OP_UNKNOWN;
    char   out[12] = "";       // set_output
    int    value = 0;
    char   ch[12] = "";        // set_cal / tare / get_cal (optional filter)
    bool   has_ch = false;
    float  gain = 1.0f, offset = 0.0f;
    bool   has_gain = false, has_offset = false;
    char   cal_id[ChannelTable::CAL_ID_LEN] = "";
    char   url[128] = "";      // ota
    char   sha256[65] = "";    // ota, 64 hex chars
    const char* error = nullptr;   // set when parsing failed (ack ok:false)
};

// Parse JSON into Command. Returns false (and sets cmd.error) on malformed input.
bool parse_command(const char* json, size_t len, Command& cmd);

struct CommandContext {
    ChannelTable*  channels;
    Outputs*       outputs;
    benhal::Nvs*   nvs;
    benhal::System* sys;
    bool* reboot_requested;     // executor sets; app reboots after the ack is published
    bool* identify_on;
};

// Execute and write the ack JSON. Always produces an ack (ok:false with "error" on failure).
// Returns ack length (0 if the buffer overflowed).
size_t execute_command(const Command& cmd, CommandContext& ctx, char* ack, size_t cap);

// Convenience: parse + execute.
size_t handle_command(const char* json, size_t len, CommandContext& ctx, char* ack, size_t cap);

} // namespace bencore
