// BEN Node — unit tests for lib/bencore (run with `pio test -e native` or `make test`).
#include <unity.h>
#include <cstring>
#include <cstdio>
#include <string>
#include "hal_mock.h"
#include "channels.h"
#include "telemetry.h"
#include "commands.h"
#include "ringbuf.h"
#include "outputs.h"
#include "alarms.h"
#include "timesync.h"
#include "node_app.h"
#include "json_mini.h"

using namespace bencore;
using namespace benhal;

extern "C" void setUp(void) {}
extern "C" void tearDown(void) {}

// Ring buffer is ~155 KB: keep one static instance for the app tests.
static TelemetryRing g_ring;

// Fill a table with the sample values from PROTOCOL.md's telemetry example.
static void fill_example(ChannelTable& t) {
    t.set_raw(CH_T_IN_1, 21.4, 342);
    t.set_raw(CH_T_IN_2, 21.9, 350);
    t.set_raw(CH_T_OUT_1, 33.0, 528);
    t.set_raw(CH_RH, 41.2, 27000);
    t.set_raw(CH_DP_AISLE, 12.3, 738);
    t.set_digital(CH_LEAK, false);
    t.set_digital(CH_DOOR, false);
    t.set_raw(CH_AI0_MA, 12.01, 15997);
    t.set_cal_id("c-2026-11-07-01");
}

// ------------------------------------------------------------------ calibration
void test_calibration_apply_gain_offset() {
    ChannelTable t;
    t.set_raw(CH_T_IN_1, 20.0, 320);
    TEST_ASSERT_FLOAT_WITHIN(1e-6, 20.0, t.value(CH_T_IN_1));           // identity by default
    TEST_ASSERT_TRUE(t.set_cal(CH_T_IN_1, 1.002f, -0.13f));
    TEST_ASSERT_FLOAT_WITHIN(1e-4, 20.0 * 1.002 - 0.13, t.value(CH_T_IN_1));
    TEST_ASSERT_FLOAT_WITHIN(1e-9, 20.0, t.raw(CH_T_IN_1));              // raw untouched
    TEST_ASSERT_EQUAL(320, t.counts(CH_T_IN_1));
}

void test_calibration_rejects_bad_values() {
    ChannelTable t;
    TEST_ASSERT_FALSE(t.set_cal(CH_T_IN_1, 0.0f, 0.0f));
    TEST_ASSERT_FALSE(t.set_cal(CH_T_IN_1, 5.0f, 0.0f));
    TEST_ASSERT_FALSE(t.set_cal(CH_T_IN_1, NAN, 0.0f));
    TEST_ASSERT_FALSE(t.set_cal(CH_LEAK, 1.0f, 0.0f));                  // digital channels have no cal
    TEST_ASSERT_FLOAT_WITHIN(1e-9, 1.0, t.cal(CH_T_IN_1).gain);
}

void test_calibration_digital_passthrough() {
    ChannelTable t;
    t.set_digital(CH_DOOR, true);
    t.set_counter(CH_PULSE_KWH, 123456);
    TEST_ASSERT_FLOAT_WITHIN(0, 1.0, t.value(CH_DOOR));
    TEST_ASSERT_FLOAT_WITHIN(0, 123456.0, t.value(CH_PULSE_KWH));
}

void test_calibration_nvs_roundtrip() {
    MockNvs nvs;
    ChannelTable a;
    a.set_cal(CH_DP_AISLE, 0.998f, 1.25f);
    a.set_cal(CH_AI2_MA, 1.01f, -0.02f);
    a.set_cal_id("c-2026-11-07-01");
    TEST_ASSERT_TRUE(a.save(nvs));
    TEST_ASSERT_EQUAL(1, nvs.commits);
    ChannelTable b;
    TEST_ASSERT_TRUE(b.load(nvs));
    TEST_ASSERT_FLOAT_WITHIN(1e-6, 0.998, b.cal(CH_DP_AISLE).gain);
    TEST_ASSERT_FLOAT_WITHIN(1e-6, 1.25, b.cal(CH_DP_AISLE).offset);
    TEST_ASSERT_FLOAT_WITHIN(1e-6, -0.02, b.cal(CH_AI2_MA).offset);
    TEST_ASSERT_EQUAL_STRING("c-2026-11-07-01", b.cal_id());
    TEST_ASSERT_FLOAT_WITHIN(1e-6, 1.0, b.cal(CH_T_IN_1).gain);         // untouched channel stays identity
}

void test_cal_id_truncation() {
    ChannelTable t;
    t.set_cal_id("this-cal-id-is-far-too-long-to-fit-in-32-bytes-0123456789");
    TEST_ASSERT_EQUAL(31, (int)strlen(t.cal_id()));
    t.set_cal_id("");
    TEST_ASSERT_EQUAL_STRING("uncal", t.cal_id());
}

