"""Virtual BEN nodes: in-process objects that speak the PROTOCOL.md telemetry/cmd/ack JSON.

Used by the dashboard I/O test (simulation mode), by commissioning in ``--sim`` mode and by the
firmware protocol contract tests. No broker is needed: ``poll()`` returns the telemetry payload a
real node would publish and ``command(dict)`` returns the ack a real node would send. If
``paho-mqtt`` is importable, ``MqttPublisher`` can push the same payloads to a real broker.

Node assignment: ``node1`` is the room node (supply/return reference, RH, aisle ΔP, leak, door,
4–20 mA meter input, S0 pulse counter, relays). ``node2..`` each carry two racks
(``T_in_1/2`` = rack A inlet at two heights, ``T_in_3/4`` = rack B, ``T_out_1..4`` likewise).

Raw values follow the sensor interfaces: DS18B20 raw is 1/16 °C counts, SHT45 raw is the 16-bit
ticks of the datasheet formulas, SDP810 raw is Pa x 240 (scale factor for the 125 Pa part),
ADS1115 raw is counts at ±4.096 V (125 µV/LSB) across the 165 Ω shunt. Calibration (``gain``,
``offset``) is applied to the engineering value exactly as the firmware does:
``value = gain * raw_eng + offset``.
"""
from __future__ import annotations

import random
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

FW_VERSION = "1.0.0-sim"
UNIT_DEFAULT = "ben-demo"
RELAYS = ("relay1", "relay2", "relay3", "relay4")
RELAY_FUNCTIONS = {"relay1": "cooling enable", "relay2": "lights", "relay3": "fan boost", "relay4": "spare"}
SHUNT_OHM = 165.0
ADS_LSB_V = 4.096 / 32768.0


def _ds18b20_raw(c: float) -> int:
    return int(round(c * 16.0))


def _sht45_t_raw(c: float) -> int:
    return int(round((c + 45.0) / 175.0 * 65535.0))


def _sht45_rh_raw(rh: float) -> int:
    return int(round((rh + 6.0) / 125.0 * 65535.0))


def _sdp810_raw(pa: float) -> int:
    return int(round(pa * 240.0))


def _ads_raw(ma: float) -> int:
    return int(round(ma / 1000.0 * SHUNT_OHM / ADS_LSB_V))


