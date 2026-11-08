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


# ================================================================ 1. controls network (Pro and Lite)
def _right_zones(c, mgmt_pts, wan_pts, mgmt_label_pos=0.55, wan_label_pos=0.15):
    """Zones 2, 3, 4 on the right-hand side; identical on both controls sheets."""
    c.parts.append(f'<rect x="1090" y="110" width="470" height="330" rx="14" fill="none" stroke="{GREEN}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(1106, 136, "ZONE 2 — MANAGEMENT VLAN 30  (10.30.0.0/24)", 15, GREEN, weight=700)
    c.parts.append(f'<rect x="1090" y="470" width="470" height="200" rx="14" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(1106, 496, "ZONE 3 — CUSTOMER IT  (physically separate)", 15, MUTED, weight=700)
    c.parts.append(f'<rect x="1090" y="700" width="470" height="200" rx="14" fill="none" stroke="{POWER}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(1106, 726, "ZONE 4 — REMOTE SUPPORT (optional, outbound only)", 15, POWER, weight=700)
    c.box(1120, 170, 200, 100, "PANEL HMI / DASHBOARD", ["7 in panel or screen at the door", "HTTPS :8000 · WSS :9001"], GREEN, name_size=13, sub_size=11)
    c.box(1340, 170, 200, 100, "ENGINEERING LAPTOP", ["SSH keys only", "MQTT TLS :8884"], GREEN, name_size=14, sub_size=11)
    c.box(1120, 310, 420, 100, "MANAGEMENT PORT (edge computer NIC 2)", ["separate NIC, separate cable · only ports marked MGMT", "edge API reachable; PLC, Pods, meters are NOT reachable from here"], GREEN, name_size=13, sub_size=11)
    c.wire(mgmt_pts, GREEN, width=2.5, label="NIC 2 · VLAN 30 only", label_pos=mgmt_label_pos)
    c.wire([(1220, 310), (1220, 270)], GREEN, width=2); c.wire([(1440, 310), (1440, 270)], GREEN, width=2)
    c.box(1120, 520, 420, 120, "CUSTOMER SWITCH / FIREWALL / WAN", ["their servers, their fiber, their rules", "NO cable to the controls switch. NO controller interface here.", "shared with BEN only: power, cooling, the room"], MUTED, name_size=14, sub_size=11)
    c.text(1120, 660, "✕  no link on purpose", 14, LIFE, weight=700)
    c.box(1120, 750, 420, 130, "WIREGUARD wg0 → support.schreiberai.com", ["edge computer initiates · nothing listens on WAN", "customer runs: ben-vpn-support.sh up / down · auto-off 48 h", "inbound over tunnel: SSH + API only"], POWER, name_size=14, sub_size=11, dashed=True)
    c.wire(wan_pts, POWER, width=2, dashed=True, label="optional WAN NIC (USB)", label_pos=wan_label_pos)


def controls_network():
    c = Canvas(1600, 1140, "BEN Engine — Controls Network One-Line — BEN Controls Pro — Schreiber AI — IFC Rev B",
               "IEC 62443 zones: Z1 control (PLC, Axioline I/O, transmitters) · Z1.5 data (edge computer) · Z1T Thread mesh (Pods, DTLS/mTLS) · Z2 management · customer IT isolated · life safety hardwired (sheet 05)")
    # zone frames
    c.parts.append(f'<rect x="40" y="110" width="700" height="530" rx="14" fill="none" stroke="{SIGNAL}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(56, 136, "ZONE 1 — CONTROL  (VLAN 20, 10.20.0.0/24 · no default route, no WAN)", 15, SIGNAL, weight=700)
    c.parts.append(f'<rect x="770" y="110" width="290" height="530" rx="14" fill="none" stroke="{GREEN}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(786, 136, "ZONE 1.5 — DATA (edge host)", 15, GREEN, weight=700)
    c.parts.append(f'<rect x="40" y="670" width="1020" height="230" rx="14" fill="none" stroke="{SIGNAL}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(56, 696, "ZONE 1T — BEN MESH  (Thread 2.4 GHz, fd00:ben::/64 · DTLS join · mTLS MQTT · stub network, no route out)", 15, SIGNAL, weight=700)

    # --- zone 1: PLC, I/O, switch, RTU chain, transmitters
    plc = c.box(60, 165, 310, 100, "PLC — PLCnext AXC F 2152", ["IEC 61131-3 interlocks · 10.20.0.10", "Modbus TCP / OPC UA server · Modbus RTU master", "UL 508 · IEC 62443-4-1 process"], SIGNAL, name_size=15, sub_size=11)
    io = c.box(60, 295, 310, 110, "AXIOLINE F I/O", ["DI16 ×2 · DOR (enable chain) · DO8", "RTD4 ×2..8 (Pt1000) · AI4 I ×1..4 (4–20 mA)", "RS UNI (RS-485) · local bus from the PLC"], SIGNAL, name_size=15, sub_size=11)
    c.wire([(215, 265), (215, 295)], SIGNAL, 3, label="Axioline local bus", label_pos=0.5, label_dy=5, label_size=10)
    sw = c.box(400, 165, 320, 100, "MANAGED SWITCH", ["Phoenix FL SWITCH 2008 / Moxa EDS-2010", "VLAN 20 ports · PoE for Pod E · port security", "fed from the 24 VDC panel supply"], SIGNAL, name_size=15, sub_size=11)
    c.wire([(370, 215), (400, 215)], SIGNAL, 3)
    tcp = c.box(400, 295, 320, 110, "MODBUS TCP / SNMP (VLAN 20)", ["rack PDUs (SNMP v3) 10.20.0.50+", "CDU / dry cooler 10.20.0.40 · UPS NMC 10.20.0.30", "meter gateway 10.20.0.20 · polled by the edge"], SIGNAL, name_size=14, sub_size=11)
    c.wire([(560, 265), (560, 295)], SIGNAL, 2.5)
    rtu = c.box(400, 430, 320, 60, "MODBUS RTU (RS-485, PLC master)", ["power meters · UPS · cooling unit controllers · Pod E slaves"], POWER, fill=SLATE, name_size=13, sub_size=11, dashed=True)
    c.wire([(370, 380), (385, 380), (385, 460), (400, 460)], POWER, 2.5, dashed=True)
    c.label(560, 508, "RS-485 2-wire + shield · 120 Ω ends · 19200 8E1", POWER, 10)
    # transmitters row
    tx = [("Pt1000 STRINGS", ["supply · return · outdoor", "3-wire → RTD4"], SIGNAL), ("SETRA 264 / DWYER MS2", ["aisle ΔP ±125 Pa", "4–20 mA → AI4"], SIGNAL),
          ("VAISALA HMD60", ["RH / T", "4–20 mA → AI4"], SIGNAL), ("RLE SEAHAWK LD2100", ["leak zones (rope)", "zone relays → DI16"], LIFE),
          ("DOORS · EPO · FIRE AUX", ["dry contacts → DI16", "MONITOR ONLY"], LIFE)]
    for i, (nm, sub, col) in enumerate(tx):
        x = 55 + i * 137
        c.box(x, 520, 128, 90, nm, sub, col, fill=SLATE, name_size=10, sub_size=10, rx=6)
        c.wire([(x + 64, 520), (x + 64, 500), (120 + i * 40, 500), (120 + i * 40, 405)], col, 2)
    c.text(56, 630, "wired industrial transmitters: UL 61010-1 · shielded pairs, shields landed in the panel only · Class 2", 11, MUTED)

    # --- zone 1.5: edge computer, RCPs
    edge = c.box(790, 165, 250, 150, "EDGE COMPUTER", ["OnLogic Karbon 400 (alt. SIMATIC IPC227G)", "NIC 1 = 10.20.0.1 · TPM 2.0 + LUKS", "Mosquitto mTLS 8883 · chrony · OTBR", "ben_engine.api · twin · SQLite · PLC bridge"], GREEN, name_size=15, sub_size=11)
    c.wire([(720, 215), (790, 215)], SIGNAL, 3, label="NIC 1", label_pos=0.5, label_dy=-8, label_size=10)
    c.wire([(370, 245), (385, 245), (385, 280), (760, 280), (760, 250), (790, 250)], GREEN, 2, dashed=True, label="Modbus TCP 502", label_pos=0.22, label_dy=-6, label_size=10)
    rcp1 = c.box(790, 360, 115, 70, "RCP 1", ["MGM240P · USB", "OTBR wpan0"], SIGNAL, fill=SLATE, name_size=13, sub_size=10, rx=6)
    rcp2 = c.box(925, 360, 115, 70, "RCP 2", ["MGM240P · USB", "wpan1 (BEN 20/40)"], SIGNAL, fill=SLATE, name_size=13, sub_size=10, rx=6)
    c.wire([(847, 315), (847, 360)], SIGNAL, 2); c.wire([(982, 315), (982, 360)], SIGNAL, 2)
    c.note(790, 460, 250, ["edge → PLC writes only 3 registers:", "watchdog · setpoint trim · test request", "(Modbus TCP 502 or OPC UA 4840)", "edge never commands a valve or a unit", "nftables: drop in / out / forward"], GREEN, "Advisory only")

    # --- zone 1T: Pods (mesh bus inside the zone frame, below its title)
    BUS = 718
    c.wire([(847, 430), (847, 445), (778, 445), (778, BUS), (120, BUS)], SIGNAL, 2, dashed=True)
    c.wire([(982, 430), (982, 445), (1052, 445), (1052, BUS), (778, BUS)], SIGNAL, 2, dashed=True)
    c.label(560, BUS - 7, "Thread 802.15.4 mesh · self-healing · Pods route for each other", SIGNAL, 10)
    pods = [("BEN POD W", ["rack 1 rails ×2", "Pt1000 ×4 · RH · ΔP", "2×AA or 24 V"]), ("BEN POD W", ["rack 2 rails ×2", "sleepy end device", "attested · cert_id"]),
            ("BEN POD W", ["rack N …", "router-eligible on 24 V", "lqi · parent in status"]), ("BEN POD W-X", ["dry cooler / generator", "IP65 · −40…70 °C", "outdoor Pt1000"]),
            ("BEN POD W", ["door frames", "door · leak rope", "DI2 = EPO aux (monitor)"]), ("BEN POD E", ["mechanical panel / CDU", "PoE + Ethernet backup", "RS-485 slave to PLC · 2 relays"])]
    for i, (nm, sub) in enumerate(pods):
        x = 60 + i * 166
        c.box(x, 740, 150, 100, nm, sub, SIGNAL, name_size=14, sub_size=10)
        c.wire([(x + 75, 740), (x + 75, BUS)], SIGNAL, 2, dashed=True)
    c.text(56, 868, "two Pods per rack + two per unit · MQTT publish only to fd00:ben::1 · SNTP from the edge · Pod E additionally: Cat6 to the switch (PoE) and RS-485 to the PLC", 11, MUTED)

    _right_zones(c, [(1040, 205), (1078, 205), (1078, 360), (1120, 360)], [(1040, 300), (1068, 300), (1068, 815), (1120, 815)])
    c.legend(60, 920, [(SIGNAL, False, "Ethernet / Modbus TCP / SNMP — controls VLAN 20"), (SIGNAL, True, "Thread 2.4 GHz mesh (DTLS / mTLS)"), (POWER, True, "RS-485 Modbus RTU · optional outbound VPN"), (GREEN, False, "Edge host / management VLAN 30 — TLS only"), (LIFE, False, "Leak / door / EPO / fire — monitor only")])
    c.save("01_controls_network_one_line.svg")


def controls_network_lite():
    c = Canvas(1600, 1140, "BEN Engine — Controls Network One-Line — BEN Controls Lite — Schreiber AI — IFC Rev B",
               "BEN Micro / BEN 10 · same zones, same protocol, no PLC: RevPi Connect 4 runs the edge software AND the interlock service behind a hardware watchdog relay · Pods on the same BEN Mesh")
    c.parts.append(f'<rect x="40" y="110" width="1020" height="530" rx="14" fill="none" stroke="{SIGNAL}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(56, 136, "ZONE 1 + 1.5 — CONTROL AND DATA ON ONE INDUSTRIAL CONTROLLER  (VLAN 20, 10.20.0.0/24 · no default route, no WAN)", 15, SIGNAL, weight=700)
    c.parts.append(f'<rect x="40" y="670" width="1020" height="230" rx="14" fill="none" stroke="{SIGNAL}" stroke-width="1.5" stroke-dasharray="6 6"/>')
    c.text(56, 696, "ZONE 1T — BEN MESH  (Thread 2.4 GHz, fd00:ben::/64 · DTLS join · mTLS MQTT)", 15, SIGNAL, weight=700)

    rpi = c.box(60, 165, 340, 150, "REVPI CONNECT 4 (KUNBUS)", ["industrial DIN-rail · UL/CE · −25…55 °C · hardware watchdog", "NIC 1 = 10.20.0.1 (controls) · NIC 2 = 10.30.0.1 (mgmt)", "ben-interlocks.service (software PLC, 10 Hz)", "Mosquitto mTLS · OTBR · chrony · ben_engine.api · SQLite"], SIGNAL, name_size=15, sub_size=11)
    dio = c.box(60, 345, 160, 100, "REVPI DIO", ["16 DI / 16 DO 24 V", "PiBridge", "O_14 → KW1"], SIGNAL, name_size=14, sub_size=10)
    aio = c.box(240, 345, 160, 100, "REVPI AIO", ["4 × 4–20 mA", "2 × RTD Pt1000", "PiBridge"], SIGNAL, name_size=14, sub_size=10)
    c.wire([(140, 315), (140, 345)], SIGNAL, 3); c.wire([(320, 315), (320, 345)], SIGNAL, 3)
    kw1 = c.box(60, 470, 120, 70, "KW1 WDT RELAY", ["NO in enable chain", "NC → beacon"], GREEN, fill=SLATE, name_size=11, sub_size=9, rx=6)
    c.wire([(140, 445), (140, 470)], GREEN, 2.5, label="O_14", label_pos=0.5, label_dy=4, label_size=10)
    sw = c.box(440, 165, 300, 90, "SWITCH (5–8 port)", ["Phoenix FL SWITCH 2005 / Moxa EDS-2005", "controls segment only · PoE injector for Pod E"], SIGNAL, name_size=14, sub_size=11)
    c.wire([(400, 215), (440, 215)], SIGNAL, 3, label="NIC 1", label_pos=0.5, label_dy=-8, label_size=10)
    rcp = c.box(790, 165, 150, 90, "RCP", ["MGM240P · USB", "OTBR wpan0"], SIGNAL, fill=SLATE, name_size=14, sub_size=10, rx=6)
    c.wire([(400, 180), (425, 180), (425, 158), (865, 158), (865, 165)], SIGNAL, 2)
    c.text(950, 162, "USB", 10, SIGNAL, weight=600, font=MONO)
    tcp = c.box(440, 290, 300, 100, "MODBUS TCP / SNMP (VLAN 20)", ["rack PDU (SNMP v3) · UPS NMC", "cooling unit controller (Micro: 1–2 units)", "polled by ben_engine.api"], SIGNAL, name_size=13, sub_size=11)
    c.wire([(590, 255), (590, 290)], SIGNAL, 2.5)
    rtu = c.box(440, 420, 300, 60, "MODBUS RTU (RS-485 on RevPi COM)", ["power meter · UPS · cooling controller · Pod E slave"], POWER, fill=SLATE, name_size=13, sub_size=11, dashed=True)
    c.wire([(400, 290), (420, 290), (420, 450), (440, 450)], POWER, 2.5, dashed=True)
    bms = c.box(790, 290, 250, 100, "CUSTOMER BMS (option)", ["reads the SAME register map", "Modbus TCP 10.20.0.1:502 · read-only", "PLC_MODE bit 8 = LITE"], MUTED, name_size=13, sub_size=11, dashed=True)
    c.wire([(740, 215), (770, 215), (770, 340), (790, 340)], SIGNAL, 2, dashed=True)
    tx = [("Pt1000 ×2", ["supply · return", "→ AIO RTD"], SIGNAL), ("SETRA 264 ΔP", ["4–20 mA → AIO"], SIGNAL), ("VAISALA HMD60", ["RH 4–20 mA → AIO"], SIGNAL),
          ("SEAHAWK / LEAK ROPE", ["zone relay → DIO"], LIFE), ("DOORS · EPO · FIRE AUX", ["dry contacts → DIO", "MONITOR ONLY"], LIFE), ("COOLING UNITS 1–2", ["run / fault → DIO", "enable ← DO via KW1"], GREEN), ("ATS · GEN · UPS", ["contacts → DIO"], SIGNAL)]
    targets = [310, 320, 330, 188, 197, 206, 215]          # AIO bottom (Pt1000/ΔP/RH) · DIO bottom right of KW1 (contacts)
    for i, (nm, sub, col) in enumerate(tx):
        x = 55 + i * 143
        c.box(x, 565, 134, 65, nm, sub, col, fill=SLATE, name_size=10, sub_size=10, rx=6)
        yy = 546 + i * 2
        c.wire([(x + 67, 565), (x + 67, yy), (targets[i], yy), (targets[i], 445)], col, 1.6)
    c.note(790, 420, 250, ["interlock service stalls → restart 10 s", "→ HW watchdog reboot 60 s → outputs off", "→ KW1 opens → units on local control"], GREEN, "Failsafe (no PLC)")

    BUS = 718
    c.wire([(865, 255), (865, 275), (1050, 275), (1050, BUS), (120, BUS)], SIGNAL, 2, dashed=True)
    c.label(500, BUS - 7, "Thread mesh · 3 Pods on Micro, 2 per rack + 2 on BEN 10", SIGNAL, 10)
    pods = [("BEN POD W", ["cabinet inlet / outlet", "Pt1000 ×4 · RH · ΔP"]), ("BEN POD W", ["door · leak rope", "DI2 = EPO aux (monitor)"]), ("BEN POD W-X", ["outdoor condenser", "IP65"]), ("BEN POD E (option)", ["PoE to switch · RS-485 to RevPi", "2 relays (beacon, lights)"])]
    for i, (nm, sub) in enumerate(pods):
        x = 60 + i * 250
        c.box(x, 740, 230, 100, nm, sub, SIGNAL, name_size=14, sub_size=11)
        c.wire([(x + 115, 740), (x + 115, BUS)], SIGNAL, 2, dashed=True)
    c.text(56, 868, "same Pods, same firmware, same join procedure and certificates as Pro · MQTT publish only to fd00:ben::1", 11, MUTED)

    _right_zones(c, [(330, 165), (330, 96), (1078, 96), (1078, 360), (1120, 360)], [(365, 165), (365, 104), (1068, 104), (1068, 815), (1120, 815)], mgmt_label_pos=0.45, wan_label_pos=0.62)
    c.legend(60, 920, [(SIGNAL, False, "Ethernet / Modbus TCP / SNMP — controls segment"), (SIGNAL, True, "Thread 2.4 GHz mesh (DTLS / mTLS)"), (POWER, True, "RS-485 Modbus RTU · optional outbound VPN"), (GREEN, False, "Management — TLS only · watchdog / enable chain"), (LIFE, False, "Leak / door / EPO / fire — monitor only")])
    c.save("01b_controls_network_one_line_lite.svg")


# ================================================================ 2. controller panel + pod wiring
def controller_pod_wiring():
    c = Canvas(1600, 1440, "BEN Engine — BEN Controller Panel Wiring + BEN Pod E/W Wiring — Schreiber AI — IFC Rev B",
               "Left: UL 508A BEN Controls Pro panel (PLCnext + Axioline + edge computer), DIN rows and field terminal groups · Right: BEN Pod E terminal by terminal, Pod W deltas · field wiring Class 2 except relay contacts")
    # ------------------------------------------------------------- panel
    PX, PY, PW, PH = 40, 130, 740, 1200
    c.parts.append(f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="16" fill="{PANEL}" stroke="{SIGNAL}" stroke-width="3"/>')
    c.text(PX + PW / 2, PY + 32, "BEN CONTROLLER — PRO PANEL  (800 × 1000 × 300 mm, NEMA 12, UL 508A, SCCR 10 kA)", 16, TEXT, anchor="middle", weight=800)

    def din_row(y, label, items, h=78):
        c.text(PX + 16, y - 8, label, 12, MUTED, weight=700, font=MONO)
        c.parts.append(f'<rect x="{PX+12}" y="{y+h/2-3}" width="{PW-24}" height="6" fill="{SLATE}"/>')   # the DIN rail
        x = PX + 16
        out = []
        for nm, sub, col, w in items:
            out.append(c.box(x, y, w, h, nm, sub, col, fill=SLATE, name_size=10, sub_size=9, rx=6))
            x += w + 8
        return out
    rowA = din_row(200, "ROW A — MAINS IN + 24 VDC (120 VAC section behind finger-safe barrier)", [
        ("DISC + CB 20 A", ["controls circuit", "UPS-backed"], POWER, 108), ("SPD TYPE 3", ["PLT-SEC-T3-230", "FM contact → DI"], POWER, 108),
        ("PSU 1 QUINT4 10 A", ["24 VDC", "92 % eff."], POWER, 118), ("PSU 2 QUINT4 10 A", ["from house ckt", "redundant"], POWER, 118),
        ("ORING QUINT4", ["N+1 · OK contact", "→ DI PSU_RED_OK"], POWER, 118), ("UPS 24 VDC", ["QUINT4-UPS 3.4 Ah", "ON_BATTERY → DI"], POWER, 118)])
    rowB = din_row(320, "ROW B — PLC + AXIOLINE F I/O (local bus)", [
        ("AXC F 2152", ["PLCnext · 10.20.0.10", "ETH1 → switch"], SIGNAL, 138), ("DI16 #1", ["cool run", "fault · X10"], SIGNAL, 68), ("DI16 #2", ["leak · valves", "doors · EPO"], SIGNAL, 68),
        ("DOR LC/1", ["ENABLE", "CHAIN"], GREEN, 68), ("DO8", ["enables", "valves"], SIGNAL, 68), ("RTD4 ×n", ["Pt1000", "X50"], SIGNAL, 68), ("AI4 I", ["4–20 mA", "X60"], SIGNAL, 68), ("RS UNI", ["RS-485", "X80"], POWER, 68)], h=90)
    rowC = din_row(455, "ROW C — EDGE COMPUTER, SWITCH, BORDER ROUTER RCPs", [
        ("ONLOGIC KARBON 400", ["NIC1 10.20.0.1 · NIC2 10.30.0.1", "TPM 2.0 · LUKS · 24 VDC"], GREEN, 230), ("FL SWITCH 2008 / EDS", ["VLAN 20 · PoE ports", "24 VDC"], SIGNAL, 230),
        ("RCP 1", ["MGM240P USB", "N-type → roof"], SIGNAL, 108), ("RCP 2", ["MGM240P USB", "BEN 20/40"], SIGNAL, 108)], h=80)
    rowD = din_row(575, "ROW D — DOOR: HMI, SELECTOR, RESETS, BEACON", [
        ("HMI 7 in", ["PLCnext web panel", "VLAN 30"], GREEN, 150), ("SELECTOR OFF / AUTO / MAN", ["→ DI hmi_off · hmi_manual", "edge cannot change mode"], SIGNAL, 210),
        ("RESET LATCHED", ["momentary → DI"], SIGNAL, 150), ("RESET LEAK", ["momentary → DI"], SIGNAL, 100), ("BEACON", ["red · DO + NC"], LIFE, 80)], h=70)
    # field terminal groups
    c.text(PX + 16, 672, "ROW E — FIELD TERMINALS (PT 2,5 push-in, knife-disconnect on every input, shield bar, PE bar)", 12, MUTED, weight=700, font=MONO)
    groups = [("X10 COOLING DI", ["run n · fault n", "per unit (dry)"], SIGNAL), ("X20 LEAK / VALVES", ["SeaHawk zone n", "valve closed LS n"], LIFE),
              ("X30 DOORS · EPO · FIRE", ["door n · EPO loop aux", "fire alarm/trbl/rel/sup"], LIFE), ("X40 POWER DI", ["utility OK · ATS on gen", "gen run/fault · UPS batt"], SIGNAL),
              ("X50 RTD Pt1000", ["supply · return · outdoor", "3-wire, shielded"], SIGNAL), ("X60 4–20 mA", ["ΔP · RH · IT kW", "loop 24 V fused"], SIGNAL),
              ("X70 RELAY OUT", ["ENABLE CHAIN · unit enables", "valves · pump stop · beacon"], GREEN), ("X80 RS-485", ["A · B · SHD", "120 Ω end"], POWER)]
    gb = []
    for i, (nm, sub, col) in enumerate(groups):
        r, k = divmod(i, 4)
        gb.append(c.box(PX + 16 + k * 180, 685 + r * 204, 172, 82, nm, sub, col, fill=SLATE, name_size=11, sub_size=10, rx=6))
    devs = [("COOLING UNITS 1..N", ["run / fault aux contacts", "remote enable input ← X70 chain"], SIGNAL), ("ISO VALVES + SEAHAWK LD2100", ["valve actuators 24 V ← X70", "zone relays + limit switches → X20"], LIFE),
            ("FIRE PANEL / EPO LOOP AUX", ["Form C aux contacts → X30", "READ ONLY — can never open the loop"], LIFE), ("ATS · GENERATOR · UPS", ["dry contacts → X40", "Modbus RTU → X80"], SIGNAL),
            ("Pt1000 STRINGS", ["supply / return / outdoor", "→ X50 (3-wire)"], SIGNAL), ("SETRA 264 · HMD60 · kW XDCR", ["4–20 mA loops → X60", "loop-powered 24 V"], SIGNAL),
            ("ENABLE CHAIN", ["DOR relay NO in series with every", "unit enable · opens on PLC STOP"], GREEN), ("METERS · UPS · COOLING · POD E", ["RS-485 daisy chain ← X80", "19200 8E1 · 120 Ω both ends"], POWER)]
    for i, (nm, sub, col) in enumerate(devs):
        r, k = divmod(i, 4)
        b = c.box(PX + 16 + k * 180, 787 + r * 204, 172, 82, nm, sub, col, fill=SLATE, name_size=10, sub_size=9, rx=6)
        g = gb[i]
        for dx in (-30, 0, 30):      # three field conductors per group, straight down into the device box
            c.wire([(g[0] + g[2] / 2 + dx, g[1] + g[3]), (b[0] + b[2] / 2 + dx, b[1])], col, 1.6)
    c.text(PX + 16, 1085, "field devices are OUTSIDE the panel · shields landed at the panel end only · knife-disconnects on every group", 10, MUTED, font=MONO)
    c.text(PX + 16, 1108, "EPO / fire wires READ the hardwired loop. They can never open it.  (sheet 05)", 12, LIFE, weight=700)
    c.note(PX + 16, 1122, 320, ["24 VDC Class 2 outside the mains section", "18 AWG signal · 16 AWG 24 V · 12 AWG mains", "SCCR 10 kA @ 120/240 V (UL 508A SB4)", "heat ≈ 110 W typ → filter fan 100 m³/h"], MUTED, "Panel rules")
    c.note(PX + 346, 1122, 410, ["1. PSU/ORING first, then PLC rack, then edge + switch.", "2. Land PE + shield bars; bond to the container grid.", "3. Pull field cables to X10..X80; disconnects OPEN.", "4. Power up; load PLC project; record PLC_PROJECT_CRC.", "5. Close disconnects one group at a time; watch dashboard."], GREEN, "Assembly order (one action per step)")

    # ------------------------------------------------------------- Pod E
    nx, ny, nw, nh = 1130, 150, 300, 640
    c.parts.append(f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="16" fill="{PANEL}" stroke="{SIGNAL}" stroke-width="3"/>')
    c.text(nx + nw / 2, ny + 30, "BEN POD E", 22, TEXT, anchor="middle", weight=800)
    c.text(nx + nw / 2, ny + 52, "MGM240P · Thread / Eth / 485", 11, MUTED, anchor="middle")
    for i, (nm, col) in enumerate([("PWR", GREEN), ("LINK", POWER), ("IDENT", SIGNAL), ("RLY", LIFE)]):
        c.dot(nx + nw / 2 - 48 + i * 32, ny + 80, col, 6); c.text(nx + nw / 2 - 48 + i * 32, ny + 98, nm, 9, MUTED, anchor="middle")
    c.lines(nx + nw / 2, ny + 300, ["pins (logical → MGM240P)", "RLY1 32→PB0 · RLY2 33→PB1", "LEAK 36→PC0 · DOOR 39→PC1", "PULSE 34→PC2 · DI2 35→PC3", "IDENT 2→PD2 · LINK 3→PD3", "RTD CS PA0 · DRDY PA4", "I²C PC4/PC5 · DIP PA5..PA8", "SWD locked (Secure Vault)"], 10, MUTED, anchor="middle", font=MONO)

    def terminal(side, y, label, pins, color, step=20):
        x = nx - 10 if side == "L" else nx + nw - 70
        h = step * len(pins) + 12
        c.parts.append(f'<rect x="{x}" y="{y}" width="80" height="{h}" rx="4" fill="{SLATE}" stroke="{color}" stroke-width="2"/>')
        c.text(x + 40, y - 6, label, 11, color, anchor="middle", weight=700, font=MONO)
        ys = []
        for i, p in enumerate(pins):
            py = y + 16 + i * step
            c.parts.append(f'<rect x="{x+6}" y="{py-7}" width="68" height="14" rx="2" fill="{BG}"/>')
            c.text(x + 40, py + 4, p, 10, TEXT, anchor="middle", font=MONO)
            ys.append(py)
        return ys
    LX, LW = 830, 240; LR = LX + LW   # left field boxes 830..1070 ; terminals at 1120..1200
    # X3 RTD
    y3 = terminal("L", 170, "X3 RTD", ["RTD1 +", "RTD1 −", "RTD1 S", "RTD2 +", "RTD2 −", "RTD2 S", "RTD3 +", "RTD3 −", "RTD3 S", "RTD4 +", "RTD4 −", "RTD4 S"], SIGNAL, step=18)
    c.box(LX, 165, LW, 230, "Pt1000 PROBES ×4 → T_in_1..2, T_out_1..2", ["class A, 3-wire, 2 m PTFE leads", "+ / − excitation, S = sense (lead comp.)", "ADS124S08 24-bit, 500 µA IDAC, ratiometric", "T_in at rack face 1/3 + 2/3 height", "T_out at rack rear · ±0.15 °C k=2", "shield → Pod shield pin only"], SIGNAL, name_size=11, sub_size=10)
    for k in range(12):
        c.wire([(LR, 185 + k * 17), (nx - 10, y3[k])], SIGNAL, 1.4)
    # X4 DI/leak
    y4 = terminal("L", 420, "X4 DI/LEAK", ["DI1 C", "DI1 NO", "DI2 C", "DI2 NO", "LEAK A", "LEAK B"], SIGNAL)
    c.box(LX, 410, LW, 140, "DOOR · EPO MONITOR · LEAK ROPE", ["DI1: door reed, dry, HIGH = open", "DI2: releasing panel / EPO AUX — MONITOR ONLY", "LEAK: resistive rope 2-wire, comparator 50 kΩ", "3.3 V wetting, 20 ms debounce"], SIGNAL, name_size=11, sub_size=10)
    for k in range(6):
        c.wire([(LR, 430 + k * 20), (nx - 10, y4[k])], SIGNAL if k < 2 or k > 3 else LIFE, 1.6)
    # X5 4-20 mA + X8 pulse
    y5 = terminal("L", 575, "X5 4-20mA", ["AI0 +", "AI0 −", "AI1 +", "AI1 −"], POWER)
    c.box(LX, 565, LW, 100, "4–20 mA ×2 (isolated) → ai0..1_mA", ["loop-powered from X2 24 V → xmtr → AI+", "165 Ω 0.1 % shunt · ±0.02 mA", "typical: CDU pressure, flow, UPS output"], POWER, name_size=11, sub_size=10)
    for k in range(4):
        c.wire([(LR, 585 + k * 20), (nx - 10, y5[k])], POWER, 1.6)
    y8 = terminal("L", 690, "X8 PULSE", ["S0 +", "S0 −"], SIGNAL)
    c.box(LX, 680, LW, 60, "METER S0 PULSE → pulse_kwh", ["opto 5–27 V · 1000 imp/kWh · ≤ 100 Hz"], SIGNAL, name_size=11, sub_size=10)
    for k in range(2):
        c.wire([(LR, 700 + k * 20), (nx - 10, y8[k])], SIGNAL, 1.6)
    c.text(LX, 765, "P1 (+, red tube) → cold aisle tap · P2 (−, blue) → hot aisle tap · SDP810 on board", 10, MUTED)
    # right side terminals
    RX = 1455
    y1 = terminal("R", 170, "X1 RJ45", ["PoE+DATA"], SIGNAL)
    c.lines(RX, 180, ["PoE switch port", "802.3af class 0", "Cat6 ≤ 90 m", "W5500 MAC/PHY", "path = eth"], 10, SIGNAL)
    c.wire([(nx + nw + 10, y1[0]), (RX - 8, y1[0])], SIGNAL, 2.5)
    y2 = terminal("R", 250, "X2 24VDC", ["V+", "0V"], POWER)
    c.lines(RX, 262, ["24 VDC alt.", "18–30 V · 1 A fuse", "also loop supply"], 10, POWER)
    c.wire([(nx + nw + 10, y2[0]), (RX - 8, y2[0])], POWER, 2); c.wire([(nx + nw + 10, y2[1]), (RX - 8, y2[1])], POWER, 2)
    y6 = terminal("R", 340, "X6 RELAYS", ["R1 COM", "R1 NO", "R1 NC", "R2 COM", "R2 NO", "R2 NC"], LIFE)
    c.lines(RX, 352, ["relay1 FAILSAFE", "beacon / fan boost", "drops 60 s after", "broker loss", "relay2 lights", "holds last state", "≤ 5 A pilot duty", "snubber + MOV"], 10, LIFE, lh=15)
    for k in range(6):
        c.wire([(nx + nw + 10, y6[k]), (RX - 8, y6[k])], LIFE, 1.6)
    y7 = terminal("R", 490, "X7 RS-485", ["A", "B", "SHD"], POWER)
    c.lines(RX, 500, ["Modbus RTU slave", "to PLC X80 /", "RevPi COM", "19200 8E1", "120 Ω jumper", "path = rs485"], 10, POWER, lh=15)
    for k in range(3):
        c.wire([(nx + nw + 10, y7[k]), (RX - 8, y7[k])], POWER, 1.6)
    c.text(RX, 600, "NOT in the cooling-", 10, GREEN, weight=700); c.text(RX, 614, "enable chain: that is", 10, GREEN, weight=700); c.text(RX, 628, "the controller's relay", 10, GREEN, weight=700)
    c.note(LX, 800, 730, ["Relay contacts are Class 1: #14 Cu THHN in their own conduit; everything else Class 2.", "Shields land at the Pod end only. Bond the DIN rail (Pod E) / rack rail (Pod W).", "Plug X3..X8 LAST, after the edge shows the Pod attested and online.", "Label: unit · node id · serial · EUI-64 · cert_id (from the provisioning record)."], MUTED, "Pod wiring rules")

    # ------------------------------------------------------------- Pod W deltas
    wx, wy = 830, 930
    c.parts.append(f'<rect x="{wx}" y="{wy}" width="730" height="300" rx="16" fill="{PANEL}" stroke="{SIGNAL}" stroke-width="3"/>')
    c.text(wx + 20, wy + 34, "BEN POD W (wireless) — same board family, what changes", 18, TEXT, weight=800)
    c.lines(wx + 20, wy + 64, ["SAME:  X3 RTD ×4 · X4 DI1 / DI2 / LEAK · X8 pulse · P1/P2 ΔP tubing · SHT45 on board · LEDs IDENT / LINK",
                                "NOT FITTED:  X1 RJ45/PoE · X5 4–20 mA · X6 relays · X7 RS-485  (no wired path: Thread only, no outputs)",
                                "POWER:  BT1 = 2 × AA LiFeS2 (L91) ≈ 1.4 y at 1 Hz, ≈ 4 y at 0.2 Hz (calculated)  OR  X2 24 VDC → router-eligible",
                                "MOUNT:  clip-on rack rail 95 × 60 × 28 mm, 2 per rack (front top, rear bottom)  ·  W-X: IP65 115 × 90 × 55 mm, U.FL antenna",
                                "RADIO:  Thread sleepy end device, 1 s poll on battery · label 'Contains FCC ID / IC' per MGM240P datasheet · ch 25",
                                "JOIN:  label QR = serial · EUI-64 · PSKd → ben-add-pod.sh → 10 min joiner window → DTLS → mTLS → attest (cert_id)",
                                "PROBES:  T_in_1 at 1/3, T_in_2 at 2/3 rack height on the front rail; T_out_1/2 same heights on the rear rail",
                                "BATTERY:  battery_pct < 20 % alarm → swap cells → re-attach + re-attest within 60 s; buffer lost, identity kept"], 11, MUTED, lh=22)
    c.text(wx + 20, wy + 262, "Nothing on a Pod W can switch anything: no outputs. Life safety: DI2 reads an aux contact only.", 11, LIFE, weight=700)

    # ground + legend
    c.wire([(PX + 40, PY + PH), (PX + 40, PY + PH + 30), (PX + 150, PY + PH + 30)], GREEN, 2.5)
    c.text(PX + 160, PY + PH + 35, "panel PE bar → container bonding grid (#6 Cu green) · shield bar isolated from PE, bonded at one point", 12, GREEN)
    c.legend(830, 1250, [(SIGNAL, False, "Signal / sensor / Ethernet (Class 2)"), (POWER, False, "24 VDC · 4–20 mA loops · RS-485 (Class 2)"), (LIFE, False, "Life-safety contact — MONITOR ONLY · relay contacts (Class 1)"), (GREEN, False, "Ground / bond · enable chain · failsafe")])
    c.save("02_controller_pod_wiring.svg")


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
    controls_network_lite()
    controller_pod_wiring()
    for t in ("micro", "ben10", "ben20", "ben40"):
        power_one_line(t)
    cooling_air()
    cooling_liquid()
    life_safety()
