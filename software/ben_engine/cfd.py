"""BEN Engine 2-D thermal lattice-Boltzmann airflow solver.

What it is
----------
A plan-view (looking down) model of the air inside one BEN container. The flow is solved with a
D2Q9 lattice-Boltzmann BGK scheme; temperature and a "hot-air tracer" are carried as two D2Q5
passive scalars advected by that flow. Everything is numpy-vectorised; no compiled extensions.

Geometry (all from ``Config``)
------------------------------
* Domain: the container interior ``int_l_m`` x ``int_w_m``. Walls are full-way bounce-back
  (no-slip) and adiabatic for the scalars.
* One rack row along the back wall. Across the width: hot aisle (behind the racks, against the
  wall) / rack depth / cold aisle (in front). Racks are **fan zones with a heat source**: the
  velocity inside them is relaxed toward the server-fan face velocity (front -> back) and
  heat is injected so that the air leaving a rack is ``P_rack / (m_dot cp)`` warmer than it entered.
* Cooling units are interleaved in the row (in-row style) and are fan zones with the opposite
  direction (hot aisle -> cold aisle). Air passing through a unit is reset to the supply
  temperature and the tracer is reset to zero, i.e. they are the sink for heat and tracer.
  The unit face velocity is sized from the derived ``airflow_cfm`` (plus bypass) and the unit
  face area, so the solved loop carries the design airflow.
* Containment: the gaps between the ends of the rack row and the container end walls are the
  only plan-view leakage path between hot and cold aisle. With ``containment=True`` they are
  closed by door/panel segments that keep a small open fraction (seal gaps, cable cut-outs);
  with ``containment=False`` they are fully open.
* A tracer with concentration 1 is released in the rack cells (hot exhaust), 0 at cooling
  units. The mean tracer at a rack's inlet face is the fraction of that rack's inlet air that
  came from the hot side without passing through a cooling unit: the **recirculation index**.

Scaling and honesty
-------------------
The lattice Mach number is kept low (max lattice speed ``U_LAT`` = 0.08) and the relaxation time
``tau`` is 0.6 (lattice viscosity 0.033), which is stable with BGK, bounce-back and fan-zone
forcing. The resulting lattice Reynolds number (printed in the metrics as ``re_lattice``) is of
order 10^2, while the real container flow is of order 10^5. There is no turbulence model: the
large lattice viscosity plays the role of a crude eddy viscosity. Also, a plan view cannot show
over-rack or under-floor recirculation and treats the room as depth-averaged. Use the results
as a *relative / qualitative* tool: which rack sees the most recirculation, how much containment
helps, where the hot spot sits, and as an input profile for the twin, not as absolute
temperatures certified to a tenth of a degree.

Twin coupling
-------------
``recirculation_profile(cfg)`` returns one recirculation fraction per rack. Put it into
``TwinParams.recirculation_profile`` (added for this purpose); when set and of length
``cfg.racks`` the twin uses it per rack instead of the scalar ``TwinParams.recirculation``
plus its built-in position bias. ``apply_to_params(metrics, params)`` does this for you.

CLI
---
``python -m ben_engine.cfd --tier ben150 --png /tmp/x.png [--open] [--steps N]``
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .config import Config, COOLING_LIBRARY, canonical_tier

# ------------------------------------------------------------------ constants
AIR_RHO = 1.18
AIR_CP = 1006.0
AIR_NU = 1.5e-5          # m2/s kinematic viscosity, real air
CFM_TO_M3S = 0.000471947
U_LAT = 0.08             # max lattice speed (Mach ~0.14 with cs=1/sqrt(3))
TAU = 0.6                # BGK relaxation time for the flow
PRANDTL = 0.7
RACK_W_M = 0.60          # rack width along the row
UNIT_W_M = 0.30          # in-row cooling unit width along the row
RACK_H_M = 2.0           # height used to turn plan-view face lengths into areas
DOOR_LEAK_FRACTION = 0.08  # open fraction of a closed containment door segment

# D2Q9
C9 = np.array([[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]], dtype=int)
W9 = np.array([4 / 9] + [1 / 9] * 4 + [1 / 36] * 4)
OPP9 = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])
# D2Q5
C5 = np.array([[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1]], dtype=int)
W5 = np.array([1 / 3] + [1 / 6] * 4)
OPP5 = np.array([0, 3, 4, 1, 2])

# Schreiber AI dark style
BG = "#0B1018"
FG = "#EDF4FF"
CYAN = "#66E3FF"
MUTED = "#8DA2BF"


# ------------------------------------------------------------------ geometry
@dataclass
class Layout:
    """Cell-space description of the container plan view."""
    dx: float
    nx: int
    ny: int
    solid: np.ndarray                 # bool (nx, ny) walls, doors
    rack_mask: np.ndarray             # bool: rack fan/heat cells
    unit_mask: np.ndarray             # bool: cooling unit fan cells
    rack_cells: List[Tuple[slice, slice]]   # per rack (x-slice, y-slice)
    unit_cells: List[Tuple[slice, slice]]
    y_hot: Tuple[int, int]            # hot aisle y index range
    y_rack: Tuple[int, int]
    y_cold: Tuple[int, int]
    containment: bool
    door_cells: int = 0
    door_open_cells: int = 0
    notes: List[str] = field(default_factory=list)


def air_unit_count(cfg: Config) -> Tuple[int, int]:
    """(total, running) air-moving units in the plan view.

    Air- and water-cooled tiers: the configured cooling units (in-row / RDHx fans). Direct liquid
    cooling: the CDUs move no room air, so the residual air-side heat (30 % in the twin) is
    assumed handled by one in-row air unit per two racks plus one standby. This is an
    assumption of the CFD layout, reported in ``layout_notes``.
    """
    d = cfg.derived()
    if COOLING_LIBRARY[cfg.cooling]["medium"] == "liquid":
        n_run = max(1, math.ceil(cfg.racks / 2))
        return n_run + 1, n_run
    return d["cooling_units_total"], d["cooling_units_n"]


def layout_unit_count(cfg: Config) -> Tuple[int, int]:
    """(total, running) air units in the modelled row. Single-row tiers: all units. The BEN 2000 hall is
    modelled one row-bay at a time (docs/TIER_AND_ENCLOSURE_DECISION.md: "CFD per module"), so the
    units are shared evenly over ``rows``."""
    n_u, n_run = air_unit_count(cfg)
    rows = cfg.derived()["rows"]
    if rows <= 1:
        return n_u, n_run
    return max(1, math.ceil(n_u / rows)), max(1, math.ceil(n_run / rows))


def lattice_speed(tier: str) -> float:
    """Max lattice speed per tier (the BEN 5 cabinet's tiny compressed layout needs a lower Mach number)."""
    tier = canonical_tier(tier)
    return 0.04 if tier in ("ben5", "ben1") else U_LAT


def grid_dx(tier: str) -> float:
    """Cell size per tier chosen so a default run finishes in well under a minute (hall: 100 mm cells per row bay)."""
    tier = canonical_tier(tier)
    return {"ben5": 0.02, "ben30": 0.025, "ben150": 0.025, "ben500": 0.05, "ben2000": 0.10,
            "ben1": 0.02, "ben300": 0.025, "ben700": 0.05}.get(tier, 0.025)   # Rev 2: BEN 1 tiny grid; dense tiers as their container size


def build_layout(cfg: Config, containment: bool = True, dx: Optional[float] = None) -> Layout:
    d = cfg.derived()
    g = d["geometry"]
    L, W = g["int_l_m"], g["int_w_m"]
    dx = dx or grid_dx(cfg.tier)
    notes: List[str] = []
    rows = d["rows"]
    n_r = cfg.racks
    if rows > 1:
        # hall: one row bay (cold aisle + rack row + hot aisle) of the interior width; results are tiled over the rows
        W = W / rows
        n_r = d["racks_per_row"]
        notes.append(f"{g['label']} hall modelled as one of {rows} row bays ({n_r} racks, {W:.2f} m wide); per-rack results tiled over the rows")
    if d["kind"] == "cabinet" and containment:
        containment = False
        notes.append("BEN 5 cabinet has no aisle containment; doors treated as open")
    if d["kind"] == "minirack":
        containment = False
        notes.append(f"BEN 1 {cfg.form}: plan view of the mini rack interior (front intake to rear exhaust); no aisle containment"
                     + ("; open frame, the rack's fans are the IT devices' own" if cfg.form == "rack10" else "; cabinet extraction fans N+1"))
    if g.get("liquid_first"):
        notes.append(f"Liquid-first tier (Rev 2): CDUs move no room air; air side modelled with one in-row air unit per 2 racks + 1 standby standing in for the "
                     f"{d['fancoils_total']} trim-loop fan coils that carry the {COOLING_LIBRARY[cfg.cooling].get('air_residual', 0.1):.0%} residual air-side heat")
    elif COOLING_LIBRARY[cfg.cooling]["medium"] == "liquid":
        notes.append("DLC tier: CDUs move no room air; air side modelled with one in-row air unit per 2 racks + 1 standby "
                     "handling the 30 % residual air-side heat")
    nx, ny = int(round(L / dx)) + 2, int(round(W / dx)) + 2   # +2 for wall cells
    solid = np.zeros((nx, ny), bool)
    solid[0, :] = solid[-1, :] = True
    solid[:, 0] = solid[:, -1] = True

    # aisles across the width (y). y=1 is the front (cold) wall, y=ny-2 the back (hot) wall.
    inner = ny - 2
    hot_d = max(2, int(round(0.22 * inner)))
    rack_d = max(2, int(round(0.45 * inner)))
    y_hot = (ny - 1 - hot_d, ny - 1)              # [a, b)
    y_rack = (y_hot[0] - rack_d, y_hot[0])
    y_cold = (1, y_rack[0])

    n_u, n_u_run = layout_unit_count(cfg)
    rack_w = max(2, int(round(RACK_W_M / dx)))
    unit_w = max(1, int(round(UNIT_W_M / dx)))
    row_len = n_r * rack_w + n_u * unit_w
    inner_x = nx - 2
    if row_len > inner_x - 2:
        # compress widths to fit (BEN 5 cabinet and odd configs)
        scale = (inner_x - 2) / row_len
        rack_w = max(2, int(rack_w * scale))
        unit_w = max(1, int(unit_w * scale))
        row_len = n_r * rack_w + n_u * unit_w
        notes.append(f"row compressed to fit: rack {rack_w*dx:.2f} m, unit {unit_w*dx:.2f} m")
    x0 = 1 + (inner_x - row_len) // 2

    # interleave: distribute units as evenly as possible among racks (unit after rack k when due)
    order: List[str] = []
    placed_u = 0
    for k in range(n_r):
        order.append("R")
        due = int(round((k + 1) * n_u / n_r))
        while placed_u < due:
            order.append("U")
            placed_u += 1
    while placed_u < n_u:
        order.append("U")
        placed_u += 1

    rack_mask = np.zeros((nx, ny), bool)
    unit_mask = np.zeros((nx, ny), bool)
    rack_cells, unit_cells = [], []
    x = x0
    ys = slice(y_rack[0], y_rack[1])
    for item in order:
        if item == "R":
            xs = slice(x, x + rack_w)
            rack_mask[xs, ys] = True
            rack_cells.append((xs, ys))
            x += rack_w
        else:
            xs = slice(x, x + unit_w)
            unit_mask[xs, ys] = True
            unit_cells.append((xs, ys))
            x += unit_w
    x_end = x

    # containment doors: wall segments from row ends to container end walls, spanning rack depth,
    # with a leakage fraction of open cells when closed.
    door_cells = door_open_cells = 0
    for xd in (x0 - 1, x_end):
        if 1 <= xd <= nx - 2:
            cells = list(range(y_rack[0], y_rack[1]))
            door_cells += len(cells)
            if containment:
                n_open = max(1, int(round(DOOR_LEAK_FRACTION * len(cells))))
                open_idx = set(np.linspace(0, len(cells) - 1, n_open + 2, dtype=int)[1:-1].tolist())
                for j, yc in enumerate(cells):
                    if j in open_idx:
                        door_open_cells += 1
                    else:
                        solid[xd, yc] = True
            else:
                door_open_cells += len(cells)
    return Layout(dx, nx, ny, solid, rack_mask, unit_mask, rack_cells, unit_cells,
                  y_hot, y_rack, y_cold, containment, door_cells, door_open_cells, notes)


# ------------------------------------------------------------------ solver
def _feq9(rho: np.ndarray, ux: np.ndarray, uy: np.ndarray) -> np.ndarray:
    usq = 1.5 * (ux * ux + uy * uy)
    f = np.empty((9,) + rho.shape)
    for i in range(9):
        cu = 3.0 * (C9[i, 0] * ux + C9[i, 1] * uy)
        f[i] = W9[i] * rho * (1.0 + cu + 0.5 * cu * cu - usq)
    return f


def _geq5(T: np.ndarray, ux: np.ndarray, uy: np.ndarray) -> np.ndarray:
    g = np.empty((5,) + T.shape)
    for i in range(5):
        g[i] = W5[i] * T * (1.0 + 3.0 * (C5[i, 0] * ux + C5[i, 1] * uy))
    return g


def _stream(f: np.ndarray, c: np.ndarray) -> np.ndarray:
    out = np.empty_like(f)
    for i in range(c.shape[0]):
        out[i] = np.roll(np.roll(f[i], c[i, 0], axis=0), c[i, 1], axis=1)
    return out


class LBMSolver:
    """D2Q9 flow + two D2Q5 scalars (temperature, hot-air tracer) on a BEN plan-view layout."""

    def __init__(self, cfg: Config, layout: Layout, tau: float = TAU, u_lat: float = U_LAT,
                 supply_c: float = 20.0, load: float = 1.0, supply_ratio: float = 1.10,
                 active_units: Optional[List[bool]] = None):
        """``supply_ratio`` = cooling-unit airflow / rack airflow (1.10 = 10 % bypass, the twin
        default). ``active_units`` marks which units run; an inactive (standby or failed) unit is a
        solid block, and the running units share the whole supply airflow."""
        self.cfg, self.lay = cfg, layout
        d = cfg.derived()
        cl = COOLING_LIBRARY[cfg.cooling]
        dx = layout.dx
        self.tau, self.u_lat = tau, u_lat
        nu_lat = (tau - 0.5) / 3.0
        self.tau_T = 0.5 + 3.0 * nu_lat / PRANDTL
        self.supply_c = supply_c
        n_units_all = len(layout.unit_cells)
        if active_units is None:
            # mirror the twin: N units run, the redundant ones stand by
            n_run = min(n_units_all, layout_unit_count(cfg)[1])
            active_units = [i < n_run for i in range(n_units_all)]
        self.active_units = list(active_units)
        unit_mask = np.zeros_like(layout.unit_mask)
        solid = layout.solid.copy()
        for on, (xs, ys) in zip(self.active_units, layout.unit_cells):
            if on:
                unit_mask[xs, ys] = True
            else:
                solid[xs, ys] = True
        layout.solid = solid
        layout.unit_mask = unit_mask
        self.supply_ratio = supply_ratio

        # ---- physical flows
        it_kw = cfg.it_kw * load
        n_r = len(layout.rack_cells)                                       # racks in the modelled row (hall: one row bay)
        flow_total = d["airflow_cfm"] * CFM_TO_M3S * max(0.2, load) * n_r / cfg.racks   # m3/s through the modelled racks
        air_frac = 1.0 if cl["medium"] == "air" else 0.3                  # DLC: residual air-side heat
        rack_kw = it_kw / cfg.racks * air_frac
        n_u = max(1, sum(1 for a in self.active_units if a))
        rack_face_m = (layout.rack_cells[0][0].stop - layout.rack_cells[0][0].start) * dx
        unit_face_m = (layout.unit_cells[0][0].stop - layout.unit_cells[0][0].start) * dx if layout.unit_cells else rack_face_m
        self.u_rack_phys = flow_total / n_r / (rack_face_m * RACK_H_M)
        # running units share the supply airflow (rack flow x supply_ratio)
        self.u_unit_phys = flow_total * supply_ratio / n_u / (unit_face_m * RACK_H_M)
        u_max_phys = max(self.u_rack_phys, self.u_unit_phys, 1e-6)
        self.dt = dx * u_lat / u_max_phys                                  # s per lattice step
        self.u_rack = self.u_rack_phys / u_max_phys * u_lat
        self.u_unit = self.u_unit_phys / u_max_phys * u_lat
        m_dot = flow_total / n_r * AIR_RHO                                  # kg/s per rack
        self.dT_rack = rack_kw * 1000.0 / max(m_dot * AIR_CP, 1e-6)        # K rise across a rack
        n_depth = layout.y_rack[1] - layout.y_rack[0]
        # source per rack cell per step so that u_design * width * dT = total heat (lattice units)
        self.src_T = self.u_rack * self.dT_rack / n_depth
        self.src_C = self.u_rack * 1.0 / n_depth
        self.re_lattice = self.u_unit * (layout.y_cold[1] - layout.y_cold[0]) / nu_lat
        cold_aisle_m = (layout.y_cold[1] - layout.y_cold[0]) * dx
        self.re_real = self.u_unit_phys * cold_aisle_m / AIR_NU
        self.alpha_rack = 0.5    # server fans: soft prescribed velocity (pressure can slow them)
        self.alpha_unit = 1.0    # cooling unit blowers: hard prescribed velocity

        # ---- fields
        nx, ny = layout.nx, layout.ny
        self.rho = np.ones((nx, ny))
        self.ux = np.zeros((nx, ny))
        self.uy = np.zeros((nx, ny))
        self.T = np.full((nx, ny), supply_c + 0.5 * self.dT_rack)
        self.C = np.zeros((nx, ny))
        self.f = _feq9(self.rho, self.ux, self.uy)
        self.g = _geq5(self.T, self.ux, self.uy)
        self.h = _geq5(self.C, self.ux, self.uy)
        self.solid = layout.solid
        self.fluid = ~self.solid
        self.rack = layout.rack_mask
        self.unit = layout.unit_mask
        self.steps_done = 0

    # ---- one lattice step
    def step(self):
        f, g, h = self.f, self.g, self.h
        rho = f.sum(0)
        ux = (f[1] + f[5] + f[8] - f[3] - f[6] - f[7]) / rho
        uy = (f[2] + f[5] + f[6] - f[4] - f[7] - f[8]) / rho
        # fan zones: relax velocity toward target (racks blow +y: cold aisle -> hot aisle; units -y)
        ux = np.where(self.rack, (1 - self.alpha_rack) * ux, ux)
        uy = np.where(self.rack, (1 - self.alpha_rack) * uy + self.alpha_rack * self.u_rack, uy)
        ux = np.where(self.unit, 0.0, ux)
        uy = np.where(self.unit, -self.u_unit, uy)
        ux[self.solid] = 0.0
        uy[self.solid] = 0.0
        self.rho, self.ux, self.uy = rho, ux, uy

        # flow collision (BGK) + bounce-back on solids
        feq = _feq9(rho, ux, uy)
        fpost = f - (f - feq) / self.tau
        fpost[:, self.solid] = f[OPP9][:, self.solid]
        self.f = _stream(fpost, C9)

        # scalars
        T = g.sum(0)
        Cc = h.sum(0)
        # sources: racks heat and release tracer; units reset to supply / zero
        T = np.where(self.rack, T + self.src_T, T)
        Cc = np.where(self.rack, np.minimum(1.0, Cc + self.src_C), Cc)
        T = np.where(self.unit, self.supply_c, T)
        Cc = np.where(self.unit, 0.0, Cc)
        geq = _geq5(T, ux, uy)
        heq = _geq5(Cc, ux, uy)
        gpost = g - (g - geq) / self.tau_T
        hpost = h - (h - heq) / self.tau_T
        # scalar bounce-back (adiabatic / zero-flux walls)
        gpost[:, self.solid] = g[OPP5][:, self.solid]
        hpost[:, self.solid] = h[OPP5][:, self.solid]
        self.g = _stream(gpost, C5)
        self.h = _stream(hpost, C5)
        self.T, self.C = T, Cc
        self.steps_done += 1

    # ---- probes
    def rack_inlet_faces(self) -> List[Tuple[slice, int]]:
        yf = self.lay.y_rack[0] - 2
        return [(xs, yf) for xs, _ in self.lay.rack_cells]

    def rack_outlet_faces(self) -> List[Tuple[slice, int]]:
        yf = self.lay.y_rack[1]
        return [(xs, yf) for xs, _ in self.lay.rack_cells]

    def metrics(self) -> Dict[str, Any]:
        lay = self.lay
        inlet_T = [float(self.T[xs, yf].mean()) for xs, yf in self.rack_inlet_faces()]
        inlet_C = [float(np.clip(self.C[xs, yf].mean(), 0.0, 1.0)) for xs, yf in self.rack_inlet_faces()]
        outlet_T = [float(self.T[xs, yf].mean()) for xs, yf in self.rack_outlet_faces()]
        y_ret = lay.y_rack[1]
        return_T = [float(self.T[xs, y_ret].mean()) for on, (xs, _) in zip(self.active_units, lay.unit_cells) if on] or [float("nan")]
        cold = np.zeros_like(self.rho, bool)
        cold[:, lay.y_cold[0]:lay.y_cold[1]] = True
        hot = np.zeros_like(self.rho, bool)
        hot[:, lay.y_hot[0]:lay.y_hot[1]] = True
        cold &= self.fluid
        hot &= self.fluid
        # pressure: p = rho cs^2 in lattice units; convert with rho_air (dx/dt)^2
        scale = AIR_RHO * (lay.dx / self.dt) ** 2
        dp_pa = float((self.rho[cold].mean() - self.rho[hot].mean()) / 3.0 * scale)
        umag = np.sqrt(self.ux ** 2 + self.uy ** 2)
        # hall: the modelled row bay stands for every row; tile the per-rack results to cfg.racks
        reps = max(1, math.ceil(self.cfg.racks / max(1, len(inlet_T))))
        inlet_T = (inlet_T * reps)[: self.cfg.racks]
        inlet_C = (inlet_C * reps)[: self.cfg.racks]
        outlet_T = (outlet_T * reps)[: self.cfg.racks]
        return {
            "tier": self.cfg.tier, "racks": self.cfg.racks, "racks_modelled": len(lay.rack_cells), "rows": self.cfg.derived()["rows"], "containment": lay.containment,
            "active_units": list(self.active_units), "supply_ratio": self.supply_ratio,
            "grid": [lay.nx, lay.ny], "dx_m": lay.dx, "dt_s": self.dt, "steps": self.steps_done,
            "sim_time_s": self.steps_done * self.dt,
            "supply_c": self.supply_c,
            "rack_inlet_c": [round(v, 2) for v in inlet_T],
            "rack_outlet_c": [round(v, 2) for v in outlet_T],
            "recirculation_index": [round(v, 3) for v in inlet_C],
            "max_rack_inlet_c": round(max(inlet_T), 2),
            "supply_to_inlet_rise_k": round(float(np.mean(inlet_T)) - self.supply_c, 2),
            "worst_rack": int(np.argmax(inlet_T)) + 1,
            "return_c_mean": round(float(np.nanmean(return_T)), 2),
            "aisle_dp_proxy_pa": round(dp_pa, 2),
            "design_rack_delta_t_k": round(self.dT_rack, 2),
            "u_rack_face_m_s": round(self.u_rack_phys, 3), "u_unit_face_m_s": round(self.u_unit_phys, 3),
            "u_lattice_max": round(float(umag[self.fluid].max()), 4), "tau": self.tau,
            "re_lattice": round(self.re_lattice, 1), "re_real_estimate": round(self.re_real, 0),
            "door_leak_open_fraction": round(lay.door_open_cells / max(lay.door_cells, 1), 3),
            "layout_notes": lay.notes,
        }


# ------------------------------------------------------------------ steady scalar transport
def steady_scalar(solver: "LBMSolver", source: float, dirichlet_value: float, diffusivity: float = 0.003) -> np.ndarray:
    """Exact steady state of a passive scalar on the solver's current velocity field.

    First-order upwind finite volumes in the bounded (non-conservative) form: each fluid cell's
    value is the inflow-weighted mean of its upstream neighbours plus source / inflow, with a
    small explicit diffusivity (lattice units) and zero-flux walls. Cooling-unit cells are fixed
    at ``dirichlet_value``; rack cells receive ``source`` per lattice step. This is what the D2Q5
    LBM scalars converge to, but reached in one sparse direct solve instead of the tens of
    thousands of steps a slow hot-aisle leakage loop would need.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import spsolve

    lay = solver.lay
    nx, ny = lay.nx, lay.ny
    fluid = solver.fluid
    idx = -np.ones((nx, ny), dtype=int)
    idx[fluid] = np.arange(int(fluid.sum()))
    n = int(fluid.sum())
    mx, my = solver.rho * solver.ux, solver.rho * solver.uy
    rows, cols, vals = [], [], []
    rhs = np.zeros(n)
    diag = np.zeros(n)
    unit = solver.unit
    I, J = np.nonzero(fluid)
    ii = idx[I, J]
    src = np.where(solver.rack[I, J], source, 0.0)
    rhs += np.bincount(ii, src, minlength=n)
    for dxn, dyn in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        In, Jn = I + dxn, J + dyn
        ok = (In >= 0) & (In < nx) & (Jn >= 0) & (Jn < ny)
        ok &= fluid[np.clip(In, 0, nx - 1), np.clip(Jn, 0, ny - 1)]
        a, b, an, bn = I[ok], J[ok], In[ok], Jn[ok]
        jj = idx[an, bn]
        # mass flux through the face from neighbour into cell (positive = inflow)
        fn = 0.5 * ((mx[a, b] + mx[an, bn]) * (-dxn) + (my[a, b] + my[an, bn]) * (-dyn))
        inflow = np.maximum(fn, 0.0) + diffusivity
        kk = ii[ok]
        diag += np.bincount(kk, inflow, minlength=n)
        rows.append(kk)
        cols.append(jj)
        vals.append(-inflow)
    rows.append(np.arange(n)); cols.append(np.arange(n)); vals.append(diag + 1e-12)
    rows = np.concatenate(rows); cols = np.concatenate(cols); vals = np.concatenate(vals)
    # Dirichlet in cooling-unit cells: overwrite rows
    fixed = unit[I, J]
    fixed_ids = ii[fixed]
    keep = ~np.isin(rows, fixed_ids)
    rows, cols, vals = rows[keep], cols[keep], vals[keep]
    rows = np.concatenate([rows, fixed_ids]); cols = np.concatenate([cols, fixed_ids]); vals = np.concatenate([vals, np.ones(len(fixed_ids))])
    rhs[fixed_ids] = dirichlet_value
    A = coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
    sol = spsolve(A, rhs)
    out = np.full((nx, ny), dirichlet_value)
    out[fluid] = sol
    return out


# ------------------------------------------------------------------ public API
def default_steps(tier: str) -> int:
    """Upper bound on lattice steps for the flow field (stops earlier on convergence)."""
    tier = canonical_tier(tier)
    return {"ben5": 3000, "ben30": 4000, "ben150": 5000, "ben500": 5000, "ben2000": 3000, "ben1": 2000, "ben300": 5000, "ben700": 5000}.get(tier, 4000)


def run_cfd(cfg: Config, containment: bool = True, steps: Optional[int] = None, out_png: Optional[str] = None,
            dx: Optional[float] = None, load: float = 1.0, supply_c: float = 20.0,
            supply_ratio: float = 1.10, failed_units: Optional[List[int]] = None,
            check_every: int = 250, tol_u: float = 2e-3, return_solver: bool = False) -> Dict[str, Any]:
    """Run the flow to steady state, solve the steady scalars, return the metrics dict.

    ``steps=None`` runs the D2Q9 flow up to ``default_steps(tier)`` lattice steps but stops early
    once the velocity field changes by less than ``tol_u`` (lattice units) over ``check_every``
    steps. The temperature and tracer fields reported are then the exact steady state on that
    velocity field (``steady_scalar``); the D2Q5 LBM transient values at the last step are kept
    in ``lbm_transient_inlet_c`` for comparison. The dict also carries ``fields`` (numpy arrays:
    T, C, ux, uy, solid, rack, unit) and ``png`` when one was written.
    """
    t0 = time.perf_counter()
    lay = build_layout(cfg, containment=containment, dx=dx)
    active = None
    if failed_units:
        # failed unit(s) off; the standby unit starts (as the twin's controller does)
        d = cfg.derived()
        n_all = len(lay.unit_cells)
        active = [False] * n_all
        healthy = [i for i in range(n_all) if i not in set(failed_units)]
        for i in healthy[: layout_unit_count(cfg)[1]]:
            active[i] = True
    s = LBMSolver(cfg, lay, load=load, supply_c=supply_c, supply_ratio=supply_ratio, active_units=active,
                  u_lat=lattice_speed(cfg.tier))
    max_steps = steps or default_steps(cfg.tier)
    converged = False
    prev_u = None
    history: List[float] = []
    du_hist: List[float] = []
    for k in range(1, max_steps + 1):
        s.step()
        if k % check_every == 0 or k == max_steps:
            m = float(np.mean([s.T[xs, yf].mean() for xs, yf in s.rack_inlet_faces()]))
            if not np.isfinite(m) or not np.isfinite(s.rho).all():
                raise FloatingPointError("CFD diverged (non-finite field); lower U_LAT or raise TAU")
            history.append(m)
            umag = np.sqrt(s.ux ** 2 + s.uy ** 2)
            if prev_u is not None:
                du = float(np.abs(umag - prev_u).max())
                du_hist.append(du)
                # velocity field steady: max change over the interval below tol_u (lattice units)
                if steps is None and du < tol_u and k >= min(1500, max_steps // 2):
                    converged = True
                    break
            prev_u = umag
    # transient (LBM D2Q5) inlet temperatures at the last step, kept for comparison
    lbm_inlet = [round(float(s.T[xs, yf].mean()), 2) for xs, yf in s.rack_inlet_faces()]
    # steady scalars on the converged velocity field
    s.T = steady_scalar(s, s.src_T, s.supply_c)
    s.C = np.clip(steady_scalar(s, s.src_C, 0.0), 0.0, 1.0)
    met = s.metrics()
    met["flow_converged"] = converged
    met["flow_du_history"] = [round(v, 5) for v in du_hist]
    met["runtime_s"] = round(time.perf_counter() - t0, 2)
    met["lbm_transient_inlet_c"] = lbm_inlet
    met["lbm_transient_time_s"] = round(s.steps_done * s.dt, 3)
    met["inlet_mean_history_c"] = [round(v, 3) for v in history]
    met["fields"] = {"T": s.T, "C": s.C, "ux": s.ux, "uy": s.uy, "solid": lay.solid,
                     "rack": lay.rack_mask, "unit": lay.unit_mask}
    if out_png:
        plot_fields(met, out_png)
        met["png"] = out_png
    if return_solver:
        met["solver"] = s
    return met


def recirculation_profile(cfg: Config, containment: bool = True, **kw) -> List[float]:
    """Per-rack recirculation fractions for ``TwinParams.recirculation_profile``."""
    m = run_cfd(cfg, containment=containment, **kw)
    return list(m["recirculation_index"])


def apply_to_params(metrics: Dict[str, Any], params):
    """Copy CFD recirculation indices into a TwinParams (returns the same object)."""
    params.recirculation_profile = list(metrics["recirculation_index"])
    params.recirculation = float(np.mean(metrics["recirculation_index"]))
    return params


def metrics_json(metrics: Dict[str, Any]) -> str:
    """Metrics without the numpy fields, as JSON."""
    return json.dumps({k: v for k, v in metrics.items() if k not in ("fields", "solver")}, indent=2)


# ------------------------------------------------------------------ plotting
def plot_fields(metrics: Dict[str, Any], out_png: str, title: Optional[str] = None) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, LinearSegmentedColormap

    F = metrics["fields"]
    T, C, ux, uy = F["T"], F["C"], F["ux"], F["uy"]
    solid, rack, unit = F["solid"], F["rack"], F["unit"]
    dx = metrics["dx_m"]
    nx, ny = T.shape
    extent = [0, nx * dx, 0, ny * dx]

    plt.rcParams.update({"text.color": FG, "axes.labelcolor": FG, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.edgecolor": "#223044", "font.family": "DejaVu Sans"})
    fig_h = min(12.0, max(5.5, 2 * 13 * ny / nx * 1.15 + 1.9))
    fig, axes = plt.subplots(2, 1, figsize=(13, fig_h), facecolor=BG)
    hot_cmap = LinearSegmentedColormap.from_list("ben_hot", ["#0B1018", "#1F4F8F", CYAN, "#F2F5A0", "#FF6B4A"])
    rec_cmap = LinearSegmentedColormap.from_list("ben_rec", ["#0B1018", "#14405A", CYAN, "#FFFFFF"])

    Tm = np.ma.array(T, mask=solid).T
    Cm = np.ma.array(np.clip(C, 0, 1), mask=solid).T
    for ax, field_, cmap, label in ((axes[0], Tm, hot_cmap, "Air temperature [°C]"),
                                    (axes[1], Cm, rec_cmap, "Hot-air tracer (1 = rack exhaust, 0 = supply)")):
        ax.set_facecolor(BG)
        im = ax.imshow(field_, origin="lower", extent=extent, cmap=cmap, aspect="equal", interpolation="bilinear")
        # overlays
        ax.imshow(np.ma.array(np.ones_like(T), mask=~rack).T, origin="lower", extent=extent,
                  cmap=ListedColormap(["#2A3344"]), alpha=0.55, aspect="equal")
        ax.imshow(np.ma.array(np.ones_like(T), mask=~unit).T, origin="lower", extent=extent,
                  cmap=ListedColormap([CYAN]), alpha=0.35, aspect="equal")
        ax.imshow(np.ma.array(np.ones_like(T), mask=~solid).T, origin="lower", extent=extent,
                  cmap=ListedColormap(["#3A4556"]), aspect="equal")
        cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
        cb.ax.yaxis.set_tick_params(color=MUTED)
        cb.outline.set_edgecolor("#223044")
        plt.setp(cb.ax.get_yticklabels(), color=FG)
        ax.set_title(label, loc="left", fontsize=11, color=FG)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
    # velocity arrows on the temperature panel
    stride = max(1, nx // 60)
    X, Y = np.meshgrid((np.arange(nx) + 0.5) * dx, (np.arange(ny) + 0.5) * dx, indexing="ij")
    msk = ~solid
    axes[0].quiver(X[::stride, ::stride], Y[::stride, ::stride],
                   np.where(msk, ux, 0)[::stride, ::stride], np.where(msk, uy, 0)[::stride, ::stride],
                   color=FG, alpha=0.55, scale=metrics["u_lattice_max"] * 25, width=0.0015)
    # rack labels
    ri = metrics["recirculation_index"]
    n_on = sum(1 for a in metrics["active_units"] if a)
    ttl = title or (f"Schreiber AI · BEN Engine CFD · {metrics['tier']} · {metrics['racks']} racks · "
                    f"containment {'closed' if metrics['containment'] else 'OPEN'} · {n_on}/{len(metrics['active_units'])} cooling units running · "
                    f"supply/rack airflow {metrics['supply_ratio']:.2f}")
    fig.suptitle(ttl, color=CYAN, fontsize=13, x=0.01, ha="left", y=1 - 0.12 / fig_h, va="top")
    sub1 = (f"max rack inlet {metrics['max_rack_inlet_c']:.1f} °C · supply→inlet rise {metrics['supply_to_inlet_rise_k']:.2f} K · "
            f"recirculation per rack {', '.join(f'{v:.2f}' for v in ri)} · worst rack {metrics['worst_rack']} · "
            f"aisle ΔP proxy {metrics['aisle_dp_proxy_pa']:.1f} Pa")
    sub2 = (f"grid {metrics['grid'][0]}×{metrics['grid'][1]} @ {metrics['dx_m']} m · Re lattice {metrics['re_lattice']:.0f} vs real ~{metrics['re_real_estimate']:.0e} · "
            f"2-D plan view, laminar, qualitative/relative tool · fields are the steady state on the converged LBM velocity field")
    top = 1 - 0.95 / fig_h
    fig.text(0.01, 1 - 0.55 / fig_h, sub1, color=MUTED, fontsize=8.5, ha="left")
    fig.text(0.01, 1 - 0.80 / fig_h, sub2, color=MUTED, fontsize=8.5, ha="left")
    fig.tight_layout(rect=[0, 0, 1, top])
    fig.savefig(out_png, dpi=110, facecolor=BG)
    plt.close(fig)
    return out_png


# ------------------------------------------------------------------ CLI
def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="BEN Engine 2-D thermal LBM airflow solver")
    ap.add_argument("--tier", default="ben150")
    ap.add_argument("--profile", default="ai_inference")
    ap.add_argument("--climate", default="temperate")
    ap.add_argument("--png", default=None, help="output PNG path")
    ap.add_argument("--open", action="store_true", help="containment doors open")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--dx", type=float, default=None, help="cell size in m (default per tier)")
    ap.add_argument("--load", type=float, default=1.0)
    ap.add_argument("--supply-ratio", type=float, default=1.10, help="unit airflow / rack airflow")
    ap.add_argument("--fail-unit", type=int, action="append", default=None, help="0-based unit index to fail (repeatable)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cfg = Config.preset(a.tier, a.profile, a.climate)
    m = run_cfd(cfg, containment=not a.open, steps=a.steps, out_png=a.png, dx=a.dx, load=a.load,
                supply_ratio=a.supply_ratio, failed_units=a.fail_unit)
    if a.json:
        print(metrics_json(m))
    else:
        print(f"BEN Engine CFD — {m['tier']} — {m['racks']} racks — containment {'closed' if m['containment'] else 'open'} — "
              f"units running {m['active_units']} — supply ratio {m['supply_ratio']}")
        print(f"  grid {m['grid'][0]}x{m['grid'][1]} @ {m['dx_m']} m, {m['steps']} flow steps ({m['sim_time_s']:.1f} s of flow), "
              f"runtime {m['runtime_s']} s, flow_converged={m['flow_converged']}; scalars solved to steady state")
        print(f"  LBM transient inlet (for comparison) {m['lbm_transient_inlet_c']}")
        print(f"  rack inlet C        {m['rack_inlet_c']}")
        print(f"  recirculation index {m['recirculation_index']}")
        print(f"  max inlet {m['max_rack_inlet_c']} C, rise {m['supply_to_inlet_rise_k']} K, return {m['return_c_mean']} C, "
              f"aisle dP proxy {m['aisle_dp_proxy_pa']} Pa")
        print(f"  Re lattice {m['re_lattice']} vs real ~{m['re_real_estimate']:.0f}; u_lat max {m['u_lattice_max']}; tau {m['tau']}")
        if a.png:
            print(f"  png {a.png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