// ------------------------------------------------------------------ tare
void test_tare_zeroes_dp() {
    ChannelTable t;
    t.set_raw(CH_DP_AISLE, 0.7, 42);
    TEST_ASSERT_TRUE(t.tare(CH_DP_AISLE));
    TEST_ASSERT_FLOAT_WITHIN(1e-6, 0.0, t.value(CH_DP_AISLE));
    t.set_raw(CH_DP_AISLE, 13.0, 780);                                   // later reading: offset still applied
    TEST_ASSERT_FLOAT_WITHIN(1e-5, 12.3, t.value(CH_DP_AISLE));
}

void test_tare_respects_gain_and_rejects_untareable() {
    ChannelTable t;
    t.set_cal(CH_DP_AISLE, 1.1f, 0.0f);
    t.set_raw(CH_DP_AISLE, 2.0, 120);
    TEST_ASSERT_TRUE(t.tare(CH_DP_AISLE));
    TEST_ASSERT_FLOAT_WITHIN(1e-5, 0.0, t.value(CH_DP_AISLE));
    TEST_ASSERT_FLOAT_WITHIN(1e-5, -2.2, t.cal(CH_DP_AISLE).offset);
    t.set_raw(CH_T_IN_1, 21.0, 336);
    TEST_ASSERT_FALSE(t.tare(CH_T_IN_1));                                // temperatures are not tareable
    TEST_ASSERT_FALSE(t.tare(CH_AI1_MA));                                // tareable but no reading yet
}

// ------------------------------------------------------------------ JSON shape
void test_telemetry_json_matches_protocol() {
    ChannelTable t; fill_example(t);
    char buf[512];
    size_t n = build_telemetry(t, 1762560000ULL, 42, buf, sizeof buf);
    TEST_ASSERT_GREATER_THAN(0, (int)n);
    const char* expect =
        "{\"ts\":1762560000,\"seq\":42,"
        "\"ch\":{\"T_in_1\":21.4,\"T_in_2\":21.9,\"T_out_1\":33,\"RH\":41.2,\"dP_aisle\":12.3,\"leak\":0,\"door\":0,\"ai0_mA\":12.01},"
        "\"raw\":{\"T_in_1\":342,\"T_in_2\":350,\"T_out_1\":528,\"RH\":27000,\"dP_aisle\":738,\"ai0_mA\":15997},"
        "\"cal_id\":\"c-2026-11-07-01\"}";
    TEST_ASSERT_EQUAL_STRING(expect, buf);
    TEST_ASSERT_EQUAL(strlen(expect), n);
}

void test_telemetry_json_calibrated_values_and_omits_missing() {
    ChannelTable t;
    t.set_raw(CH_T_IN_1, 20.0, 320);
    t.set_cal(CH_T_IN_1, 1.002f, -0.13f);
    char buf[256];
    build_telemetry(t, 0, 1, buf, sizeof buf);
    // 20*1.002-0.13 = 19.91 ; nothing else present ; cal_id default
    TEST_ASSERT_EQUAL_STRING("{\"ts\":0,\"seq\":1,\"ch\":{\"T_in_1\":19.91},\"raw\":{\"T_in_1\":320},\"cal_id\":\"uncal\"}", buf);
}

void test_telemetry_json_overflow_returns_zero() {
    ChannelTable t; fill_example(t);
    char buf[64];
    TEST_ASSERT_EQUAL(0, (int)build_telemetry(t, 1, 1, buf, sizeof buf));
}

void test_telemetry_full_channel_set_fits_in_msg_cap() {
    ChannelTable t;
    for (int i = 0; i < CH_COUNT; ++i) {
        ChannelId id = (ChannelId)i;
        if (CHANNELS[i].kind == KIND_ANALOG) t.set_raw(id, -123.456, -2147483647);
        else if (CHANNELS[i].kind == KIND_DIGITAL) t.set_digital(id, true);
        else t.set_counter(id, 4294967295u);
    }
    t.set_cal_id("c-2026-11-07-01-very-long-id-xx");
    char buf[NodeApp::MSG_CAP];
    size_t n = build_telemetry(t, 4102444800ULL, 4294967295u, buf, sizeof buf);
    TEST_ASSERT_GREATER_THAN(0, (int)n);
    TEST_ASSERT_LESS_THAN((int)sizeof buf, (int)n);
}

void test_status_json_matches_protocol() {
    StatusInfo s{};
    s.fw = "1.0.0"; s.uptime_s = 3601; s.rssi = 0; s.ip = "10.20.0.31"; s.heap = 180000; s.n_errors = 0;
    s.buffered = 0; s.clock_valid = true;
    char buf[256];
    build_status(s, buf, sizeof buf);
    TEST_ASSERT_EQUAL_STRING("{\"fw\":\"1.0.0\",\"uptime_s\":3601,\"rssi\":0,\"ip\":\"10.20.0.31\",\"heap\":180000,\"errors\":[],\"buffered\":0,\"clock_valid\":true}", buf);
    s.errors[0] = "clock not synced"; s.n_errors = 1;
    build_status(s, buf, sizeof buf);
    TEST_ASSERT_NOT_NULL(strstr(buf, "\"errors\":[\"clock not synced\"]"));
}

