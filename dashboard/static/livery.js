// BEN Engine Rev 2 livery for the 3-D twin (brand/v2/livery, docs/REV2_DECISION.md §1, web/kit/BRAND_GUIDE.md §6–7).
// Outdoor modules, cabinets and the hall: Shop White body, Night Navy data plate band along the bottom of the long side,
// lockup-deep + "BEN ENGINE" top left, tier designation and tier product line right. BEN 1: Night Navy body, S2 band,
// lockup-signal / stack-signal. White-label: the partner name replaces the lockup; the band keeps "Schreiber AI" as the
// manufacturer field (licence rule). Masters are drawn from dashboard/static/brand/ (copies of brand/v2, never redrawn).
import * as THREE from './vendor/three/three.module.js';

export const LV = {
  shop: '#F4F7FB', paper: '#EEF4FC', night: '#06101F', s1: '#0B1A31', s2: '#0F2342', s3: '#16305A', border: '#24406B',
  signal: '#4C9DFF', deep: '#1E40AF', ink: '#0B1A31', slate: '#4A5D7A', fog: '#B2C1D8', steel: '#8EA7C8',
};
export const BODY = { shop: 0xF4F7FB, night: 0x06101F };

/** Tier product lines (same strings as brand/v2/livery/gen_livery.py PRODUCT_LINE and the web product page). */
export const PRODUCT_LINE = {
  ben1: 'Mini rack', ben5: 'Outdoor cabinet', ben30: '10 ft module', ben150: '20 ft module',
  ben300: 'Dense liquid · 20 ft', ben500: '40 ft module', ben700: 'Dense liquid · 40 ft', ben2000: 'Prefabricated hall',
};

const MASTERS = { 'lockup-deep': 6.527, 'lockup-signal': 6.527, 'stack-deep': 520.7 / 165, 'stack-signal': 520.7 / 165, 'mark-signal': 1, 'small-mark-32-signal': 1 };
const img = {};
const live = new Set();          // canvases drawn with a pending asset; redrawn once assets / fonts arrive
let fontsReady = false;

function svgImage(url, pxH) {
  return fetch(url).then(r => (r.ok ? r.text() : Promise.reject(new Error(url)))).then(txt => new Promise((res) => {
    const vb = /viewBox="([\d.\s-]+)"/.exec(txt); const [, , w, h] = vb ? vb[1].trim().split(/\s+/).map(Number) : [0, 0, 100, 100];
    const W = Math.round(pxH * w / h), H = pxH;   // give the root explicit pixel size so the raster is crisp and not letterboxed
    const fixed = txt.replace(/<svg\b([^>]*?)\swidth="[^"]*"/, '<svg$1').replace(/<svg\b([^>]*?)\sheight="[^"]*"/, '<svg$1').replace('<svg', `<svg width="${W}" height="${H}"`);
    const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null);
    im.src = URL.createObjectURL(new Blob([fixed], { type: 'image/svg+xml' }));
  })).catch(() => null);
}

function redrawAll() { for (const r of live) { r.draw(); r.tex.needsUpdate = true; } }

/** Load the masters and the brand fonts once; redraw every livery canvas when they arrive. */
export const liveryReady = (async () => {
  await Promise.all(Object.keys(MASTERS).map(async (k) => { img[k] = await svgImage(`brand/${k}.svg`, k.startsWith('stack') ? 660 : 400); }));
  try {
    await Promise.all(['800 64px Archivo', '900 64px Archivo', '600 32px "IBM Plex Mono"', '500 32px "IBM Plex Mono"'].map(f => document.fonts.load(f, 'BEN 3φ')));
    fontsReady = true;
  } catch (_) { /* system fallback */ }
  redrawAll();
  return true;
})();

const qrCache = {};
function qrImage(tier) {
  if (!(tier in qrCache)) { qrCache[tier] = null; svgImage(`brand/qr/${tier}-qr.svg`, 256).then(im => { qrCache[tier] = im; redrawAll(); }); }
  return qrCache[tier];
}

