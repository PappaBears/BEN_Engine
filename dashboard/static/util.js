// Shared helpers: API client, formatting, DOM, sparklines (canvas, no library).

export const BRAND = {
  graphite: '#0B1018', slate: '#152234', panel: '#1B2B42', text: '#EDF4FF', muted: '#9FB3CC',
  cyan: '#66E3FF', amber: '#FFC66D', red: '#FF707D', green: '#6EE7A8',
};

export const reducedMotion = () => window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export class ApiError extends Error {
  constructor(status, detail, body) { super(detail); this.status = status; this.body = body; }
}

export async function api(path, opts = {}) {
  const init = { method: opts.method || (opts.body !== undefined ? 'POST' : 'GET'), headers: {} };
  if (opts.body !== undefined) { init.headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(opts.body); }
  const r = await fetch(path, init);
  const ct = r.headers.get('content-type') || '';
  const body = ct.includes('json') ? await r.json() : await r.text();
  if (!r.ok) {
    const detail = (body && body.detail) || (body && body.errors && body.errors.join('; ')) || (typeof body === 'string' ? body : r.statusText);
    throw new ApiError(r.status, detail, body);
  }
  return body;
}

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (v === true) el.setAttribute(k, '');
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c === undefined || c === null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

export const fmt = {
  num(v, d = 1) { return (v === null || v === undefined || Number.isNaN(v)) ? '—' : Number(v).toFixed(d); },
  kw(v) { return fmt.num(v, 1); },
  pct(v) { return fmt.num(v, 0); },
  hms(s) {
    s = Math.max(0, Math.floor(s || 0));
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}`;
  },
  clock(ts) { return ts ? new Date(ts * 1000).toLocaleTimeString([], { hour12: false }) : '—'; },
  iso(ts) { return ts ? new Date(ts * 1000).toISOString().replace('T', ' ').slice(0, 19) + 'Z' : '—'; },
  ago(sec) { if (sec === null || sec === undefined) return '—'; if (sec < 60) return `${Math.round(sec)} s`; if (sec < 3600) return `${Math.floor(sec / 60)} min ${Math.round(sec % 60)} s`; return `${(sec / 3600).toFixed(1)} h`; },
};

/** Temperature colour ramp (°C) shared by sensors, particles and tiles. */
export function tempColor(c) {
  const stops = [[16, 0x3a7bff], [20, 0x66e3ff], [24, 0x6ee7a8], [28, 0xffc66d], [33, 0xff8a5c], [40, 0xff707d]];
  if (c === null || c === undefined || Number.isNaN(c)) return 0x9fb3cc;
  if (c <= stops[0][0]) return stops[0][1];
  for (let i = 1; i < stops.length; i++) {
    if (c <= stops[i][0]) {
      const [c0, a] = stops[i - 1], [c1, b] = stops[i];
      const t = (c - c0) / (c1 - c0);
      return lerpColor(a, b, t);
    }
  }
  return stops[stops.length - 1][1];
}
export function lerpColor(a, b, t) {
  const ar = a >> 16 & 255, ag = a >> 8 & 255, ab = a & 255, br = b >> 16 & 255, bg = b >> 8 & 255, bb = b & 255;
  return (Math.round(ar + (br - ar) * t) << 16) | (Math.round(ag + (bg - ag) * t) << 8) | Math.round(ab + (bb - ab) * t);
}
export const hex = (n) => '#' + n.toString(16).padStart(6, '0');

/**
 * Sparkline: draws one or more series on a canvas. series = [{values:[], color}], optional band {min,max}.
 */
export function drawSparkline(canvas, series, opts = {}) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 260, hgt = canvas.clientHeight || 56;
  if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(hgt * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(hgt * dpr); }
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, hgt);
  const pad = 4;
  let lo = Infinity, hi = -Infinity;
  for (const s of series) for (const v of s.values) if (v !== null && v !== undefined && !Number.isNaN(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  if (opts.band) { lo = Math.min(lo, opts.band.min); hi = Math.max(hi, opts.band.max); }
  if (!isFinite(lo)) { ctx.fillStyle = BRAND.muted; ctx.font = '11px ' + getComputedStyle(canvas).fontFamily; ctx.fillText('no data yet', 8, hgt / 2 + 4); return; }
  if (hi - lo < (opts.minSpan || 1)) { const m = (hi + lo) / 2, s = (opts.minSpan || 1) / 2; lo = m - s; hi = m + s; }
  const y = (v) => hgt - pad - (v - lo) / (hi - lo) * (hgt - 2 * pad);
  const n = Math.max(...series.map(s => s.values.length), 2);
  const x = (i) => pad + i / (n - 1) * (w - 2 * pad);
  if (opts.band) {
    ctx.fillStyle = 'rgba(110,231,168,0.08)';
    ctx.fillRect(0, y(opts.band.max), w, Math.max(1, y(opts.band.min) - y(opts.band.max)));
  }
  if (opts.limit !== undefined) {
    ctx.strokeStyle = 'rgba(255,112,125,0.6)'; ctx.setLineDash([3, 3]); ctx.beginPath(); ctx.moveTo(0, y(opts.limit)); ctx.lineTo(w, y(opts.limit)); ctx.stroke(); ctx.setLineDash([]);
  }
  for (const s of series) {
    ctx.strokeStyle = s.color || BRAND.cyan; ctx.lineWidth = s.width || 1.5; ctx.beginPath();
    let started = false;
    s.values.forEach((v, i) => {
      if (v === null || v === undefined || Number.isNaN(v)) { started = false; return; }
      const px = x(i + (n - s.values.length)), py = y(v);
      if (!started) { ctx.moveTo(px, py); started = true; } else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }
  ctx.fillStyle = BRAND.muted; ctx.font = '10px ' + (getComputedStyle(canvas).fontFamily || 'monospace');
  ctx.textAlign = 'right';
  ctx.fillText(fmt.num(hi, opts.digits ?? 1), w - 4, 11);
  ctx.fillText(fmt.num(lo, opts.digits ?? 1), w - 4, hgt - 5);
}

export function download(text, filename, type = 'text/csv') {
  const blob = text instanceof Blob ? text : new Blob([text], { type });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename; document.body.append(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}

/** Resolve a sensor id (Twin.sensors()) to its live value in a state dict. */
export function sensorValue(id, st) {
  if (!st) return null;
  let m;
  if ((m = /^T_in_r(\d+)_/.exec(id))) return st.rack_inlet_c?.[+m[1] - 1] ?? null;
  if ((m = /^T_out_r(\d+)/.exec(id))) return st.rack_outlet_c?.[+m[1] - 1] ?? null;
  switch (id) {
    case 'T_supply': return st.supply_c;
    case 'T_return': return st.return_c;
    case 'RH_room': return st.rh_pct;
    case 'dP_aisle': return st.aisle_dp_pa;
    case 'leak_floor': return st.leak ? 1 : 0;
    case 'door_main': return st.door_open ? 1 : 0;
    case 'P_utility': return st.power?.utility_kw;
  }
  return null;
}