void test_topic_builder() {
    char t[96];
    TEST_ASSERT_GREATER_THAN(0, (int)build_topic(t, sizeof t, "ben20-0007", "node3", "telemetry"));
    TEST_ASSERT_EQUAL_STRING("ben/ben20-0007/node/node3/telemetry", t);
    char small[16];
    TEST_ASSERT_EQUAL(0, (int)build_topic(small, sizeof small, "ben20-0007", "node3", "telemetry"));
}

void test_json_writer_escapes_and_trims() {
    char buf[128]; JsonWriter w(buf, sizeof buf);
    w.begin_object(); w.kv("s", "a\"b\\c\n"); w.kv_num("z", 0.0, 2); w.kv_num("n", -0.001, 2); w.kv_num("x", 2.50, 2); w.end_object();
    TEST_ASSERT_EQUAL_STRING("{\"s\":\"a\\\"b\\\\c\\n\",\"z\":0,\"n\":0,\"x\":2.5}", buf);
}

// ------------------------------------------------------------------ command parsing
void test_parse_set_output() {
    Command c;
    TEST_ASSERT_TRUE(parse_command("{\"id\":\"uuid-1\",\"op\":\"set_output\",\"out\":\"relay1\",\"value\":1}", 0, c));
    TEST_ASSERT_EQUAL(OP_SET_OUTPUT, c.op);
    TEST_ASSERT_EQUAL_STRING("uuid-1", c.id);
    TEST_ASSERT_EQUAL_STRING("relay1", c.out);
    TEST_ASSERT_EQUAL(1, c.value);
}

void test_parse_set_cal_and_tare_and_ota() {
    Command c;
    TEST_ASSERT_TRUE(parse_command("{ \"op\" : \"set_cal\", \"ch\":\"T_in_1\", \"gain\":1.002, \"offset\":-0.13, \"cal_id\":\"c-2026-11-07-01\" }", 0, c));
    TEST_ASSERT_EQUAL(OP_SET_CAL, c.op);
    TEST_ASSERT_FLOAT_WITHIN(1e-6, 1.002, c.gain);
    TEST_ASSERT_FLOAT_WITHIN(1e-6, -0.13, c.offset);
    TEST_ASSERT_EQUAL_STRING("c-2026-11-07-01", c.cal_id);
    TEST_ASSERT_EQUAL_STRING("", c.id);
    TEST_ASSERT_TRUE(parse_command("{\"op\":\"tare\",\"ch\":\"dP_aisle\"}", 0, c));
    TEST_ASSERT_EQUAL(OP_TARE, c.op);
    std::string sha(64, 'a');
    std::string ota = "{\"op\":\"ota\",\"url\":\"https://gw.ben.local/fw/ben-node-1.0.1.bin\",\"sha256\":\"" + sha + "\"}";
    TEST_ASSERT_TRUE(parse_command(ota.c_str(), 0, c));
    TEST_ASSERT_EQUAL(OP_OTA, c.op);
    TEST_ASSERT_EQUAL_STRING("https://gw.ben.local/fw/ben-node-1.0.1.bin", c.url);
    TEST_ASSERT_TRUE(parse_command("{\"op\":\"identify\"}", 0, c));
    TEST_ASSERT_EQUAL(OP_IDENTIFY, c.op);
    TEST_ASSERT_TRUE(parse_command("{\"op\":\"reboot\"}", 0, c));
    TEST_ASSERT_EQUAL(OP_REBOOT, c.op);
    TEST_ASSERT_TRUE(parse_command("{\"op\":\"get_cal\"}", 0, c));
    TEST_ASSERT_EQUAL(OP_GET_CAL, c.op);
}

void test_parse_malformed_inputs() {
    Command c;
    const char* bad[] = {
        "", "garbage", "{", "{\"op\":\"reboot\"", "{\"op\":\"reboot\"}x", "[1,2]", "{\"op\":}",
        "{\"op\":\"set_output\",\"out\":\"relay1\"}",            // missing value
        "{\"op\":\"set_output\",\"out\":\"relay9\",\"value\":1}", // unknown output
        "{\"op\":\"set_output\",\"out\":\"relay1\",\"value\":2}", // bad value
        "{\"op\":\"set_cal\",\"ch\":\"nope\",\"gain\":1}",         // unknown channel
        "{\"op\":\"set_cal\",\"ch\":\"T_in_1\"}",                  // no coefficients
        "{\"op\":\"tare\"}",                                        // missing ch
        "{\"op\":\"ota\",\"url\":\"ftp://x\",\"sha256\":\"abc\"}", // bad url + sha
        "{\"op\":\"ota\",\"url\":\"https://x/fw.bin\",\"sha256\":\"zz\"}",
        "{\"op\":\"format_flash\"}",                                // unknown op
        "{\"id\":\"x\"}",                                           // missing op
        "{\"op\":\"reboot\",\"gain\":0x10}",                        // hex is not JSON
        "{\"op\":\"set_output\",\"out\":\"relay1\",\"value\":\"1\"}", // string instead of number
    };
    for (auto s : bad) {
        bool ok = parse_command(s, 0, c);
        char msg[200]; snprintf(msg, sizeof msg, "should reject: %s", s);
        TEST_ASSERT_FALSE_MESSAGE(ok, msg);
        TEST_ASSERT_NOT_NULL(c.error);
    }
    TEST_ASSERT_FALSE(parse_command(nullptr, 0, c));
}

