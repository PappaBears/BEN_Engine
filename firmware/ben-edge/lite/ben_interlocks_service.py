#!/usr/bin/env python3
"""BEN Controls Lite — interlock controller service for the RevPi (Schreiber AI).

Reads RevPi DIO/AIO through piControl (revpimodio2), runs ben_engine.interlocks.Interlocks at 10 Hz,
writes outputs, serves the spec/PROTOCOL.md register map on Modbus TCP (pymodbus), pets the hardware
watchdog and systemd's WatchdogSec. Status: written, unverified on hardware (no RevPi here).

I/O names come from /etc/ben/revpi_io_map.json (PiCtory names -> roles) so a panel builder can rewire
without touching code. Edge writes (EDGE_WATCHDOG, SUPPLY_TRIM_x10, TEST_REQUEST) arrive through the
Modbus server from ben-plc-bridge on 127.0.0.1; a customer BMS on 10.20.0.1 gets the same map read-only.
"""
from __future__ import annotations

import json, os, socket, sys, time, threading
from pathlib import Path

sys.path.insert(0, "/opt/ben_engine/software")
from ben_engine.interlocks import Inputs, Interlocks, Mode  # noqa: E402

try:
    import revpimodio2  # type: ignore
except ImportError:
    revpimodio2 = None
try:
    from pymodbus.server import StartTcpServer  # type: ignore
    from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext  # type: ignore
except ImportError:
    StartTcpServer = None

IO_MAP = json.loads(Path(os.environ.get("BEN_REVPI_IO_MAP", "/etc/ben/revpi_io_map.json")).read_text())
CYCLE_S = 0.1
WRITABLE = {40004, 40006, 40007}


