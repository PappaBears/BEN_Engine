"""PLC ↔ edge bridge for the BEN Controller.

Polls the controller's Modbus TCP holding registers (the map in firmware/ben-plc/modbus_map.csv,
served by the PLCnext on BEN Controls Pro or by the software controller on BEN Controls Lite),
scales them, publishes them as BEN protocol telemetry/status under node ids ``plc1..plcN``,
and writes the three writable registers (EDGE_WATCHDOG, SUPPLY_TRIM_x10, TEST_REQUEST).

No third-party dependency: a minimal Modbus TCP client (FC3 read holding registers, FC6/FC16
write) is implemented on sockets. MQTT publishing uses paho-mqtt when it is installed; without
it, snapshots go to a callback and to the log. ``--sim`` runs an in-process Modbus server backed by
:class:`ben_engine.interlocks.Interlocks` so the bridge can be exercised with no hardware.
"""
from __future__ import annotations

import csv
import json
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = REPO_ROOT / "firmware" / "ben-plc" / "modbus_map.csv"


# ----------------------------------------------------------------------------- register map
@dataclass
class Register:
    address: int
    name: str
    type: str
    rw: str
    scale: float
    unit: str
    description: str

    @property
    def offset(self) -> int:
        return self.address - 40001


def load_map(path: Path | str = MAP_PATH) -> List[Register]:
    regs: List[Register] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                scale = float(row.get("scale") or 1)
            except ValueError:
                scale = 1.0
            regs.append(Register(int(row["address"]), row["name"], row.get("type", "uint16"), row.get("rw", "R").upper(),
                                 scale, row.get("unit", ""), row.get("description", "")))
    regs.sort(key=lambda r: r.address)
    return regs


def decode(reg: Register, raw: int) -> Any:
    if reg.type == "int16" and raw >= 0x8000:
        raw -= 0x10000
    if reg.type == "bits":
        return raw
    if reg.type == "enum":
        return raw
    if reg.scale and reg.scale != 1:
        return raw / reg.scale
    return raw


# ----------------------------------------------------------------------------- Modbus TCP client
class ModbusError(RuntimeError):
    pass


