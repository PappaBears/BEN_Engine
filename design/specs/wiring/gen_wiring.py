#!/usr/bin/env python3
"""BEN Engine — one-line wiring diagram generator (Schreiber AI, IFC Rev A).

Generates hand-readable SVG one-lines: boxes with names and plain-language callouts, not IEC
symbol soup. Electrical sizes come from software/ben_engine/config.py so the drawings never
drift from the selector.   Run:  python3 gen_wiring.py   (writes *.svg next to this file)
"""
from __future__ import annotations
import math, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "software"))
from ben_engine.config import Config, PROFILE_DEFAULTS  # noqa: E402

# ---------------------------------------------------------------- palette (web/kit/brand.json)
BG, PANEL, SLATE = "#0B1018", "#1B2B42", "#152234"
TEXT, MUTED = "#EDF4FF", "#9FB3CC"
SIGNAL, POWER, LIFE, GREEN = "#66E3FF", "#FFC66D", "#FF707D", "#6EE7A8"
FONT = "'Inter','Segoe UI',system-ui,sans-serif"
MONO = "'JetBrains Mono',Consolas,monospace"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Canvas:
    def __init__(self, w: int, h: int, title: str, subtitle: str = ""):
        self.w, self.h = w, h
        self.parts: list[str] = []
        self.parts.append(f'<rect width="{w}" height="{h}" fill="{BG}"/>')
        # title bar
        self.parts.append(f'<rect x="0" y="0" width="{w}" height="78" fill="{SLATE}"/>')
        self.parts.append(f'<rect x="0" y="78" width="{w}" height="3" fill="{SIGNAL}"/>')
        self.text(32, 42, title, 30, TEXT, weight=700)
        if subtitle:
            self.text(32, 66, subtitle, 15, MUTED)
        # SAI monogram (brand rule: cyan on graphite)
        self.parts.append(f'<rect x="{w-110}" y="18" width="78" height="42" rx="8" fill="{BG}" stroke="{SIGNAL}" stroke-width="2"/>')
        self.text(w - 71, 47, "SAI", 22, SIGNAL, anchor="middle", weight=800, font=MONO)

    def text(self, x, y, s, size=16, color=TEXT, anchor="start", weight=400, font=FONT, italic=False):
        st = " font-style='italic'" if italic else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{st}>{esc(s)}</text>')

    def lines(self, x, y, items, size=14, color=MUTED, lh=None, anchor="start", font=FONT):
        lh = lh or int(size * 1.35)
        for i, s in enumerate(items):
            self.text(x, y + i * lh, s, size, color, anchor=anchor, font=font)

    def box(self, x, y, w, h, name, sub=(), color=SIGNAL, fill=PANEL, name_size=18, sub_size=13, rx=10, dashed=False):
        dash = ' stroke-dasharray="8 6"' if dashed else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{color}" stroke-width="2.5"{dash}/>')
        cy = y + 26 if sub else y + h / 2 + 6
        self.text(x + w / 2, cy, name, name_size, TEXT, anchor="middle", weight=700)
        for i, s in enumerate(sub):
            self.text(x + w / 2, y + 48 + i * (sub_size + 5), s, sub_size, MUTED, anchor="middle")
        return (x, y, w, h)

    def wire(self, pts, color=SIGNAL, width=3, dashed=False, label=None, label_pos=0.5, label_dy=-8, label_size=13, arrow=False):
        d = " ".join(f"{'M' if i == 0 else 'L'}{px},{py}" for i, (px, py) in enumerate(pts))
        dash = ' stroke-dasharray="10 7"' if dashed else ""
        mk = f' marker-end="url(#arr-{color.strip("#")})"' if arrow else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dash}{mk}/>')
        if label:
            # place label at fraction along the polyline
            total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
            target = total * label_pos
            acc = 0
            for i in range(len(pts) - 1):
                seg = math.dist(pts[i], pts[i + 1])
                if acc + seg >= target:
                    t = (target - acc) / seg if seg else 0
                    lx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
                    ly = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
                    break
                acc += seg
            self.label(lx, ly + label_dy, label, color, label_size)

    def label(self, x, y, s, color=SIGNAL, size=13):
        w = len(s) * size * 0.58 + 14
        self.parts.append(f'<rect x="{x - w/2}" y="{y - size - 2}" width="{w}" height="{size + 8}" rx="4" fill="{BG}" opacity="0.92"/>')
        self.text(x, y, s, size, color, anchor="middle", weight=600, font=MONO)

    def dot(self, x, y, color=SIGNAL, r=5):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

    def legend(self, x, y, entries, title="Legend"):
        h = 34 + 26 * len(entries)
        self.parts.append(f'<rect x="{x}" y="{y}" width="330" height="{h}" rx="8" fill="{SLATE}" stroke="{MUTED}" stroke-width="1"/>')
        self.text(x + 14, y + 22, title, 14, TEXT, weight=700)
        for i, (color, dashed, name) in enumerate(entries):
            yy = y + 46 + i * 26
            dash = ' stroke-dasharray="8 6"' if dashed else ""
            self.parts.append(f'<line x1="{x+14}" y1="{yy}" x2="{x+64}" y2="{yy}" stroke="{color}" stroke-width="3.5"{dash}/>')
            self.text(x + 76, yy + 5, name, 13, MUTED)

    def note(self, x, y, w, lines, color=MUTED, title=None):
        h = 20 + 20 * len(lines) + (24 if title else 0)
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{SLATE}" stroke="{color}" stroke-width="1.5"/>')
        yy = y + 24
        if title:
            self.text(x + 14, yy, title, 14, color, weight=700); yy += 24
        self.lines(x + 14, yy, lines, 13, TEXT if color == MUTED else color)

    def save(self, name: str):
        defs = "".join(
            f'<marker id="arr-{c.strip("#")}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
            for c in (SIGNAL, POWER, LIFE, GREEN, MUTED))
        footer = (f'<text x="32" y="{self.h-18}" font-family="{FONT}" font-size="12" fill="{MUTED}">'
                  f'{esc("Schreiber AI · BEN Engine · generated by design/specs/wiring/gen_wiring.py from software/ben_engine/config.py · Not for construction until stamped by the EOR")}</text>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-label="{esc(name)}">'
               f"<defs>{defs}</defs>" + "".join(self.parts) + footer + "</svg>")
        (HERE / name).write_text(svg)
        print("wrote", name, f"{len(svg)//1024} kB")


