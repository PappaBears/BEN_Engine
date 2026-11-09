#!/usr/bin/env python3
"""BEN Engine one-page sales sheet (brand package touchpoint 2), US Letter.

    python3 brand/v2/print/gen_sales_sheet.py          # writes sales-sheet-ben.html (+ .png and .pdf with --render)

Numbers are the Rev 2 decision table (docs/REV2_DECISION.md §2) as verified in software/ben_engine/config.py (the BEN 1000 target ships as BEN 700); nothing measured yet is shown as a number:
proof slots and prices are yellow "fact pending" chips until a pilot result or a quote fills them.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from brandlib import C, qr_group  # noqa: E402

URL = "https://schreiberai.com/hello?src=sheet-ben"

LINEUP = [  # tier, IT kW, enclosure, who it is for — docs/REV2_DECISION.md §2
    ("BEN 1", "0.2–1.5", "Indoor mini rack, 120 V plug-in", "Tiny business: one or two AI boxes, NAS, firewall", True),
    ("BEN 5", "2–5", "Outdoor 24U cabinet, IP66", "Small business outdoors", False),
    ("BEN 30", "10–30", "10 ft module", "SMB private cloud", False),
    ("BEN 150", "50–150", "20 ft module", "Air or rear-door cooling", False),
    ("BEN 300", "150–300", "20 ft, liquid-first", "One or two current liquid racks", True),
    ("BEN 500", "150–500", "40 ft module", "Direct liquid + CDU", False),
    ("BEN 700", "400–700", "40 ft, liquid-first", "Up to five liquid racks", True),
]


def build() -> str:
    qsvg, total = qr_group(URL, 0, 0, 25, C["night"], C["shop"])
    qr = f'<svg class="qr" viewBox="0 0 {total:.3f} {total:.3f}" role="img" aria-label="QR code: {URL}">{qsvg}</svg>'
    lockup = (HERE.parent / "lockup-deep.svg").read_text(encoding="utf-8").replace("<svg ", '<svg class="lk" ', 1)
    tiers = "".join(
        f'<div class="t{" new" if new else ""}"><span class="tn">{n}</span><span class="kw">{kw} kW</span><span class="en">{en}</span><span class="wh">{wh}</span>'
        + ('<span class="nw">new in Rev 2</span>' if new else "") + "</div>" for n, kw, en, wh, new in LINEUP)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BEN Engine sales sheet</title>
<link rel="stylesheet" href="../fonts/fonts.css">
<style>
@page {{ size: 8.5in 11in; margin: 0; }}
:root {{ --night:#06101F; --s2:#0F2342; --border:#24406B; --signal:#4C9DFF; --deep:#1E40AF; --amber:#FFB020;
  --shop:#F4F7FB; --paper:#EEF4FC; --ink:#0B1A31; --slate:#4A5D7A; --fog:#B2C1D8; --steel:#8EA7C8; --pend:#FBE7A1; --rule:#D7DFEA; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: #8EA7C8; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ width: 8.5in; height: 11in; margin: 0 auto; background: var(--shop); color: var(--ink); position: relative; overflow: hidden;
  padding: .5in .6in .95in; display: grid; gap: .17in; align-content: start; font: 400 10.5pt/1.5 "IBM Plex Sans", Arial, sans-serif; }}
.hd {{ display: flex; justify-content: space-between; align-items: center; padding-bottom: .16in; border-bottom: 3pt solid var(--deep); }}
.hd .lk {{ width: 3.1in; height: auto; display: block; }}
.hd .meta {{ text-align: right; font: 500 8pt/1.5 "IBM Plex Mono", Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--slate); }}
.hd .meta b {{ color: var(--ink); font-weight: 600; }}
.eyebrow {{ font: 500 8.5pt/1.3 "IBM Plex Mono", Consolas, monospace; letter-spacing: .1em; text-transform: uppercase; color: var(--deep); margin: .06in 0 0; }}
h1 {{ margin: 0; font: 900 28pt/1.06 "Archivo", "Arial Black", Arial, sans-serif; font-stretch: 125%; letter-spacing: -.01em; text-wrap: balance; }}
h1 em {{ font-style: normal; color: var(--deep); }}
.lede {{ margin: 0; font-size: 11.5pt; line-height: 1.5; color: var(--slate); max-width: 6.6in; }}
.lede b {{ color: var(--ink); }}
h2 {{ margin: .02in 0 -.06in; font: 600 8.5pt/1.3 "IBM Plex Mono", Consolas, monospace; letter-spacing: .1em; text-transform: uppercase; color: var(--slate); }}
.row {{ display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); border-top: 1.5pt solid var(--ink); border-bottom: 1pt solid var(--rule); }}
.t {{ padding: .1in .07in .12in; border-right: 1pt solid var(--rule); display: grid; gap: .03in; align-content: start; position: relative; }}
.t:last-child {{ border-right: 0; }}
.t.new {{ background: #E8EEF6; }}
.tn {{ font: 800 12pt/1.1 "Archivo", Arial, sans-serif; font-stretch: 112%; white-space: nowrap; }}
.kw {{ font: 600 8.5pt/1.2 "IBM Plex Mono", Consolas, monospace; color: var(--deep); white-space: nowrap; }}
.en {{ font-size: 7.6pt; line-height: 1.35; color: var(--ink); }}
.wh {{ font-size: 7.2pt; line-height: 1.35; color: var(--slate); }}
.nw {{ font: 600 6.3pt/1 "IBM Plex Mono", Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--deep); margin-top: .02in; }}
.note {{ margin: -.08in 0 0; font: 400 7.6pt/1.45 "IBM Plex Mono", Consolas, monospace; color: var(--slate); }}
.why {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .16in; }}
.why div {{ border-top: 1pt solid var(--rule); padding-top: .08in; }}
.why b {{ display: block; font: 800 11pt/1.2 "Archivo", Arial, sans-serif; margin-bottom: .03in; }}
.why p {{ margin: 0; font-size: 9pt; line-height: 1.45; color: var(--slate); }}
.pf {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .14in; }}
.pf div {{ background: #E8EEF6; border-radius: 6pt; padding: .12in .14in; display: grid; gap: .05in; align-content: start; }}
.chip {{ justify-self: start; font: 600 7.5pt/1 "IBM Plex Mono", Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--ink); background: var(--pend); padding: 3pt 6pt; border-radius: 3pt; }}
.pf span {{ font-size: 8.6pt; line-height: 1.4; color: var(--slate); }}
.cta {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: .25in; padding: .18in .22in; border-radius: 8pt; background: var(--night); color: var(--paper); }}
.cta b {{ display: block; font: 800 16pt/1.15 "Archivo", Arial, sans-serif; font-stretch: 112%; }}
.cta p {{ margin: .05in 0 .12in; font: 500 8.5pt/1.5 "IBM Plex Mono", Consolas, monospace; color: var(--fog); }}
.btn {{ display: inline-block; background: var(--amber); color: var(--night); font: 600 11pt/1 "IBM Plex Sans", Arial, sans-serif; padding: .11in .18in; border-radius: 5pt; text-decoration: none; }}
.qrp {{ background: var(--shop); border-radius: 6pt; padding: .04in; display: grid; justify-items: center; gap: .03in; }}
.qr {{ width: 1.05in; height: 1.05in; display: block; }}
.qrp span {{ font: 600 6.2pt/1.2 "IBM Plex Mono", Consolas, monospace; letter-spacing: .04em; color: var(--ink); padding-bottom: .03in; }}
.ftr {{ position: absolute; left: 0; right: 0; bottom: 0; }}
.legal {{ position: absolute; left: .6in; right: .6in; bottom: .46in; font: 400 7pt/1.4 "IBM Plex Mono", Consolas, monospace; color: var(--slate); display: flex; justify-content: space-between; gap: .2in; }}
.dp {{ display: flex; align-items: center; gap: 1.6em; height: 2.6em; padding: 0 1.4em; background: var(--s2); border-top: 1px solid var(--border); font: 600 7.4pt/1 "IBM Plex Mono", Consolas, monospace; letter-spacing: .16em; text-transform: uppercase; color: var(--fog); white-space: nowrap; overflow: hidden; }}
.dp::before, .dp::after {{ content: ""; flex: none; width: .7em; height: .7em; border-radius: 50%; background: var(--night); box-shadow: inset 0 0 0 1.5px var(--steel); }}
.dp span {{ flex: none; }} .dp i {{ flex: none; width: 1px; height: 1em; background: var(--border); }} .dp b {{ color: var(--signal); font-weight: 600; }} .dp .grow {{ flex: 1; }}
@media screen {{ body {{ padding: .3in 0; }} .page {{ box-shadow: 0 18px 40px rgba(6,16,31,.35); }} }}
@media print {{ body {{ padding: 0; background: #fff; }} }}
</style></head>
<body><main class="page">
<header class="hd">{lockup}<div class="meta"><b>BEN Engine, by Schreiber AI</b><br>Veteran-owned · schreiberai.com</div></header>
<div>
<p class="eyebrow">Modular data centers, sized by IT power · Rev 2</p>
<h1>Your own AI infrastructure, <em>arrives finished.</em></h1>
</div>
<p class="lede">BEN Engine puts power, cooling, compute and controls in one sealed box, from a mini rack on an office shelf to a liquid-cooled 40 ft module. <b>Schreiber AI designs, builds, commissions and watches it.</b> Fixed scope, a price up front, and the risks on the table before the price.</p>
<h2>The lineup · the number is the maximum IT power in <span style="text-transform:none">kW</span></h2>
<div class="row">{tiers}</div>
<p class="note">Outdoor tiers: NEMA 4X / IP66, hose-tested, hardening H1 / H2 / H3. BEN 300 and BEN 700: direct liquid W45, CDU N+1; sold once the real footprint passes our interference checks. BEN 2000 (2 MW hall) on request.</p>
<div class="why">
<div><b>One model, every document.</b><p>Drawings, bill of materials, alarm limits and the quote come from the same configuration, so they agree.</p></div>
<div><b>Risks before price.</b><p>You see which risks BEN covers by design, which we monitor and which stay with you, before you see a number.</p></div>
<div><b>Your crew runs it.</b><p>Local-first controls, a digital twin from day one, and a commissioning script you watch on your own pad.</p></div>
</div>
<h2>Proof</h2>
<div class="pf">
<div><span class="chip">fact pending</span><span>BEN 1 lighthouse unit: measured IT load and noise at 1 m, first install</span></div>
<div><span class="chip">fact pending</span><span>BEN 300 lighthouse unit: measured PUE at full liquid load</span></div>
<div><span class="chip">fact pending</span><span>Starting price per tier, quoted · days from order to site acceptance</span></div>
</div>
<div class="cta"><div><b>Book a 20-minute call.</b><p>Scan for the 5-minute survey, starting prices and a time that suits you.</p><a class="btn" href="{URL}">Book a 20-minute call</a></div>
<div class="qrp">{qr}<span>schreiberai.com/hello</span></div></div>
<div class="legal"><span>Schreiber AI is a Schreiber Holding LLC company.</span><span>Numbers: configuration model, Rev 2 · yellow = not yet measured</span></div>
<div class="ftr"><div class="dp"><span><b>Schreiber AI</b></span><i></i><span>BEN Engine</span><i></i><span>Sales sheet</span><i></i><span>BEN 1 – BEN 700</span><i></i><span>Rev 2</span><span class="grow"></span><span>1 / 1</span></div></div>
</main></body></html>
"""