class ModbusTcpClient:
    """Minimal Modbus TCP master: FC3 read holding registers, FC6 write single, FC16 write multiple."""

    def __init__(self, host: str, port: int = 502, unit_id: int = 1, timeout: float = 2.0):
        self.host, self.port, self.unit_id, self.timeout = host, port, unit_id, timeout
        self._sock: Optional[socket.socket] = None
        self._tid = 0

    def connect(self):
        self.close()
        s = socket.create_connection((self.host, self.port), timeout=self.timeout)
        s.settimeout(self.timeout)
        self._sock = s

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def _xfer(self, pdu: bytes) -> bytes:
        if self._sock is None:
            self.connect()
        assert self._sock is not None
        self._tid = (self._tid + 1) & 0xFFFF
        adu = struct.pack(">HHHB", self._tid, 0, len(pdu) + 1, self.unit_id) + pdu
        self._sock.sendall(adu)
        hdr = self._recv(7)
        tid, _proto, length, _uid = struct.unpack(">HHHB", hdr)
        body = self._recv(length - 1)
        if tid != self._tid:
            raise ModbusError("transaction id mismatch")
        if body[0] & 0x80:
            raise ModbusError(f"exception code {body[1]} for function {body[0] & 0x7F}")
        return body

    def _recv(self, n: int) -> bytes:
        assert self._sock is not None
        buf = b""
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ModbusError("connection closed")
            buf += chunk
        return buf

    def read_holding(self, offset: int, count: int) -> List[int]:
        body = self._xfer(struct.pack(">BHH", 3, offset, count))
        nbytes = body[1]
        return list(struct.unpack(">" + "H" * (nbytes // 2), body[2:2 + nbytes]))

    def write_single(self, offset: int, value: int):
        self._xfer(struct.pack(">BHH", 6, offset, value & 0xFFFF))

    def write_multiple(self, offset: int, values: List[int]):
        payload = struct.pack(">BHHB", 16, offset, len(values), 2 * len(values)) + struct.pack(">" + "H" * len(values), *[v & 0xFFFF for v in values])
        self._xfer(payload)


# ----------------------------------------------------------------------------- simulation server
class SimModbusServer:
    """In-process Modbus TCP slave serving the Interlocks register image (BEN Controls Lite behaviour).

    Used by ``--sim`` and by the tests. Writable registers are applied to the interlock inputs:
    EDGE_WATCHDOG → ``Inputs.edge_watchdog``, SUPPLY_TRIM_x10 → ``supply_trim_k``, TEST_REQUEST → test request.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 0, n_cooling: int = 4, unit_kw: float = 35.0, lite: bool = True):
        from .interlocks import Interlocks, Inputs
        self.il = Interlocks(n_cooling=n_cooling, unit_kw=unit_kw, n_leak_zones=2, n_doors=1, lite=lite)
        self.x = Inputs(cooling_run_fb=[True, True, True, False], cooling_fault_in=[False] * 4, leak_zone=[False, False],
                        valve_closed_ls=[False, False], door_open=[False], it_kw=96.0)
        self.x.cooling_run_fb = [True] * min(n_cooling, 3) + [False] * max(0, n_cooling - 3)
        self.x.cooling_fault_in = [False] * n_cooling
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((host, port))
        self._srv.listen(4)
        self.port = self._srv.getsockname()[1]
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self.writes: List[tuple] = []

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        try:
            self._srv.close()
        except OSError:
            pass

    def tick(self, dt: float = 1.0):
        with self._lock:
            self.il.step(self.x, dt)

    def _image(self) -> Dict[int, int]:
        with self._lock:
            return self.il.registers(self.x, project_crc=0xBE11)

    def _serve(self):
        self._srv.settimeout(0.5)
        while not self._stop.is_set():
            try:
                conn, _ = self._srv.accept()
            except (socket.timeout, OSError):
                continue
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket):
        conn.settimeout(5.0)
        try:
            while not self._stop.is_set():
                hdr = conn.recv(7)
                if len(hdr) < 7:
                    return
                tid, proto, length, uid = struct.unpack(">HHHB", hdr)
                body = conn.recv(length - 1)
                fc = body[0]
                if fc == 3:
                    off, cnt = struct.unpack(">HH", body[1:5])
                    img = self._image()
                    vals = [img.get(40001 + off + i, 0) & 0xFFFF for i in range(cnt)]
                    pdu = struct.pack(">BB", 3, 2 * cnt) + struct.pack(">" + "H" * cnt, *vals)
                elif fc in (6, 16):
                    if fc == 6:
                        off, val = struct.unpack(">HH", body[1:5]); vals = [val]
                    else:
                        off, cnt, nb = struct.unpack(">HHB", body[1:6]); vals = list(struct.unpack(">" + "H" * cnt, body[6:6 + nb]))
                    self._apply_writes(off, vals)
                    pdu = body[:5]
                else:
                    pdu = struct.pack(">BB", fc | 0x80, 1)
                conn.sendall(struct.pack(">HHHB", tid, proto, len(pdu) + 1, uid) + pdu)
        except (socket.timeout, OSError, struct.error):
            return
        finally:
            conn.close()

    def _apply_writes(self, off: int, vals: List[int]):
        with self._lock:
            for i, v in enumerate(vals):
                addr = 40001 + off + i
                self.writes.append((addr, v))
                if addr == 40004:
                    self.x.edge_watchdog = v
                elif addr == 40006:
                    sv = v - 0x10000 if v >= 0x8000 else v
                    self.x.supply_trim_k = sv / 10.0
                elif addr == 40007:
                    self.x.test_request = v


# ----------------------------------------------------------------------------- bridge
@dataclass
class Snapshot:
    ts: float
    values: Dict[str, Any]
    raw: Dict[str, int]
    ok: bool
    error: str = ""
    seq: int = 0


class PlcBridge:
    """Poll the controller, decode the map, publish. ``publish`` receives (topic, payload_dict)."""

    def __init__(self, host: str, port: int = 502, unit: str = "unit1", map_path: Path | str = MAP_PATH,
                 publish: Optional[Callable[[str, Dict[str, Any]], None]] = None, node_id: str = "plc1"):
        self.regs = load_map(map_path)
        self.by_name = {r.name: r for r in self.regs}
        self.client = ModbusTcpClient(host, port)
        self.unit, self.node_id = unit, node_id
        self.publish = publish or (lambda t, p: None)
        self.seq = 0
        self.watchdog = 0
        self.last: Optional[Snapshot] = None
        self.fw = "plc-bridge 1.0.0"
        lo, hi = self.regs[0].offset, self.regs[-1].offset
        self._span = (lo, hi - lo + 1)

    # -- one cycle -------------------------------------------------------------------------
    def poll(self) -> Snapshot:
        self.seq += 1
        try:
            lo, count = self._span
            raw_block: List[int] = []
            for start in range(lo, lo + count, 100):
                raw_block += self.client.read_holding(start, min(100, lo + count - start))
            raw = {r.name: raw_block[r.offset - lo] for r in self.regs if 0 <= r.offset - lo < len(raw_block)}
            values = {r.name: decode(r, raw[r.name]) for r in self.regs if r.name in raw}
            snap = Snapshot(time.time(), values, raw, True, seq=self.seq)
        except (OSError, ModbusError) as e:
            self.client.close()
            snap = Snapshot(time.time(), {}, {}, False, error=f"{type(e).__name__}: {e}", seq=self.seq)
        self.last = snap
        self._emit(snap)
        return snap

    def kick_watchdog(self):
        self.watchdog = (self.watchdog + 1) & 0xFFFF
        self.client.write_single(self.by_name["EDGE_WATCHDOG"].offset, self.watchdog)

    def set_supply_trim(self, trim_k: float):
        self.client.write_single(self.by_name["SUPPLY_TRIM_x10"].offset, int(round(trim_k * 10)))

    def request_test(self, code: int):
        self.client.write_single(self.by_name["TEST_REQUEST"].offset, code)

    def _emit(self, snap: Snapshot):
        base = f"ben/{self.unit}/node/{self.node_id}"
        if snap.ok:
            self.publish(f"{base}/telemetry", {"ts": snap.ts, "seq": snap.seq, "ch": snap.values, "raw": snap.raw, "cal_id": "plc-map"})
            self.publish(f"ben/{self.unit}/plc/interlocks", {"ts": snap.ts, **{k: v for k, v in snap.values.items() if k.startswith(("PLC_", "COOL", "LEAK", "VALVE", "DOOR", "EPO", "FIRE", "ATS", "GEN", "UPS", "EDGE", "FAIL"))}})
        self.publish(f"{base}/status", {"fw": self.fw, "device": "plc-bridge", "ok": snap.ok, "error": snap.error, "ts": snap.ts,
                                       "mode": snap.values.get("PLC_MODE"), "lite": bool((snap.raw.get("PLC_MODE", 0) & 0x100)) if snap.ok else None})

    # -- loop ----------------------------------------------------------------------------------
    def run(self, period_s: float = 1.0, cycles: Optional[int] = None, on_cycle: Optional[Callable[[Snapshot], None]] = None):
        n = 0
        while cycles is None or n < cycles:
            t0 = time.time()
            snap = self.poll()
            if snap.ok:
                try:
                    self.kick_watchdog()
                except (OSError, ModbusError):
                    pass
            if on_cycle:
                on_cycle(snap)
            n += 1
            time.sleep(max(0.0, period_s - (time.time() - t0)))


def mqtt_publisher(host: str, port: int = 1883, cafile: Optional[str] = None, certfile: Optional[str] = None, keyfile: Optional[str] = None):
    """Return a publish(topic, dict) callable backed by paho-mqtt, or None when paho is not installed."""
    try:
        import paho.mqtt.client as mqtt  # type: ignore
    except ImportError:
        return None
    c = mqtt.Client(client_id="ben-plc-bridge", protocol=mqtt.MQTTv311)
    if cafile:
        c.tls_set(ca_certs=cafile, certfile=certfile, keyfile=keyfile)
    c.connect(host, port, keepalive=30)
    c.loop_start()
    return lambda topic, payload: c.publish(topic, json.dumps(payload), qos=0, retain=topic.endswith("/status"))


def main(argv=None) -> int:
    import argparse, os
    ap = argparse.ArgumentParser(description="BEN Controller PLC ↔ MQTT bridge (Modbus TCP register map → BEN protocol)")
    ap.add_argument("--host", default=os.environ.get("BEN_PLC_IP", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("BEN_PLC_PORT", "502")))
    ap.add_argument("--unit", default=os.environ.get("BEN_UNIT", "unit1"))
    ap.add_argument("--mqtt", default=os.environ.get("BEN_MQTT_HOST", ""), help="broker host; empty = log only")
    ap.add_argument("--mqtt-port", type=int, default=int(os.environ.get("BEN_MQTT_PORT", "1883")))
    ap.add_argument("--cafile", default=os.environ.get("BEN_MQTT_CA"))
    ap.add_argument("--certfile", default=os.environ.get("BEN_MQTT_CERT"))
    ap.add_argument("--keyfile", default=os.environ.get("BEN_MQTT_KEY"))
    ap.add_argument("--period", type=float, default=1.0)
    ap.add_argument("--cycles", type=int, default=None, help="stop after N cycles (tests/demos)")
    ap.add_argument("--sim", action="store_true", help="run against an in-process simulated controller")
    a = ap.parse_args(argv)
    sim = None
    if a.sim:
        sim = SimModbusServer(port=0).start()
        a.host, a.port = "127.0.0.1", sim.port
        print(f"simulated BEN Controls Lite controller on 127.0.0.1:{sim.port}")
    pub = mqtt_publisher(a.mqtt, a.mqtt_port, a.cafile, a.certfile, a.keyfile) if a.mqtt else None
    if a.mqtt and pub is None:
        print("paho-mqtt not installed; logging only")

    def log(topic, payload):
        if pub:
            pub(topic, payload)
        if topic.endswith("/interlocks"):
            print(json.dumps({k: payload[k] for k in list(payload)[:8]}))

    br = PlcBridge(a.host, a.port, a.unit, publish=log)

    def on_cycle(snap: Snapshot):
        if sim:
            sim.tick(a.period)
        if not snap.ok:
            print("poll failed:", snap.error)

    try:
        br.run(a.period, a.cycles, on_cycle)
    except KeyboardInterrupt:
        pass
    finally:
        if sim:
            sim.stop()
    return 0 if (br.last and br.last.ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