# ---------------------------------------------------------------- electrical sizing helpers (NEC 2023, Cu 75 °C)
FEEDER = {30: "#10 Cu", 50: "#8 Cu", 60: "#6 Cu", 100: "#3 Cu", 150: "#1/0 Cu", 200: "#3/0 Cu", 225: "#4/0 Cu",
          250: "250 kcmil Cu", 400: "600 kcmil Cu (or 2×#3/0)", 600: "2×350 kcmil Cu", 800: "3×300 kcmil Cu",
          1000: "3×400 kcmil Cu", 1200: "4×350 kcmil Cu", 1600: "5×400 kcmil Cu", 2000: "6×400 kcmil Cu"}
EGC = {30: "#10", 50: "#10", 60: "#10", 100: "#8", 150: "#6", 200: "#6", 225: "#4", 250: "#4", 400: "#3",
       600: "#1", 800: "#1/0", 1000: "#2/0", 1200: "#3/0", 1600: "#4/0", 2000: "250 kcmil"}
FRAMES = [15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 500, 600, 700, 800, 1000, 1200, 1600, 2000]
XFMR = [15, 30, 45, 75, 112.5, 150, 225, 300, 500, 750]


def frame(a: float) -> int:
    return next((f for f in FRAMES if f >= a), 2000)


def feeder_for(a: int) -> str:
    key = next((k for k in sorted(FEEDER) if k >= a), 2000)
    return FEEDER[key]


def egc_for(a: int) -> str:
    key = next((k for k in sorted(EGC) if k >= a), 2000)
    return EGC[key]


def amps(kw: float, v_ll: int, three_phase: bool, pf=0.95) -> float:
    kva = kw / pf
    return kva * 1000 / (math.sqrt(3) * v_ll) if three_phase else kva * 1000 / v_ll