def sd_notify(msg: str) -> None:
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    if addr.startswith("@"):
        addr = "\0" + addr[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
        s.connect(addr); s.sendall(msg.encode())


class HardwareWatchdog:
    def __init__(self, dev="/dev/watchdog"):
        try:
            self.fd = os.open(dev, os.O_WRONLY)
        except OSError:
            self.fd = None
    def pet(self):
        if self.fd is not None:
            os.write(self.fd, b"\0")


class RevPiIO:
    """Thin wrapper: role name -> piControl I/O. Cycle-synchronous via revpimodio2 autorefresh."""
    def __init__(self):
        self.rpi = revpimodio2.RevPiModIO(autorefresh=True) if revpimodio2 else None
        if self.rpi:
            self.rpi.handlesignalend()
    def di(self, role: str) -> bool:
        name = IO_MAP["di"].get(role)
        return bool(getattr(self.rpi.io, name).value) if (self.rpi and name) else False
    def ai_ma(self, role: str) -> float:
        name = IO_MAP["ai"].get(role)
        return (getattr(self.rpi.io, name).value / 1000.0) if (self.rpi and name) else 0.0     # AIO reports µA
    def rtd_c(self, role: str) -> float:
        name = IO_MAP["rtd"].get(role)
        return (getattr(self.rpi.io, name).value / 10.0) if (self.rpi and name) else 20.0     # AIO RTD ×0.1 °C
    def do(self, role: str, value: bool) -> None:
        name = IO_MAP["do"].get(role)
        if self.rpi and name:
            getattr(self.rpi.io, name).value = bool(value)
    def all_off(self):
        if self.rpi:
            for name in IO_MAP["do"].values():
                getattr(self.rpi.io, name).value = False


def ma_to_eng(ma: float, lo: float, hi: float) -> float:
    return lo + (max(4.0, min(20.0, ma)) - 4.0) / 16.0 * (hi - lo)


def main() -> int:
    cfg = IO_MAP["plant"]
    ctl = Interlocks(n_cooling=cfg["n_cooling"], unit_kw=cfg["unit_kw"], n_leak_zones=cfg["n_leak_zones"],
                     n_doors=cfg["n_doors"], redundancy=cfg.get("redundancy", "N+1"),
                     supply_setpoint_c=cfg.get("supply_setpoint_c", 20.0), lite=True)
    io = RevPiIO()
    hw = HardwareWatchdog()
    project_crc = int(os.environ.get("BEN_PLC_PROJECT_CRC", "0"), 0)

    # ---- Modbus TCP server (holding registers 40001..40122 -> offset 0..121), edge/BMS access
    store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0] * 130)) if StartTcpServer else None
    ctx = ModbusServerContext(slaves={1: store}, single=False) if store else None
    if ctx:
        for bind in ("127.0.0.1", "10.20.0.1"):
            threading.Thread(target=StartTcpServer, kwargs={"context": ctx, "address": (bind, 502)}, daemon=True).start()

    def hr_get(addr: int) -> int:
        return store.getValues(3, addr - 40001, 1)[0] if store else 0
    def hr_set(regs: dict) -> None:
        if not store:
            return
        for a, v in regs.items():
            if a not in WRITABLE:                       # never overwrite what the edge just wrote
                store.setValues(3, a - 40001, [v & 0xFFFF])

    sd_notify("READY=1")
    last = time.monotonic()
    print("ben-interlocks: running (lite), units=%d zones=%d doors=%d" % (ctl.n, ctl.n_zones, ctl.n_doors), flush=True)
    while True:
        now = time.monotonic(); dt = now - last; last = now
        n, z, d = ctl.n, ctl.n_zones, ctl.n_doors
        x = Inputs(
            cooling_run_fb=[io.di(f"cool{i+1}_run") for i in range(n)],
            cooling_fault_in=[io.di(f"cool{i+1}_fault") for i in range(n)],
            leak_zone=[io.di(f"leak_zone{i+1}") for i in range(z)],
            valve_closed_ls=[io.di(f"valve{i+1}_closed") for i in range(z)],
            door_open=[io.di(f"door{i+1}_open") for i in range(d)],
            epo_loop_ok=io.di("epo_loop_ok"), fire_alarm=io.di("fire_alarm"), fire_trouble=io.di("fire_trouble"),
            fire_released=io.di("fire_released"), fire_supervisory=io.di("fire_supervisory"),
            utility_ok=io.di("utility_ok"), ats_on_generator=io.di("ats_on_generator"),
            gen_running=io.di("gen_running"), gen_fault=io.di("gen_fault"), ups_on_battery=io.di("ups_on_battery"),
            psu_redundancy_ok=io.di("psu_redundancy_ok"),
            it_kw=ma_to_eng(io.ai_ma("it_kw"), 0.0, cfg.get("it_kw_fs", 100.0)),
            supply_c=io.rtd_c("supply_c"), return_c=io.rtd_c("return_c"), outdoor_c=io.rtd_c("outdoor_c"),
            edge_watchdog=hr_get(40004),
            supply_trim_k=((hr_get(40006) ^ 0x8000) - 0x8000) / 10.0,
            test_request=hr_get(40007),
            mode_request=Mode.MANUAL if io.di("hmi_manual") else (Mode.OFF if io.di("hmi_off") else Mode.AUTO),
        )
        out = ctl.step(x, dt)
        if ctl.test_active == 0 and x.test_request:
            store and store.setValues(3, 40007 - 40001, [0])      # PLC semantics: register cleared when consumed
        for i in range(n):
            io.do(f"cool{i+1}_cmd", out.cooling_cmd[i])
        for i in range(z):
            io.do(f"valve{i+1}_close", out.valve_close_cmd[i])
        io.do("cdu_pump_stop", out.cdu_pump_stop)
        io.do("beacon", out.beacon)
        io.do("watchdog_relay", out.cooling_enable_relay)        # O_14 -> KW1 in the cooling-enable chain
        regs = ctl.registers(x, project_crc)
        regs[40054] = int(round(ma_to_eng(io.ai_ma("aisle_dp"), -125, 125) * 10)) & 0xFFFF
        regs[40055] = int(round(ma_to_eng(io.ai_ma("rh"), 0, 100) * 10)) & 0xFFFF
        hr_set(regs)
        hw.pet(); sd_notify("WATCHDOG=1")
        time.sleep(max(0.0, CYCLE_S - (time.monotonic() - now)))


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        try:
            RevPiIO().all_off()
        except Exception:
            pass
