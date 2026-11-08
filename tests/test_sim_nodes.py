"""Virtual nodes speak PROTOCOL.md: telemetry shape, cmd/ack semantics, calibration maths."""
from ben_engine.config import Config
from ben_engine.twin import Twin
from ben_engine.sim_nodes import NodeFleet, SimNode, RELAYS, MqttPublisher


def _fleet():
    cfg = Config.preset("ben20")
    tw = Twin(cfg, seed=1)
    for _ in range(30):
        tw.step(1.0)
    return cfg, tw, NodeFleet(cfg, seed=1)


def test_fleet_topology_and_telemetry_shape():
    cfg, tw, fl = _fleet()
    assert fl.nodes[0].kind == "room" and len(fl.nodes) == 1 + (cfg.racks + 1) // 2
    msgs = fl.poll_all(tw.state())
    assert msgs[0][0] == "ben/ben-demo/node/node1/telemetry"
    for topic, p in msgs:
        assert set(p) == {"ts", "seq", "ch", "raw", "cal_id"}
        assert p["seq"] == 1 and isinstance(p["ch"], dict) and isinstance(p["raw"], dict)
    room = msgs[0][1]["ch"]
    for ch in ("T_ref", "RH", "dP_aisle", "leak", "door", "ai0_mA", "pulse_kwh", "relay1"):
        assert ch in room
    rack = msgs[1][1]["ch"]
    assert {"T_in_1", "T_in_2", "T_in_3", "T_in_4", "T_out_1", "T_out_4"} <= set(rack)
    # DS18B20 raw is 1/16 C counts and ch == raw/16 before calibration
    assert abs(rack["T_in_1"] - msgs[1][1]["raw"]["T_in_1"] / 16.0) < 1e-9
    assert 4.0 <= room["ai0_mA"] <= 20.0


def test_commands_and_acks():
    cfg, tw, fl = _fleet()
    st = tw.state()
    fl.poll_all(st)
    t = "ben/ben-demo/node/node2/cmd"
    ack_topic, ack = fl.handle(t, {"id": "a1", "op": "set_output", "out": "relay1", "value": 1})
    assert ack_topic.endswith("/ack") and ack == {"id": "a1", "ok": True, "result": {"out": "relay1", "value": 1, "function": "cooling enable"}}
    _, bad = fl.handle(t, {"id": "a2", "op": "set_output", "out": "relay9", "value": 1})
    assert bad["ok"] is False and "relay9" in bad["error"]
    _, cal_ack = fl.handle(t, {"id": "a3", "op": "set_cal", "ch": "T_in_1", "gain": 1.002, "offset": -0.13, "cal_id": "c-1"})
    assert cal_ack["ok"] and cal_ack["result"]["stored"] == "nvs"
    _, get = fl.handle(t, {"id": "a4", "op": "get_cal"})
    assert get["result"]["channels"]["T_in_1"]["gain"] == 1.002 and get["result"]["cal_id"] == "c-1"
    raw = fl.by_id["node2"].poll(st)
    assert abs(raw["ch"]["T_in_1"] - (1.002 * raw["raw"]["T_in_1"] / 16.0 - 0.13)) < 1e-3
    assert raw["cal_id"] == "c-1"
    _, ident = fl.handle(t, {"op": "identify"})
    assert ident["ok"] and "id" in ident
    _, unk = fl.handle(t, {"id": "x", "op": "fly"})
    assert unk["ok"] is False
    _, ota = fl.handle(t, {"id": "x", "op": "ota", "url": "http://x", "sha256": "0"})
    assert ota["ok"] is False
    assert fl.handle("other/topic", {}) is None
    _, none = fl.handle("ben/ben-demo/node/node77/cmd", {"id": "q", "op": "identify"})
    assert none["ok"] is False


def test_tare_zeroes_pressure_and_contacts_follow_twin():
    cfg, tw, fl = _fleet()
    room = fl.nodes[0]
    st = tw.state()
    before = room.poll(st)["ch"]["dP_aisle"]
    assert abs(before) > 0.5
    _, ack = fl.handle(room.topic("cmd"), {"id": "t", "op": "tare", "ch": "dP_aisle"})
    assert ack["ok"]
    assert abs(room.poll(st)["ch"]["dP_aisle"]) < 1e-6
    tw.inject("door_open")
    tw.step(1.0)
    assert room.poll(tw.state())["ch"]["door"] == 1
    tw.clear("door_open")
    tw.step(1.0)
    assert room.poll(tw.state())["ch"]["door"] == 0


def test_status_and_outputs_callback():
    seen = []
    n = SimNode("node9", "room", on_output=lambda nid, out, v: seen.append((nid, out, v)))
    n.command({"op": "set_output", "out": "relay3", "value": 1})
    assert seen == [("node9", "relay3", 1)]
    s = n.status()
    assert s["fw"] and "uptime_s" in s and isinstance(s["errors"], list)
    assert all(r in n.outputs for r in RELAYS)


def test_mqtt_publisher_optional():
    pub = MqttPublisher(host="127.0.0.1", port=1)
    assert pub.available in (True, False)
    assert pub.publish("x", {}) in (True, False)
    pub.close()