# ================================================================ 1. controls network
def controls_network():
    c = Canvas(1600, 1060, "BEN Engine — Controls Network One-Line — Schreiber AI — IFC Rev A",
               "Zone model per IEC 62443: controls VLAN 20 · management VLAN 30 · customer IT isolated · life-safety hardwired (not on this drawing: see 05)")
    c.parts.append(f'<rect x="40" y="110" width="1020" height="790" rx="14" fill="none" stroke="{SIGNAL}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(56, 136, "ZONE 1 — CONTROLS VLAN 20  (10.20.0.0/24)  — no default route, no WAN", 15, SIGNAL, weight=700)
    c.parts.append(f'<rect x="1090" y="110" width="470" height="330" rx="14" fill="none" stroke="{GREEN}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(1106, 136, "ZONE 2 — MANAGEMENT VLAN 30  (10.30.0.0/24)", 15, GREEN, weight=700)
    c.parts.append(f'<rect x="1090" y="470" width="470" height="200" rx="14" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(1106, 496, "ZONE 3 — CUSTOMER IT  (physically separate)", 15, MUTED, weight=700)
    c.parts.append(f'<rect x="1090" y="700" width="470" height="200" rx="14" fill="none" stroke="{POWER}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(1106, 726, "ZONE 4 — REMOTE SUPPORT (optional, outbound only)", 15, POWER, weight=700)

    c.box(380, 170, 380, 120, "BEN GATEWAY", ["Raspberry Pi 5 · Mosquitto · chrony · ben_engine.api", "eth0 = 10.20.0.1 (controls) · eth0.30 = 10.30.0.1 (mgmt)", "nftables: drop in / out / forward by default"], SIGNAL, sub_size=12)
    c.box(380, 360, 380, 90, "PoE SWITCH (managed, 802.3af)", ["8–24 ports · VLAN 20 untagged · VLAN 30 tagged on uplink", "fed from the controls UPS circuit"], SIGNAL, sub_size=12)
    c.wire([(570, 290), (570, 360)], SIGNAL, label="trunk: VLAN 20 + VLAN 30", label_pos=0.5, label_dy=5)

    for i in range(4):
        x = 70 + i * 170
        c.box(x, 560, 150, 110, f"BEN NODE {i+1}", ["ESP32 · PoE class 0", "T_in/T_out · RH · dP", "leak · door · 4 relays"], SIGNAL, name_size=15, sub_size=11)
        c.wire([(x + 75, 560), (x + 75, 500), (450 + i * 20, 500), (450 + i * 20, 450)], SIGNAL, width=2.5, label="PoE Cat6" if i == 0 else None, label_pos=0.25)
    c.text(70, 700, "one node per 1–2 racks + one at the mechanical panel · MQTT publish only to the gateway · SNTP from 10.20.0.1", 12, MUTED)

    # right-hand drop from the switch feeds PDUs and CDU without crossing the node row
    c.wire([(700, 450), (700, 480), (755, 480), (755, 745)], SIGNAL, 2.5)
    c.box(780, 560, 250, 90, "MODBUS TCP ↔ RTU GATEWAY", ["(or meters with native Ethernet)", "10.20.0.20"], SIGNAL, name_size=14, sub_size=11)
    c.wire([(905, 560), (905, 420), (760, 420)], SIGNAL, width=2.5)
    for i, nm in enumerate(["POWER METER (service)", "POWER METER (UPS out)", "UPS (Modbus)", "COOLING UNITS (Modbus)"]):
        y = 705 + i * 46
        c.box(800, y, 230, 38, nm, (), POWER if "METER" in nm else SIGNAL, fill=SLATE, name_size=13)
        c.wire([(1030, y + 19), (1060, y + 19)], POWER, width=2.5, dashed=True)
    c.wire([(1040, 650), (1060, 650), (1060, 870)], POWER, width=2.5, dashed=True)
    c.wire([(1030, 630), (1040, 630), (1040, 650)], POWER, width=2.5, dashed=True)
    c.label(915, 686, "RS-485 2-wire + shield · 120 Ω ends · 9600 8N1 · daisy chain", POWER, 10)

    for i in range(2):
        c.box(70 + i * 260, 745, 240, 70, f"RACK PDU {i+1}..{i+1+5} (SNMP v3)", ["Ethernet to PoE switch · per-outlet kW", "10.20.0.50+"], SIGNAL, name_size=13, sub_size=11)
        c.wire([(190 + i * 260, 745), (190 + i * 260, 730), (755, 730)], SIGNAL, width=2)
    c.box(590, 745, 150, 70, "CDU / DRY COOLER", ["Modbus TCP · 10.20.0.40", "(liquid variants)"], SIGNAL, name_size=12, sub_size=11)
    c.wire([(740, 780), (755, 780)], SIGNAL, width=2)

    c.box(1120, 170, 200, 100, "DASHBOARD SCREEN", ["panel PC at the door", "HTTPS :8000 · WSS :9001"], GREEN, name_size=14, sub_size=11)
    c.box(1340, 170, 200, 100, "ENGINEERING LAPTOP", ["SSH keys only", "MQTT TLS :8883"], GREEN, name_size=14, sub_size=11)
    c.box(1120, 310, 420, 100, "UPLINK PORT (VLAN 30 tagged)", ["from the PoE switch trunk · only ports marked MGMT", "gateway reachable; nodes and meters are NOT reachable from here"], GREEN, name_size=14, sub_size=11)
    c.wire([(760, 390), (1000, 390), (1000, 360), (1120, 360)], GREEN, width=2.5, label="VLAN 30 only", label_pos=0.4)
    c.wire([(1220, 310), (1220, 270)], GREEN, width=2); c.wire([(1440, 310), (1440, 270)], GREEN, width=2)

    c.box(1120, 520, 420, 120, "CUSTOMER SWITCH / FIREWALL / WAN", ["their servers, their fiber, their rules", "NO cable to the controls switch. NO gateway interface here.", "shared with BEN only: power, cooling, the room"], MUTED, name_size=14, sub_size=11)
    c.text(1120, 660, "✕  no link on purpose", 14, LIFE, weight=700)

    c.box(1120, 750, 420, 130, "WIREGUARD wg0 → support.schreiberai.com", ["gateway initiates · nothing listens on WAN", "customer runs: ben-vpn-support.sh up / down · auto-off 48 h", "inbound over tunnel: SSH + API only"], POWER, name_size=14, sub_size=11, dashed=True)
    c.wire([(760, 230), (1075, 230), (1075, 815), (1120, 815)], POWER, width=2, dashed=True, label="optional WAN NIC (USB)", label_pos=0.2)

    c.legend(60, 915, [(SIGNAL, False, "Ethernet / MQTT / SNMP — controls VLAN 20"), (POWER, True, "RS-485 Modbus RTU · optional outbound VPN"), (GREEN, False, "Management VLAN 30 — TLS only")])
    c.save("01_controls_network_one_line.svg")


# ================================================================ 2. node wiring
def node_wiring():
    c = Canvas(1600, 1290, "BEN Engine — BEN Node v1 Wiring, Terminal by Terminal — Schreiber AI — IFC Rev A",
               "Olimex ESP32-POE-ISO + BEN-IOB-1 I/O board in a 6-module DIN enclosure · field wiring is Class 2 except relay contacts (Class 1, separate conduit)")
    nx, ny, nw, nh = 580, 150, 440, 920
    c.parts.append(f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="16" fill="{PANEL}" stroke="{SIGNAL}" stroke-width="3"/>')
    c.text(nx + nw / 2, ny + 34, "BEN NODE v1", 24, TEXT, anchor="middle", weight=800)
    c.text(nx + nw / 2, ny + 58, "ESP32 · firmware/ben-node · 1 Hz MQTT", 13, MUTED, anchor="middle")
    for i, (nm, col) in enumerate([("PWR", GREEN), ("LINK", POWER), ("IDENT", SIGNAL), ("RLY1-4", LIFE)]):
        c.dot(nx + 110 + i * 75, ny + 92, col, 7); c.text(nx + 110 + i * 75, ny + 114, nm, 11, MUTED, anchor="middle")
    c.lines(nx + nw / 2, ny + 136, ["IDENT: solid = identify · 1 Hz blink = gateway lost", "(failsafe active) · short blip = normal"], 11, MUTED, anchor="middle")
    c.lines(nx + nw / 2, ny + 500, ["GPIO map", "1-Wire 4 · SDA 13 · SCL 16", "relays 32 33 14 15", "leak 36 · door 39 · pulse 34", "EPO mon 35 · IDENT LED 2 · spare 5"], 12, MUTED, anchor="middle", font=MONO)

    def terminal(side, y, label, pins, color):
        x = nx - 10 if side == "L" else nx + nw - 70
        h = 22 * len(pins) + 14
        c.parts.append(f'<rect x="{x}" y="{y}" width="80" height="{h}" rx="4" fill="{SLATE}" stroke="{color}" stroke-width="2"/>')
        c.text(x + 40, y - 6, label, 12, color, anchor="middle", weight=700, font=MONO)
        ys = []
        for i, p in enumerate(pins):
            py = y + 18 + i * 22
            c.parts.append(f'<rect x="{x+6}" y="{py-8}" width="68" height="16" rx="2" fill="{BG}"/>')
            c.text(x + 40, py + 4, p, 11, TEXT, anchor="middle", font=MONO)
            ys.append(py)
        return ys

    LX, LW = 40, 440            # left column boxes
    LR = LX + LW                # right edge of left boxes (480); terminal pins start at nx-10 = 570

    # ---- X3 1-Wire
    y1 = terminal("L", 300, "X3 1-WIRE", ["3V3", "DATA GPIO4", "0V"], SIGNAL)
    c.text(LX, 232, "DS18B20 STRINGS (8 max) · 3-wire CAT5: blue 3V3, white-blue DATA, brown 0V · ≤ 20 m", 12, SIGNAL, weight=600)
    for i in range(4):
        c.box(LX + i * 110, 244, 100, 34, f"T_in_{i+1}", (), SIGNAL, fill=SLATE, name_size=12, rx=6)
        c.box(LX + i * 110, 288, 100, 34, f"T_out_{i+1}", (), SIGNAL, fill=SLATE, name_size=12, rx=6)
    c.text(LX, 342, "T_in at rack face (1/3 and 2/3 height) · T_out at rack rear · daisy chain, stubs < 1 m", 11, MUTED)
    for k in range(3):
        c.wire([(LR, 305 + k * 12), (nx - 10, y1[k])], SIGNAL, 2)
    c.parts.append(f'<rect x="{LR+12}" y="{y1[0]-1}" width="8" height="{y1[1]-y1[0]}" fill="{POWER}" rx="2"/>')
    c.text(LR - 190, y1[2] + 16, "4.7 kΩ pull-up (one, 3V3→DATA) →", 10, POWER, font=MONO)

    # ---- X4 I2C / SDP
    y2 = terminal("L", 400, "X4 I2C/SDP", ["3V3", "SDA GPIO13", "SCL GPIO16", "0V"], SIGNAL)
    c.box(LX, 385, LW, 104, "SDP810-125Pa  → dP_aisle", ["I²C 0x25 · ±125 Pa · tare with both taps open to the same room", "P+ (red tube) → COLD aisle tap    P− (blue tube) → HOT aisle tap", "3/16 in silicone ≤ 3 m per side · taps flush with containment · no kinks"], SIGNAL, name_size=14, sub_size=11)
    for k in range(4):
        c.wire([(LR, 410 + k * 20), (nx - 10, y2[k])], SIGNAL, 2)
    c.box(LX, 500, LW, 56, "SHT45  → T_ref / RH", ["I²C 0x44 · on the I/O board · vent hole toward the cold aisle · sunshield"], SIGNAL, name_size=13, sub_size=11)
    c.text(LX, 574, "ADS1115 (I²C 0x48) is on the I/O board — its inputs are X5 below", 11, MUTED)

    # ---- X5 4-20 mA
    y3 = terminal("L", 600, "X5 4-20mA", ["AI0+", "AI0−", "AI1+", "AI1−", "AI2+", "AI2−", "AI3+", "AI3−"], POWER)
    c.box(LX, 582, LW, 190, "4–20 mA TRANSMITTERS  → ai0..3_mA", ["loop-powered: 24 V (X2 V+) → transmitter → AI+ · AI− is 0 V", "165 Ω 0.1 % shunt per channel on the I/O board (0.66–3.30 V)", "ADS1115 gain 1 (±4.096 V), 16-bit → ±0.02 mA after calibration", "typical: supply/return water T · flow · CDU pressure · UPS output", "shielded twisted pair · shield landed at the node end ONLY"], POWER, name_size=13, sub_size=11)
    for k in range(8):
        c.wire([(LR, 612 + k * 20), (nx - 10, y3[k])], POWER, 1.8)

    # ---- X6 digital
    y4 = terminal("L", 820, "X6 DIGITAL", ["LEAK EXC", "LEAK SENSE", "DOOR C", "DOOR NO", "PULSE +", "PULSE −", "EPO C", "EPO NO"], SIGNAL)
    c.box(LX, 800, LW, 130, "LEAK ROPE · DOOR REED · S0 PULSE · EPO MONITOR", ["leak rope: 3V3 excitation, 100 k / 10 k divider, HIGH = wet  (GPIO36)", "door: reed to 0 V, 10 k pull-up, HIGH = open  (GPIO39)", "pulse: meter S0 output (5–27 V) via opto, 1000 imp/kWh  (GPIO34)", "EPO / fire panel AUX dry contact → MONITOR ONLY  (GPIO35)"], SIGNAL, name_size=12, sub_size=11)
    for k in range(8):
        c.wire([(LR, 828 + k * 16), (nx - 10, y4[k])], SIGNAL if k < 6 else LIFE, 1.8)
    c.text(LX, 952, "EPO wires READ the hardwired loop. They can never open it.", 12, LIFE, weight=700)

    # ---- right side
    RX, RW = 1130, 410
    y5 = terminal("R", 185, "X1 RJ45", ["PoE+DATA"], SIGNAL)
    c.box(RX, 165, RW, 64, "PoE SWITCH PORT (802.3af class 0, ≤ 12.95 W)", ["Cat6 shielded ≤ 90 m · shield bonded at the switch · node isolated 3 kV"], SIGNAL, name_size=13, sub_size=11)
    c.wire([(nx + nw + 10, y5[0]), (RX, 197)], SIGNAL, 3)
    y6 = terminal("R", 262, "X2 12-24V", ["V+", "0V"], POWER)
    c.box(RX, 250, RW, 64, "ALT. POWER 12–24 VDC (if no PoE) · 1 A fuse · reverse-protected", ["also the 24 V source for the 4–20 mA loops on X5 · 2 A Class 2 supply"], POWER, name_size=12, sub_size=11)
    c.wire([(nx + nw + 10, y6[0]), (RX, 282)], POWER, 2.5); c.wire([(nx + nw + 10, y6[1]), (RX, 302)], POWER, 2.5)

    y7 = terminal("R", 380, "X7 RELAYS", ["R1 COM", "R1 NO", "R1 NC", "R2 COM", "R2 NO", "R2 NC", "R3 COM", "R3 NO", "R3 NC", "R4 COM", "R4 NO", "R4 NC"], LIFE)
    loads = [("relay1 — COOLING UNIT REMOTE ENABLE  (FAILSAFE)", ["drops 60 s after the last gateway contact → unit runs on its own controller", "in series with the unit's enable input · 24 V pilot ≤ 1 A · RC snubber 100 Ω / 0.1 µF"], GREEN),
             ("relay2 — CONTAINER LIGHTS", ["120/230 VAC contactor coil ≤ 5 A · MOV 275 V across the coil", "holds last state on gateway loss"], POWER),
             ("relay3 — FAN BOOST / ECONOMIZER OVERRIDE", ["dry contact to the cooling controller DI", "holds last state on gateway loss"], POWER),
             ("relay4 — SPARE (default: local 'controls fault' beacon)", ["24 VDC beacon ≤ 1 A · flyback diode in ULN2003 driver", "holds last state on gateway loss"], POWER)]
    for i, (nm, sub, col) in enumerate(loads):
        by = 365 + i * 118
        c.box(RX, by, RW, 100, nm, sub + ["COM = supply · NO = load · NC spare"], col, name_size=12, sub_size=10)
        for k in range(3):
            c.wire([(nx + nw + 10, y7[i * 3 + k]), (1060 + k * 14, y7[i * 3 + k]), (1060 + k * 14, by + 28 + k * 22), (RX, by + 28 + k * 22)], col, 1.8)
    c.note(RX, 850, RW, ["Relay contacts are Class 1: #14 Cu THHN in their own conduit.", "GPIO 32 / 33 / 14 / 15 drive a ULN2003; relays 10 A rated, used ≤ 5 A.", "Snubber across every AC load; MOV on every coil."], MUTED, "Relay wiring rules")
    c.note(RX, 960, RW, ["1. Mount the node on the DIN rail. Bond the rail.", "2. Land every shield at the node end only.", "3. Plug X3..X7 LAST, after the gateway shows the node online.", "4. Tape P+ red and P− blue before routing the tubing.", "5. Write unit / node id on the front label."], GREEN, "Assembly order (one action per step)")

    # ground
    c.wire([(nx + 40, ny + nh), (nx + 40, ny + nh + 36), (nx + 150, ny + nh + 36)], GREEN, 2.5)
    c.text(nx + 160, ny + nh + 41, "DIN rail bonded to the panel ground bar (#12 Cu green) · all shields land here", 12, GREEN)
    c.legend(LX, 1120, [(SIGNAL, False, "Signal / sensor (3.3 V, Class 2)"), (POWER, False, "Power / 4–20 mA loops (24 V, Class 2)"), (LIFE, False, "Life-safety contact — MONITOR ONLY"), (GREEN, False, "Ground / bond · failsafe relay load")])
    c.save("02_node_wiring.svg")


# ================================================================ 3. power one-line per tier
def power_one_line(tier: str):
    cfg = Config.preset(tier)
    d = cfg.derived()
    g = d["geometry"]
    three = not g["voltage"].startswith("208/240")
    v_ll = 480 if g["voltage"].startswith("480") else (208 if three else 240)
    svc = d["service_breaker_a"]
    cool_a = frame(amps(d["cooling_elec_kw"] + 0.5, v_ll, three) * 1.25)
    ups_each_a = frame(d["ups_kva_each"] * 1000 / ((math.sqrt(3) * v_ll) if three else v_ll) * 1.25)
    if v_ll == 480:
        xf_kva = next((k for k in XFMR if k >= cfg.it_kw / 0.95 * 1.1), 750)
        pdu_v, pdu_three = 208, True
    else:
        xf_kva = None
        pdu_v, pdu_three = (208, True) if three else (240, False)
    pdu_a = frame(amps(d["per_rack_kw"], pdu_v, pdu_three) * 1.25)
    gen_kw = int(math.ceil(d["total_kw"] * 1.25 / 25.0) * 25)
    racks_word = "rack" if cfg.racks == 1 else "racks"
    title = f"BEN Engine — Power One-Line — {d['tier_label']} ({cfg.it_kw:.0f} kW IT, {cfg.racks} {racks_word}, {cfg.redundancy}) — Schreiber AI — IFC Rev A"
    c = Canvas(1600, 1100, title,
               f"{PROFILE_DEFAULTS[cfg.profile]['label']} preset · {g['voltage']} · service {svc} A · total {d['total_kw']} kW ({d['total_kva']} kVA) · UPS {d['ups_modules']}×{d['ups_kva_each']} kVA · battery {d['battery_kwh']} kWh for {cfg.ups_minutes} min · PUE est. {d['pue_estimate']}")

    X, W = 130, 420
    BUS = X + W // 2
    def stage(y, name, sub, color=POWER, h=86, dashed=False):
        return c.box(X, y, W, h, name, sub, color, name_size=16, sub_size=11, dashed=dashed)

    s1 = stage(110, "UTILITY", [f"{g['voltage']} from the site transformer / pad", "customer-provided per SITE_REQUIREMENTS"])
    s2 = stage(226, "SERVICE ENTRANCE + MAIN", [f"main breaker {svc} A frame · SPD TYPE 1 on the line side", f"feeder {feeder_for(svc)} + EGC {egc_for(svc)} in conduit · ground ring + rods"])
    ats_sub = [f"{svc} A, 3-pole, open transition, 10 s start delay", "weekly generator exercise · Modbus to gateway"] if (cfg.generator or tier != "micro") else [f"{svc} A manual transfer (generator-ready option)", "ATS fitted when the generator is ordered"]
    s3 = stage(342, "ATS — AUTOMATIC TRANSFER SWITCH", ats_sub)
    s4 = stage(458, f"UPS  {d['ups_modules']} × {d['ups_kva_each']} kVA  ({cfg.redundancy})", [f"online double-conversion · Li-ion {d['battery_kwh']} kWh / {cfg.ups_minutes} min · maintenance bypass", f"input / output breakers {ups_each_a} A each · SNMP + Modbus to gateway"])
    if xf_kva:
        s5 = stage(574, f"TRANSFORMER {xf_kva} kVA  480 Δ → 208Y/120 V", ["K-13 rated · in the power section · X0 bonded here only", f"secondary main {frame(xf_kva*1000/(math.sqrt(3)*208)*1.25)} A"])
        yd = 690
    else:
        s5 = None; yd = 574
    s6 = stage(yd, "IT DISTRIBUTION PANEL  (critical)", [f"{pdu_v} V {'3φ' if pdu_three else '1φ'} · {cfg.racks} rack feed{'s' if cfg.racks > 1 else ''} × 2 (A/B) · SPD TYPE 2", "branch metering (Modbus) · EPO shunt trip"])
    for a, b in [(s1, s2), (s2, s3), (s3, s4), (s4, s5 or s6)] + ([(s5, s6)] if s5 else []):
        c.wire([(BUS, a[1] + a[3]), (BUS, b[1])], POWER, 4)
    c.label(BUS + 130, s2[1] - 9, f"{svc} A · {feeder_for(svc)}", POWER, 12)

    # racks (two rows above 6)
    yp = yd + 112
    per_row = min(cfg.racks, 6)
    rw = 64
    for i in range(cfg.racks):
        row, col = divmod(i, per_row)
        rx = X + col * (rw + 10); ry = yp + row * 78
        c.box(rx, ry, rw, 66, f"R{i+1}", [f"{d['per_rack_kw']} kW", f"{pdu_a} A A+B"], POWER, fill=SLATE, name_size=12, sub_size=9, rx=6)
        if row == 0:
            c.wire([(rx + rw / 2, yd + 86), (rx + rw / 2, ry)], POWER, 2)
        else:
            c.wire([(rx + rw / 2, ry - 12), (rx + rw / 2, ry)], POWER, 2)
    rows = (cfg.racks + per_row - 1) // per_row
    c.lines(X, yp + rows * 78 + 4, [f"each rack: two PDUs (A and B paths{' from separate UPS' if cfg.redundancy == '2N' else ''}) · {pdu_a} A branch · {feeder_for(pdu_a)}", "locking receptacle · PDU per-outlet metering over SNMP"], 11, MUTED)

    # generator
    gx = 620
    c.box(gx, 342, 300, 86, f"GENERATOR  {gen_kw} kW  (option)", ["diesel / NG · outdoor · 24 h tank", "generator-ready = ATS + pad + conduit · Modbus status"], POWER, dashed=not cfg.generator, name_size=14, sub_size=11)
    c.wire([(gx, 385), (X + W, 385)], POWER, 3, dashed=not cfg.generator, label=f"{svc} A", label_pos=0.5)

    # mechanical / controls / house: tapped between ATS and UPS
    tap_y = s3[1] + s3[3] + 15
    c.dot(BUS, tap_y, POWER, 5)
    c.wire([(BUS, tap_y), (590, tap_y), (590, 525), (gx, 525)], SIGNAL, 3, label=f"{cool_a} A · {feeder_for(cool_a)}", label_pos=0.45, label_dy=-8)
    c.box(gx, 470, 300, 110, "MECHANICAL PANEL  (separate from IT)", [f"{d['cooling_units_total']} × {d['cooling_label'].split(' +')[0]}", f"{d['cooling_elec_kw']} kW electrical · feeder {cool_a} A", "fed AFTER the ATS, BEFORE the UPS (generator-backed)", "own breaker + disconnect at each unit · SPD type 2"], SIGNAL, name_size=13, sub_size=11)
    c.wire([(590, 525), (590, 735), (gx, 735)], POWER, 2)
    c.box(gx, 700, 300, 70, "HOUSE LOADS  (lights, receptacles, heaters)", ["20 A circuits · GFCI receptacles · ATS side, not UPS"], POWER, name_size=12, sub_size=11)
    c.box(gx, 600, 300, 80, "CONTROLS CIRCUIT  (UPS-backed, 20 A)", ["gateway · PoE switch · nodes · releasing-panel charger", "from the IT panel, own breaker, labelled CONTROLS"], SIGNAL, name_size=13, sub_size=11)
    c.wire([(X + W, yd + 40), (580, yd + 40), (580, 640), (gx, 640)] if yd + 40 > 640 else [(X + W, yd + 40), (gx, 640)], SIGNAL, 2.5, label="20 A · #12 Cu", label_pos=0.5)

    # EPO loop down the far left, shunt trips enter from the left
    ex = 980
    c.box(ex, 110, 560, 150, "EPO LOOP — HARDWIRED (see 05 Life-Safety)", ["EPO stations at each door → series NC loop → shunt trips:", "UPS output breaker · IT panel main · mechanical panel main", "node EPO MONITOR reads an AUX contact only · NFPA 70 645.10 / 645.11"], LIFE, name_size=15, sub_size=12)
    c.wire([(ex, 150), (X + W + 20, 150), (X + W + 20, 96), (70, 96), (70, s6[1] + 60)], LIFE, 2.5, dashed=True)
    for s in (s4, s6):
        c.wire([(70, s[1] + 60), (X, s[1] + 60)], LIFE, 2.5, dashed=True); c.label(100, s[1] + 52, "shunt trip", LIFE, 10)
    c.wire([(ex, 170), (950, 170), (950, 495), (920, 495)], LIFE, 2.5, dashed=True); c.label(950, 330, "shunt trip", LIFE, 10)

    c.note(ex, 290, 560, ["TYPE 1 SPD at the service entrance (line side of main), 100 kA/phase", "TYPE 2 SPD in the IT panel and the mechanical panel, 50 kA/phase", "TYPE 3 in rack PDUs (built in)", "SPD status contacts → BEN node spare DI · annunciated on the dashboard"], POWER, "Surge protection")
    c.note(ex, 435, 560, ["Container shell = bonding grid: four corner castings bonded #2/0 Cu to the ground ring", f"Ground ring #2 bare Cu · {'3' if tier == 'ben40' else '2'} rods 8 ft Cu-clad ≥ 6 ft apart · ≤ 5 Ω target (measure, record)", "Equipment grounding conductors per NEC 250.122 (sizes on the feeders)", "Isolated ground bar in the IT panel · rack rails bonded #6 Cu", "Separately derived system at the transformer: X0 → GEC at the transformer only" if xf_kva else "No separately derived system: neutral bonded at the service only", "Lightning: Class II air terminals on 20 / 40 ft containers in high-keraunic sites (option)"], GREEN, "Grounding and bonding")
    c.note(ex, 625, 560, [f"Service {svc} A @ {g['voltage']}: calc {d['service_amps_calc']} A incl. 125 % continuous", f"Total {d['total_kw']} kW = IT {cfg.it_kw} + cooling {d['cooling_elec_kw']} + aux", f"UPS carries IT only: {d['ups_modules']} × {d['ups_kva_each']} kVA, 15 % headroom, {cfg.redundancy}", f"Battery {d['battery_kwh']} kWh Li-ion for {cfg.ups_minutes} min at full IT (90 % DoD)", f"Rack branch {pdu_a} A @ {pdu_v} V {'3φ' if pdu_three else '1φ'} for {d['per_rack_kw']} kW/rack", "Selective coordination main > ATS > UPS > panel > branch — EOR verifies TCC", "Arc-flash labels at every panel per NFPA 70E after final equipment selection"], MUTED, "Sizes come from ben_engine.config — change the config, not this drawing")
    c.legend(ex, 860, [(POWER, False, "Power — normal / UPS path"), (SIGNAL, False, "Power — mechanical / controls circuits"), (LIFE, True, "EPO loop (hardwired, shunt trips)"), (GREEN, False, "Grounding / bonding")])
    c.save(f"03_power_one_line_{tier}.svg")


# ================================================================ 4. cooling one-lines
def cooling_air():
    cfg = Config.preset("ben20"); d = cfg.derived()
    c = Canvas(1600, 990, "BEN Engine — Cooling One-Line (Air: in-row DX + condensers) — Schreiber AI — IFC Rev A",
               f"BEN 10 / BEN 20 default · example BEN 20: {cfg.it_kw:.0f} kW IT, {d['cooling_units_total']} × {d['cooling_unit_kw_derated']} kW in-row DX ({cfg.redundancy}), {d['airflow_cfm']} cfm · hot-aisle containment · economizer option")
    # container outline
    c.parts.append(f'<rect x="80" y="130" width="900" height="520" rx="10" fill="none" stroke="{MUTED}" stroke-width="2"/>')
    c.text(90, 152, "INSIDE CONTAINER (ISO 20 ft HC)  — cold aisle at the door side, hot aisle contained", 13, MUTED)
    # racks & inrow alternation
    x = 110
    for i in range(cfg.racks + d["cooling_units_total"]):
        is_unit = i % 2 == 1
        if is_unit:
            c.box(x, 300, 70, 160, "IN-ROW", ["DX", "30 kW", "EC fans"], SIGNAL, fill=SLATE, name_size=12, sub_size=10, rx=6)
        else:
            c.box(x, 300, 70, 160, "RACK", ["19.2 kW", "front→back"], POWER, fill=SLATE, name_size=12, sub_size=10, rx=6)
        x += 82
    c.text(110, 290, "COLD AISLE  (supply 18–27 °C, ASHRAE A1/A2)   ← T_in sensors at rack face, 1/3 and 2/3 height", 13, SIGNAL, weight=600)
    c.text(110, 490, "HOT AISLE — CONTAINED (return 35–45 °C)   ← T_out sensors · dP_aisle taps: cold side (+) / hot side (−)", 13, LIFE, weight=600)
    c.wire([(110, 520), (900, 520)], SIGNAL, 2, arrow=True, label="airflow: cold aisle → rack → hot aisle → in-row → cold aisle (closed loop, 125 cfm/kW)", label_pos=0.5, label_dy=24)
    # refrigerant lines to condensers
    for k in range(d["cooling_units_total"]):
        ux = 110 + 82 * (2 * k + 1) + 35
        c.wire([(ux, 300), (ux, 200), (1050, 200)], GREEN, 2, dashed=True)
    c.label(600, 190, "refrigerant liquid + suction (R-410A/R-32), insulated, ≤ 30 m equivalent per unit", GREEN, 11)
    # condensers outside
    for k in range(d["cooling_units_total"]):
        c.box(1050, 140 + k * 76, 220, 62, f"CONDENSER {k+1}", ["outdoor · ≥ 1 m clear · mech. panel"], GREEN, fill=SLATE, name_size=12, sub_size=10, rx=6)
    c.text(1050, 130, "OUTSIDE — condenser pad / roof frame", 13, GREEN)
    # economizer
    c.box(1300, 140, 240, 130, "ECONOMIZER (option)", ["outdoor air damper + filter bank", "+ mixing section, dP_filter via ai0", "enabled below 18 °C dry bulb"], SIGNAL, name_size=13, sub_size=11, dashed=True)
    # mechanical panel + controls
    c.box(1050, 560, 490, 120, "MECHANICAL PANEL", [f"{d['cooling_units_total']} units × own breaker + local disconnect at each unit", "condensers on own circuits · fed after ATS, before UPS", "unit controllers run standalone · Modbus to gateway · relay1 = enable (failsafe)"], SIGNAL, name_size=14, sub_size=11)
    c.wire([(1050, 620), (980, 620), (980, 460), (900, 460)], SIGNAL, 2.5, dashed=True, label="Modbus RTU/TCP + 24 V enable", label_pos=0.3)
    # condensate, leak
    c.box(80, 680, 440, 80, "CONDENSATE + LEAK", ["each in-row: condensate pump → drain to outside, trap, heat-traced in cold climates", "leak rope under every unit and along the drain → node 'leak' (critical alarm)"], LIFE, name_size=13, sub_size=11)
    c.box(560, 680, 420, 80, "CONTROLS SEQUENCE (gateway)", ["units on own setpoints; gateway trims supply setpoint ±2 K by T_in max", "N+1: rotate lead unit weekly · fault → remaining units ramp"], SIGNAL, name_size=13, sub_size=11)
    c.note(1050, 700, 490, ["supply air 20 °C ± 2 · return ≤ 42 °C · aisle dP 5–15 Pa positive", f"derate 1.5 %/K above 35 °C outdoor (config) → {d['cooling_unit_kw_derated']} kW/unit at design", "filters MERV 8 pre / MERV 13 at economizer · change at dP_filter 150 Pa"], MUTED, "Setpoints and limits")
    c.legend(80, 800, [(SIGNAL, False, "Air path / controls"), (GREEN, True, "Refrigerant lines"), (POWER, False, "IT racks (heat source)"), (LIFE, False, "Condensate / leak")])
    c.save("04_cooling_one_line_air.svg")


def cooling_liquid():
    cfg = Config.preset("ben40"); d = cfg.derived()
    c = Canvas(1600, 990, "BEN Engine — Cooling One-Line (Liquid: DLC → CDU → dry cooler) — Schreiber AI — IFC Rev A",
               f"BEN 40 default (BEN 20 option) · example BEN 40: {cfg.it_kw:.0f} kW IT in {cfg.racks} racks, {d['cooling_units_total']} × CDU ({cfg.redundancy}) · RDHx for residual air heat")
    c.parts.append(f'<rect x="80" y="130" width="860" height="520" rx="10" fill="none" stroke="{MUTED}" stroke-width="2"/>')
    c.text(90, 152, "INSIDE CONTAINER (ISO 40 ft HC)", 13, MUTED)
    # racks with cold plates
    for i in range(6):
        rx = 110 + i * 92
        c.box(rx, 300, 80, 150, f"RACK {i+1}..", ["cold plates", "+ RDHx door", "19.2 kW"], POWER, fill=SLATE, name_size=12, sub_size=10, rx=6)
        c.wire([(rx + 20, 450), (rx + 20, 500)], SIGNAL, 2.5); c.wire([(rx + 60, 500), (rx + 60, 450)], LIFE, 2.5)
    c.text(110, 290, "TCS — technology cooling loop (secondary): supply 30–40 °C / return +10 K · PG25 · quick-disconnects per server", 13, SIGNAL, weight=600)
    c.wire([(110, 500), (700, 500)], SIGNAL, 4, label="TCS SUPPLY 30 °C  (blue)", label_pos=0.5, label_dy=22)
    c.wire([(110, 530), (700, 530)], LIFE, 4, label="TCS RETURN 40 °C  (red)", label_pos=0.5, label_dy=24)
    for k in range(d["cooling_units_total"]):
        cx = 720 + k * 110
        c.box(cx, 460, 100, 150, f"CDU {k+1}", ["300 kW", "plate HX", "pumps N+1", "Modbus TCP"], SIGNAL, fill=SLATE, name_size=13, sub_size=10, rx=6)
        c.wire([(700, 500), (cx, 500)], SIGNAL, 3); c.wire([(700, 530), (cx, 530)], LIFE, 3)
        c.wire([(cx + 50, 460), (cx + 50, 200), (1050, 200)], GREEN, 3)
        c.wire([(cx + 80, 460), (cx + 80, 230), (1050, 230)], POWER, 3)
    c.label(760, 182, "FWS facility water (primary): 25–35 °C PG30, return +8 K · 3 in. insulated", GREEN, 11)
    # dry coolers outside
    for k in range(2):
        c.box(1050, 140 + k * 100, 240, 80, f"DRY COOLER {k+1}", ["adiabatic pads option > 32 °C", "EC fans, 480 V from mech. panel"], GREEN, fill=SLATE, name_size=13, sub_size=10, rx=6)
    c.text(1050, 130, "OUTSIDE — dry cooler pad (N+1), ≥ 2 m clearance, winterised", 13, GREEN)
    c.box(1320, 140, 220, 180, "GLYCOL SKID", ["expansion tank · air separator", "makeup + chemical pot feeder", "glycol % check quarterly", "pressure 2–4 bar"], GREEN, name_size=13, sub_size=11)
    # RDHx + residual air
    c.box(1050, 350, 490, 90, "RESIDUAL AIR: rear-door heat exchangers + 1 in-row", ["~20–30 % of IT heat is still air · RDHx on TCS return · one in-row DX for humidity/standby", "SHT45 RH 20–80 % · dew-point ≥ 3 K below coldest surface (condensation guard)"], SIGNAL, name_size=13, sub_size=11)
    # leak, controls
    c.box(80, 680, 440, 80, "LEAK DETECTION — CRITICAL", ["rope under every manifold, CDU and rack · drip trays with drains", "leak → gateway 'critical' alarm → CDU isolates affected branch (CDU's own logic)"], LIFE, name_size=13, sub_size=11)
    c.box(560, 680, 380, 80, "CONTROLS (gateway)", ["CDU keeps TCS supply setpoint on its own · gateway monitors", "Modbus TCP: temps, flows, dP, pump speeds · relay1 enable (failsafe)"], SIGNAL, name_size=13, sub_size=11)
    c.box(1050, 560, 490, 100, "MECHANICAL PANEL", ["CDUs and dry coolers: own breakers, local disconnects, after ATS before UPS", "CDU pumps on UPS (option) for ride-through during generator start (30 s thermal mass)"], SIGNAL, name_size=14, sub_size=11)
    c.note(1050, 690, 490, ["flow ~1.5 L/min per kW at ΔT 10 K · TCS pressure ≤ 4 bar · filters 50 µm", "fill: PG25 deionised, biocide, inhibitor · sample at commissioning and yearly", "freeze: dry cooler loop PG30 to −15 °C; trace heat below"], MUTED, "Setpoints and limits")
    c.legend(80, 800, [(SIGNAL, False, "TCS supply (cold) / controls"), (LIFE, False, "TCS return (hot) / leak"), (GREEN, False, "FWS facility water (dry cooler loop)"), (POWER, False, "FWS return / IT racks")])
    c.save("04_cooling_one_line_liquid.svg")


# ================================================================ 5. life safety
def life_safety():
    c = Canvas(1600, 1040, "BEN Engine — Life-Safety One-Line (Hardwired) — Schreiber AI — IFC Rev A",
               "HARDWIRED and separate from controls · NFPA 72 detection · NFPA 2001 clean agent · NFPA 70 Art. 645 EPO · listed releasing panel · the controls bus only reads dry contacts")
    panel = c.box(600, 330, 400, 200, "RELEASING CONTROL PANEL (listed, FM/UL)", ["24 VDC, supervised circuits (open/short/ground fault)", "2 × 12 V 18 Ah batteries, 24 h standby + 10 min alarm", "cross-zoned detection → 30 s delay → release", "own 120 V circuit, breaker locked ON, red label"], LIFE, name_size=16, sub_size=12)
    # detection
    dets = [("SMOKE DETECTORS zone 1", "photoelectric, ceiling, 2 per 25 m²"), ("SMOKE DETECTORS zone 2", "cross-zone, hot aisle + return"), ("VESDA / aspirating (option)", "early warning, pipe in return air"), ("HEAT DETECTOR", "fixed 57 °C, mechanical section")]
    for i, (nm, sub) in enumerate(dets):
        y = 120 + i * 90
        c.box(80, y, 360, 70, nm, [sub, "Class B IDC, 4.7 kΩ EOL"], LIFE, name_size=13, sub_size=11)
        c.wire([(440, y + 35), (520, y + 35), (520, 400), (600, 400)], LIFE, 2.5)
    c.label(520, 115, "supervised initiating circuits, FPLR cable, red", LIFE, 11)
    # EPO stations
    for i in range(2):
        y = 500 + i * 90
        c.box(80, y, 360, 70, f"EPO STATION — door {i+1}", ["mushroom head, protective cover, labelled", "NC contacts in series loop"], LIFE, name_size=13, sub_size=11)
    c.wire([(440, 535), (480, 535), (480, 625), (440, 625)], LIFE, 2.5)
    c.wire([(480, 580), (560, 580), (560, 480), (600, 480)], LIFE, 2.5, label="EPO loop (series NC)", label_pos=0.3)
    # abort / manual
    c.box(80, 690, 360, 70, "ABORT STATION + MANUAL RELEASE", ["abort: hold to pause 30 s countdown", "manual release: dual action, at exit"], LIFE, name_size=13, sub_size=11)
    c.wire([(440, 725), (540, 725), (540, 500), (600, 500)], LIFE, 2.5)
    # outputs
    outs = [("CLEAN AGENT CYLINDER(S) — FK-5-1-12 / IG-541", "supervised actuator · nozzles sized for room volume at 5–8 % design concentration"),
            ("HORN/STROBES + 'DO NOT ENTER' sign", "pre-discharge horn, discharge strobe, outside sign"),
            ("DAMPERS CLOSE · ECONOMIZER CLOSE · IN-ROW FANS OFF", "relay to mechanical panel — hardwired, fail-closed dampers"),
            ("SHUNT TRIPS — UPS output · IT panel · mech. panel", "EPO shunt trips; UPS stops output; batteries disconnect (NEC 645.11)"),
            ("DOOR INTERLOCKS", "doors unlock on alarm for egress (fail-safe), auto-closers hold the agent")]
    for i, (nm, sub) in enumerate(outs):
        y = 120 + i * 100
        c.box(1080, y, 460, 80, nm, [sub], LIFE, name_size=12, sub_size=11)
        c.wire([(1000, 360 + i * 20), (1040, 360 + i * 20), (1040, y + 40), (1080, y + 40)], LIFE, 2.5)
    c.label(1040, 100, "supervised releasing / notification circuits", LIFE, 11)
    # the wall between life safety and controls
    c.parts.append(f'<rect x="60" y="800" width="1480" height="3" fill="{SIGNAL}"/>')
    c.text(70, 790, "BELOW THE LINE: CONTROLS (reads only)", 13, SIGNAL, weight=700)
    c.box(600, 820, 400, 70, "BEN NODE  X6 'EPO C / EPO NO'  + spare DI", ["reads panel AUX dry contacts: ALARM · TROUBLE · RELEASED · EPO", "MONITOR ONLY — cannot open, close or inhibit anything above the line"], SIGNAL, name_size=13, sub_size=11)
    c.wire([(800, 530), (800, 820)], SIGNAL, 2.5, dashed=True, label="AUX dry contacts (Form C), unsupervised, to node", label_pos=0.5)
    c.box(1080, 820, 460, 70, "GATEWAY → DASHBOARD / ALARM", ["ben/<unit>/alarm sev=critical · SMS/e-mail via customer's system", "no command path back to the panel exists (by design)"], SIGNAL, name_size=13, sub_size=11)
    c.wire([(1000, 855), (1080, 855)], SIGNAL, 2.5, dashed=True)
    c.note(80, 820, 500, ["1. Life-safety circuits: FPLR/FPLP red cable, own conduit, no shared boxes.", "2. Releasing panel on its own locked-on breaker, not on the controls UPS.", "3. The node sees the panel through dry contacts only (dashed line).", "4. Test per NFPA 72 ch. 14 yearly; log in docs/MAINTENANCE.md records.", "5. Nothing on MQTT / Modbus / SNMP can release agent or trip EPO."], LIFE, "Rules")
    c.legend(1160, 690, [(LIFE, False, "Life-safety circuits — hardwired, supervised"), (SIGNAL, True, "Dry-contact status to controls (read only)")])
    c.save("05_life_safety_one_line.svg")


if __name__ == "__main__":
    controls_network()
    node_wiring()
    for t in ("micro", "ben10", "ben20", "ben40"):
        power_one_line(t)
    cooling_air()
    cooling_liquid()
    life_safety()