void test_parse_tolerates_unknown_and_nested_fields() {
    Command c;
    TEST_ASSERT_TRUE(parse_command("{\"id\":\"q\",\"op\":\"identify\",\"meta\":{\"from\":\"gw\",\"n\":[1,2]},\"extra\":null}", 0, c));
    TEST_ASSERT_EQUAL(OP_IDENTIFY, c.op);
}

void test_parse_oversized_string_truncates_safely() {
    std::string big = "{\"id\":\"" + std::string(500, 'A') + "\",\"op\":\"reboot\"}";
    Command c;
    TEST_ASSERT_TRUE(parse_command(big.c_str(), 0, c));
    TEST_ASSERT_EQUAL((int)sizeof c.id - 1, (int)strlen(c.id));            // truncated, NUL-terminated
}

// ------------------------------------------------------------------ command execution + acks
struct Rig {
    MockHal m; ChannelTable ch; Outputs out{&m.gpio}; bool reboot = false, ident = false;
    CommandContext ctx{&ch, &out, &m.nvs, &m.sys, &reboot, &ident};
    char ack[NodeApp::MSG_CAP];
    Rig() { out.begin(); fill_example(ch); }
    size_t run(const char* json) { return handle_command(json, strlen(json), ctx, ack, sizeof ack); }
};

void test_ack_set_output() {
    Rig r;
    r.run("{\"id\":\"u1\",\"op\":\"set_output\",\"out\":\"relay2\",\"value\":1}");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"u1\",\"ok\":true,\"result\":{\"out\":\"relay2\",\"value\":1,\"commanded\":1,\"failsafe_active\":false}}", r.ack);
    TEST_ASSERT_TRUE(r.m.gpio.read(RELAYS[1].pin));
    r.run("{\"id\":\"u2\",\"op\":\"set_output\",\"out\":\"relay2\",\"value\":0}");
    TEST_ASSERT_FALSE(r.m.gpio.read(RELAYS[1].pin));
}

void test_ack_error_shape() {
    Rig r;
    r.run("{\"id\":\"u3\",\"op\":\"set_output\",\"out\":\"relay9\",\"value\":1}");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"u3\",\"ok\":false,\"error\":\"unknown output\"}", r.ack);
    r.run("not json");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"\",\"ok\":false,\"error\":\"malformed json\"}", r.ack);
}

void test_ack_set_cal_persists_and_get_cal_reads_back() {
    Rig r;
    r.run("{\"id\":\"c1\",\"op\":\"set_cal\",\"ch\":\"T_in_1\",\"gain\":1.002,\"offset\":-0.13,\"cal_id\":\"c-2026-11-07-01\"}");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"c1\",\"ok\":true,\"result\":{\"ch\":\"T_in_1\",\"gain\":1.002,\"offset\":-0.13,\"cal_id\":\"c-2026-11-07-01\",\"saved\":true}}", r.ack);
    TEST_ASSERT_EQUAL(1, r.m.nvs.commits);
    float g = 0; TEST_ASSERT_TRUE(r.m.nvs.get_f32("g_ti1", g)); TEST_ASSERT_FLOAT_WITHIN(1e-6, 1.002, g);
    r.run("{\"id\":\"c2\",\"op\":\"get_cal\",\"ch\":\"T_in_1\"}");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"c2\",\"ok\":true,\"result\":{\"cal_id\":\"c-2026-11-07-01\",\"channels\":{\"T_in_1\":{\"gain\":1.002,\"offset\":-0.13}}}}", r.ack);
    r.run("{\"id\":\"c3\",\"op\":\"get_cal\"}");
    TEST_ASSERT_NOT_NULL(strstr(r.ack, "\"ai3_mA\":{\"gain\":1,\"offset\":0}"));
    TEST_ASSERT_NOT_NULL(strstr(r.ack, "\"dP_aisle\""));
    TEST_ASSERT_NULL(strstr(r.ack, "\"leak\""));
    r.run("{\"id\":\"c4\",\"op\":\"set_cal\",\"ch\":\"T_in_1\",\"gain\":9}");
    TEST_ASSERT_NOT_NULL(strstr(r.ack, "\"ok\":false"));
}

void test_ack_tare() {
    Rig r;
    r.run("{\"id\":\"t1\",\"op\":\"tare\",\"ch\":\"dP_aisle\"}");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"t1\",\"ok\":true,\"result\":{\"ch\":\"dP_aisle\",\"offset\":-12.3,\"value\":0,\"saved\":true}}", r.ack);
    r.run("{\"id\":\"t2\",\"op\":\"tare\",\"ch\":\"T_in_1\"}");
    TEST_ASSERT_NOT_NULL(strstr(r.ack, "\"ok\":false"));
}

