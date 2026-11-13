// BEN Engine twin: procedural equipment models and canvas textures (no external model files).
// Real proportions with recognisable details: perforated rack doors, 1U/2U trays with status LEDs, rear liquid manifolds with
// quick-disconnect hoses, CDU / fan-coil grilles and HMI, UPS frames with louvres, lithium cabinets with module drawers,
// switchboard sections with breaker faces, dry-cooler fan guards, pad-mount transformer fins. Static detail is merged per
// object and material (mergeParts), so a rack costs a handful of draw calls, not hundreds.
import * as THREE from './vendor/three/three.module.js';

let ANISO = 4;
/** The scene sets the renderer's max anisotropy once it knows it. */
export function setAnisotropy(a) { ANISO = Math.max(1, Math.min(4, a || 1)); }   // 4x: crisp at grazing angles without the 16x cost on software GL

const FONT = '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif';
const MONO = '"IBM Plex Mono", ui-monospace, monospace';

// ----------------------------------------------------------------------------- materials (shared)
const std = (color, roughness, metalness, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness, metalness, ...extra });
export const EM = {
  rackSteel: std(0x1b1f26, 0.48, 0.5),       // powder-coated black rack frame
  rackFrame: std(0x0f1216, 0.55, 0.5),
  chrome: std(0xc9ced6, 0.22, 0.95),
  steel: std(0x8d96a3, 0.38, 0.85),
  galv: std(0xa9b1bb, 0.45, 0.8),
  darkSteel: std(0x2c333d, 0.5, 0.7),
  rubber: std(0x15171b, 0.85, 0.0),
  hose: std(0x1e2228, 0.6, 0.05),
  pipeSupply: std(0x5cd6ff, 0.35, 0.35),
  pipeReturn: std(0xff8a3d, 0.35, 0.35),
  copper: std(0xb87333, 0.35, 0.9),
  equipLight: std(0xd9dee5, 0.42, 0.35),       // RAL 7035-like light grey cabinet paint
  equipMid: std(0x9aa3ae, 0.45, 0.45),
  equipDark: std(0x353c46, 0.5, 0.5),
  brass: std(0xc8a24a, 0.3, 0.9),
  red: std(0xc8102e, 0.35, 0.3),
  yellow: std(0xf2c94c, 0.6, 0.1),
  green: std(0x4d6b52, 0.55, 0.35),            // pad-mount transformer green
  insulation: std(0xe9d9a6, 0.95, 0.0),
  black: std(0x0b0d10, 0.6, 0.3),
  fanBlade: std(0x2a2f36, 0.45, 0.4),
};
const ledMat = new Map();
export function led(color) { if (!ledMat.has(color)) ledMat.set(color, new THREE.MeshBasicMaterial({ color, toneMapped: false })); return ledMat.get(color); }

// ----------------------------------------------------------------------------- merge helper
const UNIT_BOX = new THREE.BoxGeometry(1, 1, 1);
const cylCache = new Map();
function cylGeo(seg) { if (!cylCache.has(seg)) cylCache.set(seg, new THREE.CylinderGeometry(1, 1, 1, seg, 1)); return cylCache.get(seg); }
const torCache = new Map();
function torGeo(r, t, seg) { const k = `${r}|${t}|${seg}`; if (!torCache.has(k)) torCache.set(k, new THREE.TorusGeometry(r, t, 6, seg)); return torCache.get(k); }
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _p = new THREE.Vector3(), _s = new THREE.Vector3();

/** Collects static detail parts; build() merges them into one mesh per material. */
export class Parts {
  constructor() { this.list = []; }
  add(geo, mat, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = 1, sz = 1) {
    _m.compose(_p.set(x, y, z), _q.setFromEuler(_e.set(rx, ry, rz)), _s.set(sx, sy, sz));
    this.list.push({ geo, mat, m: _m.clone() }); return this;
  }
  box(w, h, d, mat, x, y, z, rx = 0, ry = 0, rz = 0) { return this.add(UNIT_BOX, mat, x, y, z, rx, ry, rz, w, h, d); }
  /** Cylinder of radius r and length len along the given axis ('x' | 'y' | 'z'). */
  cyl(r, len, mat, x, y, z, axis = 'y', seg = 12) {
    const rot = axis === 'x' ? [0, 0, Math.PI / 2] : axis === 'z' ? [Math.PI / 2, 0, 0] : [0, 0, 0];
    return this.add(cylGeo(seg), mat, x, y, z, ...rot, r, len, r);
  }
  /** Pipe segment between two points. */
  pipe(a, b, r, mat, seg = 10) {
    const dir = new THREE.Vector3().subVectors(b, a); const len = dir.length(); if (len < 1e-4) return this;
    _q.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    _m.compose(_p.addVectors(a, b).multiplyScalar(0.5), _q, _s.set(r, len, r));
    this.list.push({ geo: cylGeo(seg), mat, m: _m.clone() }); return this;
  }
  ring(r, t, mat, x, y, z, axis = 'y', seg = 32) {
    const rot = axis === 'y' ? [Math.PI / 2, 0, 0] : axis === 'x' ? [0, Math.PI / 2, 0] : [0, 0, 0];
    return this.add(torGeo(r, t, seg), mat, x, y, z, ...rot);
  }
  build(parent, { cast = false, receive = true } = {}) {
    for (const mesh of mergeParts(this.list)) { mesh.castShadow = cast; mesh.receiveShadow = receive; parent.add(mesh); }
    this.list = []; return parent;
  }
}
export function mergeParts(list) {
  const byMat = new Map();
  for (const p of list) { if (!byMat.has(p.mat)) byMat.set(p.mat, []); byMat.get(p.mat).push(p); }
  const out = [];
  for (const [mat, items] of byMat) {
    let n = 0; const gs = [];
    for (const p of items) { const g = (p.geo.index ? p.geo.toNonIndexed() : p.geo.clone()); g.applyMatrix4(p.m); gs.push(g); n += g.attributes.position.count; }
    const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2);
    let o = 0;
    for (const g of gs) { const c = g.attributes.position.count; pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3); if (g.attributes.uv) uv.set(g.attributes.uv.array, o * 2); o += c; g.dispose(); }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.computeBoundingSphere();
    out.push(new THREE.Mesh(geo, mat));
  }
  return out;
}

/** Box whose front face (dir '-z' | '+z' | '+x' | '-x') carries its own material. */
export function faceBox(w, h, d, bodyMat, frontMat, dir = '-z') {
  const idx = { '+x': 0, '-x': 1, '+y': 2, '-y': 3, '+z': 4, '-z': 5 }[dir];
  const mats = [bodyMat, bodyMat, bodyMat, bodyMat, bodyMat, bodyMat]; mats[idx] = frontMat;
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mats); m.castShadow = true; m.receiveShadow = true;
  return m;
}

