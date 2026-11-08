#include "commands.h"
#include "json_mini.h"
#include <cstring>
#include <cstdio>
#include <cmath>

namespace bencore {

static const struct { const char* name; CmdOp op; } OPS[] = {
    {"set_output", OP_SET_OUTPUT}, {"get_cal", OP_GET_CAL}, {"set_cal", OP_SET_CAL}, {"tare", OP_TARE},
    {"identify", OP_IDENTIFY}, {"reboot", OP_REBOOT}, {"ota", OP_OTA},
};

static void copy_str(char* dst, size_t cap, const char* src) { snprintf(dst, cap, "%s", src ? src : ""); }

static bool is_hex64(const char* s) {
    if (!s || strlen(s) != 64) return false;
    for (; *s; ++s) if (!isxdigit((unsigned char)*s)) return false;
    return true;
}

bool parse_command(const char* json, size_t len, Command& cmd) {
    cmd = Command{};
    JsonFlat j;
    if (!j.parse(json, len)) { cmd.error = "malformed json"; return false; }
    const char* id = j.get_str("id");
    if (id) copy_str(cmd.id, sizeof cmd.id, id);
    const char* op = j.get_str("op");
    if (!op) { cmd.error = "missing op"; return false; }
    for (auto& o : OPS) if (strcmp(o.name, op) == 0) cmd.op = o.op;
    if (cmd.op == OP_UNKNOWN) { cmd.error = "unknown op"; return false; }

    double num;
    switch (cmd.op) {
        case OP_SET_OUTPUT: {
            const char* out = j.get_str("out");
            if (!out) { cmd.error = "missing out"; return false; }
            copy_str(cmd.out, sizeof cmd.out, out);
            if (relay_by_name(out) < 0) { cmd.error = "unknown output"; return false; }
            if (!j.get_num("value", num)) { cmd.error = "missing value"; return false; }
            if (num != 0 && num != 1) { cmd.error = "value must be 0 or 1"; return false; }
            cmd.value = (int)num;
            break;
        }
        case OP_SET_CAL: {
            const char* ch = j.get_str("ch");
            if (!ch) { cmd.error = "missing ch"; return false; }
            copy_str(cmd.ch, sizeof cmd.ch, ch); cmd.has_ch = true;
            if (channel_by_name(ch) < 0) { cmd.error = "unknown channel"; return false; }
            if (j.get_num("gain", num)) { cmd.gain = (float)num; cmd.has_gain = true; }
            if (j.get_num("offset", num)) { cmd.offset = (float)num; cmd.has_offset = true; }
            if (!cmd.has_gain && !cmd.has_offset) { cmd.error = "missing gain/offset"; return false; }
            if (!std::isfinite(cmd.gain) || !std::isfinite(cmd.offset)) { cmd.error = "non-finite coefficient"; return false; }
            const char* cid = j.get_str("cal_id");
            if (cid) copy_str(cmd.cal_id, sizeof cmd.cal_id, cid);
            break;
        }
        case OP_TARE: {
            const char* ch = j.get_str("ch");
            if (!ch) { cmd.error = "missing ch"; return false; }
            copy_str(cmd.ch, sizeof cmd.ch, ch); cmd.has_ch = true;
            if (channel_by_name(ch) < 0) { cmd.error = "unknown channel"; return false; }
            break;
        }
        case OP_GET_CAL: {
            const char* ch = j.get_str("ch");
            if (ch) { copy_str(cmd.ch, sizeof cmd.ch, ch); cmd.has_ch = true;
                      if (channel_by_name(ch) < 0) { cmd.error = "unknown channel"; return false; } }
            break;
        }
        case OP_OTA: {
            const char* url = j.get_str("url"); const char* sha = j.get_str("sha256");
            if (!url || !*url) { cmd.error = "missing url"; return false; }
            if (strncmp(url, "https://", 8) != 0 && strncmp(url, "http://", 7) != 0) { cmd.error = "url must be http(s)"; return false; }
            if (!is_hex64(sha)) { cmd.error = "sha256 must be 64 hex chars"; return false; }
            copy_str(cmd.url, sizeof cmd.url, url); copy_str(cmd.sha256, sizeof cmd.sha256, sha);
            break;
        }
        case OP_IDENTIFY: {
            if (j.get_num("value", num)) cmd.value = num != 0; else cmd.value = 1;
            break;
        }
        default: break;
    }
    return true;
}

static void write_cal_entry(JsonWriter& w, const ChannelTable& t, int i) {
    w.key_object(CHANNELS[i].name);
    w.kv_num("gain", t.cal((ChannelId)i).gain, 6);
    w.kv_num("offset", t.cal((ChannelId)i).offset, 4);
    w.end_object();
}

static size_t finish(JsonWriter& w) { return w.overflowed() ? 0 : w.length(); }

static size_t ack_error(const Command& cmd, const char* err, char* ack, size_t cap) {
    JsonWriter w(ack, cap);
    w.begin_object(); w.kv("id", cmd.id); w.kv("ok", false); w.kv("error", err); w.end_object();
    return finish(w);
}

size_t execute_command(const Command& cmd, CommandContext& ctx, char* ack, size_t cap) {
    if (cmd.error) return ack_error(cmd, cmd.error, ack, cap);
    JsonWriter w(ack, cap);
    auto head = [&]() { w.begin_object(); w.kv("id", cmd.id); w.kv("ok", true); w.key_object("result"); };
    auto tail = [&]() { w.end_object(); w.end_object(); return finish(w); };

    switch (cmd.op) {
        case OP_SET_OUTPUT: {
            int idx = relay_by_name(cmd.out);
            if (!ctx.outputs || !ctx.outputs->set(idx, cmd.value != 0)) return ack_error(cmd, "output rejected", ack, cap);
            head(); w.kv("out", cmd.out); w.kv("value", (long long)(ctx.outputs->actual(idx) ? 1 : 0));
            w.kv("commanded", (long long)(ctx.outputs->commanded(idx) ? 1 : 0));
            w.kv("failsafe_active", ctx.outputs->failsafe_active());
            return tail();
        }
        case OP_GET_CAL: {
            head(); w.kv("cal_id", ctx.channels->cal_id());
            w.key_object("channels");
            for (int i = 0; i < CH_COUNT; ++i) {
                if (CHANNELS[i].kind != KIND_ANALOG) continue;
                if (cmd.has_ch && strcmp(CHANNELS[i].name, cmd.ch) != 0) continue;
                write_cal_entry(w, *ctx.channels, i);
            }
            w.end_object();
            return tail();
        }
        case OP_SET_CAL: {
            int i = channel_by_name(cmd.ch);
            const Cal& cur = ctx.channels->cal((ChannelId)i);
            float g = cmd.has_gain ? cmd.gain : cur.gain;
            float o = cmd.has_offset ? cmd.offset : cur.offset;
            if (!ctx.channels->set_cal((ChannelId)i, g, o)) return ack_error(cmd, "calibration rejected (gain out of 0.5..2 or channel not analog)", ack, cap);
            if (cmd.cal_id[0]) ctx.channels->set_cal_id(cmd.cal_id);
            bool saved = ctx.nvs ? ctx.channels->save(*ctx.nvs) : false;
            head(); w.kv("ch", cmd.ch); w.kv_num("gain", g, 6); w.kv_num("offset", o, 4);
            w.kv("cal_id", ctx.channels->cal_id()); w.kv("saved", saved);
            return tail();
        }
        case OP_TARE: {
            int i = channel_by_name(cmd.ch);
            if (!ctx.channels->tare((ChannelId)i)) return ack_error(cmd, "tare rejected (channel not tareable or no reading)", ack, cap);
            bool saved = ctx.nvs ? ctx.channels->save(*ctx.nvs) : false;
            head(); w.kv("ch", cmd.ch); w.kv_num("offset", ctx.channels->cal((ChannelId)i).offset, 4);
            w.kv_num("value", ctx.channels->value((ChannelId)i), CHANNELS[i].decimals); w.kv("saved", saved);
            return tail();
        }
        case OP_IDENTIFY: {
            if (ctx.identify_on) *ctx.identify_on = cmd.value != 0;
            if (ctx.sys) ctx.sys->identify(cmd.value != 0);
            head(); w.kv("identify", cmd.value != 0); return tail();
        }
        case OP_REBOOT: {
            if (ctx.reboot_requested) *ctx.reboot_requested = true;
            head(); w.kv("rebooting", true); return tail();
        }
        case OP_OTA: {
            bool started = ctx.sys ? ctx.sys->ota_begin(cmd.url, cmd.sha256) : false;
            if (!started) return ack_error(cmd, "ota could not start", ack, cap);
            head(); w.kv("ota", "started"); w.kv("sha256", cmd.sha256); return tail();
        }
        default: return ack_error(cmd, "unknown op", ack, cap);
    }
}

size_t handle_command(const char* json, size_t len, CommandContext& ctx, char* ack, size_t cap) {
    Command cmd;
    parse_command(json, len, cmd);
    return execute_command(cmd, ctx, ack, cap);
}

} // namespace bencore
