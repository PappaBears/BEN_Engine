"""BEN Engine calibration and measurement-uncertainty tools (GUM style).

Plain-language summary
----------------------
* ``linear_fit(reference, reading)`` fits the correction the node applies
  (``corrected = gain * reading + offset``) by least squares against a reference instrument and
  returns the coefficients, their standard uncertainties, the residual scatter and a function
  ``u95_at(x)`` giving the expanded (k≈2, 95 %) uncertainty of a corrected reading at ``x``.
* ``tare(readings)`` turns a set of zero readings (e.g. differential pressure with both ports
  open) into an offset and its Type A uncertainty.
* ``UncertaintySource`` + ``combine()`` build a GUM uncertainty budget: each source has a value,
  a distribution (normal / rectangular / triangular / U-shaped) whose divisor turns it into a
  standard uncertainty, a sensitivity coefficient and degrees of freedom. The combined standard
  uncertainty is the root sum of squares; the effective degrees of freedom come from
  Welch–Satterthwaite and set the coverage factor ``k`` for 95 % from Student's t.
* ``default_budget(channel, placement=...)`` returns the budget for each channel in
  spec/PROTOCOL.md (DS18B20, SHT45 temperature and RH, SDP810, ADS1115 4–20 mA loop, CT /
  power meter class 0.5) including installation (placement) effects as Type B terms.
* ``predictability_score`` compares a model's 95 % prediction interval with the margin to the
  alarm threshold: below 1 the model can tell you before the alarm does.
* ``markdown_report`` writes everything as tables.

Numbers in the default budgets are datasheet or handbook values with the source named in the
``note`` field; the "after calibration" result is whatever the arithmetic gives, not a target.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import numpy as np
from scipy import stats

DIVISORS = {"normal": 1.0, "normal_k2": 2.0, "rectangular": math.sqrt(3.0), "triangular": math.sqrt(6.0), "u_shaped": math.sqrt(2.0)}


# ------------------------------------------------------------------ fits
@dataclass
class CalResult:
    gain: float
    offset: float
    residual_std: float
    u_gain: float
    u_offset: float
    cov_gain_offset: float
    n: int
    dof: int
    x_mean: float
    reference: List[float]
    reading: List[float]
    residuals: List[float]

    def correct(self, x: float) -> float:
        return self.gain * x + self.offset

    def u_at(self, x: float) -> float:
        """Standard uncertainty of a *new* corrected reading at raw value x (coefficients + scatter)."""
        var_coef = (x * x) * self.u_gain ** 2 + self.u_offset ** 2 + 2.0 * x * self.cov_gain_offset
        return math.sqrt(max(var_coef, 0.0) + self.residual_std ** 2)

    def u95_at(self, x: float) -> float:
        k = float(stats.t.ppf(0.975, max(self.dof, 1))) if self.dof < 1000 else 1.96
        return k * self.u_at(x)

    @property
    def k95(self) -> float:
        return float(stats.t.ppf(0.975, max(self.dof, 1)))

    def to_dict(self) -> Dict[str, Any]:
        return {"gain": self.gain, "offset": self.offset, "residual_std": self.residual_std, "u_gain": self.u_gain,
                "u_offset": self.u_offset, "n": self.n, "dof": self.dof, "k95": self.k95,
                "u95_at_mean": self.u95_at(self.x_mean)}


def linear_fit(reference: Sequence[float], reading: Sequence[float]) -> CalResult:
    """Least-squares fit of ``reference = gain * reading + offset``.

    ``reference`` are the values of the reference instrument, ``reading`` the raw node readings at
    the same points. At least three points are needed for a residual estimate.
    """
    x = np.asarray(reading, dtype=float)
    y = np.asarray(reference, dtype=float)
    if x.shape != y.shape or x.size < 2:
        raise ValueError("need matching reference/reading arrays with at least 2 points")
    n = x.size
    A = np.vstack([x, np.ones(n)]).T
    coef, res, rank, sv = np.linalg.lstsq(A, y, rcond=None)
    gain, offset = float(coef[0]), float(coef[1])
    resid = y - (gain * x + offset)
    dof = max(n - 2, 1)
    s2 = float(resid @ resid) / dof if n > 2 else 0.0
    cov = s2 * np.linalg.inv(A.T @ A)
    return CalResult(gain=gain, offset=offset, residual_std=math.sqrt(s2), u_gain=math.sqrt(max(cov[0, 0], 0)),
                     u_offset=math.sqrt(max(cov[1, 1], 0)), cov_gain_offset=float(cov[0, 1]), n=n, dof=dof,
                     x_mean=float(x.mean()), reference=list(map(float, y)), reading=list(map(float, x)),
                     residuals=list(map(float, resid)))


@dataclass
class TareResult:
    offset: float          # value to ADD to readings (negative of the mean zero reading)
    mean_zero: float
    std: float
    u_offset: float        # Type A standard uncertainty of the mean
    n: int

    def to_dict(self):
        return self.__dict__.copy()


def tare(readings: Sequence[float]) -> TareResult:
    """Zero offset from repeated readings at a known zero (both pressure ports open, etc.)."""
    x = np.asarray(readings, dtype=float)
    if x.size < 1:
        raise ValueError("no readings")
    sd = float(x.std(ddof=1)) if x.size > 1 else 0.0
    return TareResult(offset=-float(x.mean()), mean_zero=float(x.mean()), std=sd, u_offset=sd / math.sqrt(x.size), n=int(x.size))


# ------------------------------------------------------------------ budgets
@dataclass
class UncertaintySource:
    name: str
    value: float                      # half-width (rectangular/triangular/U), std dev (normal) or U95 (normal_k2)
    distribution: str = "rectangular"
    type: str = "B"                   # "A" or "B"
    sensitivity: float = 1.0
    dof: float = math.inf
    unit: str = ""
    note: str = ""
    correction: float = 0.0           # known systematic effect that is corrected for (informational)

    @property
    def divisor(self) -> float:
        return DIVISORS[self.distribution]

    @property
    def u(self) -> float:
        """Standard uncertainty contribution (after sensitivity)."""
        return abs(self.sensitivity) * self.value / self.divisor


@dataclass
class Budget:
    channel: str
    unit: str
    sources: List[UncertaintySource]
    u_c: float
    nu_eff: float
    k: float
    U95: float
    total_correction: float = 0.0
    notes: List[str] = field(default_factory=list)

    def dominant(self) -> UncertaintySource:
        return max(self.sources, key=lambda s: s.u)

    def to_dict(self) -> Dict[str, Any]:
        return {"channel": self.channel, "unit": self.unit, "u_c": self.u_c, "nu_eff": self.nu_eff, "k": self.k, "U95": self.U95,
                "total_correction": self.total_correction, "dominant": self.dominant().name,
                "sources": [{"name": s.name, "value": s.value, "distribution": s.distribution, "type": s.type, "u": s.u, "dof": s.dof, "note": s.note} for s in self.sources]}


def combine(sources: Iterable[UncertaintySource], channel: str = "", unit: str = "", notes: Optional[List[str]] = None) -> Budget:
    """GUM combination: RSS of standard uncertainties, Welch–Satterthwaite effective dof, t-based k."""
    src = list(sources)
    if not src:
        raise ValueError("empty budget")
    u2 = sum(s.u ** 2 for s in src)
    u_c = math.sqrt(u2)
    denom = 0.0
    for s in src:
        if math.isfinite(s.dof) and s.dof > 0:
            denom += s.u ** 4 / s.dof
    nu_eff = math.inf if denom == 0 else u2 ** 2 / denom
    k = 1.96 if (not math.isfinite(nu_eff) or nu_eff > 1000) else float(stats.t.ppf(0.975, nu_eff))
    return Budget(channel, unit, src, u_c, nu_eff, k, k * u_c, sum(s.correction for s in src), list(notes or []))


# placement / installation effects (Type B), applied by name
PLACEMENT_EFFECTS: Dict[str, UncertaintySource] = {
    # probe within 50 mm of a perforated rack door: it sits in the mixing layer and reads 0.3–0.8 K high
    "inlet_near_perforated_door": UncertaintySource("placement: inlet probe < 50 mm from perforated door", 0.25, "rectangular", "B",
                                                     unit="K", correction=-0.55,
                                                     note="reads 0.3–0.8 K high; corrected by −0.55 K, half-width 0.25 K"),
    # probe at standard 100–150 mm stand-off, mid-height
    "inlet_standard_standoff": UncertaintySource("placement: inlet probe stand-off 100–150 mm", 0.15, "rectangular", "B", unit="K",
                                                 note="spatial non-uniformity across the rack face at the probe height"),
    # unshielded probe seeing the hot aisle: radiation from 35–45 C surfaces
    "hot_aisle_radiation": UncertaintySource("placement: radiation from hot-aisle surfaces to an unshielded probe", 0.20, "rectangular", "B",
                                             unit="K", correction=-0.20, note="+0.1…+0.4 K; corrected −0.2 K; use a radiation shield to remove"),
    # probe clipped to a metal rail: conduction toward rail temperature
    "wall_conduction_mount": UncertaintySource("placement: conduction through metal mounting", 0.15, "rectangular", "B", unit="K",
                                               note="probe stem in contact with rail or panel; stand-off clip removes most of it"),
    # pressure tap in the discharge jet of a cooling unit fan
    "pressure_tap_near_fan_discharge": UncertaintySource("placement: pressure tap within 0.5 m of a fan discharge", 3.0, "rectangular", "B",
                                                         unit="Pa", note="dynamic pressure contaminates the static reading; ±3 Pa typical at 2–3 m/s"),
    # pressure tap in quiet air behind a baffle
    "pressure_tap_quiet": UncertaintySource("placement: static tap in quiet air", 0.3, "rectangular", "B", unit="Pa",
                                            note="residual velocity effect behind baffle"),
    # RH sensor near the cooling coil: local saturation / condensation events
    "rh_near_coil": UncertaintySource("placement: RH sensor within 0.3 m of cooling coil", 3.0, "rectangular", "B", unit="%RH",
                                      note="local cold spots; move sensor to the return path"),
    # CT on a conductor near other phases: external field, and off-centre conductor
    "ct_crowded_conductor": UncertaintySource("placement: CT near adjacent phase conductors / off-centre", 0.3, "rectangular", "B", unit="%",
                                              note="external field and conductor position; percent of reading"),
}


def default_budget(channel: str, placement: Optional[Sequence[str]] = None, calibrated: bool = True,
                   reading: Optional[float] = None, cal: Optional[CalResult] = None) -> Budget:
    """Default uncertainty budget per PROTOCOL.md channel.

    ``channel`` one of: ``DS18B20`` (rack inlet/outlet), ``SHT45_T``, ``SHT45_RH``, ``SDP810``,
    ``ADS1115_4_20MA``, ``POWER_CLASS05``. ``placement`` lists keys of ``PLACEMENT_EFFECTS``.
    ``calibrated=False`` replaces the calibration terms with the bare datasheet accuracy. If a
    ``CalResult`` is given its residual scatter and coefficient uncertainty are used as the Type A
    term at ``reading``.
    """
    ch = channel.upper()
    S: List[UncertaintySource] = []
    notes: List[str] = []
    if ch == "DS18B20":
        unit = "K"
        if calibrated:
            S.append(UncertaintySource("reference thermometer (bath comparison)", 0.05, "normal_k2", "B", unit=unit, note="reference certificate U95 = 0.05 K"))
            S.append(UncertaintySource("bath uniformity / stability during comparison", 0.03, "rectangular", "B", unit=unit, note="stirred bath"))
            if cal is not None and reading is not None:
                S.append(UncertaintySource("fit residual + coefficient uncertainty (Type A)", cal.u_at(reading), "normal", "A", dof=cal.dof, unit=unit,
                                           note=f"from linear_fit, n={cal.n}"))
            else:
                S.append(UncertaintySource("calibration repeatability (Type A)", 0.04, "normal", "A", dof=9, unit=unit, note="10 readings per point"))
            S.append(UncertaintySource("post-calibration drift, 12 months", 0.10, "rectangular", "B", unit=unit, note="DS18B20 field experience 0.05–0.2 K/yr; recalibrate yearly"))
        else:
            S.append(UncertaintySource("datasheet accuracy −10…85 °C (uncalibrated)", 0.5, "rectangular", "B", unit=unit, note="DS18B20 datasheet ±0.5 K"))
        S.append(UncertaintySource("resolution 12 bit (0.0625 K)", 0.0625 / 2, "rectangular", "B", unit=unit))
        S.append(UncertaintySource("self-heating (parasitic power, moving air)", 0.05, "rectangular", "B", unit=unit, note="datasheet < 0.1 K in still air; moving air halves it"))
        S.append(UncertaintySource("thermal lag at 1 Hz, slow drift", 0.03, "rectangular", "B", unit=unit, note="TO-92 time constant ~10 s; negligible except during steps"))
        S.append(UncertaintySource("1-Wire string: supply / ground offset", 0.02, "rectangular", "B", unit=unit))
    elif ch == "SHT45_T":
        unit = "K"
        S.append(UncertaintySource("datasheet accuracy typical 0…60 °C", 0.1, "rectangular", "B", unit=unit, note="SHT45 typ ±0.1 K, max ±0.2 K"))
        if calibrated:
            S.append(UncertaintySource("reference thermometer", 0.05, "normal_k2", "B", unit=unit))
            S.append(UncertaintySource("calibration repeatability (Type A)", 0.02, "normal", "A", dof=9, unit=unit))
        S.append(UncertaintySource("drift 12 months", 0.03, "rectangular", "B", unit=unit, note="< 0.03 K/yr datasheet"))
        S.append(UncertaintySource("self-heating at 1 Hz high-precision mode", 0.02, "rectangular", "B", unit=unit))
    elif ch == "SHT45_RH":
        unit = "%RH"
        S.append(UncertaintySource("datasheet accuracy typical 0…80 %RH", 1.0, "rectangular", "B", unit=unit, note="SHT45 typ ±1.0 %RH, max ±1.8"))
        S.append(UncertaintySource("hysteresis", 0.8, "rectangular", "B", unit=unit, note="datasheet ±0.8 %RH"))
        S.append(UncertaintySource("drift 12 months", 0.2, "rectangular", "B", unit=unit, note="< 0.2 %RH/yr"))
        S.append(UncertaintySource("temperature error propagated to RH (0.1 K at 40 %RH, 22 °C)", 0.25, "rectangular", "B", unit=unit))
        if calibrated:
            S.append(UncertaintySource("reference hygrometer / salt points", 0.8, "normal_k2", "B", unit=unit, note="saturated salt or chilled-mirror reference"))
            S.append(UncertaintySource("calibration repeatability (Type A)", 0.15, "normal", "A", dof=9, unit=unit))
    elif ch == "SDP810":
        unit = "Pa"
        rd = abs(reading) if reading is not None else 12.0
        S.append(UncertaintySource("span accuracy 3 % of reading", 0.03 * rd, "rectangular", "B", unit=unit, note=f"at {rd:g} Pa; SDP810-125Pa datasheet"))
        S.append(UncertaintySource("zero-point accuracy after tare", 0.08, "rectangular", "B", unit=unit, note="datasheet zero-point accuracy 0.08 Pa"))
        S.append(UncertaintySource("zero repeatability / tare (Type A)", 0.05, "normal", "A", dof=19, unit=unit, note="20 zero readings"))
        S.append(UncertaintySource("temperature dependence of zero / span", 0.1, "rectangular", "B", unit=unit, note="0.5 %/10 K span, compensated"))
        S.append(UncertaintySource("tube length / port leak", 0.1, "rectangular", "B", unit=unit, note="≤ 2 m tube, no kinks"))
        S.append(UncertaintySource("resolution", 1 / 240 / 2, "rectangular", "B", unit=unit))
    elif ch in ("ADS1115_4_20MA", "ADS1115"):
        unit = "mA"
        S.append(UncertaintySource("ADS1115 gain error 0.01 % of reading + offset", 0.015 * 16 / 1000 + 0.003, "rectangular", "B", unit=unit,
                                   note="±0.01 % FS gain, 3 LSB offset at 125 µV/LSB → 0.0023 mA on 165 Ω"))
        S.append(UncertaintySource("shunt 165 Ω tolerance 0.1 %", 0.001 * 20, "rectangular", "B", unit=unit, note="0.1 % of 20 mA at full scale; removed by calibration if calibrated"))
        S.append(UncertaintySource("shunt temperature coefficient 25 ppm/K over 20 K", 25e-6 * 20 * 20, "rectangular", "B", unit=unit))
        S.append(UncertaintySource("ADC noise (Type A, 16 SPS averaging)", 0.002, "normal", "A", dof=15, unit=unit))
        if calibrated:
            S.append(UncertaintySource("loop calibrator reference", 0.004, "normal_k2", "B", unit=unit, note="calibrator U95 ±0.004 mA"))
            S[1] = UncertaintySource("shunt tolerance residual after calibration", 0.0005 * 20, "rectangular", "B", unit=unit)
        S.append(UncertaintySource("transmitter (sensor end) accuracy, if not calibrated as a loop", 0.016, "rectangular", "B", unit=unit,
                                   note="0.1 % of span typical 4–20 mA transmitter"))
    elif ch in ("POWER_CLASS05", "POWER", "CT"):
        unit = "% of reading"
        S.append(UncertaintySource("power meter class 0.5 (IEC 61557-12)", 0.5, "rectangular", "B", unit=unit))
        S.append(UncertaintySource("CT ratio error class 0.5 at 20–100 % In", 0.5, "rectangular", "B", unit=unit))
        S.append(UncertaintySource("CT phase displacement 30 arcmin at PF 0.95", math.tan(math.acos(0.95)) * math.radians(0.5) * 100, "rectangular", "B", unit=unit,
                                   note="phase error contributes tan(φ)·δ to active power"))
        S.append(UncertaintySource("CT burden / lead resistance", 0.1, "rectangular", "B", unit=unit))
        S.append(UncertaintySource("voltage input accuracy", 0.2, "rectangular", "B", unit=unit))
        S.append(UncertaintySource("repeatability at steady load (Type A)", 0.05, "normal", "A", dof=29, unit=unit))
        if calibrated:
            notes.append("class 0.5 meters are not field-calibrated; a reference power analyser comparison at commissioning verifies, not corrects")
    else:
        raise ValueError(f"unknown channel {channel}")
    for key in placement or ():
        if key not in PLACEMENT_EFFECTS:
            raise ValueError(f"unknown placement effect {key}; valid: {sorted(PLACEMENT_EFFECTS)}")
        eff = PLACEMENT_EFFECTS[key]
        if eff.unit and unit and eff.unit != unit and not (eff.unit == "%" and unit.startswith("%")):
            raise ValueError(f"placement effect {key} is in {eff.unit}, channel is in {unit}")
        S.append(eff)
    return combine(S, channel=ch, unit=unit, notes=notes)


CHANNELS = ["DS18B20", "SHT45_T", "SHT45_RH", "SDP810", "ADS1115_4_20MA", "POWER_CLASS05"]
PROTOCOL_CLAIMS = {"DS18B20": 0.25, "SHT45_T": 0.15, "SHT45_RH": 1.5, "SDP810": 0.4, "ADS1115_4_20MA": 0.02, "POWER_CLASS05": None}


def all_default_budgets(placement: Optional[Dict[str, Sequence[str]]] = None) -> Dict[str, Budget]:
    placement = placement or {}
    return {c: default_budget(c, placement.get(c)) for c in CHANNELS}


# ------------------------------------------------------------------ predictability
@dataclass
class Predictability:
    score: float              # prediction-interval half-width / alarm margin
    interval_halfwidth: float
    alarm_margin: float
    grade: str
    text: str


def predictability_score(prediction_halfwidth_95: float, predicted_value: float, alarm_threshold: float) -> Predictability:
    """How well the model can warn before the alarm.

    score = (95 % prediction-interval half-width) / (alarm threshold − predicted value).
    < 0.25 excellent, < 0.5 good, < 1 marginal, ≥ 1 the interval already touches the alarm.
    """
    margin = alarm_threshold - predicted_value
    if margin <= 0:
        return Predictability(math.inf, prediction_halfwidth_95, margin, "exceeded",
                              f"predicted value {predicted_value:.2f} is already past the alarm threshold {alarm_threshold:.2f}")
    score = prediction_halfwidth_95 / margin
    grade = "excellent" if score < 0.25 else "good" if score < 0.5 else "marginal" if score < 1.0 else "unpredictable"
    text = (f"predicted {predicted_value:.2f} ± {prediction_halfwidth_95:.2f} (95 %) against alarm at {alarm_threshold:.2f}: "
            f"margin {margin:.2f}, score {score:.2f} ({grade})")
    return Predictability(score, prediction_halfwidth_95, margin, grade, text)


# ------------------------------------------------------------------ reports
def budget_table(b: Budget) -> str:
    rows = [f"**{b.channel}** — combined standard uncertainty u_c = {b.u_c:.4g} {b.unit}, ν_eff = "
            f"{'∞' if not math.isfinite(b.nu_eff) else f'{b.nu_eff:.0f}'}, k = {b.k:.2f}, **U95 = {b.U95:.3g} {b.unit}**"
            + (f", net placement correction {b.total_correction:+.2f} {b.unit}" if b.total_correction else ""), "",
            "| Source | Type | Value | Distribution | Divisor | u_i | Note |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for s in sorted(b.sources, key=lambda s: -s.u):
        rows.append(f"| {s.name} | {s.type} | {s.value:.4g} | {s.distribution} | {s.divisor:.3g} | {s.u:.4g} | {s.note} |")
    if b.notes:
        rows.append("")
        rows.extend(f"- {n}" for n in b.notes)
    return "\n".join(rows)


def markdown_report(budgets: Dict[str, Budget], fits: Optional[Dict[str, CalResult]] = None,
                    tares: Optional[Dict[str, TareResult]] = None, title: str = "BEN Engine calibration and uncertainty report") -> str:
    out = [f"# {title}", "", "Schreiber AI · BEN Engine · GUM-style budgets (JCGM 100:2008). Expanded uncertainty U95 = k · u_c with k from "
           "Student's t at the Welch–Satterthwaite effective degrees of freedom.", ""]
    out.append("## Summary")
    out.append("")
    out.append("| Channel | u_c | k | U95 | Protocol claim (k=2) | Dominant term |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    for name, b in budgets.items():
        claim = PROTOCOL_CLAIMS.get(name)
        claim_s = f"±{claim} {b.unit}" if claim is not None else "—"
        flag = "" if claim is None else (" ✓" if b.U95 <= claim else " ✗ exceeds claim")
        out.append(f"| {name} | {b.u_c:.3g} {b.unit} | {b.k:.2f} | ±{b.U95:.3g} {b.unit}{flag} | {claim_s} | {b.dominant().name} |")
    out.append("")
    if fits:
        out.append("## Linear calibration fits (corrected = gain · reading + offset)")
        out.append("")
        out.append("| Channel | n | gain | offset | residual σ | u(gain) | u(offset) | U95 at mean |")
        out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for name, f in fits.items():
            out.append(f"| {name} | {f.n} | {f.gain:.5f} | {f.offset:+.4f} | {f.residual_std:.4f} | {f.u_gain:.2e} | {f.u_offset:.4f} | ±{f.u95_at(f.x_mean):.3f} |")
        out.append("")
    if tares:
        out.append("## Tares")
        out.append("")
        out.append("| Channel | n | mean zero | offset applied | σ | u(offset) |")
        out.append("| --- | --- | --- | --- | --- | --- |")
        for name, t in tares.items():
            out.append(f"| {name} | {t.n} | {t.mean_zero:.4f} | {t.offset:+.4f} | {t.std:.4f} | {t.u_offset:.4f} |")
        out.append("")
    out.append("## Budgets")
    out.append("")
    for name, b in budgets.items():
        out.append(budget_table(b))
        out.append("")
    return "\n".join(out)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="BEN Engine calibration / uncertainty budgets")
    ap.add_argument("--out", default=None, help="write markdown report here")
    ap.add_argument("--placement", action="append", default=[], help="CHANNEL=effect, e.g. DS18B20=inlet_near_perforated_door")
    a = ap.parse_args(argv)
    pl: Dict[str, List[str]] = {}
    for item in a.placement:
        c, e = item.split("=", 1)
        pl.setdefault(c.upper(), []).append(e)
    budgets = all_default_budgets(pl)
    md = markdown_report(budgets)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(md)
        print(f"wrote {a.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