// ----------------------------------------------------------------------------- canvas helpers
const texCache = new Map();
function canvasTex(key, w, h, draw, { srgb = true, repeat = null } = {}) {
  if (key && texCache.has(key)) return texCache.get(key);
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const g = cv.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(cv);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = ANISO; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; t.generateMipmaps = true;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  if (key) texCache.set(key, t);
  return t;
}
function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function vgrad(g, x, y, w, h, c0, c1) { const gr = g.createLinearGradient(x, y, x, y + h); gr.addColorStop(0, c0); gr.addColorStop(1, c1); g.fillStyle = gr; g.fillRect(x, y, w, h); }
function holes(g, x, y, w, h, pitch, r, color) { g.fillStyle = color; for (let j = 0, yy = y + pitch / 2; yy < y + h; j++, yy += pitch * 0.866) for (let xx = x + (j % 2 ? pitch : pitch / 2); xx < x + w; xx += pitch) { g.beginPath(); g.arc(xx, yy, r, 0, Math.PI * 2); g.fill(); } }
function slots(g, x, y, w, h, n, color, vertical = false) {
  g.fillStyle = color;
  if (vertical) { const p = w / n; for (let i = 0; i < n; i++) rr(g, x + i * p + p * 0.25, y, p * 0.5, h, p * 0.25), g.fill(); }
  else { const p = h / n; for (let i = 0; i < n; i++) rr(g, x, y + i * p + p * 0.28, w, p * 0.44, p * 0.2), g.fill(); }
}
function label(g, txt, x, y, px, color, { weight = 600, align = 'left', font = FONT } = {}) { g.font = `${weight} ${px}px ${font}`; g.fillStyle = color; g.textAlign = align; g.textBaseline = 'middle'; g.fillText(txt, x, y); }
function screw(g, x, y, r = 3) { g.fillStyle = '#8a929c'; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill(); g.strokeStyle = '#3a4048'; g.lineWidth = 1; g.beginPath(); g.moveTo(x - r * 0.7, y); g.lineTo(x + r * 0.7, y); g.stroke(); }

// ----------------------------------------------------------------------------- rack fronts
/** Rack face with 1U/2U trays; returns { map, emissive }. profile 'nvl72' (GB300-class liquid rack) or 'std' (air servers). */
export function rackFrontTextures(units, profile = 'std') {
  const key = `rack|${units}|${profile}`;
  if (texCache.has(key)) return texCache.get(key);
  const W = 512, H = 2048, uh = H / units;
  const items = [];
  if (profile === 'nvl72') {
    const seq = [['mgmt', 1], ['blank', 1], ...Array(4).fill(['pwr', 1]), ...Array(10).fill(['comp', 1]), ...Array(9).fill(['nvsw', 1]), ...Array(8).fill(['comp', 1]), ...Array(4).fill(['pwr', 1])];
    let used = seq.reduce((a, s) => a + s[1], 0);
    const pad = Math.max(0, units - used); const top = Math.floor(pad / 2);
    for (let i = 0; i < top; i++) items.push(['blank', 1]);
    items.push(...seq); for (let i = 0; i < pad - top; i++) items.push(['blank', 1]);
    used = items.reduce((a, s) => a + s[1], 0); while (used > units) { items.pop(); used--; }
  } else {
    const r = rng(11); items.push(['tor', 1], ['tor', 1], ['patch', 1]);
    let u = 3; while (u < units) { const left = units - u; const k = r(); const it = left >= 2 && k < 0.45 ? ['srv2', 2] : k < 0.85 ? ['srv1', 1] : ['blank', 1]; items.push(it); u += it[1]; }
  }
  const draw = (g, emissive) => {
    g.fillStyle = emissive ? '#000' : '#07090c'; g.fillRect(0, 0, W, H);
    let y = 0; const r = rng(5);
    const ledDot = (x, yy, c, on = true) => { if (!on) return; g.fillStyle = c; g.beginPath(); g.arc(x, yy, 3.2, 0, Math.PI * 2); g.fill(); };
    for (const [kind, n] of items) {
      const h = n * uh, x0 = 14, w = W - 28, yc = y + h / 2;
      if (!emissive) {
        // rails + cage nuts
        g.fillStyle = '#20252c'; g.fillRect(0, y, 14, h); g.fillRect(W - 14, y, 14, h);
        g.fillStyle = '#5a626c'; g.fillRect(4, yc - 2, 6, 4); g.fillRect(W - 10, yc - 2, 6, 4);
      }
      if (kind === 'blank') { if (!emissive) { vgrad(g, x0, y + 1, w, h - 2, '#191d23', '#111418'); g.fillStyle = '#262b33'; g.fillRect(x0, y + 1, w, 2); } }
      else if (kind === 'comp') {          // 1U compute tray: honeycomb intake, E1.S bays, handles, LEDs
        if (!emissive) {
          vgrad(g, x0, y + 1, w, h - 2, '#2a3038', '#1b1f25');
          holes(g, x0 + 40, y + 6, 190, h - 12, 7, 2.4, '#07090b');
          for (let k = 0; k < 4; k++) { g.fillStyle = '#0d1014'; g.fillRect(x0 + 246 + k * 30, y + 6, 24, h - 12); g.fillStyle = '#6b737e'; g.fillRect(x0 + 246 + k * 30, y + h - 12, 24, 3); }
          g.fillStyle = '#9aa3ad'; g.fillRect(x0 + 4, y + 5, 22, h - 10); g.fillRect(x0 + w - 26, y + 5, 22, h - 10);
          g.fillStyle = '#76b900'; g.fillRect(x0 + 372, y + h / 2 - 1, 54, 2);
        }
        ledDot(x0 + 446, yc, '#2BB673'); ledDot(x0 + 458, yc, r() < 0.8 ? '#4C9DFF' : '#2BB673');
      } else if (kind === 'nvsw') {        // NVLink switch tray
        if (!emissive) {
          vgrad(g, x0, y + 1, w, h - 2, '#1d232a', '#14181d');
          for (let k = 0; k < 14; k++) { g.fillStyle = '#05070a'; g.fillRect(x0 + 34 + k * 24, y + 7, 18, h - 14); }
          g.fillStyle = '#9aa3ad'; g.fillRect(x0 + 4, y + 5, 18, h - 10); g.fillRect(x0 + w - 22, y + 5, 18, h - 10);
          g.fillStyle = '#76b900'; g.fillRect(x0 + 380, y + 6, 3, h - 12);
        }
        ledDot(x0 + 404, yc, '#2BB673'); ledDot(x0 + 418, yc, '#4C9DFF');
      } else if (kind === 'pwr') {         // power shelf: six PSUs
        if (!emissive) {
          g.fillStyle = '#15191e'; g.fillRect(x0, y + 1, w, h - 2);
          for (let k = 0; k < 6; k++) { const px = x0 + 6 + k * (w - 12) / 6; g.fillStyle = '#2b3139'; g.fillRect(px + 2, y + 4, (w - 12) / 6 - 4, h - 8); holes(g, px + 8, y + 7, (w - 12) / 6 - 30, h - 14, 6, 2, '#0a0c0f'); }
        }
        for (let k = 0; k < 6; k++) ledDot(x0 + 6 + (k + 1) * (w - 12) / 6 - 12, yc, '#2BB673');
      } else if (kind === 'mgmt' || kind === 'tor') {   // top-of-rack / management switch: port rows
        if (!emissive) {
          g.fillStyle = '#1e242b'; g.fillRect(x0, y + 1, w, h - 2);
          for (let k = 0; k < 24; k++) { g.fillStyle = '#05070a'; g.fillRect(x0 + 60 + k * 15, y + 6, 12, h / 2 - 8); g.fillRect(x0 + 60 + k * 15, y + h / 2 + 2, 12, h / 2 - 8); }
        }
        for (let k = 0; k < 24; k++) if (r() < 0.7) { g.fillStyle = r() < 0.8 ? '#2BB673' : '#F2C94C'; g.fillRect(x0 + 62 + k * 15, y + 4, 3, 2); }
        ledDot(x0 + 30, yc, '#2BB673');
      } else if (kind === 'patch') {
        if (!emissive) { g.fillStyle = '#121519'; g.fillRect(x0, y + 1, w, h - 2); for (let k = 0; k < 24; k++) { g.fillStyle = '#d6dbe2'; g.fillRect(x0 + 50 + k * 16, y + h / 2 - 6, 12, 12); } }
      } else if (kind === 'srv1' || kind === 'srv2') {   // 1U / 2U server: drive bays, intake mesh, ear handles
        if (!emissive) {
          vgrad(g, x0, y + 1, w, h - 2, '#3a414b', '#272c33');
          const bays = kind === 'srv2' ? 12 : 10, bw = kind === 'srv2' ? 24 : 26, rows = kind === 'srv2' ? 2 : 1, bh = (h - 12) / rows;
          for (let rw = 0; rw < rows; rw++) for (let k = 0; k < bays / rows * (kind === 'srv2' ? 1 : 1); k++) { const bx = x0 + 34 + k * (bw + 3); if (bx + bw > x0 + 360) break; g.fillStyle = '#15191e'; g.fillRect(bx, y + 6 + rw * bh, bw, bh - 3); g.fillStyle = '#626a75'; g.fillRect(bx + 2, y + 6 + rw * bh + bh - 9, bw - 4, 3); }
          holes(g, x0 + 370, y + 6, 90, h - 12, 7, 2.3, '#0b0d10');
          g.fillStyle = '#aab2bc'; g.fillRect(x0 + 2, y + 4, 16, h - 8); g.fillRect(x0 + w - 18, y + 4, 16, h - 8);
        }
        ledDot(x0 + 26, y + 9, '#2BB673'); ledDot(x0 + 26, y + 19, r() < 0.85 ? '#4C9DFF' : '#F2C94C');
        for (let k = 0; k < (kind === 'srv2' ? 6 : 5); k++) if (r() < 0.6) { g.fillStyle = '#2BB673'; g.fillRect(x0 + 38 + k * 54, y + 8, 3, 3); }
      }
      if (!emissive) { g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(x0, y + h - 1, w, 1); }
      y += h;
    }
  };
  const map = canvasTex(null, W, H, (g) => draw(g, false));
  const emissive = canvasTex(null, W, H, (g) => draw(g, true));
  const out = { map, emissive }; texCache.set(key, out); return out;
}