function volt(v) {   // '120 V 1ph 15/20 A plug-in' -> '120 V 1φ'; '12.47 kV MV service → 480 V 3ph' -> '12.47 kV'
  const m = /^\s*([\d/.,]+\s*k?V(?:\s*\dph)?)/.exec(v || '');
  return (m ? m[1] : (v || '')).replace('3ph', '3φ').replace('1ph', '1φ');
}
function kw(v) { v = Number(v); if (!Number.isFinite(v)) return '?'; return v >= 10 || v === Math.round(v) ? Math.round(v).toLocaleString('en-US') : String(v); }

/** Everything the livery prints, from the configuration payload. Serial is the sample format <TIER>-<YYWW>-0001 (gen_livery.py). */
export function liveryInfo(cfg, d) {
  const g = d.geometry || {};
  const mini = (d.kind || g.kind) === 'minirack';
  const label = d.tier_label || cfg.tier.toUpperCase();
  const serial = `${label.replace(/\s+/g, '')}-2646-0001`;
  const rated = kw(mini ? (g.it_kw_max_form || g.it_kw_max || cfg.it_kw) : (g.it_kw_max || cfg.it_kw));
  const ip = mini ? 'IP20' : 'IP66';
  const fields = ['Schreiber AI', 'BEN Engine', label, `S/N ${serial}`, `Rated ${rated} kW IT`, volt(d.voltage), ip, 'Rev 2'];
  return {
    lineup: cfg.lineup || 'rev1', tier: cfg.tier, label, productLine: PRODUCT_LINE[cfg.tier] || '', serial, rated, ip, fields,
    bandText: fields.join(' · '), whiteLabel: !!cfg.white_label, brand: cfg.brand || 'Schreiber AI', mini, form: cfg.form || '',
    bodyColor: mini ? LV.night : LV.shop,
  };
}

// --------------------------------------------------------------------------- canvas helpers
function setFont(g, weight, px, family, stretch) {
  g.font = `${weight} ${px}px ${family}`;
  try { g.fontStretch = stretch || 'normal'; } catch (_) { /* older canvas */ }
}
const ARCHIVO = 'Archivo, "Arial Black", Arial, sans-serif', MONO = '"IBM Plex Mono", Consolas, monospace';
function track(g, em, px) { try { g.letterSpacing = `${(em * px).toFixed(2)}px`; } catch (_) { /* no letterSpacing */ } }
function text(g, s, x, y, { weight = 600, px, family = MONO, color, align = 'left', tracking = 0, stretch } = {}) {
  setFont(g, weight, px, family, stretch); track(g, tracking, px); g.fillStyle = color; g.textAlign = align; g.textBaseline = 'alphabetic';
  // letterSpacing adds trailing space after the last glyph: shift right-aligned text by it
  g.fillText(s, align === 'right' ? x + tracking * px : align === 'center' ? x + tracking * px / 2 : x, y);
  track(g, 0, px);
}
function measure(g, s, px, weight, family, tracking, stretch) { setFont(g, weight, px, family, stretch); track(g, tracking, px); const w = g.measureText(s).width; track(g, 0, px); return w; }

