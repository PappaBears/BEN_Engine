"""BEN Engine digital twin.

A deterministic lumped-parameter model of one BEN unit: rack thermal masses, cooling units with
capacity and fan curves, a recirculation fraction (from CFD or default), the container envelope,
and the power chain (utility → ATS → UPS → PDUs → racks, plus generator).

The twin is the single source of truth for simulation mode (no hardware), for commissioning
rehearsal, for automated sweeps, and for prediction (analysis.py fits its parameters from
measured data and then runs it forward).

Integration: explicit Euler with sub-stepping; stable for dt <= 5 s at the default time constants.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .config import Config, COOLING_LIBRARY, CLIMATE_DESIGN

AIR_CP_J_KGK = 1006.0
AIR_RHO = 1.18          # kg/m3 at ~25 C sea level
CFM_TO_M3S = 0.000471947


@dataclass
class SensorSpec:
    id: str
    kind: str          # temperature, humidity, pressure, power, contact, leak
    location_m: tuple  # x, y, z inside container, origin at door-end floor centreline
    unit: str
    u95: float         # expanded uncertainty after calibration (k=2)
    node: str          # which BEN node / equipment reports it


@dataclass
class TwinParams:
    """Physical parameters analysis.py can fit. Defaults are design values."""
    rack_mass_kg: float = 60.0           # effective thermal mass of air+metal in a rack flow path
    rack_delta_t_design_k: float = 12.0  # server ΔT at design flow
    recirculation: float = 0.08          # fraction of hot exhaust re-entering inlets (CFD overrides)
    bypass: float = 0.10                 # fraction of cold supply bypassing racks
    supply_setpoint_c: float = 20.0
    envelope_ua_w_k: float = 45.0        # overall UA of insulated container (100 mm PIR)
    room_air_mass_kg: float = 40.0
    ups_eff: float = 0.96
    pdu_eff: float = 0.995
    cooling_time_constant_s: float = 90.0
    sensor_noise_c: float = 0.08         # 1-sigma noise on temperature channels
    sensor_noise_pa: float = 0.3
    fan_law_exp: float = 2.7             # fan power ∝ speed^2.7 (real fans, not ideal 3)
    # Optional per-rack recirculation fractions from cfd.recirculation_profile(); when set
    # (length == racks) it replaces the scalar `recirculation` and the built-in position bias.
    recirculation_profile: Optional[List[float]] = None


class Twin:
    FAULTS = ("cooling_unit_fail", "utility_loss", "door_open", "filter_clog", "leak", "sensor_drift", "generator_fail")

    def __init__(self, cfg: Config, params: Optional[TwinParams] = None, seed: int = 0, outdoor_c: Optional[float] = None):
        errs = cfg.validate()
        if errs:
            raise ValueError("; ".join(errs))
        self.cfg = cfg
        self.d = cfg.derived()
        self.p = params or TwinParams()
        self.rng = random.Random(seed)
        self.t = 0.0
        clim = CLIMATE_DESIGN[cfg.climate]
        self.outdoor_c = outdoor_c if outdoor_c is not None else (clim["t_design_c"] - 10.0)
        self.it_fraction = 0.6
        n = cfg.racks
        self.rack_inlet_c = [self.p.supply_setpoint_c + 1.5] * n
        self.rack_outlet_c = [self.p.supply_setpoint_c + 1.5 + self.p.rack_delta_t_design_k * 0.6] * n
        self.room_c = self.p.supply_setpoint_c + 4.0
        self.supply_c = self.p.supply_setpoint_c
        self.return_c = self.room_c + 6
        nunits = self.d["cooling_units_total"]
        self.cooling_units = [{"on": i < self.d["cooling_units_n"], "kw": 0.0, "fan_pct": 60.0, "ok": True} for i in range(nunits)]
        # N+1 / 2N: redundant units idle; they start on failure
        self.faults: Dict[str, Dict[str, Any]] = {}
        self.ups_soc = 100.0
        self.utility_ok = True
        self.generator_on = False
        self.generator_start_timer = 0.0
        self.rh = 42.0
        self.filter_dp_pa = 25.0
        self.drift_c = 0.0
        self._alarm_state: Dict[str, Dict[str, Any]] = {}
        self._seq = 0

    # ------------------------------------------------------------------ controls
    def set_it_load(self, fraction: float):
        self.it_fraction = max(0.0, min(1.2, fraction))

    def set_outdoor(self, c: float):
        self.outdoor_c = c

    def inject(self, name: str, **params):
        if name not in self.FAULTS:
            raise ValueError(f"unknown fault {name}; valid: {self.FAULTS}")
        self.faults[name] = params
        if name == "cooling_unit_fail":
            u = int(params.get("unit", 0))
            if u < len(self.cooling_units):
                self.cooling_units[u]["ok"] = False
                self.cooling_units[u]["on"] = False
        if name == "utility_loss":
            self.utility_ok = False
            self.generator_start_timer = 12.0 if self.cfg.generator else -1
        if name == "sensor_drift":
            self.drift_c = float(params.get("delta_c", 1.5))

    def clear(self, name: str, **params):
        self.faults.pop(name, None)
        if name == "cooling_unit_fail":
            u = int(params.get("unit", 0))
            if u < len(self.cooling_units):
                self.cooling_units[u]["ok"] = True
        if name == "utility_loss":
            self.utility_ok = True
            self.generator_on = False
        if name == "sensor_drift":
            self.drift_c = 0.0
        if name == "filter_clog":
            self.filter_dp_pa = 25.0

    # ------------------------------------------------------------------ physics
    def _cooling_control(self, dt: float):
        """Start standby units when an active unit fails; modulate fans on return temp."""
        active_needed = self.d["cooling_units_n"]
        running = [u for u in self.cooling_units if u["on"] and u["ok"]]
        if len(running) < active_needed:
            for u in self.cooling_units:
                if u["ok"] and not u["on"]:
                    u["on"] = True
                    running.append(u)
                    if len(running) >= active_needed:
                        break
        # fan modulation: target return temp = supply + 12 K
        err = self.return_c - (self.p.supply_setpoint_c + 12.0)
        target_fan = max(30.0, min(100.0, 60.0 + 8.0 * err))
        # capacity shortfall: every running unit at full fan and the return still 2 K over target starts a standby unit
        # (clogged filters, derated units); the sequencer stops it again once the error is gone
        if running and err > 2.0 and all(u["fan_pct"] >= 98.0 for u in running):
            for u in self.cooling_units:
                if u["ok"] and not u["on"]:
                    u["on"] = True
                    u["fan_pct"] = 60.0
                    break
        for u in self.cooling_units:
            if u["on"] and u["ok"]:
                u["fan_pct"] += (target_fan - u["fan_pct"]) * min(1.0, dt / self.p.cooling_time_constant_s)
            else:
                u["fan_pct"] = 0.0

    def step(self, dt: float = 1.0):
        n_sub = max(1, int(math.ceil(dt / 1.0)))
        h = dt / n_sub
        for _ in range(n_sub):
            self._step_once(h)
        self.t += dt
        self._seq += 1

    def _step_once(self, h: float):
        cfg, p, d = self.cfg, self.p, self.d
        it_kw = cfg.it_kw * self.it_fraction
        rack_kw = it_kw / cfg.racks
        cl = COOLING_LIBRARY[cfg.cooling]
        self._cooling_control(h)

        # ---- power chain
        if not self.utility_ok:
            if self.generator_start_timer > 0:
                self.generator_start_timer -= h
                if self.generator_start_timer <= 0 and "generator_fail" not in self.faults:
                    self.generator_on = True
            on_battery = not self.generator_on
        else:
            on_battery = False
        ups_in_kw = it_kw / p.ups_eff / p.pdu_eff
        if on_battery:
            # battery_kwh at nominal; discharge
            self.ups_soc -= (ups_in_kw * h / 3600.0) / max(d["battery_kwh"], 0.1) * 100.0 * 0.9
            self.ups_soc = max(0.0, self.ups_soc)
            if self.ups_soc <= 0.0:
                it_kw = 0.0
                rack_kw = 0.0
        else:
            self.ups_soc = min(100.0, self.ups_soc + h / 3600.0 / 4.0 * 100.0)  # 4 h recharge
        # cooling loses power on battery unless generator (mechanical load is not on UPS, except the BEN 5 cabinet)
        cooling_powered = self.utility_ok or self.generator_on or (d["kind"] == "cabinet")

        # ---- cooling capacity and electrical
        cool_kw_total = 0.0
        cool_elec = 0.0
        derate = d["cooling_derate"]
        for u in self.cooling_units:
            if u["on"] and u["ok"] and cooling_powered:
                cap = cl["unit_kw"] * derate * (u["fan_pct"] / 100.0) ** 0.8
                # clog reduces airflow → capacity; on liquid cooling only the 30 % air-side residual path has filters
                if "filter_clog" in self.faults:
                    cap *= 0.75 if cl["medium"] != "liquid" else (1.0 - 0.25 * 0.3)
                u["kw"] = cap
                cool_kw_total += cap
                cool_elec += cap / cl["cop"] * (0.6 + 0.4 * (u["fan_pct"] / 100.0) ** p.fan_law_exp)
            else:
                u["kw"] = 0.0
        self.cooling_kw_elec = cool_elec

        # ---- air side
        if cl["medium"] == "air":
            flow_m3s = d["airflow_cfm"] * CFM_TO_M3S * max(0.2, self.it_fraction)
            mcp = flow_m3s * AIR_RHO * AIR_CP_J_KGK  # W/K
            # supply temperature: cooling pulls return air down; limited by capacity
            supply_target = max(p.supply_setpoint_c, self.return_c - (cool_kw_total * 1000.0) / max(mcp * (1 - p.bypass), 1.0))
        else:
            # liquid: 70 % of heat to liquid loop, 30 % residual air handled by small AHU in the twin via same math
            flow_m3s = d["airflow_cfm"] * CFM_TO_M3S * max(0.2, self.it_fraction)
            mcp = flow_m3s * AIR_RHO * AIR_CP_J_KGK
            supply_target = max(p.supply_setpoint_c, self.return_c - (cool_kw_total * 1000.0 * 0.3) / max(mcp, 1.0))
            rack_kw = rack_kw * 0.3  # air-side residual only
        self.supply_c += (supply_target - self.supply_c) * min(1.0, h / 30.0)

        # envelope + door
        door_gain_w = 0.0
        if "door_open" in self.faults:
            door_gain_w = 800.0 * max(0.0, self.outdoor_c - self.room_c) / 10.0 + 300.0
        env_w = p.envelope_ua_w_k * (self.outdoor_c - self.room_c) + d["envelope_gain_kw"] * 1000.0 * 0.3 + door_gain_w

        # rack inlet = mix of supply and recirculated outlet, plus envelope effect on room
        door_mult = 1.6 if "door_open" in self.faults else 1.0
        recirc_scalar = p.recirculation * door_mult
        prof = p.recirculation_profile if (p.recirculation_profile and len(p.recirculation_profile) == cfg.racks) else None
        per_rack_flow = mcp / cfg.racks
        for i in range(cfg.racks):
            if prof is not None:
                # CFD-derived per-rack recirculation replaces the generic position bias
                recirc = min(0.95, max(0.0, prof[i] * door_mult))
                pos_bias = 0.0
            else:
                recirc = recirc_scalar
                # per-rack position effect: racks far from cooling see +0.3 K per position along the row
                # (CFD overrides via recirculation profile); multi-row halls bias per row position
                rpr = d["racks_per_row"]
                pos_bias = 0.3 * (i % rpr) / max(1, rpr - 1)
            inlet_target = (1 - recirc) * self.supply_c + recirc * self.rack_outlet_c[i] + pos_bias
            tau = p.rack_mass_kg * AIR_CP_J_KGK / max(per_rack_flow, 1.0)
            self.rack_inlet_c[i] += (inlet_target - self.rack_inlet_c[i]) * min(1.0, h / max(tau, 5.0))
            dT = (rack_kw * 1000.0) / max(per_rack_flow, 1.0)
            outlet_target = self.rack_inlet_c[i] + dT
            self.rack_outlet_c[i] += (outlet_target - self.rack_outlet_c[i]) * min(1.0, h / max(tau, 5.0))
        mean_out = sum(self.rack_outlet_c) / cfg.racks
        # return air = rack outlets mixed with bypass, plus envelope
        return_target = (1 - p.bypass) * mean_out + p.bypass * self.supply_c + env_w / max(mcp, 1.0)
        self.return_c += (return_target - self.return_c) * min(1.0, h / 40.0)
        self.room_c = 0.5 * (self.supply_c + self.return_c)

        # pressure: containment ΔP rises with fan speed^2; filter clog adds
        fan = max([u["fan_pct"] for u in self.cooling_units] + [0.0]) / 100.0
        if "filter_clog" in self.faults:
            self.filter_dp_pa = min(250.0, self.filter_dp_pa + 0.02 * h)
        self.aisle_dp_pa = 12.0 * fan ** 2 * (1.0 if cl["medium"] == "air" else 0.3)
        # humidity drifts toward outdoor-ish with door open, else held by cooling unit
        rh_target = 42.0 if "door_open" not in self.faults else 60.0
        self.rh += (rh_target - self.rh) * min(1.0, h / 600.0)

        self.it_kw_now = it_kw
        aux_kw = cool_elec + 0.5 + 0.02 * cfg.it_kw
        self.utility_kw = (ups_in_kw + aux_kw) if (self.utility_ok or self.generator_on) else 0.0
        self.pue = (ups_in_kw + aux_kw) / it_kw if it_kw > 0.5 else float("nan")
        self._update_alarms()

    # ------------------------------------------------------------------ alarms
    def _alarm(self, aid: str, sev: str, msg: str, active: bool):
        st = self._alarm_state.get(aid)
        if active:
            self._alarm_state[aid] = {"id": aid, "sev": sev, "msg": msg, "active": True, "since": st["since"] if st and st["active"] else self.t}
        elif st and st["active"]:
            st["active"] = False
            st["cleared"] = self.t

    def _update_alarms(self):
        a_max = {"A1": 27.0, "A2": 35.0, "A3": 40.0, "A4": 45.0}[self.d["ashrae_class"]]
        for i, tin_true in enumerate(self.rack_inlet_c):
            tin = tin_true + self.drift_c  # alarms act on the *reported* reading, as the gateway does
            self._alarm(f"rack{i+1}_inlet_high", "alarm" if tin > a_max else "warn", f"Rack {i+1} inlet {tin:.1f} C exceeds {a_max - 2:.0f} C warning", tin > a_max - 2)
            self._alarm(f"rack{i+1}_inlet_crit", "critical", f"Rack {i+1} inlet {tin:.1f} C exceeds ASHRAE {self.d['ashrae_class']} max {a_max:.0f} C", tin > a_max)
        for i, u in enumerate(self.cooling_units):
            self._alarm(f"cool{i+1}_fail", "alarm", f"Cooling unit {i+1} failed", not u["ok"])
        self._alarm("utility_loss", "alarm", "Utility power lost; on UPS" if not self.generator_on else "Utility lost; generator running", not self.utility_ok)
        self._alarm("ups_low", "critical", f"UPS state of charge {self.ups_soc:.0f} %", self.ups_soc < 30.0)
        self._alarm("door_open", "warn", "Container door open", "door_open" in self.faults)
        self._alarm("leak", "critical", "Leak detected under floor", "leak" in self.faults)
        self._alarm("filter_dp", "warn", f"Filter ΔP {self.filter_dp_pa:.0f} Pa, replace filters", self.filter_dp_pa > 150.0)

    # ------------------------------------------------------------------ outputs
    def _noise(self, sigma: float) -> float:
        return self.rng.gauss(0.0, sigma)

    def state(self) -> Dict[str, Any]:
        p = self.p
        ups_runtime = (self.ups_soc / 100.0 * self.d["battery_kwh"] * 0.9) / max(self.it_kw_now / p.ups_eff, 0.1) * 60.0 if hasattr(self, "it_kw_now") else 0.0
        return {
            "t": self.t, "seq": self._seq,
            "tier": self.cfg.tier, "profile": self.cfg.profile,
            "outdoor_c": round(self.outdoor_c, 2),
            "it_kw": round(getattr(self, "it_kw_now", 0.0), 2), "it_fraction": self.it_fraction,
            "rack_inlet_c": [round(x + self._noise(p.sensor_noise_c) + self.drift_c, 2) for x in self.rack_inlet_c],
            "rack_outlet_c": [round(x + self._noise(p.sensor_noise_c), 2) for x in self.rack_outlet_c],
            "supply_c": round(self.supply_c + self._noise(p.sensor_noise_c), 2),
            "return_c": round(self.return_c + self._noise(p.sensor_noise_c), 2),
            "room_c": round(self.room_c, 2),
            "aisle_dp_pa": round(getattr(self, "aisle_dp_pa", 0.0) + self._noise(p.sensor_noise_pa), 2),
            "filter_dp_pa": round(self.filter_dp_pa, 1),
            "rh_pct": round(self.rh + self._noise(0.3), 1),
            "cooling_units": [dict(u, kw=round(u["kw"], 2), fan_pct=round(u["fan_pct"], 1)) for u in self.cooling_units],
            "cooling_kw_elec": round(getattr(self, "cooling_kw_elec", 0.0), 2),
            "power": {
                "utility_ok": self.utility_ok, "utility_kw": round(getattr(self, "utility_kw", 0.0), 2),
                "ups_kw": round(getattr(self, "it_kw_now", 0.0) / p.ups_eff, 2), "ups_soc_pct": round(self.ups_soc, 1),
                "ups_runtime_min": round(min(ups_runtime, 999.0), 1), "ups_on_battery": (not self.utility_ok) and (not self.generator_on),
                "generator_on": self.generator_on,
                "pdu_kw": [round(getattr(self, "it_kw_now", 0.0) / self.cfg.racks, 2)] * self.cfg.racks,
            },
            "pue": round(self.pue, 3) if hasattr(self, "pue") and not math.isnan(self.pue) else None,
            "alarms": [dict(v) for v in self._alarm_state.values() if v["active"]],
            "faults": sorted(self.faults.keys()),
            "door_open": "door_open" in self.faults, "leak": "leak" in self.faults,
        }

    def rack_positions(self) -> List[tuple]:
        """(x, y) floor position of every rack, origin at the door-end floor centreline. Single-row modules put the
        row on the centreline; the BEN 2000 hall places ``rows`` rows across the interior width (hot/cold aisles between)."""
        g = self.d["geometry"]
        rows = self.d["rows"]
        rpr = self.d["racks_per_row"]
        pitch = g["int_l_m"] / (rpr + 1)
        out = []
        for i in range(self.cfg.racks):
            r, k = divmod(i, rpr)
            x = pitch * (k + 1)
            y = 0.0 if rows == 1 else -g["int_w_m"] / 2 + g["int_w_m"] * (r + 1) / (rows + 1)
            out.append((x, y))
        return out

    def sensors(self) -> List[SensorSpec]:
        g = self.d["geometry"]
        out: List[SensorSpec] = []
        for i, (x, y) in enumerate(self.rack_positions()):
            node = f"node{i // 2 + 1}"
            for z in (0.4, 1.2, 1.8):
                out.append(SensorSpec(f"T_in_r{i+1}_{z}", "temperature", (round(x, 3), round(y - 0.55, 3), z), "C", 0.25, node))
            out.append(SensorSpec(f"T_out_r{i+1}", "temperature", (round(x, 3), round(y + 0.55, 3), 1.2), "C", 0.25, node))
        out.append(SensorSpec("T_supply", "temperature", (0.3, -0.6, 0.3), "C", 0.25, "node1"))
        out.append(SensorSpec("T_return", "temperature", (0.3, 0.6, 2.2), "C", 0.25, "node1"))
        modules = self.d["modules"]
        for m in range(modules):
            # room sensors per module (one set for single-module tiers)
            sfx = "" if modules == 1 else f"_m{m+1}"
            xm = g["int_l_m"] * (m + 0.5) / modules
            out.append(SensorSpec(f"RH_room{sfx}", "humidity", (round(xm, 3), 0.0, 1.5), "%RH", 1.5, "node1"))
            out.append(SensorSpec(f"dP_aisle{sfx}", "pressure", (round(xm, 3), 0.0, 1.5), "Pa", 0.4, "node1"))
            out.append(SensorSpec(f"leak_floor{sfx}", "leak", (round(xm, 3), 0.0, 0.02), "bool", 0, "node1"))
        out.append(SensorSpec("door_main", "contact", (0.05, 0.0, 1.0), "bool", 0, "node1"))
        out.append(SensorSpec("P_utility", "power", (0.2, 0.9, 1.5), "kW", 0.005 * self.d["total_kw"], "meter1"))
        return out


def run_profile(cfg: Config, seconds: int = 1800, dt: float = 1.0, seed: int = 0, load=0.8, outdoor_c=None):
    """Run the twin and return a list of states (1 per dt). Used by tests and sweeps."""
    tw = Twin(cfg, seed=seed, outdoor_c=outdoor_c)
    tw.set_it_load(load)
    out = []
    for _ in range(int(seconds / dt)):
        tw.step(dt)
        out.append(tw.state())
    return out