/** Perforated door: colour map + alpha map (open area ~65 %), frame and handle strip solid. */
export function perforatedDoor() {
  const key = 'perfdoor';
  if (texCache.has(key)) return texCache.get(key);
  const W = 512, H = 2048, fr = 26;
  const map = canvasTex(null, W, H, (g) => {
    vgrad(g, 0, 0, W, H, '#2a3039', '#1c2027');
    g.fillStyle = '#353c46'; g.fillRect(0, 0, W, fr); g.fillRect(0, H - fr, W, fr); g.fillRect(0, 0, fr, H); g.fillRect(W - fr, 0, fr, H);
    g.fillStyle = '#9ba4ae'; rr(g, W - fr - 30, H * 0.44, 18, 220, 8); g.fill();   // swing handle
    g.fillStyle = '#c4ccd6'; g.fillRect(W / 2 - 46, 40, 92, 16);
    label(g, 'BEN', W / 2, 48, 13, '#0b1a31', { weight: 800, align: 'center' });
  });
  const alpha = canvasTex(null, W, H, (g) => {
    g.fillStyle = '#fff'; g.fillRect(0, 0, W, H);
    holes(g, fr + 4, fr + 70, W - 2 * fr - 8 - 40, H - 2 * fr - 140, 9, 3.6, '#000');
    g.fillStyle = '#fff'; g.fillRect(W - fr - 44, H * 0.43, 44, 250);
  }, { srgb: false });
  const out = { map, alpha }; texCache.set(key, out); return out;
}

/** Rack rear: tray rear panels with fans and liquid quick-disconnect plates. */
export function rackRearTex(units, liquid) {
  return canvasTex(`rear|${units}|${liquid}`, 256, 1024, (g, W, H) => {
    g.fillStyle = '#0a0c0f'; g.fillRect(0, 0, W, H); const uh = H / units;
    for (let u = 0; u < units; u++) {
      const y = u * uh; g.fillStyle = u % 3 === 0 ? '#1a1e24' : '#14171c'; g.fillRect(8, y + 1, W - 16, uh - 2);
      if (!liquid) for (let k = 0; k < 4; k++) { g.strokeStyle = '#2b3139'; g.lineWidth = 1.5; g.beginPath(); g.arc(40 + k * 56, y + uh / 2, uh * 0.38, 0, Math.PI * 2); g.stroke(); }
      else { g.fillStyle = '#2b3139'; g.fillRect(70, y + 3, 110, uh - 6); g.fillStyle = '#05070a'; for (let k = 0; k < 8; k++) g.fillRect(76 + k * 13, y + 5, 9, uh - 10); }
    }
  });
}