/** The data plate band: rivets, fields with 1 px Border dividers, lead in Signal Blue, QR plate on Shop White at the right. */
export function drawBand(g, x, y, w, h, fields, { ground = LV.night, rows = 1, qr = null, lead = LV.signal, color = LV.fog, rule = LV.border } = {}) {
  g.fillStyle = ground; g.fillRect(x, y, w, h);
  g.fillStyle = rule; const rh = Math.max(1, h * 0.02); g.fillRect(x, y, w, rh); g.fillRect(x, y + h - rh, w, rh);
  let fs = rows === 1 ? h / 2.6 : h / 4.4;
  const pad = fs * 1.2, rv = fs * 0.7;
  const qs = h * 0.78, qx = x + w - pad * 0.6 - qs;
  if (qr !== undefined) { g.fillStyle = LV.shop; g.fillRect(qx, y + (h - qs) / 2, qs, qs); if (qr) g.drawImage(qr, qx, y + (h - qs) / 2, qs, qs); }
  const right = (qr !== undefined ? qx - pad * 0.6 : x + w);
  const rivet = (cx) => { g.beginPath(); g.arc(cx, y + h / 2, rv / 2, 0, Math.PI * 2); g.fillStyle = LV.night; g.fill(); g.lineWidth = Math.max(1, rv * 0.15); g.strokeStyle = LV.steel; g.stroke(); };
  rivet(x + pad); rivet(right - pad);
  const x0 = x + pad * 2, x1 = right - pad * 2;
  const lines = rows === 1 ? [fields] : [fields.slice(0, 4), fields.slice(4)];
  const T = 0.16;
  // shrink until the widest row fits with at least 1.6 em gaps
  for (let k = 0; k < 20; k++) {
    const need = Math.max(...lines.map(ln => ln.reduce((a, f) => a + measure(g, f.toUpperCase(), fs, 600, MONO, T), 0) + (ln.length - 1) * fs * 1.6));
    if (need <= x1 - x0) break; fs *= 0.92;
  }
  lines.forEach((ln, r) => {
    const by = rows === 1 ? y + h / 2 + fs * 0.36 : y + h * (r === 0 ? 0.36 : 0.74) + fs * 0.36;
    const ws = ln.map(f => measure(g, f.toUpperCase(), fs, 600, MONO, T));
    const gap = (x1 - x0 - ws.reduce((a, b) => a + b, 0)) / Math.max(1, ln.length - 1);
    let cx = x0;
    ln.forEach((f, i) => {
      text(g, f.toUpperCase(), cx, by, { weight: 600, px: fs, color: r === 0 && i === 0 ? lead : color, tracking: T });
      cx += ws[i];
      if (i < ln.length - 1) { g.fillStyle = rule; g.fillRect(cx + gap / 2, by - fs * 0.85, Math.max(1, fs * 0.06), fs); cx += gap; }
    });
  });
}

function drawLockup(g, master, x, y, M) { const im = img[master]; if (im) g.drawImage(im, x, y, M * MASTERS[master], M); return !!im; }