class SimNode:
    """One virtual BEN Node. ``kind`` is 'room' or 'rack'."""

    def __init__(self, node_id: str, kind: str, rack_indices: Tuple[int, ...] = (), unit: str = UNIT_DEFAULT,
                 seed: int = 0, on_output: Optional[Callable[[str, str, int], None]] = None,
                 total_kw_fullscale: float = 200.0):
        self.node_id = node_id
        self.kind = kind
        self.rack_indices = tuple(rack_indices)
        self.unit = unit
        self.rng = random.Random(f"{seed}-{node_id}")
        self.on_output = on_output
        self.total_kw_fullscale = total_kw_fullscale
        self.seq = 0
        self.uptime_s = 0.0
        self.errors: List[str] = []
        self.outputs: Dict[str, int] = {r: 0 for r in RELAYS}
        self.cal: Dict[str, Dict[str, Any]] = {}
        self.cal_id = "factory"
        self.identify_until_s = 0.0
        self.pulse_count = 0
        self._energy_wh = 0.0
        self._last_t: Optional[float] = None
        self.last_state: Optional[Dict[str, Any]] = None
        self.ip = f"10.77.0.{10 + int(node_id.replace('node', '') or 0)}"

    # ---------------------------------------------------------------- telemetry
    def topic(self, leaf: str) -> str:
        return f"ben/{self.unit}/node/{self.node_id}/{leaf}"

    def _apply_cal(self, ch: str, value: float) -> float:
        c = self.cal.get(ch)
        if not c:
            return value
        return c.get("gain", 1.0) * value + c.get("offset", 0.0)

    def _channels(self, state: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, int]]:
        ch: Dict[str, float] = {}
        raw: Dict[str, int] = {}
        if self.kind == "rack":
            k = 1
            for ri in self.rack_indices:
                if ri < len(state["rack_inlet_c"]):
                    tin = state["rack_inlet_c"][ri]
                    tout = state["rack_outlet_c"][ri]
                    # two heights per rack: top reads slightly warmer (stratification) in the sim
                    for j, dz in enumerate((0.0, 0.4)):
                        raw[f"T_in_{k+j}"] = _ds18b20_raw(tin + dz)
                        raw[f"T_out_{k+j}"] = _ds18b20_raw(tout + dz * 0.5)
                    k += 2
            for name, r in raw.items():
                ch[name] = round(self._apply_cal(name, r / 16.0), 3)
        else:
            raw["T_ref"] = _sht45_t_raw(state["supply_c"])
            raw["RH"] = _sht45_rh_raw(state["rh_pct"])
            raw["dP_aisle"] = _sdp810_raw(state["aisle_dp_pa"])
            raw["T_return"] = _ds18b20_raw(state["return_c"])
            raw["leak"] = int(bool(state.get("leak", False)))
            raw["door"] = int(bool(state.get("door_open", False)))
            kw = state["power"]["utility_kw"]
            ma = 4.0 + 16.0 * max(0.0, min(1.0, kw / self.total_kw_fullscale))
            raw["ai0_mA"] = _ads_raw(ma)
            ch["T_ref"] = round(self._apply_cal("T_ref", -45.0 + 175.0 * raw["T_ref"] / 65535.0), 3)
            ch["RH"] = round(self._apply_cal("RH", -6.0 + 125.0 * raw["RH"] / 65535.0), 2)
            ch["dP_aisle"] = round(self._apply_cal("dP_aisle", raw["dP_aisle"] / 240.0), 3)
            ch["T_return"] = round(self._apply_cal("T_return", raw["T_return"] / 16.0), 3)
            ch["leak"] = raw["leak"]
            ch["door"] = raw["door"]
            ch["ai0_mA"] = round(self._apply_cal("ai0_mA", raw["ai0_mA"] * ADS_LSB_V / SHUNT_OHM * 1000.0), 4)
            # S0 pulse counter: 1 pulse per Wh of utility energy
            t = state.get("t", 0.0)
            if self._last_t is not None and t > self._last_t:
                self._energy_wh += kw * 1000.0 * (t - self._last_t) / 3600.0
            self._last_t = t
            self.pulse_count = int(self._energy_wh)
            ch["pulse_kwh"] = self.pulse_count
            raw["pulse_kwh"] = self.pulse_count
        for r in RELAYS:
            ch[r] = self.outputs[r]
        return ch, raw

    def poll(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Telemetry payload for the given twin state (PROTOCOL.md telemetry topic)."""
        self.last_state = state
        self.seq += 1
        t = float(state.get("t", 0.0))
        self.uptime_s = t
        ch, raw = self._channels(state)
        return {"ts": round(1_762_000_000.0 + t, 3), "seq": self.seq, "ch": ch, "raw": raw, "cal_id": self.cal_id}

    def status(self) -> Dict[str, Any]:
        return {"fw": FW_VERSION, "uptime_s": round(self.uptime_s, 1), "rssi": -55 - int(self.rng.random() * 3),
                "ip": self.ip, "heap": 180_000 - 16 * self.seq % 4000, "errors": list(self.errors),
                "node_id": self.node_id, "kind": self.kind, "racks": [i + 1 for i in self.rack_indices]}

    # ---------------------------------------------------------------- commands
    def command(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a cmd payload and return the ack payload."""
        cid = cmd.get("id") or str(uuid.uuid4())
        op = cmd.get("op")
        try:
            if op == "set_output":
                out = cmd.get("out")
                if out not in RELAYS:
                    return self._nack(cid, f"unknown output {out}")
                val = 1 if int(cmd.get("value", 0)) else 0
                self.outputs[out] = val
                if self.on_output:
                    self.on_output(self.node_id, out, val)
                return self._ack(cid, {"out": out, "value": val, "function": RELAY_FUNCTIONS[out]})
            if op == "get_output":
                return self._ack(cid, {"outputs": dict(self.outputs)})
            if op == "get_cal":
                return self._ack(cid, {"cal_id": self.cal_id, "channels": {k: dict(v) for k, v in self.cal.items()}})
            if op == "set_cal":
                ch = cmd.get("ch")
                if not ch:
                    return self._nack(cid, "missing ch")
                gain = float(cmd.get("gain", 1.0))
                offset = float(cmd.get("offset", 0.0))
                if not (0.5 <= gain <= 2.0):
                    return self._nack(cid, f"gain {gain} outside 0.5–2.0 sanity window")
                self.cal[ch] = {"gain": gain, "offset": offset, "cal_id": cmd.get("cal_id", self.cal_id)}
                self.cal_id = cmd.get("cal_id", self.cal_id)
                return self._ack(cid, {"ch": ch, "gain": gain, "offset": offset, "cal_id": self.cal_id, "stored": "nvs"})
            if op == "tare":
                ch = cmd.get("ch", "dP_aisle")
                if self.last_state is None:
                    return self._nack(cid, "no reading yet")
                raw_ch, _ = self._channels_uncal(self.last_state)
                if ch not in raw_ch:
                    return self._nack(cid, f"channel {ch} not on this node")
                gain = self.cal.get(ch, {}).get("gain", 1.0)
                offset = -gain * raw_ch[ch]
                self.cal[ch] = {"gain": gain, "offset": offset, "cal_id": self.cal_id}
                return self._ack(cid, {"ch": ch, "offset": round(offset, 4), "raw_at_tare": round(raw_ch[ch], 4)})
            if op == "identify":
                self.identify_until_s = self.uptime_s + 30.0
                return self._ack(cid, {"led": "blink 30 s", "node_id": self.node_id})
            if op == "reboot":
                self.uptime_s = 0.0
                self.seq = 0
                return self._ack(cid, {"rebooting": True})
            if op == "ota":
                return self._nack(cid, "OTA not available on a simulated node")
            return self._nack(cid, f"unknown op {op}")
        except (TypeError, ValueError) as e:
            return self._nack(cid, f"bad argument: {e}")

    def _channels_uncal(self, state):
        saved = self.cal
        self.cal = {}
        try:
            return self._channels(state)
        finally:
            self.cal = saved

    @staticmethod
    def _ack(cid: str, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": cid, "ok": True, "result": result}

    @staticmethod
    def _nack(cid: str, error: str) -> Dict[str, Any]:
        return {"id": cid, "ok": False, "error": error}


class NodeFleet:
    """All virtual nodes for one unit: node1 (room) + one node per two racks."""

    def __init__(self, cfg, unit: str = UNIT_DEFAULT, seed: int = 0, on_output=None):
        self.cfg = cfg
        self.unit = unit
        d = cfg.derived()
        fs = max(10.0, d["total_kw"] * 1.25)
        self.nodes: List[SimNode] = [SimNode("node1", "room", (), unit, seed, on_output, fs)]
        racks = list(range(cfg.racks))
        for k in range(0, len(racks), 2):
            nid = f"node{2 + k // 2}"
            self.nodes.append(SimNode(nid, "rack", tuple(racks[k:k + 2]), unit, seed, on_output, fs))
        self.by_id: Dict[str, SimNode] = {n.node_id: n for n in self.nodes}

    def poll_all(self, state: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """(topic, payload) for every node's telemetry message."""
        return [(n.topic("telemetry"), n.poll(state)) for n in self.nodes]

    def status_all(self) -> List[Tuple[str, Dict[str, Any]]]:
        return [(n.topic("status"), n.status()) for n in self.nodes]

    def handle(self, topic: str, payload: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Route a cmd topic to its node; returns (ack_topic, ack) or None if the topic is not ours."""
        parts = topic.split("/")
        if len(parts) != 5 or parts[0] != "ben" or parts[1] != self.unit or parts[2] != "node" or parts[4] != "cmd":
            return None
        node = self.by_id.get(parts[3])
        if node is None:
            return (f"ben/{self.unit}/node/{parts[3]}/ack", {"id": payload.get("id"), "ok": False, "error": "no such node"})
        return (node.topic("ack"), node.command(payload))

    def discover(self) -> List[Dict[str, Any]]:
        return [n.status() for n in self.nodes]


class MqttPublisher:
    """Optional bridge to a real broker. ``available`` is False when paho-mqtt is not installed."""

    def __init__(self, host: str = "localhost", port: int = 1883, client_id: str = "ben-sim"):
        self.available = False
        self.client = None
        try:
            import paho.mqtt.client as mqtt  # type: ignore
        except Exception:
            return
        try:
            self.client = mqtt.Client(client_id=client_id)
            self.client.connect(host, port, keepalive=30)
            self.client.loop_start()
            self.available = True
        except Exception:
            self.client = None
            self.available = False

    def publish(self, topic: str, payload: Dict[str, Any], retain: bool = False) -> bool:
        if not self.available or self.client is None:
            return False
        import json
        self.client.publish(topic, json.dumps(payload), qos=0, retain=retain)
        return True

    def close(self):
        if self.client is not None:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
