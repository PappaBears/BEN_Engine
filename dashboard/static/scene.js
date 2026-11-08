// BEN Engine 3D digital twin scene (three.js, vendored, no CDN).
// Built procedurally from the configuration + /api/sensors; animated from live twin state.
import * as THREE from './vendor/three/three.module.js';
import { OrbitControls } from './vendor/three/OrbitControls.js';
import { PointerLockControls } from './vendor/three/PointerLockControls.js';
import { tempColor, lerpColor, reducedMotion } from './util.js';

const C = { graphite: 0x0b1018, slate: 0x152234, panel: 0x1b2b42, text: 0xedf4ff, muted: 0x9fb3cc, cyan: 0x66e3ff, amber: 0xffc66d, red: 0xff707d, green: 0x6ee7a8 };
const U_M = 0.04445;

// ----------------------------------------------------------------------------- materials
const MAT = {
  shell: (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.35 }),
  liner: new THREE.MeshStandardMaterial({ color: 0x97a2b3, roughness: 0.95, metalness: 0.0, side: THREE.BackSide }),
  floor: new THREE.MeshStandardMaterial({ color: 0x2a3341, roughness: 0.85, metalness: 0.1 }),
  rack: new THREE.MeshStandardMaterial({ color: 0x1a2230, roughness: 0.6, metalness: 0.5 }),
  rackRear: new THREE.MeshStandardMaterial({ color: 0x0f1620, roughness: 0.8, metalness: 0.3 }),
  cooling: new THREE.MeshStandardMaterial({ color: 0xc9d2de, roughness: 0.5, metalness: 0.5 }),
  coolingDark: new THREE.MeshStandardMaterial({ color: 0x5b6878, roughness: 0.6, metalness: 0.5 }),
  power: new THREE.MeshStandardMaterial({ color: 0xaab4c2, roughness: 0.55, metalness: 0.45 }),
  powerDark: new THREE.MeshStandardMaterial({ color: 0x3b4656, roughness: 0.6, metalness: 0.5 }),
  battery: new THREE.MeshStandardMaterial({ color: 0x33415a, roughness: 0.6, metalness: 0.5 }),
  gateway: new THREE.MeshStandardMaterial({ color: 0x1b2b42, roughness: 0.5, metalness: 0.6 }),
  tray: new THREE.MeshStandardMaterial({ color: 0xb9c3d1, roughness: 0.4, metalness: 0.7 }),
  glass: new THREE.MeshPhysicalMaterial({ color: 0xbfe9ff, transmission: 0.0, opacity: 0.22, transparent: true, roughness: 0.1, metalness: 0.0, side: THREE.DoubleSide, depthWrite: false }),
  casting: new THREE.MeshStandardMaterial({ color: 0x2a3340, roughness: 0.7, metalness: 0.6 }),
  ground: new THREE.MeshStandardMaterial({ color: 0x0e1520, roughness: 1 }),
  pad: new THREE.MeshStandardMaterial({ color: 0x3a4250, roughness: 0.95 }),
  pipeCold: new THREE.MeshStandardMaterial({ color: 0x3fc0e0, roughness: 0.4, metalness: 0.6 }),
  pipeHot: new THREE.MeshStandardMaterial({ color: 0xe0a44a, roughness: 0.4, metalness: 0.6 }),
  fan: new THREE.MeshStandardMaterial({ color: 0x222a36, roughness: 0.5, metalness: 0.6 }),
  led: (color) => new THREE.MeshBasicMaterial({ color }),
};

function box(w, h, d, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true;
  return m;
}
function edges(obj, color = 0x000000, opacity = 0.25) {
  const g = new THREE.EdgesGeometry(obj.geometry);
  const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color, transparent: true, opacity }));
  obj.add(l); return l;
}

/** Corrugated wall: plane facing +z with a trapezoid profile along x. */
function corrugatedWall(len, height, color, period = 0.25, depth = 0.028) {
  const segs = Math.max(8, Math.round(len / period) * 4);
  const g = new THREE.PlaneGeometry(len, height, segs, 1);
  const pos = g.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i) + len / 2;
    const ph = (x % period) / period;
    const prof = ph < 0.25 ? ph / 0.25 : ph < 0.5 ? 1 : ph < 0.75 ? 1 - (ph - 0.5) / 0.25 : 0;
    pos.setZ(i, prof * depth);
  }
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, MAT.shell(color));
  m.castShadow = true; m.receiveShadow = true;
  return m;
}

/** Canvas texture of the brand mark + tier for the container side. */
function brandTexture(brand, tier, whiteLabel) {
  const cv = document.createElement('canvas'); cv.width = 2048; cv.height = 640;
  const g = cv.getContext('2d');
  g.clearRect(0, 0, cv.width, cv.height);
  // monogram (same paths as web/kit/logo-sai.svg) unless white-label
  let x0 = 90;
  if (!whiteLabel) {
    g.save(); g.translate(90, 110); g.scale(3.4, 3.4);
    g.fillStyle = '#0B1018'; roundRect(g, 0, 0, 120, 120, 24); g.fill();
    g.lineCap = 'round'; g.lineWidth = 6;
    g.strokeStyle = '#66E3FF'; g.stroke(new Path2D('M30 78c0 9 8 14 19 14 12 0 19-6 19-14 0-9-7-12-18-15-9-2-12-4-12-8 0-5 5-8 11-8 7 0 11 3 12 8'));
    g.strokeStyle = '#EDF4FF'; g.stroke(new Path2D('M78 92V40h8v52zM60 28h26'));
    g.fillStyle = '#FFC66D'; g.beginPath(); g.arc(98, 28, 5, 0, Math.PI * 2); g.fill();
    g.restore();
    x0 = 560;
  }
  g.fillStyle = '#EDF4FF'; g.font = '800 190px Inter, "Segoe UI", system-ui, sans-serif'; g.textBaseline = 'alphabetic';
  g.fillText(brand.toUpperCase(), x0, 300);
  g.fillStyle = '#66E3FF'; g.font = '300 120px Inter, "Segoe UI", system-ui, sans-serif';
  g.fillText(tier, x0 + 6, 440);
  g.fillStyle = '#9FB3CC'; g.font = '500 44px Inter, "Segoe UI", system-ui, sans-serif';
  g.fillText('BUSINESS EDGE NODE', x0 + 10, 520);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}
function roundRect(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }

/** Server-front texture: 1U slots with LEDs; used as map + emissiveMap. */
function serverFrontTexture(units) {
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = 2048;
  const g = cv.getContext('2d');
  g.scale(2, 4); g.fillStyle = '#0a0f16'; g.fillRect(0, 0, 128, 512);
  const uh = 512 / units;
  let u = 0; let seed = 7;
  const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  while (u < units) {
    const size = u % 7 === 0 ? 2 : (rnd() < 0.25 ? 2 : 1);
    const y = u * uh, hgt = size * uh;
    g.fillStyle = rnd() < 0.08 ? '#0a0f16' : '#2a3443'; g.fillRect(6, y + 1, 116, hgt - 2);
    g.fillStyle = '#151c26'; g.fillRect(10, y + 3, 70, hgt - 6);
    const leds = 2 + Math.floor(rnd() * 3);
    for (let k = 0; k < leds; k++) { g.fillStyle = k === 0 ? '#6EE7A8' : (rnd() < 0.7 ? '#66E3FF' : '#FFC66D'); g.fillRect(88 + k * 9, y + hgt / 2 - 2, 4, 4); }
    u += size;
  }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.minFilter = THREE.LinearMipmapLinearFilter;
  return t;
}

// ----------------------------------------------------------------------------- flow lines (power)
class Flow {
  constructor(points, { n = 14, color = C.green, size = 0.09 } = {}) {
    this.pts = points; this.n = n;
    this.len = [0]; for (let i = 1; i < points.length; i++) this.len.push(this.len[i - 1] + points[i].distanceTo(points[i - 1]));
    this.total = this.len[this.len.length - 1];
    this.s = new Float32Array(n).map((_, i) => i / n * this.total);
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    this.points = new THREE.Points(geo, new THREE.PointsMaterial({ color, size, sizeAttenuation: true, transparent: true, opacity: 0.95, depthWrite: false }));
    this.line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.25 }));
    this.group = new THREE.Group(); this.group.add(this.line, this.points);
    this.speed = 0.6; this.active = true; this.place();
  }
  setColor(c) { this.points.material.color.setHex(c); this.line.material.color.setHex(c); }
  at(s, out) {
    s = ((s % this.total) + this.total) % this.total;
    let i = 1; while (i < this.len.length - 1 && this.len[i] < s) i++;
    const a = this.pts[i - 1], b = this.pts[i], t = (s - this.len[i - 1]) / Math.max(1e-6, this.len[i] - this.len[i - 1]);
    return out.lerpVectors(a, b, t);
  }
  place() {
    const p = this.points.geometry.attributes.position, v = new THREE.Vector3();
    for (let i = 0; i < this.n; i++) { this.at(this.s[i], v); p.setXYZ(i, v.x, v.y, v.z); }
    p.needsUpdate = true;
  }
  update(dt) {
    if (!this.active) return;
    for (let i = 0; i < this.n; i++) this.s[i] += this.speed * dt;
    this.place();
  }
}