// --------------------------------------------------------------------------- layouts (mm values from gen_livery.py, in metres)
/** Long side of a module / hall (horizontal lockup) or a cabinet (stacked lockup). Canvas covers the whole side (L x H m). */
function drawSide(g, s, info, L, H, layout) {
  g.clearRect(0, 0, L * s, H * s);
  const cab = layout === 'cabinet';
  const post = cab ? 0.01 : (layout === 'hall' ? 0.3 : 0.16), railT = 0.11, railB = cab ? 0.14 : 0.16;
  const bh = cab ? 0.14 : 0.066 * Math.min(H, 2.9), by = H - railB - bh;
  const rows = cab || L < 5 ? 2 : 1;
  const qr = qrImage(info.tier);
  drawBand(g, post * s, by * s, (L - 2 * post) * s, bh * s, info.fields, { rows, qr });
  const archivoCap = 0.716, monoCap = 0.698;   // cap height / em
  if (cab) {
    const innerW = L - 0.08;
    const stackH = Math.min(0.2 * H, 0.72 * innerW / MASTERS['stack-deep']), M = stackH / 1.65, sy = 0.06 + 0.07 * H, cx = L / 2;
    let base;
    if (info.whiteLabel) { base = sy + 0.9 * M; text(g, info.brand.toUpperCase(), cx * s, base * s, { weight: 800, px: 0.62 * M * s / archivoCap, family: ARCHIVO, color: LV.ink, align: 'center', tracking: 0.02, stretch: 'expanded' }); base += 0.30 * M + 0.38 * M; }
    else { drawLockup(g, 'stack-deep', (cx - stackH * MASTERS['stack-deep'] / 2) * s, sy * s, stackH * s); base = sy + stackH + 0.68 * M; }
    text(g, 'BEN ENGINE', cx * s, base * s, { weight: 800, px: 0.5539 * M * s, family: ARCHIVO, color: LV.ink, align: 'center', tracking: 0.02, stretch: 'expanded' });
    const tb = base + 0.30 * M + 0.55 * M;
    text(g, info.label.toUpperCase(), cx * s, tb * s, { weight: 900, px: 0.55 * M * s / archivoCap, family: ARCHIVO, color: LV.ink, align: 'center', tracking: 0.01, stretch: 'expanded' });
    if (info.productLine) text(g, info.productLine.toUpperCase(), cx * s, (tb + 0.40 * M) * s, { weight: 500, px: 0.15 * M * s / monoCap, color: LV.slate, align: 'center', tracking: 0.08 });
    return;
  }
  const Hc = Math.min(H, 2.9), inset = 0.06 * Hc;
  const M = Math.min(0.165 * Hc, 0.8 * (L - 2 * post - 2 * inset) / MASTERS['lockup-deep']);
  const x0 = post + inset, y0 = railT + 0.10 * Hc;
  if (info.whiteLabel) {
    text(g, info.brand.toUpperCase(), x0 * s, (y0 + 0.69 * M) * s, { weight: 800, px: 0.62 * M * s / archivoCap, family: ARCHIVO, color: LV.ink, tracking: 0.02, stretch: 'expanded' });
    text(g, 'BEN ENGINE', x0 * s, (y0 + 1.37 * M) * s, { weight: 800, px: 0.5539 * M * s, family: ARCHIVO, color: LV.ink, tracking: 0.02, stretch: 'expanded' });
  } else {
    drawLockup(g, 'lockup-deep', x0 * s, y0 * s, M * s);
    text(g, 'BEN ENGINE', (x0 + 1.27213 * M) * s, (y0 + 1.37 * M) * s, { weight: 800, px: 0.5539 * M * s, family: ARCHIVO, color: LV.ink, tracking: 0.02, stretch: 'expanded' });
  }
  const xr = L - post - inset;
  text(g, info.label.toUpperCase(), xr * s, (by - 0.085 * Hc - 0.30 * M) * s, { weight: 900, px: 0.62 * M * s / archivoCap, family: ARCHIVO, color: LV.ink, align: 'right', tracking: 0.01, stretch: 'expanded' });
  if (info.productLine) text(g, info.productLine.toUpperCase(), xr * s, (by - 0.045 * Hc) * s, { weight: 500, px: 0.16 * M * s / monoCap, color: LV.slate, align: 'right', tracking: 0.08 });
}