// ----------------------------------------------------------------------------- cooling fronts
/** In-row CDU front (600 mm): perforated door, 7-inch HMI, nameplate. Returns { map, emissive }. */
export function cduFront() {
  const key = 'cdu';
  if (texCache.has(key)) return texCache.get(key);
  const W = 512, H = 1856;
  const body = (g, em) => {
    g.fillStyle = em ? '#000' : '#d3d9e1'; g.fillRect(0, 0, W, H);
    if (!em) {
      g.fillStyle = '#b9c1cb'; g.fillRect(0, 0, W, 6); g.fillRect(W / 2 - 2, 0, 4, H);
      g.fillStyle = '#c7ced7'; g.fillRect(30, 60, W - 60, 300);
      g.fillStyle = '#1d2229'; rr(g, 70, 110, 230, 150, 10); g.fill();
      g.fillStyle = '#0b1a31'; g.fillRect(330, 120, 120, 30); label(g, 'CDU', 390, 135, 20, '#eef4fc', { weight: 800, align: 'center' });
      label(g, '600 kW · W45', 390, 175, 16, '#3a4554', { align: 'center' });
      holes(g, 40, 400, W - 80, 1300, 12, 4.2, '#4c5562');
      g.fillStyle = '#7d8693'; rr(g, W / 2 + 20, 860, 16, 160, 6); g.fill(); rr(g, W / 2 - 36, 860, 16, 160, 6); g.fill();
      g.fillStyle = '#9aa3ae'; g.fillRect(0, H - 60, W, 60);
    }
    // HMI screen
    g.fillStyle = em ? '#0f2a52' : '#102544'; g.fillRect(80, 120, 210, 130);
    g.fillStyle = em ? '#4c9dff' : '#4c9dff'; g.fillRect(92, 132, 90, 6); g.fillStyle = '#5cd6ff'; g.fillRect(92, 150, 60, 30); g.fillStyle = '#ff8a3d'; g.fillRect(162, 150, 60, 30);
    g.fillStyle = '#2bb673'; g.fillRect(92, 196, 186, 4);
    label(g, '40.0°', 122, 166, 15, '#06101f', { weight: 700, align: 'center', font: MONO }); label(g, '50.1°', 192, 166, 15, '#06101f', { weight: 700, align: 'center', font: MONO });
    label(g, '904 L/min', 185, 228, 16, '#eef4fc', { weight: 600, align: 'center', font: MONO });
    g.fillStyle = '#2bb673'; g.beginPath(); g.arc(320, 236, 6, 0, Math.PI * 2); g.fill();
  };
  const out = { map: canvasTex(null, W, H, (g) => body(g, false)), emissive: canvasTex(null, W, H, (g) => body(g, true)) };
  texCache.set(key, out); return out;
}
/** In-row fan coil (300 mm): full-height perforated grille, small controller. */
export function fancoilFront() {
  return canvasTex('fancoil', 256, 1856, (g, W, H) => {
    g.fillStyle = '#d3d9e1'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#1d2229'; rr(g, 60, 50, 136, 70, 8); g.fill(); g.fillStyle = '#2bb673'; g.fillRect(74, 64, 40, 8); g.fillStyle = '#4c9dff'; g.fillRect(74, 82, 90, 6);
    holes(g, 22, 150, W - 44, H - 260, 11, 4, '#454e5a');
    for (let k = 0; k < 4; k++) { g.strokeStyle = 'rgba(40,46,54,0.55)'; g.lineWidth = 3; g.beginPath(); g.arc(W / 2, 330 + k * 420, 92, 0, Math.PI * 2); g.stroke(); }
    g.fillStyle = '#9aa3ae'; g.fillRect(0, H - 60, W, 60);
  });
}
/** Air in-row cooler front (Rev 1 / air tiers): grille with fan rings. */
export function inrowFront() {
  return canvasTex('inrow', 256, 1856, (g, W, H) => {
    g.fillStyle = '#d3d9e1'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#1d2229'; rr(g, 50, 40, 156, 80, 8); g.fill(); g.fillStyle = '#4c9dff'; g.fillRect(64, 56, 100, 8);
    slots(g, 24, 160, W - 48, H - 280, 60, '#4a5360');
    g.fillStyle = '#9aa3ae'; g.fillRect(0, H - 60, W, 60);
  });
}