// ----------------------------------------------------------------------------- scene factory
export function createScene(canvas, { onSelect, caption, walkHint } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.2;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x0b1018, 0.012);
  const camera = new THREE.PerspectiveCamera(50, 1, 0.05, 400);
  camera.position.set(8, 5, 10);
  const orbit = new OrbitControls(camera, canvas);
  orbit.enableDamping = true; orbit.dampingFactor = 0.08; orbit.maxPolarAngle = Math.PI * 0.495; orbit.minDistance = 0.5; orbit.maxDistance = 80;
  const walk = new PointerLockControls(camera, canvas);

  // lights
  scene.add(new THREE.HemisphereLight(0xcfe0ff, 0x1a2230, 0.8));
  const sun = new THREE.DirectionalLight(0xfff1dd, 2.2);
  sun.position.set(12, 16, 8); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -16; sun.shadow.camera.right = 16; sun.shadow.camera.top = 16; sun.shadow.camera.bottom = -16; sun.shadow.bias = -0.0005;
  scene.add(sun);
  const fill = new THREE.DirectionalLight(0x9fd8ff, 0.35); fill.position.set(-10, 6, -8); scene.add(fill);
  const back = new THREE.DirectionalLight(0xffffff, 0.25); back.position.set(6, 5, -12); scene.add(back);
  const interiorLights = new THREE.Group(); scene.add(interiorLights);

  // ground
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), MAT.ground); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const grid = new THREE.GridHelper(120, 120, 0x1b2b42, 0x152234); grid.position.y = 0.002; scene.add(grid);

  // model state
  const G = {}; // geometry numbers for the current config
  let payload = null, state = null;
  const groups = { shell: new THREE.Group(), compute: new THREE.Group(), cooling: new THREE.Group(), power: new THREE.Group(), controls: new THREE.Group(), fx: new THREE.Group(), hl: new THREE.Group() };
  for (const g of Object.values(groups)) scene.add(g);
  const objects = {}; // key -> Object3D (rack1, cooling1, ups, battery, ats, panel, gateway, doors, drycooler1, cdu, tray, sensor:<id>)
  let pickables = [];
  const racks = [], coolingUnits = [], dryCoolers = [], sensorMeshes = new Map(), flows = [];
  let particles = null, doorLeaves = [], roof = null, wallPos = null, wallNeg = null, decals = [];
  const mode = { walk: false, tour: false, cutaway: false, doors: false, camera: 'exterior_iso' };
  const reduce = reducedMotion();
  let highlightSel = null;
  const api = { onModeChange: null };

  const sx = (x) => x - G.intL / 2; // twin frame -> three (uncompressed)
  /** Twin x (0..intL, racks at pitch*(i+1)) -> scene x: rack sensors ride on their rack, others map onto the row span. */
  const mapX = (x, rackIndex) => {
    if (rackIndex !== undefined && G.rackX[rackIndex] !== undefined) return G.rackX[rackIndex];
    const span = G.intL - G.bayL;
    return -G.intL / 2 + G.bayL + Math.max(0, Math.min(1, x / G.intL)) * span;
  };
  const toThree = (loc, rackIndex) => new THREE.Vector3(mapX(loc[0], rackIndex), loc[2], loc[1] + (G.zOff || 0));

  /** Hall (BEN 2000): `rows` rows of racks across the interior width, each row with its racks at pitch along x; the
   *  CDU row sits along the -z long wall, fan-wall units along the +z long wall, so no units share the rack rows. */
  function computeHallLayout(cfg, d) {
    const n = cfg.racks, rows = G.rows, rpr = G.rpr;
    G.bayL = 0; G.inRow = 0; G.unitW = 1.2; G.unitX = []; G.wallUnits = 0;
    G.rackX = []; G.rackZ = []; G.rowZ = [];
    const margin = 2.2; // CDU row and fan wall keep the outer 2.2 m on each long side
    for (let r = 0; r < rows; r++) G.rowZ.push(-G.intW / 2 + G.intW * (r + 1) / (rows + 1));
    const pitch = (G.intL - 1.0) / (rpr + 1);
    for (let i = 0; i < n; i++) { const r = Math.floor(i / rpr), k = i % rpr; G.rackX[i] = -G.intL / 2 + 0.5 + pitch * (k + 1); G.rackZ[i] = G.rowZ[r]; }
    G.rowGap = rows > 1 ? G.rowZ[1] - G.rowZ[0] : G.intW;
    G.rowMargin = margin;
    void margin;
  }

  /** Pack racks + in-row units (or CDUs) into the row behind the power bay. */
  function computeRowLayout(cfg, d) {
    if (G.hall) return computeHallLayout(cfg, d);
    const n = cfg.racks;
    G.bayL = G.micro ? 0 : Math.min(1.2, Math.max(0.9, G.intL * 0.18));
    let inRow = 0, unitW = 0.3;
    if (G.air && !G.micro) inRow = d.cooling_units_total;
    else if (G.liquid) { inRow = Math.min(2, d.cooling_units_total); unitW = 0.6; }
    else if (G.water) { inRow = 1; unitW = 0.6; }
    const avail = () => G.intL - G.bayL - 0.1;
    while (inRow > 0 && n * G.rackW + inRow * unitW > avail()) inRow--;          // extras go to the wall
    if (n * G.rackW + inRow * unitW > avail()) G.bayL = Math.max(0.6, G.intL - 0.1 - n * G.rackW - inRow * unitW);
    // unit slots: n+1 gaps, pick inRow of them spread evenly, ends first
    const slots = [];
    if (inRow > 0) {
      const order = [0, n]; for (let k = 1; k < n; k++) order.push(k);
      const pick = new Set();
      if (inRow >= n + 1) for (let k = 0; k <= n; k++) pick.add(k);
      else for (let k = 0; k < inRow; k++) pick.add(Math.round(k * n / Math.max(1, inRow - 1)) || (k === 0 ? 0 : n));
      while (pick.size < inRow) pick.add(order.find(o => !pick.has(o)));
      for (let k = 0; k <= n; k++) if (pick.has(k)) slots.push(k);
    }
    const items = [];
    for (let k = 0; k <= n; k++) { if (slots.includes(k)) items.push({ kind: 'unit', w: unitW }); if (k < n) items.push({ kind: 'rack', w: G.rackW, i: k }); }
    const total = items.reduce((a, it) => a + it.w, 0);
    const gap = Math.max(0.02, (G.intL - G.bayL - total) / (items.length + 1));
    let x = -G.intL / 2 + G.bayL + gap;
    G.rackX = []; G.unitX = [];
    for (const it of items) { const cx = x + it.w / 2; if (it.kind === 'rack') G.rackX[it.i] = cx; else G.unitX.push(cx); x += it.w + gap; }
    G.unitW = unitW; G.inRow = inRow;
    G.wallUnits = Math.max(0, (G.air && !G.micro ? d.cooling_units_total : 0) - inRow);
  }

  function clearGroup(g) { while (g.children.length) { const c = g.children.pop(); c.traverse(o => { if (o.geometry) o.geometry.dispose(); }); } }

  // --------------------------------------------------------------------------- build
  function rebuild(p) {
    payload = p;
    const cfg = p.config, d = p.derived, geo = d.geometry;
    const kind = d.kind || geo.kind || (cfg.tier === 'ben5' || cfg.tier === 'micro' ? 'cabinet' : 'module');
    const micro = kind === 'cabinet', hall = kind === 'hall';
    Object.assign(G, {
      extL: geo.ext_l_m, extW: geo.ext_w_m, extH: geo.ext_h_m, intL: geo.int_l_m, intW: geo.int_w_m, intH: geo.int_h_m,
      floorTop: micro ? 0.12 : 0.17, micro, hall, kind, racks: cfg.racks, rackU: geo.rack_u,
      rows: d.rows || 1, rpr: d.racks_per_row || cfg.racks, modules: d.modules || geo.modules || 1,
      hardening: cfg.hardening || 'H1', mv: !!d.mv_service, transformers: d.transformers_total || 0, generators: d.generators_total || (cfg.generator ? 1 : 0),
    });
    G.ceiling = G.floorTop + G.intH;
    G.rackH = Math.min(G.intH - 0.15, G.rackU * U_M + 0.12);
    G.rackW = micro ? 0.6 : 0.6;
    G.rackD = Math.min(1.0, G.intW * 0.5);
    G.zOff = (micro || hall) ? 0 : -0.15; // rack row sits 15 cm toward the cold wall; sensors move with it (hall rows: see computeHallLayout)
    if (hall) G.rackD = 1.2;
    G.aisleW = hall ? (G.intW / (G.rows + 1) - G.rackD) / 2 : (G.intW - G.rackD) / 2;
    G.coldW = G.aisleW + G.zOff; G.hotW = G.aisleW - G.zOff;
    G.pitch = G.intL / (cfg.racks + 1); // twin sensor pitch (twin frame)
    G.subs = new Set(cfg.subsystems);
    G.liquid = d.cooling_label.toLowerCase().includes('liquid') || cfg.cooling === 'dlc_cdu';
    G.water = cfg.cooling === 'rdhx_drycooler';
    G.air = !G.liquid && !G.water;
    computeRowLayout(cfg, d);
    if (!G.hall) { G.rackZ = Array.from({ length: cfg.racks }, () => G.zOff); G.rowZ = [G.zOff]; }

    for (const g of Object.values(groups)) clearGroup(g);
    for (const k of Object.keys(objects)) delete objects[k];
    racks.length = 0; coolingUnits.length = 0; dryCoolers.length = 0; sensorMeshes.clear(); flows.length = 0; doorLeaves = []; decals = []; particles = null; pickables = [];
    clearGroup(interiorLights);

    buildShell(cfg, d);
    buildHardening(cfg, d);
    if (G.hall) buildHallInterior(cfg, d); else buildInterior(cfg, d);
    if (G.subs.has('compute')) buildRacks(cfg, d);
    if (G.subs.has('cooling')) { if (G.hall) buildHallCooling(cfg, d); else buildCooling(cfg, d); }
    if (G.subs.has('power')) { if (G.hall) buildHallPower(cfg, d); else buildPower(cfg, d); }
    if (G.subs.has('controls')) buildControls(cfg, d, p.sensors || []);
    buildFx(cfg, d);
    buildTour(cfg, d);
    const sh = G.hall ? G.extL * 1.2 : G.extL;
    sun.shadow.camera.left = -sh; sun.shadow.camera.right = sh; sun.shadow.camera.top = sh; sun.shadow.camera.bottom = -sh; sun.shadow.camera.updateProjectionMatrix();
    scene.fog.density = micro ? 0.02 : (hall ? 0.004 : 0.08 / Math.max(4, G.extL));
    setCamera(mode.camera, true);
    if (state) update(state);
    applyCutaway();
  }

  function buildShell(cfg, d) {
    const { extL, extW, extH, micro, hall } = G;
    const g = groups.shell;
    const color = micro ? 0x9aa5b8 : (cfg.white_label ? 0x6b7a90 : (hall ? 0x34496b : 0x2a3c5c));
    // pad (hall: slab-on-grade for the hall, the power module and the plant yard)
    const pad = hall ? box(extL + 18, 0.12, extW + 20, MAT.pad, -5, 0.06 - 0.12, 4) : box(extL + 1.2, 0.12, extW + 1.2, MAT.pad, 0, 0.06 - 0.12, 0);
    pad.receiveShadow = true; g.add(pad);
    if (micro) { // skid
      g.add(box(extL + 0.2, 0.1, 0.12, MAT.casting, 0, 0.05, -extW / 2 + 0.1)); g.add(box(extL + 0.2, 0.1, 0.12, MAT.casting, 0, 0.05, extW / 2 - 0.1));
    }
    // floor slab + roof
    const floor = box(extL, G.floorTop, extW, MAT.shell(color), 0, G.floorTop / 2, 0); g.add(floor);
    const floorTop = new THREE.Mesh(new THREE.PlaneGeometry(G.intL, G.intW), MAT.floor); floorTop.rotation.x = -Math.PI / 2; floorTop.position.y = G.floorTop + 0.001; floorTop.receiveShadow = true; floorTop.userData = { type: 'container', id: 'container' }; g.add(floorTop);
    roof = box(extL, extH - G.ceiling, extW, MAT.shell(color), 0, (extH + G.ceiling) / 2, 0); g.add(roof);
    roof.userData = { type: 'container', id: 'container' }; pickables.push(roof);
    // long walls (corrugated)
    wallPos = corrugatedWall(extL, extH, color); wallPos.position.set(0, extH / 2, extW / 2); g.add(wallPos);
    wallNeg = corrugatedWall(extL, extH, color); wallNeg.rotation.y = Math.PI; wallNeg.position.set(0, extH / 2, -extW / 2); g.add(wallNeg);
    for (const w of [wallPos, wallNeg]) { w.userData = { type: 'container', id: 'container' }; pickables.push(w); }
    // far end wall
    const endWall = corrugatedWall(extW, extH, color); endWall.rotation.y = Math.PI / 2; endWall.position.set(extL / 2, extH / 2, 0); g.add(endWall);
    endWall.userData = { type: 'container', id: 'container' }; pickables.push(endWall);
    // door end: frame + two leaves hinged at outer edges
    const doorGroup = new THREE.Group(); doorGroup.position.set(-extL / 2, 0, 0); doorGroup.userData = { type: 'doors', id: 'doors' };
    const frameMat = MAT.casting;
    doorGroup.add(box(0.12, extH, 0.12, frameMat, 0, extH / 2, -extW / 2 + 0.06), box(0.12, extH, 0.12, frameMat, 0, extH / 2, extW / 2 - 0.06), box(0.12, 0.12, extW, frameMat, 0, extH - 0.06, 0), box(0.12, 0.15, extW, frameMat, 0, 0.075, 0));
    const leafW = extW / 2 - 0.12, leafH = extH - 0.3;
    for (const side of [-1, 1]) {
      const hinge = new THREE.Group(); hinge.position.set(0, 0, side * (extW / 2 - 0.12));
      const leaf = box(0.06, leafH, leafW, MAT.shell(color), -0.03, 0.15 + leafH / 2, -side * leafW / 2);
      leaf.userData = { type: 'doors', id: 'doors' };
      // lock rods
      for (const k of [0.35, 0.65]) leaf.add(box(0.03, leafH - 0.4, 0.03, MAT.casting, -0.05, 0, -side * leafW / 2 + side * k * leafW));
      hinge.add(leaf); doorGroup.add(hinge); doorLeaves.push({ hinge, side });
      pickables.push(leaf);
    }
    objects.doors = doorGroup; g.add(doorGroup);
    // wide-body module seams on the envelope (hall: site-joined modules)
    if (hall && G.modules > 1) {
      const seamMat = new THREE.MeshStandardMaterial({ color: 0x1b2638, roughness: 0.6, metalness: 0.5 });
      for (let m = 1; m < G.modules; m++) {
        const x = -extL / 2 + extL * m / G.modules;
        for (const z of [-1, 1]) g.add(box(0.14, extH, 0.1, seamMat, x, extH / 2, z * (extW / 2 + 0.04)));
        g.add(box(0.14, 0.08, extW + 0.1, seamMat, x, extH + 0.03, 0));
      }
      // roof-edge parapet and the module ridge lines
      for (const z of [-1, 1]) g.add(box(extL + 0.1, 0.1, 0.12, MAT.casting, 0, extH + 0.03, z * (extW / 2 + 0.02)));
    }
    // corner castings + bottom rails
    if (!micro && !hall) {
      for (const x of [-1, 1]) for (const y of [0, 1]) for (const z of [-1, 1]) g.add(box(0.18, 0.12, 0.16, MAT.casting, x * (extL / 2 - 0.09), y ? extH - 0.06 : 0.06, z * (extW / 2 - 0.08)));
      for (const z of [-1, 1]) { g.add(box(extL, 0.16, 0.08, MAT.casting, 0, 0.08, z * (extW / 2 + 0.03))); g.add(box(extL, 0.08, 0.08, MAT.casting, 0, extH - 0.04, z * (extW / 2 + 0.03))); }
    }
    // brand decals on both long sides
    const tex = brandTexture(cfg.white_label ? cfg.brand : 'Schreiber AI', d.tier_label, cfg.white_label);
    const decW = Math.min(extL * 0.62, 7.5), decH = decW * 640 / 2048;
    if (decH < extH * 0.9) {
      for (const side of [1, -1]) {
        const dm = new THREE.Mesh(new THREE.PlaneGeometry(decW, decH), new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.FrontSide, depthWrite: false }));
        dm.position.set(micro ? 0 : -extL * 0.08, extH * 0.5 + (micro ? 0.2 : 0.1), side * (extW / 2 + 0.035)); dm.rotation.y = side > 0 ? 0 : Math.PI;
        g.add(dm); decals.push(dm);
      }
    }
    // utility pedestal + generator outside
    const util = hall ? box(1.2, 2.0, 1.0, MAT.powerDark, -extL / 2 - 15.5, 1.0, 5.5) : box(0.7, 1.1, 0.5, MAT.powerDark, -extL / 2 - 1.4, 0.55, extW / 2 - 0.4);
    util.userData = { type: 'utility', id: 'utility' }; g.add(util); pickables.push(util); objects.utility = util;
    util.add(box(0.5, 0.25, 0.05, MAT.power, 0, 0.2, hall ? 0.51 : 0.26));
    if (cfg.generator && !hall) {
      const gen = box(1.6, 1.5, 0.9, MAT.powerDark, extL / 2 + 1.6, 0.75, 0); gen.userData = { type: 'generator', id: 'generator' };
      const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.6, 12), MAT.casting); pipe.position.set(-0.5, 1.0, 0); gen.add(pipe);
      g.add(gen); pickables.push(gen); objects.generator = gen;
    }
    pickables.push(floorTop);
  }

  /** Hardening level visuals (docs/TIER_AND_ENCLOSURE_DECISION.md §3): H2 flood plinth, H3 vestibule / mantrap + thicker (ballistic) walls. */
  function buildHardening(cfg, d) {
    const { extL, extW, extH, micro } = G; const g = groups.shell;
    const hz = G.hardening;
    if (hz === 'H2' || hz === 'H3') {
      const plinthMat = new THREE.MeshStandardMaterial({ color: 0x4a5565, roughness: 0.95 });
      const plinth = box(extL + 0.5, micro ? 0.3 : 0.6, extW + 0.5, plinthMat, 0, (micro ? 0.3 : 0.6) / 2 - 0.1, 0);
      plinth.userData = { type: 'plinth', id: 'plinth' }; edges(plinth, 0, 0.3); g.add(plinth); pickables.push(plinth); objects.plinth = plinth;
    }
    if (hz === 'H3' && !micro) {
      const armour = new THREE.MeshStandardMaterial({ color: 0x1f2a3b, roughness: 0.7, metalness: 0.45 });
      for (const z of [-1, 1]) { const p = box(extL + 0.2, extH * 0.92, 0.12, armour, 0, extH * 0.5, z * (extW / 2 + 0.12)); p.userData = { type: 'armour', id: 'armour' }; edges(p, 0, 0.3); g.add(p); pickables.push(p); if (z > 0) objects.armour = p; }
      const pe = box(0.12, extH * 0.92, extW + 0.2, armour, extL / 2 + 0.12, extH * 0.5, 0); pe.userData = { type: 'armour', id: 'armour' }; g.add(pe); pickables.push(pe);
      // secure vestibule / mantrap at the door end
      const vW = Math.min(3.0, extW * 0.7), vH = Math.min(extH, 3.0), vL = 2.4;
      const vest = box(vL, vH, vW, MAT.shell(0x2a3c5c), -extL / 2 - vL / 2 - 0.1, vH / 2, 0); vest.userData = { type: 'vestibule', id: 'vestibule' }; edges(vest, 0, 0.35); g.add(vest); pickables.push(vest); objects.vestibule = vest;
      vest.add(box(0.08, vH * 0.7, 1.0, MAT.casting, -vL / 2 - 0.02, -vH * 0.1, 0));
      vest.add(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.1, 0.1), MAT.led(C.amber)).translateX(-vL / 2 - 0.06).translateY(vH * 0.25).translateZ(0.7));
      G.vestibuleL = vL;
    }
  }

  /** BEN 2000 hall interior: `rows` rack rows with alternating cold/hot aisles, overhead busway, DLC manifolds per row. */
  function buildHallInterior(cfg, d) {
    const g = groups.shell;
    const liner = new THREE.Mesh(new THREE.BoxGeometry(G.intL, G.intH, G.intW), MAT.liner); liner.position.set(0, G.floorTop + G.intH / 2, 0); liner.receiveShadow = true; g.add(liner);
    objects.liner = liner;
    const nL = Math.max(2, Math.round(G.intL / 4));
    for (let r = 0; r < G.rows; r++) for (let i = 0; i < nL; i++) {
      const x = -G.intL / 2 + (i + 0.5) * G.intL / nL, z = G.rowZ[r] - G.rackD / 2 - G.aisleW / 2;
      if (i % 2 === 0) { const pl = new THREE.PointLight(0xdfe9ff, 14, 9, 1.6); pl.position.set(x, G.ceiling - 0.1, z); interiorLights.add(pl); }
      g.add(box(1.2, 0.03, 0.12, MAT.led(0xeef6ff), x, G.ceiling - 0.02, z));
    }
    const aisleH = G.intH - 0.05;
    for (let r = 0; r < G.rows; r++) {
      const zc = G.rowZ[r] - (G.rackD / 2 + G.aisleW / 2), zh = G.rowZ[r] + G.rackD / 2 + G.aisleW / 2;
      const cold = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 1.2, aisleH, G.aisleW - 0.02), new THREE.MeshBasicMaterial({ color: C.cyan, transparent: true, opacity: 0.07, depthWrite: false }));
      cold.position.set(0, G.floorTop + aisleH / 2, zc); cold.userData = { type: 'aisle_cold', id: 'aisle_cold', index: r }; groups.cooling.add(cold); edges(cold, C.cyan, 0.2);
      const hot = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 1.2, aisleH, G.aisleW - 0.02), new THREE.MeshBasicMaterial({ color: C.amber, transparent: true, opacity: 0.07, depthWrite: false }));
      hot.position.set(0, G.floorTop + aisleH / 2, zh); hot.userData = { type: 'aisle_hot', id: 'aisle_hot', index: r }; edges(hot, C.amber, 0.2); groups.cooling.add(hot);
      if (r === 0) { objects.aisle_cold = cold; objects.aisle_hot = hot; }
      for (const x of [-1, 1]) {
        const door = new THREE.Mesh(new THREE.PlaneGeometry(G.aisleW - 0.04, aisleH), MAT.glass); door.rotation.y = Math.PI / 2; door.position.set(x * (G.intL / 2 - 0.65), G.floorTop + aisleH / 2, zh); groups.cooling.add(door);
        const idx = r * 2 + (x > 0 ? 1 : 0);
        door.userData = { type: 'containment', id: `containment${idx + 1}`, index: idx }; pickables.push(door); objects[door.userData.id] = door;
      }
    }
    // module partition lines on the floor (where the wide-body modules are joined)
    for (let m = 1; m < G.modules; m++) g.add(box(0.06, 0.012, G.intW, MAT.casting, -G.intL / 2 + G.intL * m / G.modules, G.floorTop + 0.006, 0));
  }

  /** BEN 2000 cooling: CDU row along the -z long wall (the configured cooling units), fan-wall units along the +z long wall, adiabatic dry coolers in the plant yard. */
  function buildHallCooling(cfg, d) {
    const g = groups.cooling, n = d.cooling_units_total;
    const cduW = 1.2, cduH = Math.min(2.1, G.intH - 0.4), cduD = 1.0, zCdu = -G.intW / 2 + cduD / 2 + 0.25;
    const span = G.intL - 2.0, step = span / n;
    for (let i = 0; i < n; i++) {
      const unit = new THREE.Group(); unit.position.set(-G.intL / 2 + 1.0 + step * (i + 0.5), G.floorTop, zCdu);
      const body = box(cduW, cduH, cduD, MAT.cooling, 0, cduH / 2, 0); body.userData = { type: 'cdu', id: 'cdu', index: i, unit: i }; unit.add(body); pickables.push(body); edges(body, 0, 0.3);
      const disp = new THREE.Mesh(new THREE.PlaneGeometry(cduW - 0.2, 0.25), MAT.led(0x66e3ff)); disp.position.set(0, cduH * 0.6, cduD / 2 + 0.003); unit.add(disp);
      const strip = new THREE.Mesh(new THREE.BoxGeometry(cduW - 0.2, 0.04, 0.02), MAT.led(C.green)); strip.position.set(0, cduH - 0.1, cduD / 2 + 0.012); unit.add(strip);
      unit.userData = { strip, body }; g.add(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = body; if (i === 0) objects.cdu = body;
    }
    // fan-wall units along the +z long wall handle the residual air-side heat
    const nFw = Math.max(2, Math.round(G.intL / 4.5)), fwW = 2.4, fwH = Math.min(G.intH - 0.3, 2.8), fwD = 0.9, zFw = G.intW / 2 - fwD / 2 - 0.2;
    for (let i = 0; i < nFw; i++) {
      const unit = new THREE.Group(); unit.position.set(-G.intL / 2 + (i + 0.5) * G.intL / nFw, G.floorTop, zFw);
      const body = box(fwW, fwH, fwD, MAT.cooling, 0, fwH / 2, 0); body.userData = { type: 'fanwall', id: `fanwall${i + 1}`, index: i }; unit.add(body); pickables.push(body); edges(body, 0, 0.3);
      for (let r = 0; r < 2; r++) for (let c = 0; c < 2; c++) { const ring = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.03, 8, 28), MAT.coolingDark); ring.position.set(-fwW / 4 + c * fwW / 2, fwH * 0.3 + r * fwH * 0.42, -fwD / 2 - 0.01); unit.add(ring); const fan = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.02, 20), MAT.fan); fan.rotation.x = Math.PI / 2; fan.position.copy(ring.position); unit.add(fan); }
      unit.userData = { strip: new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.03, 0.02), MAT.led(C.green)), body }; unit.add(unit.userData.strip); unit.userData.strip.position.set(0, fwH - 0.1, -fwD / 2 - 0.02);
      g.add(unit); objects[`fanwall${i + 1}`] = body; if (i === 0) objects.fanwall = body;
    }
    // manifolds (DLC supply/return) along each hot aisle with drops to each rack, plus the overhead busway
    for (let r = 0; r < G.rows; r++) {
      const y = G.ceiling - 0.45, z0 = G.rowZ[r] + G.rackD / 2 + 0.12;
      for (const [mat, dz] of [[MAT.pipeCold, 0], [MAT.pipeHot, 0.16]]) {
        const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, G.intL - 1.4, 12), mat); pipe.rotation.z = Math.PI / 2; pipe.position.set(0, y - dz, z0 + dz); g.add(pipe);
        for (let i = 0; i < cfg.racks; i++) { if (Math.floor(i / G.rpr) !== r) continue; const x = G.rackX[i]; const len = y - dz - (G.floorTop + G.rackH * 0.85); const drop = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, len, 8), mat); drop.position.set(x + (dz ? 0.1 : -0.1), y - dz - len / 2, z0 + dz); g.add(drop); }
      }
    }
    // adiabatic dry coolers in the plant yard beyond the fan wall (+z), on grade
    const dcW = 6.0, dcL = 2.4, zYard = G.extW / 2 + 4.5;
    for (let i = 0; i < n; i++) {
      const unit = new THREE.Group(); unit.position.set(-G.extL / 2 + 2 + dcW / 2 + i * (dcW + 0.8) - (n * (dcW + 0.8) - G.extL) / 2 * 0, 0, zYard);
      const body = box(dcW, 2.4, dcL, MAT.cooling, 0, 1.3, 0); body.userData = { type: 'drycooler', index: i, id: `cooling${i + 1}` }; unit.add(body); pickables.push(body); edges(body, 0, 0.3);
      for (const leg of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) unit.add(box(0.12, 0.1, 0.12, MAT.casting, leg[0] * (dcW / 2 - 0.2), 0.05, leg[1] * (dcL / 2 - 0.2)));
      // adiabatic pre-cooling pads on the long faces
      for (const z of [-1, 1]) unit.add(box(dcW - 0.4, 1.6, 0.06, new THREE.MeshStandardMaterial({ color: 0x3fc0e0, roughness: 0.9, transparent: true, opacity: 0.45 }), 0, 1.2, z * (dcL / 2 + 0.03)));
      const fans = []; const nf = 4;
      for (let f = 0; f < nf; f++) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.04, 8, 32), MAT.coolingDark); ring.rotation.x = Math.PI / 2; ring.position.set(-dcW / 2 + (f + 0.5) * dcW / nf, 2.56, 0); unit.add(ring);
        const blades = new THREE.Group(); blades.position.copy(ring.position);
        for (let b = 0; b < 5; b++) { const bl = box(0.45, 0.02, 0.12, MAT.fan, 0.24, 0, 0); const piv = new THREE.Group(); piv.rotation.y = b / 5 * Math.PI * 2; piv.add(bl); blades.add(piv); }
        unit.add(blades); fans.push(blades);
      }
      const strip = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.05, 0.02), MAT.led(C.green)); strip.position.set(0, 0.4, -dcL / 2 - 0.012); unit.add(strip);
      unit.userData = { strip, body, fans, unit: i }; g.add(unit); dryCoolers.push(unit);
      objects[`drycooler${i + 1}`] = body;
    }
    // glycol headers from the yard to the CDU row (under the slab, shown as two pipes along the end wall)
    for (const [mat, dz] of [[MAT.pipeCold, 0], [MAT.pipeHot, 0.3]]) { const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, zYard + G.intW / 2, 12), mat); pipe.rotation.x = Math.PI / 2; pipe.position.set(G.extL / 2 + 0.6 + dz, 0.35, zYard / 2 - G.intW / 4); g.add(pipe); }
  }

  /** BEN 2000 power: a separate power module beside the hall (switchgear, UPS strings, battery room), pad-mount transformers
   *  in an MV yard and N+1 generators in the plant yard; overhead busway into each rack row. */
  function buildHallPower(cfg, d) {
    const g = groups.power;
    const pmL = 3.66, pmW = 12.2, pmH = G.extH, pmX = -G.extL / 2 - 2.6 - pmL / 2 - (G.vestibuleL || 0);
    const shellMat = MAT.shell(cfg.white_label ? 0x6b7a90 : 0x2f4262);
    const pm = new THREE.Group(); pm.position.set(pmX, 0, 0);
    const pmFloor = box(pmL, G.floorTop, pmW, shellMat, 0, G.floorTop / 2, 0); pm.add(pmFloor);
    const pmRoof = box(pmL, 0.2, pmW, shellMat, 0, pmH - 0.1, 0); pmRoof.userData = { type: 'powermodule', id: 'powermodule' }; pm.add(pmRoof); pickables.push(pmRoof); objects.powermodule = pmRoof;
    const pmWallPos = corrugatedWall(pmL, pmH, 0x2f4262); pmWallPos.position.set(0, pmH / 2, pmW / 2); pm.add(pmWallPos);
    const pmWallNeg = corrugatedWall(pmL, pmH, 0x2f4262); pmWallNeg.rotation.y = Math.PI; pmWallNeg.position.set(0, pmH / 2, -pmW / 2); pm.add(pmWallNeg);
    const pmEnd = corrugatedWall(pmW, pmH, 0x2f4262); pmEnd.rotation.y = -Math.PI / 2; pmEnd.position.set(-pmL / 2, pmH / 2, 0); pm.add(pmEnd);
    for (const w of [pmWallPos, pmWallNeg, pmEnd]) { w.userData = { type: 'powermodule', id: 'powermodule' }; pickables.push(w); }
    G.pmRoof = pmRoof; G.pmWalls = [pmWallPos, pmWallNeg, pmEnd];
    // interior: switchgear lineup, UPS strings, battery room behind a partition
    const cabH = Math.min(2.2, pmH - 0.6);
    const sw = box(0.8, cabH, 4.0, MAT.powerDark, -pmL / 2 + 0.6, G.floorTop + cabH / 2, pmW / 2 - 2.4); sw.userData = { type: 'switchgear', id: 'switchgear' }; edges(sw, 0, 0.35); pm.add(sw); pickables.push(sw); objects.switchgear = sw;
    for (let k = 0; k < 5; k++) sw.add(new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.4, 0.5), MAT.power).translateX(0.405).translateY(0.3).translateZ(-1.6 + k * 0.8));
    const ats = box(0.6, cabH, 0.8, MAT.powerDark, -pmL / 2 + 0.5, G.floorTop + cabH / 2, pmW / 2 - 5.0); ats.userData = { type: 'ats', id: 'ats' }; edges(ats, 0, 0.35); pm.add(ats); pickables.push(ats); objects.ats = ats;
    ats.add(new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.07, 0.07), MAT.led(C.green)).translateX(0.305).translateY(0.3));
    const nStr = d.ups_modules, framesPer = 3;
    for (let m = 0; m < nStr; m++) for (let f = 0; f < framesPer; f++) {
      const z = pmW / 2 - 6.2 - (m * framesPer + f) * 0.9;
      const ups = box(1.0, cabH, 0.8, MAT.power, pmL / 2 - 0.7, G.floorTop + cabH / 2, z); ups.userData = { type: 'ups', id: 'ups', index: m }; edges(ups, 0, 0.35); pm.add(ups); pickables.push(ups);
      ups.add(new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.16), MAT.led(0x66e3ff)).translateY(0.6).translateX(-0.502).rotateY(-Math.PI / 2));
      if (m === 0 && f === 0) objects.ups = ups;
    }
    const partZ = pmW / 2 - 6.2 - nStr * framesPer * 0.9 - 0.5;
    pm.add(box(pmL - 0.2, pmH - 0.4, 0.1, new THREE.MeshStandardMaterial({ color: 0x7b8798, roughness: 0.9 }), 0, G.floorTop + (pmH - 0.4) / 2, partZ));
    const nBat = Math.min(12, Math.max(2, Math.ceil(d.battery_kwh / 120)));
    for (let b = 0; b < nBat; b++) {
      const col = b % 2, row = Math.floor(b / 2);
      const bat = box(0.8, cabH, 0.6, MAT.battery, -pmL / 2 + 0.6 + col * (pmL - 1.2), G.floorTop + cabH / 2, partZ - 0.7 - row * 0.75); bat.userData = { type: 'battery', id: 'battery', index: b }; edges(bat, 0, 0.35); pm.add(bat); pickables.push(bat);
      bat.add(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.04, 0.04), MAT.led(C.green)).translateY(cabH / 2 - 0.12).translateX(col ? -0.41 : 0.41));
      if (b === 0) objects.battery = bat;
    }
    g.add(pm); objects.pm = pm;
    // pad-mount transformers in the MV yard west of the power module
    const nX = Math.max(1, G.transformers);
    for (let t = 0; t < nX; t++) {
      const x = pmX - pmL / 2 - 3.2, z = -pmW / 2 + 2.0 + t * (pmW - 4.0) / Math.max(1, nX - 1) * (nX > 1 ? 1 : 0);
      const xf = box(2.4, 2.0, 2.2, MAT.powerDark, x, 1.0, z); xf.userData = { type: 'transformer', id: 'transformer', index: t }; edges(xf, 0, 0.35); g.add(xf); pickables.push(xf);
      for (let k = 0; k < 4; k++) xf.add(box(0.08, 1.6, 2.0, MAT.casting, -1.2 - 0.06 - k * 0.0, -0.1, 0).translateX(-k * 0.0 - 0.01 * k).translateZ(0)); // radiator fins block
      xf.add(box(0.5, 1.6, 2.0, MAT.casting, -1.45, -0.1, 0));
      for (let k = 0; k < 3; k++) xf.add(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.4, 10), MAT.power).translateY(1.2).translateZ(-0.6 + k * 0.6));
      if (t === 0) objects.transformer = xf;
    }
    // MV yard fence
    const fenceMat = new THREE.MeshStandardMaterial({ color: 0x5a6a80, roughness: 0.8, transparent: true, opacity: 0.35, side: THREE.DoubleSide });
    const fx0 = pmX - pmL / 2 - 5.2, fx1 = pmX - pmL / 2 - 1.2;
    for (const z of [-pmW / 2 - 0.5, pmW / 2 + 0.5]) g.add(new THREE.Mesh(new THREE.PlaneGeometry(fx1 - fx0, 2.4), fenceMat).translateX((fx0 + fx1) / 2).translateY(1.2).translateZ(z));
    g.add(new THREE.Mesh(new THREE.PlaneGeometry(pmW + 1.0, 2.4), fenceMat).translateX(fx0).translateY(1.2).rotateY(Math.PI / 2));
    // generators in the plant yard (north, -z side), N+1
    const nG = G.generators;
    for (let k = 0; k < nG; k++) {
      const gen = box(6.0, 3.0, 2.4, MAT.powerDark, -G.extL / 2 + 4 + k * 7.5, 1.5, -G.extW / 2 - 5.0); gen.userData = { type: 'generator', id: 'generator', index: k };
      edges(gen, 0, 0.35);
      const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 1.4, 12), MAT.casting); pipe.position.set(-2.2, 2.1, 0); gen.add(pipe);
      gen.add(box(1.4, 1.2, 2.2, MAT.coolingDark, 2.4, 0.2, 0)); // radiator end
      gen.add(box(5.6, 0.5, 2.0, MAT.casting, 0, -1.25, 0));     // belly fuel tank (48 h)
      g.add(gen); pickables.push(gen); if (k === 0) objects.generator = gen;
    }
    // busway: from the power module across to each rack row at ceiling height, drops at racks
    const trayY = G.ceiling - 0.3;
    const tray = new THREE.Group(); tray.position.set(0, trayY, 0);
    for (let r = 0; r < G.rows; r++) { tray.add(box(G.intL - 1.2, 0.12, 0.25, MAT.tray, 0, 0, G.rowZ[r])); }
    tray.add(box(0.25, 0.12, G.intW - 1.0, MAT.tray, -G.intL / 2 + 0.7, 0, 0));
    const trayPick = box(G.intL - 1.2, 0.14, 0.3, new THREE.MeshBasicMaterial({ visible: false }), 0, 0, G.rowZ[0]); trayPick.userData = { type: 'tray', id: 'tray' }; tray.add(trayPick); pickables.push(trayPick);
    g.add(tray); objects.tray = tray;
    // distribution panel (hall-side busway tap) at the door end
    const panel = box(0.5, 1.2, 0.3, MAT.power, -G.intL / 2 + 0.6, G.floorTop + 1.6, G.intW / 2 - 0.3); panel.userData = { type: 'panel', id: 'panel' }; edges(panel, 0, 0.35); g.add(panel); pickables.push(panel); objects.panel = panel;
    // power flows: utility -> transformer -> switchgear(ATS) -> UPS -> busway -> racks; generators -> switchgear
    const utilPos = objects.utility.position.clone().setY(1.2);
    const xfPos = objects.transformer.position.clone().setY(1.0);
    const atsPos = objects.ats.getWorldPosition(new THREE.Vector3());
    const upsPos = objects.ups.getWorldPosition(new THREE.Vector3());
    const panelPos = objects.panel.getWorldPosition(new THREE.Vector3());
    flows.push(Object.assign(new Flow([utilPos, new THREE.Vector3(utilPos.x, 0.4, utilPos.z), new THREE.Vector3(xfPos.x, 0.4, xfPos.z), xfPos, new THREE.Vector3(xfPos.x, 0.4, xfPos.z), new THREE.Vector3(atsPos.x, 0.4, atsPos.z), atsPos], { n: 14 }), { role: 'utility' }));
    if (objects.generator) { const gp = objects.generator.position.clone().setY(1.0); flows.push(Object.assign(new Flow([gp, new THREE.Vector3(gp.x, 0.4, gp.z), new THREE.Vector3(atsPos.x, 0.4, gp.z), new THREE.Vector3(atsPos.x, 0.4, atsPos.z), atsPos], { n: 14 }), { role: 'generator' })); }
    flows.push(Object.assign(new Flow([atsPos, new THREE.Vector3(atsPos.x, trayY - 0.1, atsPos.z), new THREE.Vector3(upsPos.x, trayY - 0.1, upsPos.z), upsPos], { n: 8 }), { role: 'ats_ups' }));
    flows.push(Object.assign(new Flow([upsPos, new THREE.Vector3(upsPos.x, trayY, upsPos.z), new THREE.Vector3(panelPos.x, trayY, 0), panelPos], { n: 10 }), { role: 'ups_panel' }));
    for (let r = 0; r < G.rows; r++) flows.push(Object.assign(new Flow([new THREE.Vector3(-G.intL / 2 + 0.7, trayY, 0), new THREE.Vector3(-G.intL / 2 + 0.7, trayY, G.rowZ[r]), new THREE.Vector3(G.intL / 2 - 0.6, trayY, G.rowZ[r])], { n: Math.max(8, Math.round(G.intL / 2)) }), { role: 'tray' }));
    for (let i = 0; i < racks.length; i++) {
      const rx = G.rackX[i], rz = G.rackZ[i], top = racks[i].position.y + G.rackH;
      flows.push(Object.assign(new Flow([new THREE.Vector3(rx, trayY, rz), new THREE.Vector3(rx, top + 0.02, rz), new THREE.Vector3(rx, top - 0.3, rz)], { n: 3, size: 0.07 }), { role: 'rack', index: i }));
    }
    for (const f of flows) g.add(f.group);
    G.powerEndX = -G.intL / 2;
  }

  function buildInterior(cfg, d) {
    const g = groups.shell;
    // insulated liner (inside-out box)
    const liner = new THREE.Mesh(new THREE.BoxGeometry(G.intL, G.intH, G.intW), MAT.liner); liner.position.set(0, G.floorTop + G.intH / 2, 0); liner.receiveShadow = true; g.add(liner);
    objects.liner = liner;
    // interior lights
    const nL = Math.max(1, Math.round(G.intL / 2.5));
    for (let i = 0; i < nL; i++) {
      const pl = new THREE.PointLight(0xdfe9ff, G.micro ? 2 : 10, G.micro ? 2.5 : 7, 1.6); pl.position.set(-G.intL / 2 + (i + 0.5) * G.intL / nL, G.ceiling - 0.1, 0); interiorLights.add(pl);
      const fixture = box(0.6, 0.03, 0.12, MAT.led(0xeef6ff), pl.position.x, G.ceiling - 0.02, G.zOff - G.rackD / 2 - G.coldW / 2); g.add(fixture);
    }
    // aisle volumes (cold cyan / hot amber) with containment doors at the hot aisle ends
    const aisleH = G.intH - 0.05;
    const cold = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 0.04, aisleH, G.coldW - 0.02), new THREE.MeshBasicMaterial({ color: C.cyan, transparent: true, opacity: 0.08, depthWrite: false }));
    cold.position.set(0, G.floorTop + aisleH / 2, G.zOff - (G.rackD / 2 + G.coldW / 2)); cold.userData = { type: 'aisle_cold', id: 'aisle_cold' }; groups.cooling.add(cold); edges(cold, C.cyan, 0.25);
    const hot = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 0.04, aisleH, G.hotW - 0.02), new THREE.MeshBasicMaterial({ color: C.amber, transparent: true, opacity: 0.08, depthWrite: false }));
    hot.position.set(0, G.floorTop + aisleH / 2, G.zOff + G.rackD / 2 + G.hotW / 2); hot.userData = { type: 'aisle_hot', id: 'aisle_hot' }; edges(hot, C.amber, 0.25); groups.cooling.add(hot);
    objects.aisle_cold = cold; objects.aisle_hot = hot;
    if (!G.micro) {
      for (const x of [-1, 1]) {
        const door = new THREE.Mesh(new THREE.PlaneGeometry(G.hotW - 0.04, aisleH), MAT.glass); door.rotation.y = Math.PI / 2; door.position.set(x * (G.intL / 2 - 0.05), G.floorTop + aisleH / 2, G.zOff + G.rackD / 2 + G.hotW / 2); groups.cooling.add(door);
        door.userData = { type: 'containment', id: `containment${x > 0 ? 2 : 1}`, index: x > 0 ? 1 : 0 }; pickables.push(door); objects[door.userData.id] = door;
        const frame = box(0.04, aisleH, 0.04, MAT.tray, x * (G.intL / 2 - 0.05), G.floorTop + aisleH / 2, G.zOff + G.rackD / 2 + 0.02); groups.cooling.add(frame);
      }
    }
  }

  function buildRacks(cfg, d) {
    const g = groups.compute;
    const tex = serverFrontTexture(G.rackU);
    for (let i = 0; i < cfg.racks; i++) {
      const rack = new THREE.Group(); rack.position.set(G.rackX[i], G.floorTop, G.rackZ ? G.rackZ[i] : G.zOff);
      const body = box(G.rackW, G.rackH, G.rackD, MAT.rack, 0, G.rackH / 2, 0); body.userData = { type: 'rack', index: i, id: `rack${i + 1}` }; rack.add(body); pickables.push(body);
      edges(body, 0x66e3ff, 0.12);
      const frontMat = new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: 0.4, roughness: 0.7, metalness: 0.2 });
      const front = new THREE.Mesh(new THREE.PlaneGeometry(G.rackW - 0.06, G.rackH - 0.1), frontMat); front.position.set(0, G.rackH / 2, -G.rackD / 2 - 0.002); front.rotation.y = Math.PI; front.userData = body.userData; rack.add(front); pickables.push(front);
      const rear = new THREE.Mesh(new THREE.PlaneGeometry(G.rackW - 0.06, G.rackH - 0.1), G.water ? MAT.pipeCold : MAT.rackRear); rear.position.set(0, G.rackH / 2, G.rackD / 2 + 0.002); rear.userData = body.userData; rack.add(rear);
      if (G.water) { const coil = box(G.rackW, G.rackH - 0.1, 0.14, MAT.coolingDark, 0, G.rackH / 2, G.rackD / 2 + 0.08); coil.userData = { type: 'cooling', index: Math.min(i, d.cooling_units_total - 1), id: `cooling${Math.min(i, d.cooling_units_total - 1) + 1}` }; rack.add(coil); pickables.push(coil); }
      // label plate
      const led = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.03, 0.01), MAT.led(C.green)); led.position.set(0, G.rackH + 0.015, -G.rackD / 2 + 0.01); rack.add(led);
      rack.userData = { front, frontMat, led, body };
      g.add(rack); racks.push(rack); objects[`rack${i + 1}`] = body;
    }
  }

  function coolingGapPositions(n) {
    return Array.from({ length: n }, (_, i) => G.unitX[i] === undefined ? null : G.unitX[i]);
  }

  function buildCooling(cfg, d) {
    const g = groups.cooling;
    const n = d.cooling_units_total;
    const unitW = G.unitW || 0.3;
    if (G.air && !G.micro) {
      const xs = coolingGapPositions(n);
      let wallIdx = 0;
      for (let i = 0; i < n; i++) {
        let x = xs[i], z = 0, w = unitW, dd = G.rackD;
        if (x === null) { x = G.intL / 2 - 0.5 - wallIdx++ * 0.7; z = G.zOff + G.rackD / 2 + G.hotW - 0.17; w = 0.6; dd = 0.3; } // wall-mounted extras
        const unit = new THREE.Group(); unit.position.set(x, G.floorTop, z + (z === 0 ? G.zOff : 0));
        const body = box(w, G.rackH, dd, MAT.cooling, 0, G.rackH / 2, 0); body.userData = { type: 'cooling', index: i, id: `cooling${i + 1}` }; unit.add(body); pickables.push(body); edges(body, 0x000000, 0.3);
        const grilleF = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.04, G.rackH - 0.2), MAT.coolingDark); grilleF.position.set(0, G.rackH / 2, -dd / 2 - 0.002); grilleF.rotation.y = Math.PI; unit.add(grilleF);
        const grilleB = grilleF.clone(); grilleB.position.z = dd / 2 + 0.002; grilleB.rotation.y = 0; unit.add(grilleB);
        const strip = new THREE.Mesh(new THREE.BoxGeometry(w - 0.06, 0.04, 0.02), MAT.led(C.green)); strip.position.set(0, G.rackH - 0.08, -dd / 2 - 0.012); unit.add(strip);
        unit.userData = { strip, body }; g.add(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = body;
      }
    } else if (G.micro) {
      // cabinet DX mounted on the +z exterior side
      for (let i = 0; i < n; i++) {
        const unit = new THREE.Group(); unit.position.set(-G.extL / 2 + 0.35 + i * 0.5, 0, G.extW / 2 + 0.14);
        const body = box(0.42, G.extH * 0.7, 0.26, MAT.cooling, 0, G.extH * 0.5, 0); body.userData = { type: 'cooling', index: i, id: `cooling${i + 1}` }; unit.add(body); pickables.push(body); edges(body, 0, 0.3);
        const fan = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.02, 24), MAT.fan); fan.rotation.x = Math.PI / 2; fan.position.set(0, G.extH * 0.72, 0.14); unit.add(fan);
        const strip = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.03, 0.02), MAT.led(C.green)); strip.position.set(0, G.extH * 0.2, 0.14); unit.add(strip);
        unit.userData = { strip, body, fan }; g.add(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = body;
      }
    } else {
      // liquid / water: CDU(s) inside at the far end + dry coolers on the roof; manifold pipes in the hot aisle
      const nCdu = G.liquid ? Math.min(2, n) : 1;
      for (let k = 0; k < nCdu; k++) {
        const w = G.unitW || 0.6;
        const x = G.unitX[k] !== undefined ? G.unitX[k] : (k === 0 ? G.intL / 2 - 0.4 : -G.intL / 2 + G.bayL + 0.4);
        const cdu = box(w, G.rackH, G.rackD, MAT.cooling, x, G.floorTop + G.rackH / 2, G.zOff); cdu.userData = { type: 'cdu', id: 'cdu' }; edges(cdu, 0, 0.3); g.add(cdu); pickables.push(cdu);
        const disp = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.1, 0.25), MAT.led(0x66e3ff)); disp.position.set(0, G.rackH * 0.3, -G.rackD / 2 - 0.003); disp.rotation.y = Math.PI; cdu.add(disp);
        if (k === 0) objects.cdu = cdu;
      }
      // manifolds along the hot aisle ceiling with drops to each rack
      const y = G.ceiling - 0.45, z0 = G.zOff + G.rackD / 2 + 0.12;
      for (const [mat, dz] of [[MAT.pipeCold, 0], [MAT.pipeHot, 0.16]]) {
        const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, G.intL - 0.2, 12), mat); pipe.rotation.z = Math.PI / 2; pipe.position.set(0, y - dz, z0 + dz); g.add(pipe);
        for (const x of G.rackX) { const len = y - dz - (G.floorTop + G.rackH * 0.85); const drop = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, len, 8), mat); drop.position.set(x + (dz ? 0.08 : -0.08), y - dz - len / 2, z0 + dz); g.add(drop); }
      }
      // dry coolers on the roof
      const dcW = Math.min(2.2, (G.extL - 0.6) / n - 0.2), dcL = Math.min(1.1, G.extW - 0.6);
      for (let i = 0; i < n; i++) {
        const unit = new THREE.Group(); unit.position.set(-G.extL / 2 + 0.4 + dcW / 2 + i * (dcW + 0.2), G.extH, 0);
        const body = box(dcW, 0.75, dcL, MAT.cooling, 0, 0.45, 0); body.userData = { type: 'drycooler', index: i, id: `cooling${i + 1}` }; unit.add(body); pickables.push(body); edges(body, 0, 0.3);
        for (const leg of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) unit.add(box(0.06, 0.1, 0.06, MAT.casting, leg[0] * (dcW / 2 - 0.1), 0.05, leg[1] * (dcL / 2 - 0.1)));
        const fans = []; const nf = Math.max(1, Math.round(dcW / 0.9));
        for (let f = 0; f < nf; f++) {
          const ring = new THREE.Mesh(new THREE.TorusGeometry(Math.min(0.38, dcL / 2 - 0.1), 0.03, 8, 32), MAT.coolingDark); ring.rotation.x = Math.PI / 2; ring.position.set(-dcW / 2 + (f + 0.5) * dcW / nf, 0.86, 0); unit.add(ring);
          const blades = new THREE.Group(); blades.position.copy(ring.position);
          for (let b = 0; b < 5; b++) { const bl = box(0.3, 0.015, 0.09, MAT.fan, 0.16, 0, 0); const piv = new THREE.Group(); piv.rotation.y = b / 5 * Math.PI * 2; piv.add(bl); blades.add(piv); }
          unit.add(blades); fans.push(blades);
        }
        const strip = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.05, 0.02), MAT.led(C.green)); strip.position.set(0, 0.2, dcL / 2 + 0.012); unit.add(strip);
        unit.userData = { strip, body, fans }; g.add(unit); dryCoolers.push(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = body;
      }
    }
  }

  function buildPower(cfg, d) {
    const g = groups.power;
    // cable tray above the rack row (containers only)
    const tray = new THREE.Group(); tray.position.set(0, G.ceiling - 0.3, G.zOff); tray.visible = !G.micro;
    tray.add(box(G.intL - 0.1, 0.04, 0.04, MAT.tray, 0, 0, -0.15), box(G.intL - 0.1, 0.04, 0.04, MAT.tray, 0, 0, 0.15));
    for (let x = -G.intL / 2 + 0.2; x < G.intL / 2 - 0.1; x += 0.3) tray.add(box(0.03, 0.03, 0.3, MAT.tray, x, 0, 0));
    const trayPick = box(G.intL - 0.1, 0.06, 0.34, new THREE.MeshBasicMaterial({ visible: false }), 0, 0, 0); trayPick.userData = { type: 'tray', id: 'tray' }; tray.add(trayPick); pickables.push(trayPick);
    g.add(tray); objects.tray = tray;

    if (G.micro) {
      // UPS at the bottom of the cabinet + small panel on the wall
      const ups = box(0.5, 0.18, 0.5, MAT.power, 0, G.floorTop + 0.09, 0); ups.userData = { type: 'ups', id: 'ups' }; g.add(ups); pickables.push(ups); objects.ups = ups;
      const bat = box(0.5, 0.14, 0.5, MAT.battery, 0, G.floorTop + 0.25, 0); bat.userData = { type: 'battery', id: 'battery' }; g.add(bat); pickables.push(bat); objects.battery = bat;
      const panel = box(0.2, 0.3, 0.08, MAT.powerDark, -G.intL / 2 + 0.15, G.floorTop + 1.0, G.intW / 2 - 0.05); panel.userData = { type: 'panel', id: 'panel' }; g.add(panel); pickables.push(panel); objects.panel = panel;
      const ats = box(0.16, 0.2, 0.08, MAT.powerDark, -G.intL / 2 + 0.15, G.floorTop + 0.6, G.intW / 2 - 0.05); ats.userData = { type: 'ats', id: 'ats' }; g.add(ats); pickables.push(ats); objects.ats = ats;
      // racks sit on top of the UPS stack
      for (const r of racks) r.position.y = G.floorTop + 0.34;
    } else {
      // power bay at the door end: floor cabinets along the end wall facing the racks (+x), ATS + panel on the hot wall
      const x0 = -G.intL / 2, zWall = G.intW / 2;
      const nBat = Math.max(1, Math.ceil(d.battery_kwh / 40));
      const nCab = d.ups_modules + nBat;
      const cabW = Math.max(0.35, Math.min(0.6, (G.intW - 0.15 - 0.05 * (nCab - 1)) / nCab));
      const cabD = Math.min(0.6, G.bayL - 0.45), cabH = Math.min(1.9, G.intH - 0.35);
      const rowW = nCab * cabW + (nCab - 1) * 0.05;
      let z = -rowW / 2 + cabW / 2;
      for (let m = 0; m < d.ups_modules; m++) {
        const ups = box(cabD, cabH, cabW, MAT.power, x0 + 0.05 + cabD / 2, G.floorTop + cabH / 2, z); ups.userData = { type: 'ups', id: 'ups' }; edges(ups, 0, 0.35); g.add(ups); pickables.push(ups);
        ups.add(new THREE.Mesh(new THREE.PlaneGeometry(cabW * 0.65, 0.16), MAT.led(0x66e3ff)).translateY(0.55).translateX(cabD / 2 + 0.002).rotateY(Math.PI / 2));
        for (let k = 0; k < 3; k++) ups.add(new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.25, cabW * 0.8), MAT.powerDark).translateY(-0.55 + k * 0.3).translateX(cabD / 2 + 0.004));
        if (m === 0) objects.ups = ups;
        z += cabW + 0.05;
      }
      for (let b = 0; b < nBat; b++) {
        const bat = box(cabD, cabH, cabW, MAT.battery, x0 + 0.05 + cabD / 2, G.floorTop + cabH / 2, z); bat.userData = { type: 'battery', id: 'battery' }; edges(bat, 0, 0.35); g.add(bat); pickables.push(bat);
        for (let k = 0; k < 6; k++) bat.add(new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.02, cabW * 0.8), MAT.coolingDark).translateY(-0.7 + k * 0.28).translateX(cabD / 2 + 0.004));
        bat.add(new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.04, 0.04), MAT.led(C.green)).translateY(cabH / 2 - 0.12).translateX(cabD / 2 + 0.006));
        if (b === 0) objects.battery = bat;
        z += cabW + 0.05;
      }
      const ats = box(0.4, 0.9, 0.22, MAT.powerDark, x0 + 0.3, G.floorTop + 1.55, zWall - 0.11); ats.userData = { type: 'ats', id: 'ats' }; edges(ats, 0, 0.35); g.add(ats); pickables.push(ats); objects.ats = ats;
      ats.add(new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.07, 0.01), MAT.led(C.green)).translateY(0.3).translateZ(-0.115));
      const panel = box(0.55, 1.0, 0.2, MAT.power, x0 + Math.min(G.bayL - 0.3, 0.85), G.floorTop + 1.5, zWall - 0.1); panel.userData = { type: 'panel', id: 'panel' }; edges(panel, 0, 0.35); g.add(panel); pickables.push(panel); objects.panel = panel;
      for (let k = 0; k < Math.min(cfg.racks + 2, 12); k++) panel.add(new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.1, 0.02), MAT.powerDark).translateX(-0.18 + (k % 4) * 0.12).translateY(0.3 - Math.floor(k / 4) * 0.2).translateZ(-0.11));
      G.powerEndX = x0 + G.bayL;
    }
    // power flow paths: utility -> ATS -> UPS -> panel -> tray -> racks
    const utilPos = objects.utility.position.clone().setY(0.9);
    const atsPos = objects.ats.getWorldPosition(new THREE.Vector3());
    const upsPos = objects.ups.getWorldPosition(new THREE.Vector3());
    const panelPos = objects.panel.getWorldPosition(new THREE.Vector3());
    const trayY = G.ceiling - 0.3;
    const wallIn = new THREE.Vector3(atsPos.x, 0.4, G.intW / 2 - 0.1);
    flows.push(Object.assign(new Flow([utilPos, new THREE.Vector3(utilPos.x, 0.4, utilPos.z), new THREE.Vector3(utilPos.x, 0.4, G.extW / 2 + 0.2), new THREE.Vector3(atsPos.x, 0.4, G.extW / 2 + 0.2), wallIn, atsPos], { n: 10 }), { role: 'utility' }));
    if (objects.generator) {
      const gp = objects.generator.position.clone().setY(1.0);
      flows.push(Object.assign(new Flow([gp, new THREE.Vector3(gp.x, 0.4, gp.z), new THREE.Vector3(gp.x, 0.4, G.extW / 2 + 0.3), new THREE.Vector3(atsPos.x, 0.4, G.extW / 2 + 0.3), wallIn, atsPos], { n: 12 }), { role: 'generator' }));
    }
    flows.push(Object.assign(new Flow([atsPos, new THREE.Vector3(atsPos.x, trayY - 0.05, atsPos.z), new THREE.Vector3(upsPos.x, trayY - 0.05, upsPos.z), upsPos], { n: 6 }), { role: 'ats_ups' }));
    flows.push(Object.assign(new Flow([upsPos, new THREE.Vector3(upsPos.x, trayY - 0.08, upsPos.z), new THREE.Vector3(panelPos.x, trayY - 0.08, panelPos.z), panelPos], { n: 6 }), { role: 'ups_panel' }));
    const trayStart = new THREE.Vector3(panelPos.x, trayY, G.zOff);
    flows.push(Object.assign(new Flow([panelPos, new THREE.Vector3(panelPos.x, trayY, panelPos.z), trayStart, new THREE.Vector3(G.intL / 2 - 0.2, trayY, G.zOff)], { n: Math.max(8, Math.round(G.intL * 2)) }), { role: 'tray' }));
    for (let i = 0; i < racks.length; i++) {
      const rx = G.rackX[i], top = racks[i].position.y + G.rackH;
      flows.push(Object.assign(new Flow([new THREE.Vector3(rx, trayY, G.zOff), new THREE.Vector3(rx, top + 0.02, G.zOff), new THREE.Vector3(rx, top - 0.3, G.zOff)], { n: 3, size: 0.07 }), { role: 'rack', index: i }));
    }
    for (const f of flows) g.add(f.group);
  }

  function buildControls(cfg, d, sensors) {
    const g = groups.controls;
    // gateway / network cabinet on the cold-aisle wall at the door end
    const gw = box(0.45, 0.55, 0.18, MAT.gateway, -G.intL / 2 + (G.micro ? 0.2 : 0.5), G.floorTop + (G.micro ? 1.2 : 1.7), -(G.intW / 2 - 0.09));
    gw.userData = { type: 'controller', id: 'controller' }; edges(gw, 0x66e3ff, 0.35); g.add(gw); pickables.push(gw); objects.controller = gw; objects.gateway = gw;
    for (let k = 0; k < 4; k++) gw.add(new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.03, 0.01), MAT.led(k % 2 ? C.cyan : C.green)).translateX(-0.15 + k * 0.08).translateY(0.2).translateZ(0.115));
    // leak-detection rope along the floor under the rack row (BEN Pod leak input)
    const ropeMat = new THREE.MeshStandardMaterial({ color: 0xffc66d, roughness: 0.8 });
    for (let r = 0; r < (G.rowZ || [G.zOff]).length; r++) {
      const rope = new THREE.Mesh(new THREE.BoxGeometry(G.intL - (G.hall ? 1.4 : 0.3), 0.015, 0.04), ropeMat);
      rope.position.set(0, G.floorTop + 0.01, (G.rowZ ? G.rowZ[r] : G.zOff) + G.rackD / 2 + 0.06); rope.userData = { type: 'leak_rope', id: 'leak_rope', index: r }; g.add(rope); pickables.push(rope); if (r === 0) objects.leak_rope = rope;
    }
    // sensors as small spheres (clamped into the interior)
    const r = G.micro ? 0.02 : 0.03;
    const geo = new THREE.SphereGeometry(r, 12, 10);
    for (const s of sensors) {
      const rm = /_r(\d+)(_|$)/.exec(s.id);
      const p = toThree(s.location_m, rm ? +rm[1] - 1 : undefined);
      p.x = THREE.MathUtils.clamp(p.x, -G.intL / 2 + 0.08, G.intL / 2 - 0.08);
      p.z = THREE.MathUtils.clamp(p.z, -G.intW / 2 + 0.08, G.intW / 2 - 0.08);
      p.y = THREE.MathUtils.clamp(p.y + G.floorTop, G.floorTop + 0.03, G.ceiling - 0.08);
      const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x9fb3cc, emissive: 0x9fb3cc, emissiveIntensity: 0.6, roughness: 0.4 }));
      m.position.copy(p); m.userData = { type: 'sensor', id: s.id, spec: s }; g.add(m); pickables.push(m); sensorMeshes.set(s.id, m); objects[`sensor:${s.id}`] = m;
    }
  }

  function buildFx(cfg, d) {
    if (!G.subs.has('cooling')) return;
    const n = Math.min(1600, Math.max(200, (G.racks || 1) * 180));
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const mat = new THREE.PointsMaterial({ size: G.micro ? 0.015 : 0.03, map: dotTexture(), alphaTest: 0.2, vertexColors: true, transparent: true, opacity: 0.9, depthWrite: false, sizeAttenuation: true });
    particles = new THREE.Points(geo, mat); particles.frustumCulled = false;
    // sources: cold-side positions of cooling units (or the far end for liquid / micro)
    const srcX = [];
    for (const u of coolingUnits) { if (u.userData.body && u.userData.body.userData.type === 'cooling' && !G.micro) srcX.push(u.position.x); }
    if (G.hall) { srcX.length = 0; for (let k = 0; k < Math.max(2, Math.round(G.intL / 4.5)); k++) srcX.push(-G.intL / 2 + (k + 0.5) * G.intL / Math.max(2, Math.round(G.intL / 4.5))); }
    if (!srcX.length) srcX.push(...(G.unitX.length ? G.unitX : [G.intL / 2 - 0.3]));
    const P = [];
    const aw = G.hall ? G.aisleW : Math.min(G.coldW, G.hotW);
    for (let i = 0; i < n; i++) {
      const r = G.racks ? i % G.racks : 0;
      const rx = G.racks ? G.rackX[r] + (Math.random() - 0.5) * (G.rackW - 0.1) : 0;
      let best = srcX[0]; for (const x of srcX) if (Math.abs(x - rx) < Math.abs(best - rx)) best = x;
      const rz = G.rackZ ? G.rackZ[r] : G.zOff;
      P.push({ r, rx, sxx: best + (Math.random() - 0.5) * 0.2, y: G.floorTop + 0.15 + Math.random() * (G.rackH - 0.25), yUp: Math.min(G.ceiling - 0.15, G.floorTop + G.rackH + 0.2 + Math.random() * 0.3), t: Math.random(), v: 0.6 + Math.random() * 0.6, lat: (Math.random() - 0.5) * (aw * 0.6),
        zc: G.hall ? rz - (G.rackD / 2 + G.aisleW / 2) : undefined, zh: G.hall ? rz + G.rackD / 2 + G.aisleW * 0.4 : undefined });
    }
    particles.userData = { P };
    groups.fx.add(particles);
    placeParticles(0);
  }

  let _dot = null;
  function dotTexture() {
    if (_dot) return _dot;
    const cv = document.createElement('canvas'); cv.width = cv.height = 64; const g = cv.getContext('2d');
    const grd = g.createRadialGradient(32, 32, 4, 32, 32, 30); grd.addColorStop(0, 'rgba(255,255,255,1)'); grd.addColorStop(0.6, 'rgba(255,255,255,0.8)'); grd.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = grd; g.fillRect(0, 0, 64, 64); _dot = new THREE.CanvasTexture(cv); return _dot;
  }
  const tmpV = new THREE.Vector3();
  function placeParticles(dt) {
    if (!particles) return;
    const { P } = particles.userData, pos = particles.geometry.attributes.position, col = particles.geometry.attributes.color;
    const st = state;
    const fan = st ? Math.max(...st.cooling_units.map(u => u.fan_pct), 0) / 100 : 0.6;
    const speed = (reduce ? 0 : 0.07) * (0.25 + fan) * (G.micro ? 2 : 1);
    const zc0 = G.zOff - (G.rackD / 2 + G.coldW / 2), zh0 = G.zOff + G.rackD / 2 + G.hotW * 0.4;
    const cSupply = new THREE.Color(tempColor(st ? st.supply_c : 20)), cHot = new THREE.Color();
    for (let i = 0; i < P.length; i++) {
      const p = P[i]; p.t = (p.t + speed * p.v * dt) % 1;
      const zc = p.zc !== undefined ? p.zc : zc0, zh = p.zh !== undefined ? p.zh : zh0;
      const outlet = st && st.rack_outlet_c[p.r] !== undefined ? st.rack_outlet_c[p.r] : 30;
      cHot.setHex(tempColor(outlet));
      let x, y, z, c;
      const t = p.t;
      if (t < 0.3) { const k = t / 0.3; x = p.sxx + (p.rx - p.sxx) * k; y = p.y; z = zc + p.lat; c = cSupply; }
      else if (t < 0.5) { const k = (t - 0.3) / 0.2; x = p.rx; y = p.y; z = zc + p.lat + (zh + p.lat - zc - p.lat) * k; c = tmpColor.copy(cSupply).lerp(cHot, k); }
      else if (t < 0.8) { const k = (t - 0.5) / 0.3; x = p.rx + (p.sxx - p.rx) * k; y = p.y + (p.yUp - p.y) * Math.min(1, k * 1.5); z = zh + p.lat; c = cHot; }
      else { const k = (t - 0.8) / 0.2; x = p.sxx; y = p.yUp + (p.y - p.yUp) * k; z = zh + p.lat - (zh - zc) * k; c = tmpColor.copy(cHot).lerp(cSupply, k); }
      pos.setXYZ(i, x, y, z); col.setXYZ(i, c.r, c.g, c.b);
    }
    pos.needsUpdate = true; col.needsUpdate = true;
  }
  const tmpColor = new THREE.Color();

  // --------------------------------------------------------------------------- live update
  function update(st) {
    state = st;
    if (!payload) return;
    const p = st.power, load = payload.config.it_kw / Math.max(1, payload.config.racks);
    racks.forEach((r, i) => {
      const kw = p.pdu_kw[i] || 0, frac = Math.min(1.3, kw / Math.max(0.1, load));
      r.userData.frontMat.emissiveIntensity = 0.15 + 1.1 * frac;
      const inlet = st.rack_inlet_c[i];
      r.userData.led.material = MAT.led(st.alarms.some(a => a.id.startsWith(`rack${i + 1}_`)) ? C.red : (frac > 0.05 ? C.green : C.muted));
      r.userData.front.material.emissive.setHex(lerpColor(0xffffff, tempColor(inlet), 0.25));
    });
    coolingUnits.forEach((u, i) => {
      const cu = st.cooling_units[i]; if (!cu) return;
      u.userData.strip.material = MAT.led(!cu.ok ? C.red : (cu.on ? C.green : C.muted));
      u.userData.fanPct = cu.ok && cu.on ? cu.fan_pct : 0;
    });
    if (G.hall) dryCoolers.forEach((u) => { const cu = st.cooling_units[u.userData.unit]; if (!cu) return; u.userData.strip.material = MAT.led(!cu.ok ? C.red : (cu.on ? C.green : C.muted)); u.userData.fanPct = cu.ok && cu.on ? cu.fan_pct : 0; });
    for (const [id, m] of sensorMeshes) {
      const s = m.userData.spec; let v = null;
      let mm;
      if ((mm = /^T_in_r(\d+)_/.exec(id))) v = st.rack_inlet_c[+mm[1] - 1];
      else if ((mm = /^T_out_r(\d+)/.exec(id))) v = st.rack_outlet_c[+mm[1] - 1];
      else if (id === 'T_supply') v = st.supply_c; else if (id === 'T_return') v = st.return_c;
      let color;
      if (s.kind === 'temperature') color = tempColor(v);
      else if (s.kind === 'leak') color = st.leak ? C.red : C.green;
      else if (s.kind === 'contact') color = st.door_open ? C.amber : C.green;
      else if (s.kind === 'power') color = p.utility_ok ? C.green : C.red;
      else color = C.cyan;
      m.material.color.setHex(color); m.material.emissive.setHex(color);
    }
    // power flows
    const lost = !p.utility_ok, battery = p.ups_on_battery, low = p.ups_soc_pct < 30;
    const flowColor = lost && low ? C.red : (battery ? C.amber : C.green);
    for (const f of flows) {
      f.setColor(f.role === 'generator' ? (p.generator_on ? C.green : C.muted) : flowColor);
      const kw = f.role === 'rack' ? (p.pdu_kw[f.index] || 0) * payload.config.racks : (f.role === 'utility' || f.role === 'generator' ? p.utility_kw : p.ups_kw);
      f.speed = reduce ? 0 : 0.25 + 1.6 * Math.min(1.2, kw / Math.max(1, payload.config.it_kw));
      f.active = f.role === 'utility' ? p.utility_ok && !p.generator_on : f.role === 'generator' ? p.generator_on : (kw > 0.01);
      f.group.visible = f.role === 'generator' ? !!objects.generator : true;
      f.points.visible = f.active;
    }
    // doors
    const want = st.door_open || mode.doors || tourWantsDoors;
    for (const l of doorLeaves) l.target = want ? 1 : 0;
    // alarms -> highlight
    syncHighlights(st.alarms);
  }

  // --------------------------------------------------------------------------- highlights
  const highlights = new Map();
  function targetObject(t) {
    if (t.object) return t.object;
    if (t.type === 'sensor') return objects[`sensor:${t.id}`];
    if (t.type === 'container') return objects.liner;
    if (t.type === 'rack') return objects[`rack${t.index + 1}`];
    if (t.type === 'cooling' || (t.type === 'drycooler' && !G.hall)) return objects[`cooling${(t.index || 0) + 1}`];
    if (t.type === 'drycooler') return objects[`drycooler${(t.index || 0) + 1}`] || objects.drycooler1;
    if (t.type === 'fanwall') return objects[`fanwall${(t.index || 0) + 1}`] || objects.fanwall;
    return objects[t.id] || objects[t.type];
  }
  function makeOutline(obj, color) {
    const bb = new THREE.Box3().setFromObject(obj); if (bb.isEmpty()) return null;
    const size = bb.getSize(new THREE.Vector3()).addScalar(0.08), center = bb.getCenter(new THREE.Vector3());
    const l = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(size.x, size.y, size.z)), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.9, depthTest: false }));
    l.position.copy(center); l.renderOrder = 10; return l;
  }
  function syncHighlights(alarms) {
    const want = new Map();
    for (const a of alarms) {
      const t = alarmTargetLocal(a); const obj = targetObject(t); if (!obj) continue;
      const key = t.type === 'sensor' ? `sensor:${t.id}` : (t.id || t.type);
      const sev = a.sev === 'critical' ? 3 : a.sev === 'alarm' ? 2 : 1;
      if (!want.has(key) || want.get(key).sev < sev) want.set(key, { obj, sev });
    }
    for (const [k, h] of highlights) if (!want.has(k)) { groups.hl.remove(h); highlights.delete(k); }
    for (const [k, w] of want) {
      if (highlights.has(k)) { highlights.get(k).material.color.setHex(w.sev >= 2 ? C.red : C.amber); continue; }
      const o = makeOutline(w.obj, w.sev >= 2 ? C.red : C.amber); if (o) { groups.hl.add(o); highlights.set(k, o); }
    }
  }
  function alarmTargetLocal(a) {
    let m;
    if ((m = /^rack(\d+)_/.exec(a.id))) return { type: 'rack', index: +m[1] - 1, id: `rack${m[1]}` };
    if ((m = /^cool(\d+)_/.exec(a.id))) return { type: 'cooling', index: +m[1] - 1, id: `cooling${m[1]}` };
    if (a.id === 'utility_loss') return { type: 'ats', id: 'ats' };
    if (a.id === 'ups_low') return { type: 'ups', id: 'ups' };
    if (a.id === 'door_open') return { type: 'doors', id: 'doors' };
    if (a.id === 'leak') return { type: 'sensor', id: 'leak_floor' };
    if (a.id === 'filter_dp') return { type: 'cooling', index: 0, id: 'cooling1' };
    return { type: 'container', id: 'container' };
  }
  let selOutline = null;
  function setSelection(sel) {
    if (selOutline) { groups.hl.remove(selOutline); selOutline = null; }
    if (!sel || sel.type === 'container') return;
    const obj = targetObject(sel); if (!obj) return;
    selOutline = makeOutline(obj, C.cyan); if (selOutline) { selOutline.material.opacity = 0.7; groups.hl.add(selOutline); }
    highlightSel = sel;
  }

  // --------------------------------------------------------------------------- picking + hover
  const ray = new THREE.Raycaster(); const ndc = new THREE.Vector2(); let downAt = null;
  const hoverable = (o) => o.visible && o.parent && isVisibleChain(o) && !(o.material && o.material.transparent && o.material.opacity < 0.2 && o.userData.type !== 'containment');
  function pickAt(clientX, clientY) {
    const r = canvas.getBoundingClientRect(); ndc.set((clientX - r.left) / r.width * 2 - 1, -((clientY - r.top) / r.height * 2 - 1));
    ray.setFromCamera(ndc, camera);
    const hits = ray.intersectObjects(pickables.filter(hoverable), false);
    const hit = hits.find(hh => hh.object.userData && hh.object.userData.type);
    return hit ? { type: hit.object.userData.type, index: hit.object.userData.index, id: hit.object.userData.id, object: hit.object } : null;
  }
  const keyOf = (sel) => sel.type === 'sensor' ? `sensor:${sel.id}` : ((sel.id || sel.type) + (G.hall && sel.index !== undefined && ['ups', 'battery', 'transformer', 'generator', 'cdu', 'drycooler', 'fanwall', 'leak_rope', 'aisle_cold', 'aisle_hot'].includes(sel.type) ? `#${sel.index}` : ''));
  let hoverKey = null, hoverOutline = null, hoverRaf = false, lastPointer = null;
  function setHover(sel, screen, source = 'pointer') {
    const key = sel ? keyOf(sel) : null;
    if (key !== hoverKey) {
      hoverKey = key;
      if (hoverOutline) { groups.hl.remove(hoverOutline); hoverOutline = null; }
      if (sel) { const obj = sel.object || targetObject(sel); if (obj) { hoverOutline = makeOutline(obj, C.cyan); if (hoverOutline) { hoverOutline.material.opacity = 0.55; groups.hl.add(hoverOutline); } } }
      canvas.style.cursor = sel ? 'pointer' : '';
    }
    if (api.onHover) api.onHover(sel ? { type: sel.type, index: sel.index, id: sel.id, key, screen, source } : null);
  }
  canvas.addEventListener('pointermove', (e) => {
    if (mode.walk || mode.tour) return;
    lastPointer = [e.clientX, e.clientY];
    if (hoverRaf) return; hoverRaf = true;
    requestAnimationFrame(() => { hoverRaf = false; if (!lastPointer) return; const sel = pickAt(lastPointer[0], lastPointer[1]); setHover(sel, { x: lastPointer[0], y: lastPointer[1] }); });
  });
  canvas.addEventListener('pointerleave', () => { lastPointer = null; setHover(null); });
  canvas.addEventListener('pointerdown', (e) => { downAt = [e.clientX, e.clientY]; });
  canvas.addEventListener('pointerup', (e) => {
    if (!downAt || mode.walk) return; const moved = Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]); downAt = null; if (moved > 5) return;
    const hit = pickAt(e.clientX, e.clientY);
    const sel = hit ? { type: hit.type, index: hit.index, id: hit.id } : { type: 'container', id: 'container' };
    setSelection(sel); onSelect && onSelect(sel);
  });
  /** Ordered, de-duplicated list of hoverable objects for keyboard cycling. */
  function hoverList() {
    const seen = new Set(), out = [];
    for (const o of pickables) { if (!hoverable(o) || !o.userData.type) continue; const k = keyOf(o.userData); if (seen.has(k)) continue; seen.add(k); out.push({ type: o.userData.type, index: o.userData.index, id: o.userData.id, object: o, key: k }); }
    const order = { container: 0, doors: 1, vestibule: 1.5, rack: 2, cooling: 3, fanwall: 3.5, drycooler: 4, cdu: 5, powermodule: 5.5, transformer: 5.7, switchgear: 5.8, ups: 6, battery: 7, ats: 8, panel: 9, utility: 10, generator: 11, controller: 12, tray: 13, containment: 14, leak_rope: 15, plinth: 15.5, armour: 15.6, sensor: 16 };
    return out.sort((a, b) => (order[a.type] ?? 20) - (order[b.type] ?? 20) || (a.index ?? 0) - (b.index ?? 0) || String(a.id).localeCompare(String(b.id)));
  }
  /** Page coordinates of an object's centre (for tooltips and tests). */
  function screenPositionOf(keyOrSel) {
    const obj = typeof keyOrSel === 'string' ? (objects[keyOrSel] || objects[`sensor:${keyOrSel}`]) : (keyOrSel.object || targetObject(keyOrSel));
    if (!obj) return null;
    const c = new THREE.Box3().setFromObject(obj).getCenter(new THREE.Vector3()).project(camera);
    const r = canvas.getBoundingClientRect();
    return { x: r.left + (c.x + 1) / 2 * r.width, y: r.top + (1 - c.y) / 2 * r.height, visible: c.z < 1 && Math.abs(c.x) <= 1 && Math.abs(c.y) <= 1 };
  }
  function hoverCycle(dir = 1) {
    const list = hoverList(); if (!list.length) return null;
    let i = list.findIndex(h => h.key === hoverKey); i = (i + dir + list.length) % list.length;
    const h = list[i]; const sp = screenPositionOf(h) || { x: 0, y: 0 };
    setHover(h, sp, 'keyboard'); return h;
  }
  function hoverSelect() { if (!hoverKey) return; const h = hoverList().find(x => x.key === hoverKey); if (h) { const sel = { type: h.type, index: h.index, id: h.id }; setSelection(sel); onSelect && onSelect(sel); } }
  function isVisibleChain(o) { while (o) { if (!o.visible) return false; o = o.parent; } return true; }

  // --------------------------------------------------------------------------- cameras
  let camTween = null;
  function fitDistance(radius) {
    const vfov = THREE.MathUtils.degToRad(camera.fov);
    const hfov = 2 * Math.atan(Math.tan(vfov / 2) * Math.max(0.5, camera.aspect || 1));
    return radius / Math.sin(Math.min(vfov, hfov) / 2) * 1.08;
  }
  function presetPose(name) {
    const { extL, extW, extH, intL, intW, rackD, floorTop } = G;
    const eye = floorTop + 1.65;
    const zc = G.zOff - (rackD / 2 + G.coldW / 2), zh = G.zOff + rackD / 2 + G.hotW / 2;
    const outdoor = G.hall ? 22 : (objects.generator ? 2.6 : 0) + 2.2; // utility pedestal / generator stand outside the ends (hall: power module + yards)
    const R = 0.5 * Math.hypot(extL + outdoor, extW + (G.hall ? 16 : 1.2), extH + 0.9);
    const centre = [G.hall ? -4 : (objects.generator ? 0 : -0.6), extH * 0.45, G.hall ? 1.5 : 0];
    if (G.hall) {
      const z0 = G.rowZ[0], zc0 = z0 - (rackD / 2 + G.aisleW / 2), zh0 = z0 + rackD / 2 + G.aisleW / 2;
      switch (name) {
        case 'cold_aisle': return { pos: [-intL / 2 + 0.9, eye, zc0], look: [intL / 2, eye - 0.35, zc0], cutaway: true };
        case 'hot_aisle': return { pos: [intL / 2 - 0.9, eye, zh0], look: [-intL / 2, eye - 0.35, zh0], cutaway: true };
        case 'power_room': { const pm = objects.pm ? objects.pm.position.x : -extL / 2 - 6; return { pos: [pm - 9, extH + 4, -11], look: [pm, 1.2, 0], cutaway: true }; }
        case 'roof': { const d = fitDistance(R * 0.7), v = new THREE.Vector3(-0.2, 1.0, 0.6).normalize().multiplyScalar(d); return { pos: [centre[0] + v.x, extH + v.y, centre[2] + v.z], look: [centre[0], extH, centre[2]], cutaway: false }; }
        default: { const d = fitDistance(R * 0.95), v = new THREE.Vector3(-0.7, 0.42, 0.95).normalize().multiplyScalar(d); return { pos: [centre[0] + v.x, centre[1] + v.y, centre[2] + v.z], look: centre, cutaway: false }; }
      }
    }
    if (G.micro && name !== 'exterior_iso' && name !== 'roof') { // a cabinet: look in from outside with the shell ghosted
      const side = name === 'hot_aisle' ? 1 : -1;
      if (name === 'power_room') return { pos: [-extL / 2 - 1.9, extH * 0.8, -extW * 0.6], look: [-intL / 2 + 0.3, floorTop + 0.45, 0], cutaway: true, doors: true };
      return { pos: [extL * 0.4, extH * 0.85, side * (extW / 2 + 1.7)], look: [0, floorTop + G.rackH * 0.5, 0], cutaway: true };
    }
    switch (name) {
      case 'cold_aisle': return { pos: [-intL / 2 + G.bayL + 0.15, eye, zc], look: [intL / 2, eye - 0.35, zc], cutaway: true };
      case 'hot_aisle': return { pos: [intL / 2 - 0.25, eye, zh + G.hotW * 0.2], look: [-intL / 2, eye - 0.35, zh + G.hotW * 0.1], cutaway: true };
      case 'power_room': return G.micro ? { pos: [-intL / 2 + 0.3, eye - 0.3, -0.2], look: [-intL / 2 + 0.1, floorTop + 0.6, intW / 2], cutaway: true }
        : { pos: [-intL / 2 + G.bayL + 2.6, extH + 1.1, -(intW / 2 + 1.9)], look: [-intL / 2 + 0.45, floorTop + 0.9, 0.1], cutaway: true };
      case 'roof': { const d = fitDistance(R * 0.62), v = new THREE.Vector3(-0.25, 1.0, 0.75).normalize().multiplyScalar(d); return { pos: [centre[0] + v.x, extH + v.y, v.z], look: [centre[0], extH, 0], cutaway: false }; }
      default: { const d = fitDistance(R), v = new THREE.Vector3(-0.78, 0.48, 0.95).normalize().multiplyScalar(d); return { pos: [centre[0] + v.x, centre[1] + v.y, v.z], look: centre, cutaway: false }; }
    }
  }
  function setCamera(name, instant = false) {
    if (!payload) return;
    exitWalk(); tour.stop(false);
    mode.camera = name;
    const pose = presetPose(name);
    mode.cutaway = pose.cutaway;
    if (pose.doors !== undefined) mode.doors = pose.doors; else if (G.micro) mode.doors = false;
    if (state) update(state);
    applyCutaway();
    flyTo(new THREE.Vector3(...pose.pos), new THREE.Vector3(...pose.look), instant || reduce ? 0 : 0.9);
    notify();
  }
  function flyTo(pos, look, dur) {
    orbit.enabled = true;
    if (dur <= 0) { camera.position.copy(pos); orbit.target.copy(look); camera.lookAt(look); orbit.update(); camTween = null; return; }
    camTween = { p0: camera.position.clone(), l0: orbit.target.clone(), p1: pos, l1: look, t: 0, dur };
  }
  function ghost(mesh, on) { // transparent but still casting shadows, so the interior keeps its indoor lighting
    if (!mesh) return;
    const m = mesh.material; m.transparent = true; m.opacity = on ? 0.06 : 1; m.depthWrite = !on; mesh.renderOrder = on ? 5 : 0;
  }
  function applyCutaway() {
    ghost(roof, mode.cutaway);
    if (G.hall && G.pmRoof) { ghost(G.pmRoof, mode.cutaway); for (const w of G.pmWalls || []) ghost(w, mode.cutaway && camera.position.y > G.extH * 0.6); }
    const inside = Math.abs(camera.position.z) < G.extW / 2 && Math.abs(camera.position.x) < G.extL / 2 && camera.position.y < G.extH;
    const near = camera.position.z >= 0 ? wallPos : wallNeg, far = near === wallPos ? wallNeg : wallPos;
    ghost(near, mode.cutaway && !inside); ghost(far, false);
    for (const dcl of decals) dcl.visible = !(mode.cutaway && !inside && ((dcl.position.z > 0) === (camera.position.z >= 0)));
  }
  function toggleCutaway() { mode.cutaway = !mode.cutaway; applyCutaway(); notify(); return mode.cutaway; }
  function toggleDoors() { mode.doors = !mode.doors; if (state) update(state); notify(); return mode.doors; }
  function notify() { api.onModeChange && api.onModeChange({ ...mode }); }

  // --------------------------------------------------------------------------- walkthrough
  const keys = new Set(); const vel = new THREE.Vector3(); const walkPos = new THREE.Vector3();
  document.addEventListener('keydown', (e) => { if (mode.walk) keys.add(e.code); });
  document.addEventListener('keyup', (e) => keys.delete(e.code));
  walk.addEventListener('unlock', () => { if (mode.walk && !walkNoLock) exitWalk(); });
  let walkNoLock = false;
  function enterWalk({ lock = true } = {}) {
    if (!payload) return; tour.stop(false); setHover(null);
    mode.walk = true; mode.cutaway = true; orbit.enabled = false; walkNoLock = !lock;
    const eye = G.floorTop + 1.7;
    const zc = G.hall ? G.rowZ[0] - (G.rackD / 2 + G.aisleW / 2) : G.zOff - (G.rackD / 2 + G.coldW / 2);
    if (G.micro) { camera.position.set(-G.extL / 2 - 1.5, eye, 0); camera.lookAt(0, G.floorTop + 0.8, 0); }
    else { camera.position.set(-G.intL / 2 + G.bayL + 0.3 + (G.hall ? 0.6 : 0), eye, zc); camera.lookAt(G.intL / 2, eye - 0.2, zc); }
    if (lock) { try { walk.lock(); } catch (_) { /* headless */ } }
    if (walkHint) walkHint.hidden = false;
    applyCutaway(); notify();
  }
  function exitWalk() {
    if (!mode.walk) return;
    mode.walk = false; keys.clear(); if (walk.isLocked) walk.unlock();
    orbit.enabled = true; orbit.target.copy(camera.position).add(camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(3)); orbit.update();
    if (walkHint) walkHint.hidden = true;
    notify();
  }
  function toggleWalk() { mode.walk ? exitWalk() : enterWalk(); }
  const obstacles = () => [...racks.map(r => r.userData.body), ...coolingUnits.map(u => u.userData.body).filter(b => b.userData.type === 'cooling' || b.userData.type === 'cdu'), ...(G.hall ? [] : [objects.ups, objects.battery]), objects.cdu].filter(Boolean);
  const bb = new THREE.Box3();
  function collide(p) {
    const m = 0.22;
    if (G.micro) { // outdoor cabinet: walk the pad, the cabinet is the obstacle
      p.x = THREE.MathUtils.clamp(p.x, -4, 4); p.z = THREE.MathUtils.clamp(p.z, -4, 4);
      return !(Math.abs(p.x) < G.extL / 2 + m && Math.abs(p.z) < G.extW / 2 + m);
    }
    p.x = THREE.MathUtils.clamp(p.x, -G.intL / 2 + m, G.intL / 2 - m);
    p.z = THREE.MathUtils.clamp(p.z, -G.intW / 2 + m, G.intW / 2 - m);
    for (const o of obstacles()) { bb.setFromObject(o).expandByScalar(m); if (bb.containsPoint(p)) return false; }
    return true;
  }
  function stepWalk(dt) {
    const run = keys.has('ShiftLeft') || keys.has('ShiftRight');
    const sp = (run ? 3.2 : 1.6);
    const f = (keys.has('KeyW') || keys.has('ArrowUp') ? 1 : 0) - (keys.has('KeyS') || keys.has('ArrowDown') ? 1 : 0);
    const r = (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) - (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0);
    if (!f && !r) return;
    const dir = camera.getWorldDirection(new THREE.Vector3()); dir.y = 0; dir.normalize();
    const right = new THREE.Vector3().crossVectors(dir, new THREE.Vector3(0, 1, 0));
    const prev = camera.position.clone();
    walkPos.copy(camera.position).addScaledVector(dir, f * sp * dt);
    if (collide(walkPos)) camera.position.x = walkPos.x, camera.position.z = walkPos.z;
    walkPos.copy(camera.position).addScaledVector(right, r * sp * dt);
    if (collide(walkPos)) camera.position.x = walkPos.x, camera.position.z = walkPos.z;
    camera.position.y = (G.micro ? 0 : G.floorTop) + 1.7;
    void prev;
  }

  // --------------------------------------------------------------------------- guided tour
  let tourWantsDoors = false;
  const tour = { running: false, t: 0, total: 0, stops: [], curve: null, lookCurve: null,
    start() { if (!payload) return; exitWalk(); orbit.enabled = false; this.running = true; this.t = 0; mode.tour = true; mode.cutaway = true; applyCutaway(); this.apply(0); notify(); },
    stop(doNotify = true) { if (!this.running) { tourWantsDoors = false; return; } this.running = false; mode.tour = false; tourWantsDoors = false; if (caption) caption.hidden = true; orbit.enabled = true; orbit.target.copy(camera.position).add(camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(4)); orbit.update(); if (state) update(state); if (doNotify) notify(); },
    toggle() { this.running ? this.stop() : this.start(); },
    seek(frac) { if (!this.running) this.start(); this.t = THREE.MathUtils.clamp(frac, 0, 0.9999) * this.total; this.apply(this.t); },
    apply(t) {
      const u = this.total ? t / this.total : 0;
      if (reduce) { // discrete hops, no motion
        const k = Math.min(this.stops.length - 1, Math.floor(u * this.stops.length)); const s = this.stops[k];
        camera.position.copy(s.pos); camera.lookAt(s.look);
      } else {
        camera.position.copy(this.curve.getPointAt(u)); camera.lookAt(this.lookCurve.getPointAt(u));
      }
      const k = Math.min(this.stops.length - 1, Math.floor(u * this.stops.length)); const s = this.stops[k];
      tourWantsDoors = !!s.doors;
      if (caption) { caption.hidden = false; caption.innerHTML = `<b>${k + 1} / ${this.stops.length} · ${s.title}</b>${s.text}`; }
      applyCutaway();
    },
    step(dt) { if (!this.running) return; this.t += dt; if (this.t >= this.total) { this.stop(); return; } this.apply(this.t); },
  };
  function buildTour(cfg, d) {
    const { extL, extW, extH, intL, intW, rackD, floorTop } = G; const eye = floorTop + 1.6;
    const zc = G.zOff - (rackD / 2 + G.coldW / 2), zh = G.zOff + rackD / 2 + G.hotW / 2;
    const st = state || {};
    const hz = `${d.hardening_label || cfg.hardening || 'H1'}: ${d.hardening_rating || 'NEMA 4X / IP66'}`;
    if (G.hall) {
      const z0 = G.rowZ[0], zc0 = z0 - (rackD / 2 + G.aisleW / 2), zh0 = z0 + rackD / 2 + G.aisleW / 2, pmX = objects.pm ? objects.pm.position.x : -extL / 2 - 6;
      const stops = [
        { title: `${d.tier_label} · prefabricated data hall`, text: `${cfg.it_kw} kW IT in ${cfg.racks} racks over ${G.rows} rows of ${G.rpr}, ${G.modules} site-joined wide-body modules, a separate power module and a plant yard. ${d.cooling_label}, ${cfg.redundancy}. Gross mass ${d.gross_kg.toLocaleString()} kg.`, pos: [-extL * 0.9, extH * 2.5 + 4, extW * 2.2 + 14], look: [-4, extH * 0.4, 2] },
        { title: 'Envelope and hardening', text: `IP66 envelope on a slab with grade beams; module seams are site-welded and sealed. ${hz}. ${G.hardening === 'H3' ? 'Secure vestibule / mantrap at the entry, ballistic wall panels.' : G.hardening === 'H2' ? 'Flood plinth 600 mm, C5-M coating, hurricane-rated doors.' : 'Keyed access, door contacts, positive-pressure interior.'}`, pos: [-extL / 2 - 7, eye + 1.5, -extW * 0.6], look: [-extL / 2, floorTop + 1.5, 0], doors: true },
        { title: 'Cold aisle, row 1', text: `Supply air at 20 °C set-point feeds the rack inlets; three inlet sensors per rack with U95 ±0.25 °C. Four rows share the fan-wall supply along the long wall.`, pos: [-intL / 2 + 0.9, eye, zc0], look: [intL / 2, eye - 0.4, zc0], doors: true },
        { title: 'Compute module', text: `${cfg.racks} × ${d.geometry.rack_u}U racks at ${d.per_rack_kw} kW each, direct liquid cooled from overhead manifolds; the busway feeds every rack PDU. Server fronts glow with PDU load.`, pos: [0, extH + 2.5, -intW * 0.9], look: [2, floorTop + 1.0, 0], doors: true },
        { title: 'CDU row and fan wall', text: `${d.cooling_units_total} × CDU (${d.cooling_units_n} duty + standby, N+1) along the north wall take ~70 % of the heat to liquid; fan-wall units along the south wall handle the air-side residual.`, pos: [intL / 2 - 1.0, eye, zh0], look: [-intL / 2, eye - 0.4, zh0] },
        { title: 'Power module', text: `${d.voltage}: ${d.transformers_total} × ${(d.transformer_kva || 2500).toLocaleString()} kVA pad-mount transformers → 480 V switchgear → ${d.ups_modules} × ${d.ups_kva_each.toLocaleString()} kVA UPS strings (2N) → busway. ${d.battery_kwh.toLocaleString()} kWh LFP in a separate battery room (NFPA 855).`, pos: [pmX - 10, extH + 5, -12], look: [pmX, 1.2, 0] },
        { title: 'Generators and plant yard', text: `${d.generators_total} × ${d.generator_kw_each.toLocaleString()} kW generators (N+1) with 48 h fuel; ${d.cooling_units_total} adiabatic dry coolers reject ${cfg.it_kw} kW at a ${d.climate.t_design_c} °C design day, water-free mode available.`, pos: [extL * 0.3, extH + 6, extW / 2 + 16], look: [0, 1.5, extW / 2 + 4] },
        { title: 'Controls module', text: `BEN Controls Pro: redundant edge computers, one PLC per module plus a plant PLC, ${d.pods} BEN Pods on a BEN Mesh with multiple border routers. Every sphere is a sensor coloured by its live value.`, pos: [-intL / 2 + 2.5, eye, zc0], look: [-intL / 2 + 0.6, floorTop + 1.6, -intW / 2] },
        { title: 'Ready for site', text: `Predicted PUE ${d.pue_estimate}. Order-to-service about 52 weeks: MV transformers and 2 MW UPS strings are the long-lead items; slab and MV service run in parallel.`, pos: [extL * 0.8, extH * 2.2 + 3, -(extW * 2 + 12)], look: [-4, extH * 0.4, 2] },
      ].map(s => ({ ...s, pos: new THREE.Vector3(...s.pos), look: new THREE.Vector3(...s.look) }));
      tour.stops = stops;
      tour.curve = new THREE.CatmullRomCurve3(stops.map(s => s.pos), false, 'centripetal', 0.3);
      tour.lookCurve = new THREE.CatmullRomCurve3(stops.map(s => s.look), false, 'centripetal', 0.3);
      tour.total = reduce ? stops.length * 4 : 7.5 * stops.length;
      return;
    }
    const stops = [
      { title: `${d.tier_label} · ${d.enclosure}`, text: `${cfg.it_kw} kW IT in ${cfg.racks} rack${cfg.racks > 1 ? 's' : ''}, ${d.cooling_label}, ${cfg.redundancy} redundancy. Gross mass ${d.gross_kg} kg.`, pos: [-extL * 0.75, extH * 1.1 + 1, extW * 1.5 + extL * 0.4 + 2], look: [0, extH * 0.45, 0] },
      { title: 'Envelope and entry', text: `${G.micro ? 'NEMA 4X / IP66 cabinet on a skid' : 'ISO corner castings, 100 mm PIR insulation, sealed to IP66'}, corrosion class ${d.climate.corrosion}, wind ${d.climate.wind_ms} m/s. ${hz}. Doors open on a reed contact; the twin raises a warning when they do.`, pos: [-extL / 2 - 2.8, eye + 0.3, -extW * 0.4], look: [-extL / 2, floorTop + 1.2, 0], doors: true },
      { title: 'Cold aisle', text: `Supply air at ${d.climate ? '20' : ''} °C set-point feeds the rack inlets; three inlet sensors per rack (0.4, 1.2, 1.8 m) with U95 ±0.25 °C. Containment keeps the aisle at a measured ΔP.`, pos: G.micro ? [extL * 0.4, extH * 0.85, -(extW / 2 + 1.7)] : [-intL / 2 + G.bayL + 0.3, eye, zc], look: G.micro ? [0, floorTop + 0.7, 0] : [intL / 2, eye - 0.4, zc], doors: true },
      { title: 'Compute module', text: `${cfg.racks} × ${d.geometry.rack_u}U racks at ${d.per_rack_kw} kW each. Server fronts glow with the PDU load; a red plate marks a rack with an active alarm.`, pos: G.micro ? [0.3, extH * 0.8, -(extW / 2 + 1.2)] : [0, eye, zc - G.coldW * 0.25], look: G.micro ? [0, floorTop + 0.6, 0] : [0.3, eye - 0.5, G.zOff], doors: true },
      { title: 'Hot aisle and cooling module', text: `${d.cooling_units_total} × ${d.cooling_label} (${d.cooling_units_n} duty + standby). Return air at supply + 12 K drives the fans; particles move at fan speed and take the colour of the air.`, pos: G.micro ? [extL * 0.4, extH * 0.85, extW / 2 + 1.7] : [intL / 2 - 0.3, eye, zh + G.hotW * 0.2], look: G.micro ? [0, floorTop + 0.7, 0] : [-intL / 2, eye - 0.4, zh] },
      { title: 'Power module', text: `${d.voltage}, ${d.service_breaker_a} A service → ATS → ${d.ups_modules} × ${d.ups_kva_each} kVA UPS → distribution → PDUs. ${d.battery_kwh} kWh LFP battery for ${cfg.ups_minutes} min${cfg.generator ? ', generator ready' : ''}. Pulses run at kW, turn amber on battery.`, pos: G.micro ? [-extL / 2 - 1.6, extH * 0.9, -extW * 0.9] : [-intL / 2 + G.bayL + 2.4, extH + 1.0, -(intW / 2 + 1.7)], look: G.micro ? [-intL / 2 + 0.2, floorTop + 0.35, 0.1] : [-intL / 2 + 0.45, floorTop + 0.9, 0.1] },
      { title: 'Controls module', text: `BEN Controller (PLC + industrial edge computer running ben_engine; a Revolution Pi on the BEN 5) with BEN Pods on the BEN Mesh, an isolated Thread/IPv6 network. Every sphere is a sensor coloured by its live value; click one for id, uncertainty, Pod and timestamp.`, pos: G.micro ? [-0.2, extH * 0.9, -(extW / 2 + 1.3)] : [-intL / 2 + 1.8, eye, zc], look: G.micro ? [-intL / 2 + 0.2, floorTop + 1.2, -intW / 2] : [-intL / 2 + 0.5, floorTop + 1.6, -intW / 2] },
      { title: G.air ? 'Roof and heat rejection' : 'Heat rejection', text: G.air ? 'In-row DX units reject heat through condensers on the roof pad. CSC plate stays valid: no structural cuts.' : `Dry coolers on the roof reject ${cfg.it_kw} kW at a design day of ${d.climate.t_design_c} °C through a glycol loop to the CDU.`, pos: [-extL * 0.25, extH + Math.max(3, extL * 0.3), extW * 1.4 + 2], look: [0, extH, 0] },
      { title: 'Ready for site', text: `Predicted PUE ${d.pue_estimate}. The same configuration drives the BOM, drawings, commissioning script and this twin.`, pos: [extL * 0.7, extH * 1.1 + 1, -(extW * 1.5 + extL * 0.4 + 2)], look: [0, extH * 0.45, 0] },
    ].map(s => ({ ...s, pos: new THREE.Vector3(...s.pos), look: new THREE.Vector3(...s.look) }));
    tour.stops = stops;
    tour.curve = new THREE.CatmullRomCurve3(stops.map(s => s.pos), false, 'centripetal', 0.3);
    tour.lookCurve = new THREE.CatmullRomCurve3(stops.map(s => s.look), false, 'centripetal', 0.3);
    tour.total = reduce ? stops.length * 4 : 7.5 * stops.length;
    void st;
  }

  // --------------------------------------------------------------------------- loop
  const clock = new THREE.Clock();
  function resize() {
    const parent = canvas.parentElement; const w = parent.clientWidth || 800, hgt = parent.clientHeight || 500;
    if (canvas.width !== Math.round(w * renderer.getPixelRatio()) || canvas.height !== Math.round(hgt * renderer.getPixelRatio())) { renderer.setSize(w, hgt, false); camera.aspect = w / hgt; camera.updateProjectionMatrix(); }
  }
  new ResizeObserver(resize).observe(canvas.parentElement);
  let pulse = 0;
  function frame() {
    const dt = Math.min(0.1, clock.getDelta());
    resize();
    if (camTween) { camTween.t += dt; const k = Math.min(1, camTween.t / camTween.dur), e = k * k * (3 - 2 * k); camera.position.lerpVectors(camTween.p0, camTween.p1, e); orbit.target.lerpVectors(camTween.l0, camTween.l1, e); if (k >= 1) camTween = null; }
    if (mode.walk) stepWalk(dt); else if (tour.running) tour.step(dt); else orbit.update();
    // doors
    for (const l of doorLeaves) { const target = (l.target || 0) * THREE.MathUtils.degToRad(125) * -l.side; const cur = l.hinge.rotation.y; l.hinge.rotation.y = reduce ? target : cur + (target - cur) * Math.min(1, dt * 3); }
    // fans
    if (!reduce) for (const u of dryCoolers) for (const f of u.userData.fans || []) f.rotation.y += dt * 6 * ((u.userData.fanPct || 0) / 100);
    if (!reduce) for (const u of coolingUnits) if (u.userData.fan) u.userData.fan.rotation.z += dt * 8 * ((u.userData.fanPct || 0) / 100);
    placeParticles(dt);
    for (const f of flows) f.update(dt);
    pulse += dt * 3;
    const op = reduce ? 0.9 : 0.55 + 0.4 * Math.sin(pulse);
    for (const h of highlights.values()) h.material.opacity = op;
    if (mode.cutaway) applyCutaway();
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  Object.assign(api, {
    rebuild, update, setCamera, toggleWalk, enterWalk, exitWalk, toggleCutaway, toggleDoors, tour, setSelection,
    render: () => renderer.render(scene, camera),
    screenPositionOf, hoverCycle, hoverSelect, hoverList, clearHover: () => setHover(null), setHoverByKey(k) { const h = hoverList().find(x => x.key === k); if (h) setHover(h, screenPositionOf(h) || { x: 0, y: 0 }, 'keyboard'); return !!h; },
    setPixelRatio(r) { renderer.setPixelRatio(r); resize(); renderer.render(scene, camera); return renderer.getPixelRatio(); },
    rackCount: () => racks.length, coolingCount: () => coolingUnits.length, sensorCount: () => sensorMeshes.size, dryCoolerCount: () => dryCoolers.length,
    rowCount: () => (G.rowZ || []).length, hallObjects: () => ({ powermodule: !!objects.pm, transformers: pickables.filter(o => o.userData && o.userData.type === 'transformer').length, generators: pickables.filter(o => o.userData && o.userData.type === 'generator').length, fanwalls: pickables.filter(o => o.userData && o.userData.type === 'fanwall').length, plinth: !!objects.plinth, vestibule: !!objects.vestibule }),
    mode, camera, objects, G,
    focus(sel) { // orbit camera to an object
      const obj = targetObject(sel); if (!obj) return; const c = new THREE.Box3().setFromObject(obj).getCenter(new THREE.Vector3());
      mode.cutaway = true; applyCutaway(); const dir = new THREE.Vector3(0.6, 0.5, -1).normalize(); exitWalk(); tour.stop(false);
      flyTo(c.clone().addScaledVector(dir, 3), c, reduce ? 0 : 0.8); setSelection(sel); notify();
    },
  });
  return api;
}