void test_ack_identify_reboot_ota() {
    Rig r;
    r.run("{\"id\":\"i\",\"op\":\"identify\"}");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"i\",\"ok\":true,\"result\":{\"identify\":true}}", r.ack);
    TEST_ASSERT_TRUE(r.m.sys.ident);
    r.run("{\"id\":\"i0\",\"op\":\"identify\",\"value\":0}");
    TEST_ASSERT_FALSE(r.m.sys.ident);
    r.run("{\"id\":\"rb\",\"op\":\"reboot\"}");
    TEST_ASSERT_EQUAL_STRING("{\"id\":\"rb\",\"ok\":true,\"result\":{\"rebooting\":true}}", r.ack);
    TEST_ASSERT_TRUE(r.reboot);
    TEST_ASSERT_EQUAL(0, r.m.sys.reboots);                               // app reboots AFTER publishing the ack
    std::string sha(64, 'b');
    std::string ota = "{\"id\":\"o\",\"op\":\"ota\",\"url\":\"https://gw.ben.local/fw.bin\",\"sha256\":\"" + sha + "\"}";
    r.run(ota.c_str());
    TEST_ASSERT_EQUAL(1, r.m.sys.ota_calls);
    TEST_ASSERT_EQUAL_STRING(sha.c_str(), r.m.sys.last_ota_sha.c_str());
    TEST_ASSERT_NOT_NULL(strstr(r.ack, "\"ota\":\"started\""));
}

// ------------------------------------------------------------------ ring buffer
void test_ring_record_size_and_pack_unpack() {
    TEST_ASSERT_EQUAL(44, (int)sizeof(TelemetryRecord));
    ChannelTable t; fill_example(t);
    TelemetryRecord r = pack_record(t, 1762560000u, 7, true);
    TEST_ASSERT_EQUAL(2140, r.t_c100[0]);
    TEST_ASSERT_EQUAL(INT16_MIN, r.t_c100[2]);                           // T_in_3 missing
    TEST_ASSERT_EQUAL(4120, r.rh_100);
    TEST_ASSERT_EQUAL(123, r.dp_10);
    TEST_ASSERT_EQUAL(12010, r.ai_ua[0]);
    TEST_ASSERT_EQUAL(4 | 8 | 16, r.flags);                              // clock valid, leak+door present and 0, no pulse
    ChannelTable u; unpack_record(r, u);
    TEST_ASSERT_FLOAT_WITHIN(0.005, 21.4, u.value(CH_T_IN_1));
    TEST_ASSERT_FALSE(u.present(CH_T_IN_3));
    TEST_ASSERT_FLOAT_WITHIN(0.05, 12.3, u.value(CH_DP_AISLE));
    TEST_ASSERT_FLOAT_WITHIN(0.0005, 12.01, u.value(CH_AI0_MA));
    TEST_ASSERT_TRUE(u.present(CH_DOOR)); TEST_ASSERT_FALSE(u.present(CH_PULSE_KWH));
}

void test_ring_wraps_and_keeps_newest() {
    RingBuffer<TelemetryRecord, 5> rb;
    TEST_ASSERT_TRUE(rb.empty());
    for (uint32_t i = 1; i <= 7; ++i) { TelemetryRecord r{}; r.seq = i; rb.push(r); }
    TEST_ASSERT_TRUE(rb.full());
    TEST_ASSERT_EQUAL(5, (int)rb.size());
    TEST_ASSERT_EQUAL(2, (int)rb.dropped());
    TelemetryRecord o{};
    TEST_ASSERT_TRUE(rb.pop(o)); TEST_ASSERT_EQUAL(3, o.seq);            // oldest surviving = 3
    TEST_ASSERT_EQUAL(4, rb.peek(0).seq);
    for (int i = 0; i < 4; ++i) TEST_ASSERT_TRUE(rb.pop(o));
    TEST_ASSERT_EQUAL(7, o.seq);
    TEST_ASSERT_FALSE(rb.pop(o));
    TEST_ASSERT_TRUE(rb.empty());
}

void test_ring_capacity_is_one_hour() {
    TEST_ASSERT_EQUAL(3600, (int)TelemetryRing::capacity());
    TEST_ASSERT_EQUAL(3600 * 44, (int)(TelemetryRing::capacity() * sizeof(TelemetryRecord)));
    g_ring.clear();
    for (uint32_t i = 0; i < 4000; ++i) { TelemetryRecord r{}; r.seq = i; g_ring.push(r); }
    TEST_ASSERT_EQUAL(3600, (int)g_ring.size());
    TEST_ASSERT_EQUAL(400, (int)g_ring.peek(0).seq);
    g_ring.clear();
}

