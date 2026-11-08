import os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.plc_bridge import SimModbusServer, PlcBridge, load_map, ModbusTcpClient, ModbusError
import pytest


@pytest.fixture
def sim():
    s = SimModbusServer(port=0).start()
    yield s
    s.stop()


def test_map_loads_and_has_writable_trio():
    regs = load_map()
    names = {r.name: r for r in regs}
    assert {"PLC_HEARTBEAT", "PLC_MODE", "EDGE_WATCHDOG", "SUPPLY_TRIM_x10", "TEST_REQUEST"} <= set(names)
    assert [r.name for r in regs if r.rw == "W"] == ["EDGE_WATCHDOG", "SUPPLY_TRIM_x10", "TEST_REQUEST"]


def test_bridge_polls_decodes_and_publishes(sim):
    got = []
    br = PlcBridge("127.0.0.1", sim.port, unit="t1", publish=lambda t, p: got.append((t, p)))
    sim.tick(1.0)
    snap = br.poll()
    assert snap.ok, snap.error
    assert snap.values["PLC_MODE"] & 0x100  # Lite bit
    assert snap.raw["PLC_PROJECT_CRC"] == 0xBE11
    topics = [t for t, _ in got]
    assert "ben/t1/node/plc1/telemetry" in topics and "ben/t1/plc/interlocks" in topics and "ben/t1/node/plc1/status" in topics
    status = dict(got)["ben/t1/node/plc1/status"]
    assert status["ok"] is True and status["lite"] is True


def test_watchdog_and_trim_writes_reach_controller(sim):
    br = PlcBridge("127.0.0.1", sim.port, publish=lambda t, p: None)
    br.poll()
    br.kick_watchdog(); br.kick_watchdog()
    br.set_supply_trim(-1.5)
    time.sleep(0.05)
    assert (40004, 2) in sim.writes
    assert sim.x.edge_watchdog == 2
    assert abs(sim.x.supply_trim_k + 1.5) < 1e-9
    snap = br.poll()
    assert snap.raw["EDGE_WATCHDOG"] == 2


def test_failover_visible_through_bridge(sim):
    br = PlcBridge("127.0.0.1", sim.port, publish=lambda t, p: None)
    before = br.poll().values["COOLING_CMD"] if "COOLING_CMD" in br.by_name else None
    # fail the lead unit at the controller, step a few seconds, standby must be commanded on
    sim.x.cooling_fault_in[0] = True
    sim.x.cooling_run_fb[0] = False
    for _ in range(8):
        sim.tick(1.0)
    snap = br.poll()
    cmd = next(v for k, v in snap.raw.items() if k.startswith("COOL") and "CMD" in k)
    assert cmd & 0b1000  # unit 4 (standby) commanded on
    assert br.last.ok


def test_connection_failure_is_reported_not_raised():
    br = PlcBridge("127.0.0.1", 1, publish=lambda t, p: None)  # nothing listens on port 1
    snap = br.poll()
    assert snap.ok is False and snap.error


def test_client_rejects_bad_function(sim):
    c = ModbusTcpClient("127.0.0.1", sim.port)
    with pytest.raises(ModbusError):
        c._xfer(b"\x2b\x00\x00")