// ----------------------------------------------------------------------------- power fronts
/** UPS frame front (Galaxy VL-class): two doors, louvre panels, colour display, status bar. { map, emissive } */
export function upsFront() {
  const key = 'ups';
  if (texCache.has(key)) return texCache.get(key);
  const W = 640, H = 1500;
  const draw = (g, em) => {
    g.fillStyle = em ? '#000' : '#e4e8ee'; g.fillRect(0, 0, W, H);
    if (!em) {
      g.fillStyle = '#c9d0d9'; g.fillRect(W / 2 - 2, 0, 4, H);
      g.fillStyle = '#2a3038'; g.fillRect(0, 0, W, 120);
      label(g, 'UPS  ·  424 kVA', 30, 60, 26, '#eef4fc', { weight: 700 });
      for (const x of [24, W / 2 + 24]) { slots(g, x, 170, W / 2 - 48, 420, 22, '#59626e'); slots(g, x, 860, W / 2 - 48, 560, 28, '#59626e'); }
      g.fillStyle = '#7d8693'; rr(g, W / 2 - 34, 640, 14, 150, 6); g.fill(); rr(g, W / 2 + 20, 640, 14, 150, 6); g.fill();
      g.fillStyle = '#1b2027'; rr(g, W / 2 + 60, 620, 240, 170, 10); g.fill();
      g.fillStyle = '#9aa3ae'; g.fillRect(0, H - 50, W, 50);
    }
    g.fillStyle = em ? '#123764' : '#14325a'; g.fillRect(W / 2 + 72, 632, 216, 130);
    g.fillStyle = '#2bb673'; g.fillRect(W / 2 + 86, 646, 70, 30); g.fillStyle = '#4c9dff'; g.fillRect(W / 2 + 166, 646, 106, 8); g.fillRect(W / 2 + 166, 662, 80, 8);
    label(g, 'ONLINE', W / 2 + 180, 720, 22, '#eef4fc', { weight: 700, align: 'center', font: MONO });
    g.fillStyle = '#2bb673'; g.fillRect(380, 92, 220, 8);
  };
  const out = { map: canvasTex(null, W, H, (g) => draw(g, false)), emissive: canvasTex(null, W, H, (g) => draw(g, true)) };
  texCache.set(key, out); return out;
}
/** Lithium battery cabinet: BMS display at the top, a row of module drawers with handles and SoC LEDs. */
export function batteryFront() {
  const key = 'batt';
  if (texCache.has(key)) return texCache.get(key);
  const W = 448, H = 1500, n = 14;
  const draw = (g, em) => {
    g.fillStyle = em ? '#000' : '#3a414c'; g.fillRect(0, 0, W, H);
    if (!em) {
      g.fillStyle = '#2b3139'; g.fillRect(0, 0, W, 150); g.fillStyle = '#1b2027'; rr(g, 40, 30, 200, 90, 8); g.fill();
      label(g, 'Li-ion', 330, 60, 24, '#eef4fc', { weight: 700, align: 'center' }); label(g, 'LFP · 16 kWh', 330, 96, 16, '#b2c1d8', { align: 'center' });
    }
    g.fillStyle = em ? '#0f2a52' : '#102544'; g.fillRect(50, 40, 180, 70); g.fillStyle = '#2bb673'; g.fillRect(62, 52, 130, 18); label(g, 'SoC 98%', 140, 92, 16, '#eef4fc', { weight: 600, align: 'center', font: MONO });
    const top = 180, mh = (H - top - 70) / n;
    for (let i = 0; i < n; i++) {
      const y = top + i * mh;
      if (!em) {
        vgrad(g, 18, y + 4, W - 36, mh - 8, '#59616d', '#454c57');
        g.fillStyle = '#21262d'; g.fillRect(18, y + mh - 6, W - 36, 3);
        g.fillStyle = '#c3cad3'; rr(g, W / 2 - 60, y + mh / 2 - 7, 120, 14, 6); g.fill();
        screw(g, 34, y + mh / 2, 4); screw(g, W - 34, y + mh / 2, 4);
        g.fillStyle = '#ccd3dc'; g.fillRect(60, y + 12, 80, 12);
      }
      for (let k = 0; k < 4; k++) { g.fillStyle = k < 3 ? '#2bb673' : (em ? '#000' : '#1b2027'); g.fillRect(W - 120 + k * 16, y + mh / 2 - 4, 10, 8); }
    }
    if (!em) { g.fillStyle = '#9aa3ae'; g.fillRect(0, H - 50, W, 50); }
  };
  const out = { map: canvasTex(null, W, H, (g) => draw(g, false)), emissive: canvasTex(null, W, H, (g) => draw(g, true)) };
  texCache.set(key, out); return out;
}
/** Switchboard section (915 mm): meter compartment, main / feeder breaker faces, nameplates, door seams. */
export function switchboardFront(section = 0) {
  return canvasTex(`swbd|${section}`, 512, 1280, (g, W, H) => {
    g.fillStyle = '#c9d0d9'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#9aa3ae'; g.fillRect(0, 0, 6, H); g.fillRect(W - 6, 0, 6, H);
    // meter compartment
    g.fillStyle = '#b4bcc6'; g.fillRect(20, 20, W - 40, 220); g.strokeStyle = '#7d8693'; g.lineWidth = 3; g.strokeRect(20, 20, W - 40, 220);
    g.fillStyle = '#1b2027'; rr(g, 60, 60, 170, 110, 8); g.fill(); g.fillStyle = '#14325a'; g.fillRect(72, 72, 146, 80);
    label(g, '480 V', 145, 100, 20, '#5cd6ff', { weight: 700, align: 'center', font: MONO }); label(g, '1,180 A', 145, 132, 18, '#eef4fc', { weight: 600, align: 'center', font: MONO });
    g.fillStyle = '#0b1a31'; g.fillRect(270, 70, 190, 40); label(g, section === 0 ? 'MAIN SWBD' : `SWBD ${section + 1}`, 365, 90, 20, '#eef4fc', { weight: 700, align: 'center' });
    g.fillStyle = '#f2c94c'; g.beginPath(); g.moveTo(365, 128); g.lineTo(395, 180); g.lineTo(335, 180); g.closePath(); g.fill(); label(g, '!', 365, 162, 30, '#06101f', { weight: 900, align: 'center' });
    // breakers
    const brk = (x, y, w, h, big) => {
      g.fillStyle = '#2a3038'; rr(g, x, y, w, h, 6); g.fill(); g.fillStyle = '#3d444e'; g.fillRect(x + 10, y + 10, w - 20, h - 20);
      g.fillStyle = '#e4e8ee'; g.fillRect(x + w / 2 - (big ? 20 : 10), y + h * 0.35, big ? 40 : 20, h * 0.3);
      g.fillStyle = '#c8102e'; g.fillRect(x + w / 2 - (big ? 14 : 7), y + h * 0.36, big ? 28 : 14, big ? 14 : 8);
      if (big) { g.fillStyle = '#1b2027'; g.fillRect(x + 20, y + 20, 90, 60); g.fillStyle = '#2bb673'; g.fillRect(x + 28, y + 28, 30, 8); }
      g.fillStyle = '#f4f7fb'; g.fillRect(x + 8, y + h - 26, w - 16, 18);
    };
    if (section === 0) { brk(60, 290, W - 120, 420, true); label(g, 'MAIN 1200 AF', W / 2, 700, 14, '#06101f', { weight: 700, align: 'center' }); for (let k = 0; k < 2; k++) brk(60 + k * 200, 780, 190, 220, false); }
    else for (let r2 = 0; r2 < 3; r2++) for (let k = 0; k < 2; k++) brk(40 + k * 220, 280 + r2 * 250, 210, 230, false);
    g.fillStyle = '#7d8693'; g.fillRect(W - 40, 560, 10, 140);
    g.fillStyle = '#9aa3ae'; g.fillRect(0, H - 40, W, 40);
  });
}
/** Wall panelboard / ATS: dead-front with breaker columns. */
export function panelboardFront(kind = 'panel') {
  return canvasTex(`pnl|${kind}`, 256, 640, (g, W, H) => {
    g.fillStyle = '#c3cad3'; g.fillRect(0, 0, W, H); g.strokeStyle = '#7d8693'; g.lineWidth = 4; g.strokeRect(6, 6, W - 12, H - 12);
    if (kind === 'ats') {
      g.fillStyle = '#1b2027'; rr(g, 40, 50, W - 80, 120, 8); g.fill(); g.fillStyle = '#2bb673'; g.fillRect(56, 70, 50, 14); g.fillStyle = '#f2c94c'; g.fillRect(120, 70, 50, 14);
      label(g, 'ATS', W / 2, 140, 26, '#eef4fc', { weight: 800, align: 'center' });
      g.fillStyle = '#2a3038'; g.fillRect(70, 240, W - 140, 260); g.fillStyle = '#e4e8ee'; g.fillRect(W / 2 - 18, 330, 36, 80);
    } else {
      g.fillStyle = '#2a3038'; g.fillRect(40, 60, W - 80, H - 140);
      for (let r2 = 0; r2 < 14; r2++) for (let k = 0; k < 2; k++) { g.fillStyle = '#4a525c'; g.fillRect(52 + k * ((W - 104) / 2 + 4), 72 + r2 * 32, (W - 104) / 2 - 4, 26); g.fillStyle = '#e4e8ee'; g.fillRect(52 + k * ((W - 104) / 2 + 4) + 40, 80 + r2 * 32, 22, 10); }
      g.fillStyle = '#f4f7fb'; g.fillRect(60, H - 60, W - 120, 26); label(g, 'PANEL LP-1', W / 2, H - 47, 14, '#06101f', { weight: 700, align: 'center' });
    }
  });
}
/** Generic louvre panel (chillers, switchgear, generator enclosures). */
export function louvreTex(base = '#c9d0d9', slot = '#59626e') {
  return canvasTex(`louvre|${base}|${slot}`, 256, 256, (g, W, H) => {
    g.fillStyle = base; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 16; i++) { vgrad(g, 10, 8 + i * 15, W - 20, 10, slot, base); }
  }, { repeat: [1, 1] });
}
/** Dry-cooler coil face: fins + tube rows. */
export function coilTex() {
  return canvasTex('coil', 512, 256, (g, W, H) => {
    g.fillStyle = '#9da6b0'; g.fillRect(0, 0, W, H);
    for (let x = 0; x < W; x += 3) { g.fillStyle = x % 6 ? '#b8c0c9' : '#7e8792'; g.fillRect(x, 0, 1, H); }
    for (let r2 = 0; r2 < 6; r2++) for (let x = 12; x < W; x += 24) { g.fillStyle = '#b87333'; g.beginPath(); g.arc(x + (r2 % 2) * 12, 20 + r2 * 42, 4, 0, Math.PI * 2); g.fill(); }
  }, { repeat: [4, 1] });
}
/** Pad-mount transformer front: two compartment doors with hasps, nameplate, warning labels. */
export function transformerFront() {
  return canvasTex('xfmr', 512, 512, (g, W, H) => {
    g.fillStyle = '#56715a'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#4a6250'; g.fillRect(W / 2 - 3, 20, 6, H - 40);
    g.strokeStyle = '#3e5444'; g.lineWidth = 4; g.strokeRect(14, 14, W / 2 - 20, H - 28); g.strokeRect(W / 2 + 6, 14, W / 2 - 20, H - 28);
    for (const x of [W / 2 - 40, W / 2 + 24]) { g.fillStyle = '#8f9a92'; g.fillRect(x, 230, 16, 60); }
    g.fillStyle = '#f2c94c'; g.fillRect(60, 60, 150, 90); g.fillStyle = '#06101f'; label(g, 'DANGER', 135, 85, 22, '#c8102e', { weight: 900, align: 'center' }); label(g, 'HIGH VOLTAGE', 135, 120, 16, '#06101f', { weight: 800, align: 'center' });
    g.fillStyle = '#e4e8ee'; g.fillRect(300, 70, 150, 60); label(g, '2500 kVA', 375, 100, 18, '#06101f', { weight: 700, align: 'center', font: MONO });
  });
}
/** Medium-voltage switchgear front: four ways, viewing windows, mimic bus. */
export function mvSwitchgearFront() {
  return canvasTex('mvsg', 1024, 512, (g, W, H) => {
    g.fillStyle = '#c3cad3'; g.fillRect(0, 0, W, H);
    for (let k = 0; k < 4; k++) {
      const x = k * W / 4; g.strokeStyle = '#7d8693'; g.lineWidth = 5; g.strokeRect(x + 8, 10, W / 4 - 16, H - 20);
      g.fillStyle = '#1b2027'; g.fillRect(x + 50, 60, W / 4 - 100, 70); g.fillStyle = '#2bb673'; g.fillRect(x + 60, 70, 30, 12);
      g.fillStyle = '#c8102e'; g.fillRect(x + W / 8 - 3, 160, 6, 160); g.fillRect(x + W / 8 - 40, 236, 80, 6);
      g.fillStyle = '#7d8693'; g.fillRect(x + W / 4 - 40, 260, 12, 80);
      g.fillStyle = '#f2c94c'; g.fillRect(x + 40, H - 100, 100, 50);
    }
  });
}