// ------------------------------------------------------------------ failsafe outputs
void test_failsafe_drops_only_failsafe_outputs_after_60s() {
    MockGpio g; Outputs o(&g); o.begin();
    TEST_ASSERT_TRUE(o.is_failsafe(0));                                  // relay1 cooling enable
    TEST_ASSERT_FALSE(o.is_failsafe(1));
    o.set(0, true); o.set(1, true);
    TEST_ASSERT_TRUE(g.read(RELAYS[0].pin)); TEST_ASSERT_TRUE(g.read(RELAYS[1].pin));
    o.tick(59999, 0, true);                                              // 59.999 s silent: nothing happens
    TEST_ASSERT_FALSE(o.failsafe_active());
    TEST_ASSERT_TRUE(g.read(RELAYS[0].pin));
    o.tick(60000, 0, true);                                              // 60 s: failsafe
    TEST_ASSERT_TRUE(o.failsafe_active());
    TEST_ASSERT_FALSE(g.read(RELAYS[0].pin));                            // relay1 dropped
    TEST_ASSERT_TRUE(g.read(RELAYS[1].pin));                             // relay2 holds last state
    TEST_ASSERT_TRUE(o.commanded(0));                                    // intent remembered
    o.tick(60001, 60001, true);                                          // gateway back
    TEST_ASSERT_FALSE(o.failsafe_active());
    TEST_ASSERT_TRUE(g.read(RELAYS[0].pin));                             // restored to commanded state
}

void test_failsafe_on_link_down_and_wraparound() {
    MockGpio g; Outputs o(&g); o.begin();
    o.set(0, true);
    o.tick(1000, 900, false);                                            // link down -> immediate failsafe
    TEST_ASSERT_TRUE(o.failsafe_active());
    TEST_ASSERT_FALSE(g.read(RELAYS[0].pin));
    // millis() wrap: last contact just before wrap, now just after
    Outputs o2(&g); o2.begin(); o2.set(0, true);
    o2.tick(100, 0xFFFFFF00u, true);                                     // 356 ms silent across the wrap
    TEST_ASSERT_FALSE(o2.failsafe_active());
}

void test_failsafe_commands_during_loss_apply_on_restore() {
    MockGpio g; Outputs o(&g); o.begin();
    o.tick(100000, 0, true);                                             // lost
    o.set(0, true);                                                      // gateway cannot really command here, but a stale cmd arriving must not energise
    TEST_ASSERT_FALSE(g.read(RELAYS[0].pin));
    o.set(3, true);                                                      // non-failsafe output: holds (stays off since it was off)
    TEST_ASSERT_FALSE(g.read(RELAYS[3].pin));
    o.tick(100001, 100001, true);
    TEST_ASSERT_TRUE(g.read(RELAYS[0].pin));
    TEST_ASSERT_TRUE(g.read(RELAYS[3].pin));
}

// ------------------------------------------------------------------ alarms
void test_alarm_thresholds_with_hold_time() {
    AlarmTable a; ChannelTable t;
    t.set_raw(CH_T_IN_1, 27.8, 445);
    Severity w;
    TEST_ASSERT_EQUAL(0, a.evaluate(t, 0, &w));                          // condition true but hold not elapsed
    TEST_ASSERT_EQUAL(0, a.evaluate(t, 29999, &w));
    TEST_ASSERT_EQUAL(1, a.evaluate(t, 30000, &w));
    TEST_ASSERT_EQUAL(SEV_WARN, w);
    TEST_ASSERT_TRUE(a.changed_since_last());
    t.set_raw(CH_T_IN_1, 33.0, 528);
    a.evaluate(t, 31000, &w);
    TEST_ASSERT_EQUAL(2, a.evaluate(t, 41000, &w));                      // allowable breached after 10 s hold
    TEST_ASSERT_EQUAL(SEV_ALARM, w);
    t.set_raw(CH_T_IN_1, 22.0, 352);
    TEST_ASSERT_EQUAL(0, a.evaluate(t, 42000, &w));                      // clears immediately
    t.set_digital(CH_LEAK, true);
    a.evaluate(t, 42000, &w); a.evaluate(t, 44000, &w);
    TEST_ASSERT_EQUAL(SEV_CRITICAL, w);
}

// ------------------------------------------------------------------ time sync
void test_timesync_anchor_and_steps() {
    MockClock c; TimeSync ts(&c);
    ts.poll();
    TEST_ASSERT_FALSE(ts.valid()); TEST_ASSERT_EQUAL(0, (int)ts.unix_s()); TEST_ASSERT_TRUE(ts.stale());
    c.advance(5000); c.set_sntp(1762560000ULL); ts.poll();
    TEST_ASSERT_TRUE(ts.valid());
    TEST_ASSERT_EQUAL(1762560000ULL, ts.unix_s());
    c.advance(10000); ts.poll();                                          // SNTP agrees (+10 s)
    TEST_ASSERT_EQUAL(1762560010ULL, ts.unix_s());
    TEST_ASSERT_EQUAL(0, (int)ts.steps());
    c.set_sntp(1762560100ULL); ts.poll();                                 // 90 s step from SNTP
    TEST_ASSERT_EQUAL(1, (int)ts.steps());
    TEST_ASSERT_EQUAL(1762560100ULL, ts.unix_s());
    TEST_ASSERT_FALSE(ts.stale());
}