/** BEN 1 12U cabinet side panel: Night Navy, stack-signal, BEN ENGINE, BEN 1, product line, S2 band (ben1-door-12u preview). */
function drawMiniPanel(g, s, info, W, H) {
  g.fillStyle = LV.night; g.fillRect(0, 0, W * s, H * s);
  g.strokeStyle = LV.border; g.lineWidth = Math.max(1, 0.004 * s); g.strokeRect(0.015 * s, 0.015 * s, (W - 0.03) * s, (H - 0.03) * s);
  const stackH = Math.min(0.26 * H, 0.66 * W / MASTERS['stack-signal']), M = stackH / 1.65, cx = W / 2, sy = 0.11 * H;
  let base;
  if (info.whiteLabel) { base = sy + 0.9 * M; text(g, info.brand.toUpperCase(), cx * s, base * s, { weight: 800, px: 0.55 * M * s / 0.716, family: ARCHIVO, color: LV.paper, align: 'center', tracking: 0.02, stretch: 'expanded' }); base += 0.68 * M; }
  else { drawLockup(g, 'stack-signal', (cx - stackH * MASTERS['stack-signal'] / 2) * s, sy * s, stackH * s); base = sy + stackH + 0.68 * M; }
  text(g, 'BEN ENGINE', cx * s, base * s, { weight: 800, px: 0.5539 * M * s, family: ARCHIVO, color: LV.fog, align: 'center', tracking: 0.02, stretch: 'expanded' });
  const tb = base + 0.30 * M + 0.62 * M;
  text(g, info.label.toUpperCase(), cx * s, tb * s, { weight: 900, px: 0.62 * M * s / 0.716, family: ARCHIVO, color: LV.paper, align: 'center', tracking: 0.01, stretch: 'expanded' });
  text(g, `${info.productLine.toUpperCase()} · ${info.form === 'rack10' ? '10-INCH 8U' : '19-INCH 12U · SOUND-DAMPED'}`, cx * s, (tb + 0.40 * M) * s, { weight: 500, px: 0.11 * M * s / 0.698, color: LV.steel, align: 'center', tracking: 0.08 });
  const bh = 0.08 * H;
  drawBand(g, 0.015 * s, (H - 0.06 * H - bh) * s, (W - 0.03) * s, bh * s, info.fields, { ground: LV.s2, rows: 2, qr: qrImage(info.tier) });
}

/** BEN 1 front plates: a lockup bezel strip (rack10 top) and the band strip (door / bezel bottom). */
function drawBezel(g, s, info, W, H) {
  g.fillStyle = LV.night; g.fillRect(0, 0, W * s, H * s);
  const M = Math.min(0.62 * H, 0.7 * W / MASTERS['lockup-signal']);
  const lw = M * MASTERS['lockup-signal'], x0 = (W - lw) / 2, y0 = (H - M) / 2;
  if (info.whiteLabel) text(g, info.brand.toUpperCase(), (W / 2) * s, (H / 2 + 0.3 * M) * s, { weight: 800, px: 0.6 * M * s / 0.716, family: ARCHIVO, color: LV.paper, align: 'center', tracking: 0.02, stretch: 'expanded' });
  else drawLockup(g, 'lockup-signal', x0 * s, y0 * s, M * s);
}
function drawBandPlate(g, s, info, W, H) { drawBand(g, 0, 0, W * s, H * s, info.fields, { ground: LV.s2, rows: 2, qr: qrImage(info.tier) }); }

// --------------------------------------------------------------------------- textures
function canvasTexture(wM, hM, maxPx, pxPerM, draw) {
  const s = Math.min(pxPerM, maxPx / wM, maxPx / hM);
  const cv = document.createElement('canvas'); cv.width = Math.max(4, Math.round(wM * s)); cv.height = Math.max(4, Math.round(hM * s));
  const g = cv.getContext('2d');
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const rec = { tex, draw: () => draw(g, s) };
  rec.draw(); live.add(rec);
  tex.userData = { livery: true, canvas: cv };
  return tex;
}

/** Side texture for a module, cabinet or hall: L x H metres. */
export function sideTexture(info, L, H, layout) { return canvasTexture(L, H, 4096, 900, (g, s) => drawSide(g, s, info, L, H, layout)); }
export function miniPanelTexture(info, W, H) { return canvasTexture(W, H, 2048, 3000, (g, s) => drawMiniPanel(g, s, info, W, H)); }
export function bezelTexture(info, W, H) { return canvasTexture(W, H, 2048, 4000, (g, s) => drawBezel(g, s, info, W, H)); }
export function bandPlateTexture(info, W, H) { return canvasTexture(W, H, 2048, 6000, (g, s) => drawBandPlate(g, s, info, W, H)); }
/** Forget the previous build's canvases (the scene calls this at the start of every rebuild). */
export function resetLivery() { for (const r of live) r.tex.dispose(); live.clear(); }
export const liveryFontsReady = () => fontsReady;