// ----------------------------------------------------------------------------- surfaces
export function floorTex(repeat) {   // dark anti-static vinyl tile with a fine speckle
  return canvasTex(`floor|${repeat}`, 512, 512, (g, W, H) => {
    g.fillStyle = '#3a414b'; g.fillRect(0, 0, W, H); const r = rng(3);
    for (let i = 0; i < 9000; i++) { g.fillStyle = r() < 0.5 ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.08)'; g.fillRect(r() * W, r() * H, 2, 2); }
    g.strokeStyle = 'rgba(15,18,22,0.6)'; g.lineWidth = 2; for (let k = 0; k <= 2; k++) { g.beginPath(); g.moveTo(k * W / 2, 0); g.lineTo(k * W / 2, H); g.stroke(); g.beginPath(); g.moveTo(0, k * H / 2); g.lineTo(W, k * H / 2); g.stroke(); }
  }, { repeat });
}
export function linerTex(repeat) {   // white steel liner panels with seams and rivets
  return canvasTex(`liner|${repeat}`, 512, 512, (g, W, H) => {
    vgrad(g, 0, 0, W, H, '#dfe4ea', '#d2d8df');
    g.fillStyle = '#aab3bd'; g.fillRect(0, 0, 3, H); g.fillRect(W - 2, 0, 2, H);
    for (let y = 30; y < H; y += 120) { g.fillStyle = '#b9c1ca'; g.beginPath(); g.arc(12, y, 3, 0, Math.PI * 2); g.fill(); }
  }, { repeat });
}
export function concreteTex(repeat) {
  return canvasTex(`concrete|${repeat}`, 512, 512, (g, W, H) => {
    g.fillStyle = '#8b9096'; g.fillRect(0, 0, W, H); const r = rng(9);
    for (let i = 0; i < 14000; i++) { const v = 110 + Math.floor(r() * 50); g.fillStyle = `rgba(${v},${v + 3},${v + 6},0.35)`; g.fillRect(r() * W, r() * H, 2 + r() * 2, 2 + r() * 2); }
    g.strokeStyle = 'rgba(40,44,50,0.5)'; g.lineWidth = 2; g.strokeRect(0, 0, W, H);
  }, { repeat });
}
export function gravelTex(repeat) {
  return canvasTex(`gravel|${repeat}`, 512, 512, (g, W, H) => {
    g.fillStyle = '#5b5f63'; g.fillRect(0, 0, W, H); const r = rng(21);
    for (let i = 0; i < 6000; i++) { const v = 70 + Math.floor(r() * 90); g.fillStyle = `rgb(${v},${v - 2},${v - 6})`; g.beginPath(); g.arc(r() * W, r() * H, 1.5 + r() * 2.6, 0, Math.PI * 2); g.fill(); }
  }, { repeat });
}
export function insulationTex() {   // cut face of the sandwich wall: steel skins + PIR core, hatched
  return canvasTex('insul', 128, 128, (g, W, H) => {
    g.fillStyle = '#e9d9a6'; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(160,130,60,0.6)'; g.lineWidth = 2; for (let k = -W; k < W * 2; k += 14) { g.beginPath(); g.moveTo(k, 0); g.lineTo(k + H, H); g.stroke(); }
  }, { repeat: [8, 1] });
}