// ------------------------------------------------------------------ node app integration
void test_app_publishes_telemetry_at_1hz_with_sequence() {
    MockHal m; m.clock.set_sntp(1762560000ULL);
    g_ring.clear();
    NodeApp app(m.hal, g_ring);
    app.provision("ben20-0007", "node3", true);
    app.begin();
    TEST_ASSERT_EQUAL_STRING("ben/ben20-0007/node/node3/cmd", m.net.subscriptions.back().c_str());
    fill_example(app.channels());
    for (int i = 0; i < 3000; i += 100) { app.tick(); m.clock.advance(100); }
    TEST_ASSERT_EQUAL(3, (int)m.net.count_on("/telemetry"));
    TEST_ASSERT_EQUAL(3, (int)app.seq());
    const auto* last = m.net.last_on("/telemetry");
    TEST_ASSERT_EQUAL_STRING("ben/ben20-0007/node/node3/telemetry", last->topic.c_str());
    TEST_ASSERT_NOT_NULL(strstr(last->payload.c_str(), "\"ts\":1762560002,\"seq\":3,"));
    TEST_ASSERT_NOT_NULL(strstr(last->payload.c_str(), "\"cal_id\":\"c-2026-11-07-01\""));
    const auto* st = m.net.last_on("/status");
    TEST_ASSERT_NOT_NULL(st); TEST_ASSERT_TRUE(st->retain);
    TEST_ASSERT_NOT_NULL(strstr(st->payload.c_str(), "\"fw\":\"1.0.0\""));
    TEST_ASSERT_EQUAL_STRING("ben20-0007", m.nvs.s["unit"].c_str());
}

void test_app_buffers_while_offline_and_replays_in_order() {
    MockHal m; m.clock.set_sntp(1762560000ULL);
    g_ring.clear();
    NodeApp app(m.hal, g_ring); app.begin();
    fill_example(app.channels());
    app.tick(); m.clock.advance(1000);                                    // seq 1 live
    m.net.up = false;
    for (int i = 0; i < 90; ++i) { app.tick(); m.clock.advance(1000); }   // 90 s offline -> seq 2..91 buffered
    TEST_ASSERT_EQUAL(90, (int)g_ring.size());
    TEST_ASSERT_TRUE(app.gateway_lost());                                 // > 60 s: failsafe active
    TEST_ASSERT_EQUAL(1, (int)m.net.count_on("/telemetry"));
    m.net.up = true;
    size_t before = m.net.published.size();
    for (int i = 0; i < 6; ++i) { app.tick(); m.clock.advance(1000); }    // 6 ticks x 20 replay = 120 > 90 + 6 live
    TEST_ASSERT_TRUE(g_ring.empty());
    TEST_ASSERT_FALSE(app.gateway_lost());
    // every telemetry message after reconnect carries increasing seq, starting at 2
    uint32_t expect = 2;
    for (size_t i = before; i < m.net.published.size(); ++i) {
        const auto& msg = m.net.published[i];
        if (msg.topic.find("/telemetry") == std::string::npos) continue;
        char key[32]; snprintf(key, sizeof key, "\"seq\":%u,", expect);
        char why[200]; snprintf(why, sizeof why, "expected %s in %s", key, msg.payload.c_str());
        TEST_ASSERT_TRUE_MESSAGE(strstr(msg.payload.c_str(), key) != nullptr, why);
        ++expect;
    }
    TEST_ASSERT_EQUAL(98, (int)expect);                                   // 2..97 delivered (90 buffered + 6 live)
    // While a backlog exists, live samples are appended to it so order is preserved:
    // 5 ticks drain 90 + 5 appended records (20 per tick), the 6th publishes live.
    TEST_ASSERT_EQUAL(95, (int)app.replayed_total());
    // replayed records carry their original timestamps, an empty raw block and a replay marker
    const auto& first_replay = m.net.published[before];
    TEST_ASSERT_NOT_NULL(strstr(first_replay.payload.c_str(), "\"ts\":1762560001,\"seq\":2,"));
    TEST_ASSERT_NOT_NULL(strstr(first_replay.payload.c_str(), "\"raw\":{},\"cal_id\":\"c-2026-11-07-01\",\"replay\":true}"));
    TEST_ASSERT_NOT_NULL(strstr(first_replay.payload.c_str(), "\"T_in_1\":21.4,"));
    TEST_ASSERT_NULL(strstr(first_replay.payload.c_str(), "pulse_kwh"));                 // never sampled -> omitted
    const auto* live = m.net.last_on("/telemetry");
    TEST_ASSERT_NULL(strstr(live->payload.c_str(), "replay"));
}