if __name__ == "__main__":
    out = HERE / "sales-sheet-ben.html"
    out.write_text(build(), encoding="utf-8")
    print("wrote", out.relative_to(HERE.parent.parent.parent))
    if "--render" in sys.argv:
        js = f"""
import {{ createRequire }} from 'node:module';
const require = createRequire('/opt/node22/lib/node_modules/');
let pw; try {{ pw = require('playwright'); }} catch {{ pw = createRequire(import.meta.url)('playwright'); }}
const b = await pw.chromium.launch({{ args: ['--no-sandbox'] }});
const p = await b.newPage({{ viewport: {{ width: 816, height: 1056 }}, deviceScaleFactor: 2 }});
await p.emulateMedia({{ media: 'print' }});
await p.goto('file://{out}', {{ waitUntil: 'networkidle' }});
await p.waitForTimeout(400);
await p.screenshot({{ path: '{HERE / "sales-sheet-ben.png"}', clip: {{ x: 0, y: 0, width: 816, height: 1056 }} }});
await p.pdf({{ path: '{HERE / "sales-sheet-ben.pdf"}', width: '8.5in', height: '11in', printBackground: true }});
await b.close();
"""
        tmp = HERE / ".render-sheet.mjs"
        tmp.write_text(js)
        try:
            subprocess.run(["node", str(tmp)], check=True)
        finally:
            tmp.unlink()
        print("rendered sales-sheet-ben.png and sales-sheet-ben.pdf")