// ----------------------------------------------------------------------------- labels (zone tags in cutaway)
export function zoneLabel(title, sub, color = '#4C9DFF') {
  const meas = document.createElement('canvas').getContext('2d');
  meas.font = `700 40px ${FONT}`; const tw = meas.measureText(title).width; meas.font = `500 28px ${FONT}`; const sw = meas.measureText(sub).width;
  const W = Math.ceil(Math.max(tw, sw) + 84), H = 172;
  const tex = canvasTex(`zone|${title}|${sub}|${color}`, W, H, (g) => {
    g.clearRect(0, 0, W, H);
    g.fillStyle = 'rgba(6,16,31,0.9)'; rr(g, 4, 4, W - 8, H - 46, 14); g.fill();
    g.strokeStyle = color; g.lineWidth = 3; rr(g, 4, 4, W - 8, H - 46, 14); g.stroke();
    g.fillStyle = color; g.fillRect(22, 24, 8, H - 94);
    label(g, title, 46, 46, 40, '#eef4fc', { weight: 700 });
    label(g, sub, 46, 94, 28, '#b2c1d8', { weight: 500 });
    g.fillStyle = color; g.beginPath(); g.moveTo(W / 2 - 14, H - 43); g.lineTo(W / 2 + 14, H - 43); g.lineTo(W / 2, H - 14); g.closePath(); g.fill();
  });
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, depthWrite: false, sizeAttenuation: false, transparent: true }));
  const k = 0.00042; sp.center.set(0.5, 0.0); sp.scale.set(W * k, H * k, 1); sp.renderOrder = 20;
  return sp;
}

// ----------------------------------------------------------------------------- models
/** Fan guard + blades on a horizontal deck (dry cooler, condenser, chiller). Returns the spinning blade group. */
export function fanGuard(parts, parent, x, y, z, r) {
  for (const k of [1, 0.72, 0.44]) parts.ring(r * k, 0.008, EM.darkSteel, x, y + 0.03, z, 'y', 36);
  parts.ring(r + 0.02, 0.025, EM.equipMid, x, y, z, 'y', 36);
  for (let s = 0; s < 8; s++) { const a = s / 8 * Math.PI; parts.box(2 * r, 0.008, 0.012, EM.darkSteel, x, y + 0.03, z, 0, a, 0); }
  const blades = new THREE.Group(); blades.position.set(x, y - 0.04, z);
  const blade = new THREE.BoxGeometry(r * 0.85, 0.012, r * 0.28);
  for (let b = 0; b < 5; b++) { const piv = new THREE.Group(); piv.rotation.y = b / 5 * Math.PI * 2; const m = new THREE.Mesh(blade, EM.fanBlade); m.position.x = r * 0.45; m.rotation.x = 0.35; piv.add(m); blades.add(piv); }
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.14, r * 0.14, 0.06, 16), EM.black); blades.add(hub);
  parent.add(blades); return blades;
}

/** A rack: W x H x D, front at -z. Body is the pickable / solid; returns { group, body, front, frontMat, led }. */
export function rackModel({ W, H, D, U, profile = 'std', liquid = false, rearDoor = true }) {
  const group = new THREE.Group();
  const base = 0.09;   // casters + levelling feet under the frame
  const body = new THREE.Mesh(new THREE.BoxGeometry(W, H - base, D), EM.rackSteel); body.position.y = base + (H - base) / 2; body.castShadow = body.receiveShadow = true; group.add(body);
  const { map, emissive } = rackFrontTextures(U, profile);
  const frontMat = new THREE.MeshStandardMaterial({ map, emissiveMap: emissive, emissive: 0xffffff, emissiveIntensity: 1.0, roughness: 0.55, metalness: 0.4 });
  const fh = H - base - 0.12;
  const front = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.07, fh), frontMat); front.position.set(0, base + 0.06 + fh / 2, -D / 2 - 0.004); front.rotation.y = Math.PI; group.add(front);
  // perforated front door (alpha holes show the trays behind)
  const pd = perforatedDoor();
  const door = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.01, H - base - 0.02), new THREE.MeshStandardMaterial({ map: pd.map, alphaMap: pd.alpha, alphaToCoverage: true, alphaTest: 0.02, roughness: 0.45, metalness: 0.5, side: THREE.DoubleSide }));
  door.position.set(0, base + (H - base) / 2, -D / 2 - 0.022); door.rotation.y = Math.PI; door.castShadow = false; group.add(door);
  const P = new Parts();
  // door hinges + frame lip, casters, levelling feet, top cable entry brushes, side panel seam
  for (const yy of [0.35, 1.0, H - 0.35]) P.box(0.012, 0.06, 0.02, EM.steel, W / 2 - 0.005, yy, -D / 2 - 0.016);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    P.cyl(0.032, 0.026, EM.rubber, sx * (W / 2 - 0.07), 0.034, sz * (D / 2 - 0.09), 'x', 14);
    P.box(0.05, 0.02, 0.06, EM.steel, sx * (W / 2 - 0.07), 0.065, sz * (D / 2 - 0.09));
    P.cyl(0.022, 0.008, EM.darkSteel, sx * (W / 2 - 0.03), 0.004, sz * (D / 2 - 0.04), 'y', 12);
    P.cyl(0.006, 0.08, EM.steel, sx * (W / 2 - 0.03), 0.045, sz * (D / 2 - 0.04), 'y', 6);
  }
  P.box(W, 0.02, 0.02, EM.rackFrame, 0, base + 0.01, -D / 2 - 0.01);
  for (const sx of [-1, 1]) P.box(0.004, H - base - 0.2, 0.003, EM.rackFrame, sx * (W / 2 + 0.001), base + (H - base) / 2, 0);
  P.box(W * 0.6, 0.012, 0.12, EM.black, 0, H + 0.006, D * 0.25); P.box(W * 0.6, 0.012, 0.12, EM.black, 0, H + 0.006, -D * 0.2);
  // rear
  const rearMat = new THREE.MeshStandardMaterial({ map: rackRearTex(U, liquid), roughness: 0.7, metalness: 0.3 });
  const rear = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.07, fh), rearMat); rear.position.set(0, base + 0.06 + fh / 2, D / 2 + 0.004); group.add(rear);
  if (liquid) {
    // vertical rack manifolds (supply left, return right from the rear) with a UQD hose pair to every tray
    const zr = D / 2 + 0.05, x1 = -W / 2 + 0.075, x2 = W / 2 - 0.075, y0 = base + 0.15, y1 = H - 0.05;
    P.cyl(0.024, y1 - y0, EM.pipeSupply, x1, (y0 + y1) / 2, zr, 'y', 14); P.cyl(0.024, y1 - y0, EM.pipeReturn, x2, (y0 + y1) / 2, zr, 'y', 14);
    for (const [x, m] of [[x1, EM.pipeSupply], [x2, EM.pipeReturn]]) { P.cyl(0.03, 0.04, EM.steel, x, y1 + 0.01, zr, 'y', 14); P.box(0.07, 0.03, 0.07, EM.darkSteel, x, y0 - 0.02, zr); void m; }
    const trays = Math.min(27, Math.max(8, Math.round(U * 0.6)));
    for (let k = 0; k < trays; k++) {
      const yy = y0 + 0.06 + k * (y1 - y0 - 0.12) / (trays - 1);
      for (const [x, dir] of [[x1, 1], [x2, -1]]) {
        P.cyl(0.0085, 0.11, EM.hose, x + dir * 0.06, yy, zr - 0.012, 'x', 6);
        P.cyl(0.013, 0.03, EM.steel, x + dir * 0.125, yy, zr - 0.02, 'x', 8);   // quick disconnect
        P.cyl(0.011, 0.026, x === x1 ? EM.pipeSupply : EM.pipeReturn, x + dir * 0.02, yy, zr, 'x', 6);   // colour-coded port
      }
    }
  } else if (rearDoor) {
    const door2 = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.01, H - base - 0.02), new THREE.MeshStandardMaterial({ map: pd.map, alphaMap: pd.alpha, alphaToCoverage: true, alphaTest: 0.02, roughness: 0.45, metalness: 0.5, side: THREE.DoubleSide }));
    door2.position.set(0, base + (H - base) / 2, D / 2 + 0.02); group.add(door2);
  }
  P.build(group);
  const ledM = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.018, 0.006), led(0x2bb673)); ledM.position.set(0, H - 0.05, -D / 2 - 0.03); group.add(ledM);
  return { group, body, front, frontMat, led: ledM };
}