void test_app_handles_cmd_and_acks_and_resets_contact_timer() {
    MockHal m; g_ring.clear();
    NodeApp app(m.hal, g_ring); app.begin();
    fill_example(app.channels());
    m.net.inject("ben/unit0/node/node0/cmd", "{\"id\":\"abc\",\"op\":\"set_output\",\"out\":\"relay1\",\"value\":1}");
    const auto* ack = m.net.last_on("/ack");
    TEST_ASSERT_NOT_NULL(ack);
    TEST_ASSERT_EQUAL_STRING("ben/unit0/node/node0/ack", ack->topic.c_str());
    TEST_ASSERT_NOT_NULL(strstr(ack->payload.c_str(), "\"id\":\"abc\",\"ok\":true"));
    TEST_ASSERT_TRUE(m.gpio.read(RELAYS[0].pin));
    m.net.inject("ben/unit0/node/node9/cmd", "{\"id\":\"zzz\",\"op\":\"reboot\"}");   // someone else's node
    TEST_ASSERT_FALSE(app.reboot_requested());
    TEST_ASSERT_EQUAL(1, (int)m.net.count_on("/ack"));
    m.net.inject("ben/unit0/node/node0/cmd", "{\"id\":\"r\",\"op\":\"reboot\"}");
    TEST_ASSERT_TRUE(app.reboot_requested());
    m.net.inject("ben/unit0/node/node0/cmd", "{{{");
    TEST_ASSERT_NOT_NULL(strstr(m.net.last_on("/ack")->payload.c_str(), "\"ok\":false"));
}

void test_app_dip_provisioning() {
    MockHal m; g_ring.clear();
    NodeApp app(m.hal, g_ring);
    app.provision("ben10-0002", "nodeX", true);
    app.provision_from_dip(0x0B);
    TEST_ASSERT_EQUAL_STRING("node11", app.identity().node_id);
    TEST_ASSERT_EQUAL_STRING("ben10-0002", app.identity().unit);
    NodeApp app2(m.hal, g_ring); app2.begin();                           // reads persisted unit; node id from NVS was "nodeX"
    TEST_ASSERT_EQUAL_STRING("ben10-0002", app2.identity().unit);
    TEST_ASSERT_TRUE(app2.identity().provisioned);
}

void test_app_status_reports_errors_when_unsynced() {
    MockHal m; g_ring.clear();
    NodeApp app(m.hal, g_ring); app.begin();
    app.tick();
    const auto* st = m.net.last_on("/status");
    TEST_ASSERT_NOT_NULL(st);
    TEST_ASSERT_NOT_NULL(strstr(st->payload.c_str(), "\"errors\":[\"clock not synced\"]"));
    TEST_ASSERT_NOT_NULL(strstr(st->payload.c_str(), "\"clock_valid\":false"));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_calibration_apply_gain_offset);
    RUN_TEST(test_calibration_rejects_bad_values);
    RUN_TEST(test_calibration_digital_passthrough);
    RUN_TEST(test_calibration_nvs_roundtrip);
    RUN_TEST(test_cal_id_truncation);
    RUN_TEST(test_tare_zeroes_dp);
    RUN_TEST(test_tare_respects_gain_and_rejects_untareable);
    RUN_TEST(test_telemetry_json_matches_protocol);
    RUN_TEST(test_telemetry_json_calibrated_values_and_omits_missing);
    RUN_TEST(test_telemetry_json_overflow_returns_zero);
    RUN_TEST(test_telemetry_full_channel_set_fits_in_msg_cap);
    RUN_TEST(test_status_json_matches_protocol);
    RUN_TEST(test_topic_builder);
    RUN_TEST(test_json_writer_escapes_and_trims);
    RUN_TEST(test_parse_set_output);
    RUN_TEST(test_parse_set_cal_and_tare_and_ota);
    RUN_TEST(test_parse_malformed_inputs);
    RUN_TEST(test_parse_tolerates_unknown_and_nested_fields);
    RUN_TEST(test_parse_oversized_string_truncates_safely);
    RUN_TEST(test_ack_set_output);
    RUN_TEST(test_ack_error_shape);
    RUN_TEST(test_ack_set_cal_persists_and_get_cal_reads_back);
    RUN_TEST(test_ack_tare);
    RUN_TEST(test_ack_identify_reboot_ota);
    RUN_TEST(test_ring_record_size_and_pack_unpack);
    RUN_TEST(test_ring_wraps_and_keeps_newest);
    RUN_TEST(test_ring_capacity_is_one_hour);
    RUN_TEST(test_failsafe_drops_only_failsafe_outputs_after_60s);
    RUN_TEST(test_failsafe_on_link_down_and_wraparound);
    RUN_TEST(test_failsafe_commands_during_loss_apply_on_restore);
    RUN_TEST(test_alarm_thresholds_with_hold_time);
    RUN_TEST(test_timesync_anchor_and_steps);
    RUN_TEST(test_app_publishes_telemetry_at_1hz_with_sequence);
    RUN_TEST(test_app_buffers_while_offline_and_replays_in_order);
    RUN_TEST(test_app_handles_cmd_and_acks_and_resets_contact_timer);
    RUN_TEST(test_app_dip_provisioning);
    RUN_TEST(test_app_status_reports_errors_when_unsynced);
    return UNITY_END();
}
