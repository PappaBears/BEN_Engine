"""BEN Controls interlock state machine — the executable reference (Schreiber AI).

This is the *same* logic that runs:

* on **BEN Controls Lite** (BEN 5 / BEN 30) as a systemd service on the RevPi, driving RevPi DIO/AIO
  through piControl, with the RevPi hardware watchdog relay in the cooling-enable chain;
* on **BEN Controls Pro** (BEN 150/500) as IEC 61131-3 structured text on the PLCnext controller
  (`firmware/ben-plc/BenInterlocks.st`). The ST file is a transcription of this class; the unit tests in
  `tests/test_interlocks.py` are the acceptance for both.

Design rules (CONTROLS_SPEC.md §1): life safety is hardwired and only *monitored* here; the edge computer
only *advises* (setpoint trim, test request); every output has a defined state when inputs are lost.

The class is pure Python with no I/O. Call :meth:`Interlocks.step` once per cycle with an :class:`Inputs`
snapshot and the elapsed seconds; read :class:`Outputs`. :meth:`Interlocks.registers` renders the same
Modbus holding-register block the PLC serves (spec/PROTOCOL.md "PLC ↔ edge"), so a Lite controller and a
Pro controller look identical on the wire.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import IntEnum
from typing import Dict, List, Optional

# --------------------------------------------------------------------------- constants (tunable per unit)
COOLING_START_FEEDBACK_S = 90.0      # unit must report RUN within this time after CMD, else FAULT
COOLING_FAULT_RETRY_S = 600.0        # a faulted unit is retried after 10 min (one retry, then latched)
COOLING_ROTATE_S = 7 * 24 * 3600.0   # weekly lead rotation
COOLING_MIN_RUN_S = 300.0            # anti-short-cycle
VALVE_TRAVEL_S = 30.0                # isolation valve must reach its limit switch within this time
DOOR_ALARM_S = 300.0                 # door open > 5 min -> alarm
EDGE_WATCHDOG_S = 30.0               # edge counter unchanged for this long -> EDGE_LOST
GEN_START_FAIL_S = 60.0              # generator commanded (by ATS) but not running
SUPPLY_TRIM_LIMIT_K = 2.0            # edge may trim the supply setpoint by at most ±2 K
KW_PER_UNIT_MARGIN = 0.85            # a unit is counted at 85 % of nameplate when sizing N


class Mode(IntEnum):
    OFF = 0
    AUTO = 1
    MANUAL = 2
    TEST = 3
    FAULT = 4


class AtsSource(IntEnum):
    NONE = 0
    UTILITY = 1
    GENERATOR = 2
    TRANSFER = 3


class GenState(IntEnum):
    OFF = 0
    STARTING = 1
    RUNNING = 2
    COOLDOWN = 3
    FAULT = 4
    NOT_READY = 5


class Alarm(IntEnum):
    """Bit positions of ALARM_WORD (register 40120)."""
    COOLING_CAPACITY_LOST = 0
    ALL_UNITS_FAULTED = 1
    LEAK_ISOLATION_ACTIVE = 2
    VALVE_FAULT = 3
    DOOR_OPEN_LONG = 4
    EPO_LOOP_OPEN = 5
    FIRE_ALARM = 6
    GENERATOR_FAULT = 7
    ATS_ON_GENERATOR = 8
    EDGE_LOST = 9
    PSU_REDUNDANCY_LOST = 10
    UPS_24V_ON_BATTERY = 11


# --------------------------------------------------------------------------- I/O images
@dataclass
class Inputs:
    """One scan of the field inputs. Lists are indexed by unit/zone/door (0-based)."""
    cooling_run_fb: List[bool]                 # run feedback per cooling unit (aux contact / Modbus RTU)
    cooling_fault_in: List[bool]               # unit's own fault contact (or comms loss)
    leak_zone: List[bool]                      # SeaHawk zone contacts (hardwired)
    valve_closed_ls: List[bool]                # isolation valve closed limit switches
    door_open: List[bool]
    epo_loop_ok: bool = True                   # EPO loop aux contact (monitor only)
    fire_alarm: bool = False                   # releasing panel aux (monitor only)
    fire_trouble: bool = False
    fire_released: bool = False
    fire_supervisory: bool = False
    utility_ok: bool = True                    # ATS utility available
    ats_on_generator: bool = False             # ATS position contact
    gen_running: bool = False                  # generator run contact
    gen_fault: bool = False
    ups_on_battery: bool = False
    psu_redundancy_ok: bool = True
    it_kw: float = 0.0
    supply_c: float = 20.0
    return_c: float = 30.0
    outdoor_c: float = 20.0
    edge_watchdog: int = 0                     # counter the edge writes every second (40004)
    supply_trim_k: float = 0.0                 # edge request (40006 / 10)
    test_request: int = 0                      # 40007
    mode_request: Mode = Mode.AUTO             # from the panel HMI selector


@dataclass
class Outputs:
    cooling_cmd: List[bool]
    valve_close_cmd: List[bool]
    cdu_pump_stop: bool
    cooling_enable_relay: bool                 # the hardware chain: FALSE = every unit on its own local control
    beacon: bool
    supply_setpoint_c: float
    alarm_word: int

    def alarm(self, a: Alarm) -> bool:
        return bool(self.alarm_word >> int(a) & 1)


@dataclass
class _UnitState:
    cmd: bool = False
    faulted: bool = False
    latched: bool = False                      # second failure -> stays out until manual reset
    since_cmd_s: float = 1e9                   # time since last command change
    fault_since_s: float = 0.0
    run_s: float = 0.0


# --------------------------------------------------------------------------- the state machine
class Interlocks:
    """Cooling N+1 sequencing and failover · leak isolation · door/EPO monitoring · ATS/generator
    supervision · edge watchdog · failsafe table. Pure logic, no I/O."""

    def __init__(self, n_cooling: int, unit_kw: float, n_leak_zones: int, n_doors: int,
                 redundancy: str = "N+1", supply_setpoint_c: float = 20.0, lite: bool = False):
        if n_cooling < 1:
            raise ValueError("at least one cooling unit")
        self.n = n_cooling
        self.unit_kw = unit_kw
        self.n_zones = n_leak_zones
        self.n_doors = n_doors
        self.redundancy = redundancy
        self.base_setpoint_c = supply_setpoint_c
        self.lite = lite
        self.units = [_UnitState() for _ in range(n_cooling)]
        self.lead = 0
        self.rotate_s = 0.0
        self.failover_count = 0
        self.last_failover_s = 65535.0
        self.valve_cmd = [False] * n_leak_zones
        self.valve_since_s = [0.0] * n_leak_zones
        self.valve_fault = [False] * n_leak_zones
        self.cdu_pump_stop = False
        self.door_s = [0.0] * n_doors
        self.edge_wd_last = None
        self.edge_wd_age_s = 0.0
        self.edge_lost = True                  # until the first counter change
        self.gen_since_s = 0.0
        self.gen_state = GenState.OFF
        self.gen_run_s = 0.0
        self.mode = Mode.AUTO
        self.heartbeat = 0
        self.t = 0.0
        self.alarm_word = 0
        self.test_active = 0
        self.test_since_s = 0.0
        self.last_outputs: Optional[Outputs] = None

    # ----------------------------------------------------------------- helpers
    def units_required(self, it_kw: float) -> int:
        """N for the load (ceil(it_kw / (unit_kw * margin))), at least 1, plus the redundancy margin."""
        import math
        n = max(1, math.ceil(it_kw / (self.unit_kw * KW_PER_UNIT_MARGIN))) if it_kw > 0 else 1
        extra = {"N": 0, "N+1": 1, "2N": n}.get(self.redundancy, 1)
        return min(self.n, n + extra)

    def reset_latched(self, idx: Optional[int] = None) -> None:
        """Manual reset from the HMI (not from the edge): clears latched unit faults."""
        for i, u in enumerate(self.units):
            if idx is None or i == idx:
                u.latched = False
                u.faulted = False

    def _set_alarm(self, a: Alarm, on: bool) -> None:
        if on:
            self.alarm_word |= 1 << int(a)
        else:
            self.alarm_word &= ~(1 << int(a))

    # ----------------------------------------------------------------- the scan
    def step(self, x: Inputs, dt_s: float) -> Outputs:
        self.t += dt_s
        self.heartbeat = (self.heartbeat + 1) & 0xFFFF

        # ---- edge watchdog (the edge only advises; its loss changes nothing safety-relevant)
        if self.edge_wd_last is None or x.edge_watchdog != self.edge_wd_last:
            self.edge_wd_last = x.edge_watchdog
            self.edge_wd_age_s = 0.0
            self.edge_lost = self.edge_wd_last is None
        else:
            self.edge_wd_age_s += dt_s
            if self.edge_wd_age_s >= EDGE_WATCHDOG_S:
                self.edge_lost = True
        self._set_alarm(Alarm.EDGE_LOST, self.edge_lost)

        # ---- mode
        self.mode = Mode(x.mode_request)

        # ---- life safety: MONITOR ONLY. Nothing below acts on the loop or the panel.
        self._set_alarm(Alarm.EPO_LOOP_OPEN, not x.epo_loop_ok)
        self._set_alarm(Alarm.FIRE_ALARM, x.fire_alarm)

        # ---- doors
        for i in range(self.n_doors):
            self.door_s[i] = self.door_s[i] + dt_s if x.door_open[i] else 0.0
        self._set_alarm(Alarm.DOOR_OPEN_LONG, any(s >= DOOR_ALARM_S for s in self.door_s))

        # ---- power supervision
        self._set_alarm(Alarm.ATS_ON_GENERATOR, x.ats_on_generator)
        self._set_alarm(Alarm.UPS_24V_ON_BATTERY, x.ups_on_battery)
        self._set_alarm(Alarm.PSU_REDUNDANCY_LOST, not x.psu_redundancy_ok)
        self._generator(x, dt_s)

        # ---- leak isolation (hardwired zones only; Pod leak is advisory on the dashboard)
        self._leak(x, dt_s)

        # ---- cooling
        self._cooling(x, dt_s)

        # ---- edge setpoint trim: clamped, ignored when the edge is lost or mode is not AUTO
        trim = 0.0 if (self.edge_lost or self.mode != Mode.AUTO) else max(-SUPPLY_TRIM_LIMIT_K, min(SUPPLY_TRIM_LIMIT_K, x.supply_trim_k))
        setpoint = self.base_setpoint_c + trim

        # ---- test requests (failover sweep etc.) accepted only in AUTO with no alarm
        self._tests(x, dt_s)

        # ---- the hardware enable chain: the units are allowed to follow BEN only when the controller is
        # healthy and in AUTO/TEST; otherwise the relay drops and every unit runs on its own controller.
        healthy = self.mode in (Mode.AUTO, Mode.TEST) and not self.alarm_word >> int(Alarm.ALL_UNITS_FAULTED) & 1
        enable_relay = healthy
        if self.mode == Mode.OFF or self.mode == Mode.FAULT:
            enable_relay = False

        beacon = self.alarm_word != 0 and (self.alarm_word & ~(1 << int(Alarm.EDGE_LOST))) != 0

        self.last_outputs = Outputs(
            cooling_cmd=[u.cmd for u in self.units],
            valve_close_cmd=list(self.valve_cmd),
            cdu_pump_stop=self.cdu_pump_stop,
            cooling_enable_relay=enable_relay,
            beacon=beacon,
            supply_setpoint_c=setpoint,
            alarm_word=self.alarm_word,
        )
        return self.last_outputs

    # ----------------------------------------------------------------- cooling N+1 and failover
    def _cooling(self, x: Inputs, dt_s: float) -> None:
        n_req = self.units_required(x.it_kw)
        # 1. fault detection per unit: fault contact, or commanded but no run feedback within the window
        for i, u in enumerate(self.units):
            u.since_cmd_s += dt_s
            if u.cmd and x.cooling_run_fb[i]:
                u.run_s += dt_s
            no_feedback = u.cmd and not x.cooling_run_fb[i] and u.since_cmd_s >= COOLING_START_FEEDBACK_S
            if (x.cooling_fault_in[i] or no_feedback) and not u.faulted and not u.latched:
                u.faulted = True
                u.fault_since_s = 0.0
                if u.cmd:
                    self.failover_count += 1
                    self.last_failover_s = 0.0
                u.cmd = False
                u.since_cmd_s = 0.0
            elif u.faulted:
                u.fault_since_s += dt_s
                if not x.cooling_fault_in[i] and u.fault_since_s >= COOLING_FAULT_RETRY_S:
                    # one automatic retry; a second fault latches until a manual reset
                    if u.latched:
                        pass
                    else:
                        u.faulted = False
                        u.latched = u.run_s < COOLING_MIN_RUN_S  # it never ran properly -> latch after retry
        self.last_failover_s = min(65535.0, self.last_failover_s + dt_s)

        # 2. lead rotation (weekly) among healthy units
        self.rotate_s += dt_s
        if self.rotate_s >= COOLING_ROTATE_S:
            self.rotate_s = 0.0
            self.lead = (self.lead + 1) % self.n

        # 3. choose the units to run: lead first, then round-robin, skipping faulted/latched
        available = [i for i in range(self.n) if not self.units[i].faulted and not self.units[i].latched]
        order = [(self.lead + k) % self.n for k in range(self.n)]
        chosen = [i for i in order if i in available][:n_req]
        if self.mode in (Mode.AUTO, Mode.TEST):
            for i, u in enumerate(self.units):
                want = i in chosen
                if want != u.cmd:
                    # anti-short-cycle: do not stop a healthy unit that has run < MIN_RUN unless it is a swap
                    if not want and u.run_s < COOLING_MIN_RUN_S and len(chosen) >= n_req and u.since_cmd_s < COOLING_MIN_RUN_S:
                        continue
                    u.cmd = want
                    u.since_cmd_s = 0.0
                    if want:
                        u.run_s = 0.0
        elif self.mode == Mode.OFF:
            for u in self.units:
                u.cmd = False

        running = sum(1 for i, u in enumerate(self.units) if u.cmd and x.cooling_run_fb[i])
        n_needed_no_redundancy = self.units_required(x.it_kw) - {"N": 0, "N+1": 1, "2N": 0}.get(self.redundancy, 1)
        self._set_alarm(Alarm.COOLING_CAPACITY_LOST, len(available) < n_req)
        self._set_alarm(Alarm.ALL_UNITS_FAULTED, len(available) == 0)
        self._running = running
        self._n_required = n_req
        self._n_min = max(1, n_needed_no_redundancy)

    # ----------------------------------------------------------------- leak isolation
    def _leak(self, x: Inputs, dt_s: float) -> None:
        any_iso = False
        pump_stop = False
        for z in range(self.n_zones):
            if x.leak_zone[z] and not self.valve_cmd[z]:
                self.valve_cmd[z] = True            # close the zone's isolation valve, latch until reset
                self.valve_since_s[z] = 0.0
            if self.valve_cmd[z]:
                any_iso = True
                self.valve_since_s[z] += dt_s
                if not x.valve_closed_ls[z] and self.valve_since_s[z] >= VALVE_TRAVEL_S:
                    self.valve_fault[z] = True
                if self.valve_fault[z] and x.leak_zone[z]:
                    pump_stop = True                # valve failed and the zone is still wet: stop the pumps
        self.cdu_pump_stop = pump_stop
        self._set_alarm(Alarm.LEAK_ISOLATION_ACTIVE, any_iso)
        self._set_alarm(Alarm.VALVE_FAULT, any(self.valve_fault))

    def reset_leak(self, zone: Optional[int] = None) -> None:
        """Manual reset after the zone is dry and inspected (HMI only, never from the edge)."""
        for z in range(self.n_zones):
            if zone is None or z == zone:
                self.valve_cmd[z] = False
                self.valve_fault[z] = False
        self.cdu_pump_stop = False

    # ----------------------------------------------------------------- generator / ATS supervision
    def _generator(self, x: Inputs, dt_s: float) -> None:
        if x.gen_fault:
            self.gen_state = GenState.FAULT
        elif x.gen_running:
            self.gen_state = GenState.RUNNING
            self.gen_run_s += dt_s
            self.gen_since_s = 0.0
        elif not x.utility_ok:
            # ATS has (or will) call for the generator; we only supervise the start
            self.gen_since_s += dt_s
            self.gen_state = GenState.STARTING if self.gen_since_s < GEN_START_FAIL_S else GenState.FAULT
        else:
            self.gen_state = GenState.COOLDOWN if self.gen_run_s > 0 and self.gen_since_s < 300 else GenState.OFF
            self.gen_since_s += dt_s
            if self.gen_state == GenState.OFF:
                self.gen_run_s = 0.0
        self._set_alarm(Alarm.GENERATOR_FAULT, self.gen_state == GenState.FAULT)

    def ats_source(self, x: Inputs) -> AtsSource:
        if x.ats_on_generator:
            return AtsSource.GENERATOR
        if x.utility_ok:
            return AtsSource.UTILITY
        return AtsSource.TRANSFER if self.gen_state == GenState.STARTING else AtsSource.NONE

    # ----------------------------------------------------------------- tests requested by the edge
    def _tests(self, x: Inputs, dt_s: float) -> None:
        if self.test_active:
            self.test_since_s += dt_s
            if self.test_active == 1 and self.test_since_s >= 1.0:
                # failover sweep: stop the lead unit once; the sequencer brings the standby in
                u = self.units[self.lead]
                if u.cmd:
                    u.cmd = False
                    u.since_cmd_s = 0.0
                    self.failover_count += 1
                    self.last_failover_s = 0.0
                self.test_active = 0
            elif self.test_active in (2, 3) and self.test_since_s >= 1.0:
                self.test_active = 0            # UPS / generator tests are requested from their own controllers
            return
        safe_alarms = (1 << int(Alarm.EDGE_LOST)) | (1 << int(Alarm.ATS_ON_GENERATOR))
        if x.test_request in (1, 2, 3) and self.mode == Mode.AUTO and (self.alarm_word & ~safe_alarms) == 0 and not self.edge_lost:
            self.test_active = x.test_request
            self.test_since_s = 0.0

    # ----------------------------------------------------------------- Modbus image (spec/PROTOCOL.md)
    def registers(self, x: Inputs, project_crc: int = 0) -> Dict[int, int]:
        """Holding registers exactly as the PLC serves them. Lite sets bit 8 of PLC_MODE."""
        def bits(flags: List[bool]) -> int:
            return sum(1 << i for i, f in enumerate(flags) if f)
        def i16(v: float) -> int:
            n = int(round(v))
            return n & 0xFFFF
        o = self.last_outputs or self.step(x, 0.0)
        r = {
            40001: self.heartbeat,
            40002: int(self.mode) | (0x100 if self.lite else 0),
            40003: project_crc & 0xFFFF,
            40004: x.edge_watchdog & 0xFFFF,
            40005: int(self.edge_lost),
            40006: i16(x.supply_trim_k * 10),
            40007: self.test_active,
            40010: bits(o.cooling_cmd),
            40011: bits(x.cooling_run_fb),
            40012: bits([u.faulted or u.latched for u in self.units]),
            40013: self.lead + 1,
            40014: self._n_required if hasattr(self, "_n_required") else self.units_required(x.it_kw),
            40015: self.failover_count & 0xFFFF,
            40016: int(min(65535, self.last_failover_s)),
            40020: bits(x.leak_zone),
            40021: bits(o.valve_close_cmd),
            40022: bits(x.valve_closed_ls),
            40023: bits(self.valve_fault),
            40024: int(o.cdu_pump_stop),
            40030: bits(x.door_open),
            40031: int(min(65535, max(self.door_s) if self.door_s else 0)),
            40032: int(x.epo_loop_ok),
            40033: bits([x.fire_alarm, x.fire_trouble, x.fire_released, x.fire_supervisory]),
            40040: int(self.ats_source(x)),
            40041: int(self.gen_state),
            40042: int(min(65535, self.gen_run_s)),
            40043: int(x.ups_on_battery),
            40044: int(x.utility_ok),
            40050: int(round(x.it_kw * 10)) & 0xFFFF,
            40051: i16(x.supply_c * 10),
            40052: i16(x.return_c * 10),
            40053: i16(x.outdoor_c * 10),
            40120: self.alarm_word,
            40121: int(x.psu_redundancy_ok),
        }
        return r


# --------------------------------------------------------------------------- failsafe table (documentation + test oracle)
FAILSAFE_TABLE = [
    # (output, "controller alive, edge lost", "controller dead / watchdog relay dropped")
    ("cooling_cmd",          "sequencer continues on its own setpoints", "units run on their own local controllers (enable chain open)"),
    ("valve_close_cmd",      "unchanged — leak isolation needs no edge",  "valves hold position (spring-return option closes), CDU keeps its own leak logic"),
    ("cdu_pump_stop",        "unchanged",                                 "released — CDU's own protection governs"),
    ("cooling_enable_relay", "held (edge is advisory)",                   "dropped by the hardware watchdog"),
    ("supply_setpoint_c",    "base setpoint, trim ignored",               "n/a — units on local setpoints"),
    ("beacon",               "lit if any non-edge alarm",                 "lit by the watchdog's NC contact"),
]