/** Small-business IT bezels (BEN 1): UPS, battery pack, switch, NAS, GPU server, mini AI box, edge box, patch panel, PDU. */
export function bezelTex(kind, nU = 1, wide = true) {
  return canvasTex(`bezel|${kind}|${nU}|${wide}`, wide ? 1024 : 512, 96 * nU, (g, W, H) => {
    const ear = wide ? 40 : 0;
    g.fillStyle = '#1a1e24'; g.fillRect(0, 0, W, H);
    if (ear) { g.fillStyle = '#8f98a3'; g.fillRect(0, 0, ear, H); g.fillRect(W - ear, 0, ear, H); for (const x of [ear / 2, W - ear / 2]) { screw(g, x, H * 0.3, 6); screw(g, x, H * 0.7, 6); } }
    const x0 = ear + 10, x1 = W - ear - 10;
    const dot = (x, y, c) => { g.fillStyle = c; g.beginPath(); g.arc(x, y, 6, 0, Math.PI * 2); g.fill(); };
    if (kind === 'ups' || kind === 'battery') {
      vgrad(g, x0, 4, x1 - x0, H - 8, '#2a3038', '#1b1f25'); holes(g, x0 + 20, 12, (x1 - x0) * 0.55, H - 24, 14, 4.5, '#0b0d10');
      if (kind === 'ups') { g.fillStyle = '#0f2a52'; g.fillRect(x1 - 300, H / 2 - 34, 170, 68); label(g, '1500VA', x1 - 215, H / 2, 26, '#5cd6ff', { weight: 700, align: 'center', font: MONO }); dot(x1 - 90, H / 2, '#2bb673'); dot(x1 - 60, H / 2, '#f2c94c'); }
      else { label(g, 'Li-ion EBM', x1 - 200, H / 2, 28, '#b2c1d8', { weight: 600, align: 'center' }); dot(x1 - 50, H / 2, '#2bb673'); }
    } else if (kind === 'switch') {
      g.fillStyle = '#20262d'; g.fillRect(x0, 4, x1 - x0, H - 8);
      const n = wide ? 24 : 8; for (let k = 0; k < n; k++) for (let r = 0; r < 2; r++) { const px = x0 + 80 + k * ((x1 - x0 - 200) / n); g.fillStyle = '#05070a'; g.fillRect(px, 10 + r * (H / 2 - 4), (x1 - x0 - 200) / n - 6, H / 2 - 16); g.fillStyle = '#2bb673'; g.fillRect(px + 2, 8 + r * (H / 2 - 4), 6, 3); }
      for (let k = 0; k < 4; k++) { g.fillStyle = '#05070a'; g.fillRect(x1 - 110 + (k % 2) * 50, 12 + Math.floor(k / 2) * (H / 2 - 4), 40, H / 2 - 18); }
    } else if (kind === 'nas') {
      g.fillStyle = '#23292f'; g.fillRect(x0, 4, x1 - x0, H - 8);
      for (let k = 0; k < 4; k++) { const bx = x0 + 30 + k * (x1 - x0 - 120) / 4; g.fillStyle = '#121519'; g.fillRect(bx, 10, (x1 - x0 - 120) / 4 - 12, H - 20); g.fillStyle = '#7d8693'; g.fillRect(bx + 10, H - 22, (x1 - x0 - 120) / 4 - 32, 6); dot(bx + 20, 22, '#2bb673'); }
      dot(x1 - 40, H / 2, '#4c9dff');
    } else if (kind === 'ai_box' || kind === 'gpu') {
      vgrad(g, x0, 4, x1 - x0, H - 8, '#3a414b', '#272c33'); holes(g, x0 + 20, 10, (x1 - x0) * 0.62, H - 20, 12, 4.4, '#0b0d10');
      g.fillStyle = '#76b900'; g.fillRect(x1 - 210, H / 2 - 3, 110, 6); dot(x1 - 60, H / 2 - 12, '#2bb673'); dot(x1 - 60, H / 2 + 14, '#4c9dff');
    } else if (kind === 'edge') {
      g.fillStyle = '#20262d'; g.fillRect(x0, 4, x1 - x0, H - 8); for (let k = 0; k < 18; k++) { g.fillStyle = '#2d343c'; g.fillRect(x0 + 20 + k * 22, 10, 12, H - 20); }
      label(g, 'BEN Controls', x1 - 170, H / 2, 24, '#b2c1d8', { weight: 600, align: 'center' }); dot(x1 - 40, H / 2, '#2bb673');
    } else if (kind === 'patch') {
      g.fillStyle = '#121519'; g.fillRect(x0, 4, x1 - x0, H - 8); const n = wide ? 24 : 12; for (let k = 0; k < n; k++) { g.fillStyle = '#e4e8ee'; g.fillRect(x0 + 40 + k * (x1 - x0 - 80) / n, H / 2 - 16, (x1 - x0 - 80) / n - 10, 32); }
    } else if (kind === 'pdu') {
      g.fillStyle = '#20262d'; g.fillRect(x0, 4, x1 - x0, H - 8); for (let k = 0; k < 6; k++) { g.fillStyle = '#0b0d10'; rr(g, x0 + 30 + k * 60, 16, 44, H - 32, 6); g.fill(); } dot(x1 - 30, H / 2, '#2bb673');
    }
  });
}
