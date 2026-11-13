// BEN Engine 3D digital twin scene (three.js, vendored, no CDN).
// Built procedurally from the configuration + /api/sensors; animated from live twin state.
import * as THREE from './vendor/three/three.module.js';
import { OrbitControls } from './vendor/three/OrbitControls.js';
import { PointerLockControls } from './vendor/three/PointerLockControls.js';
import { tempColor, lerpColor, reducedMotion } from './util.js';
import { liveryInfo, sideTexture, miniPanelTexture, bezelTexture, bandPlateTexture, resetLivery, BODY, LV } from './livery.js';
import * as EQ from './equipment.js';
const { EM, Parts, faceBox } = EQ;

// Schreiber AI brand v2 (brand/v2/tokens.json). One job per colour: cyan = Signal Blue (selection, hover, edges); hold / red / green /
// info = status (alarms, LEDs) only; heat (aisles, airflow, pipes, temperature sensors) uses the thermal ramp, never amber.
// `amber` is kept as a Rev 1 key name and now means Hold (caution), as in util.js BRAND.
const C = { graphite: 0x06101f, slate: 0x0b1a31, panel: 0x0f2342, text: 0xeef4fc, muted: 0x8ea7c8, cyan: 0x4c9dff, amber: 0xf2c94c, hold: 0xf2c94c, red: 0xff6369, green: 0x2bb673, info: 0x5cd6ff };
const T = { cool: 0x5cd6ff, warm: 0xff8a3d };   // thermal ramp ends (tokens --thermal-cool / --thermal-warm)
// Rev 1 shell paint, kept so a saved Rev 1 configuration renders as it did (docs/REVISION_POLICY.md).
const REV1 = { body: 0x2a3c5c, wl: 0x6b7a90, hall: 0x34496b, cab: 0x9aa5b8, pm: 0x2f4262 };
const U_M = 0.04445;

// ----------------------------------------------------------------------------- materials
const MAT = {
  shell: (color) => { const m = new THREE.MeshStandardMaterial({ color, roughness: 0.5, metalness: 0.35 }); m.userData.env = true; m.userData.envI = 0.45; return m; },
  liner: new THREE.MeshStandardMaterial({ color: 0x97a2b3, roughness: 0.95, metalness: 0.0, side: THREE.BackSide }),
  linerPanel: new THREE.MeshStandardMaterial({ color: 0xd3d8de, roughness: 0.8, metalness: 0.05 }),
  section: new THREE.MeshStandardMaterial({ color: 0xe9d9a6, roughness: 0.95 }),
  floor: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.78, metalness: 0.05 }),
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
  ground: new THREE.MeshStandardMaterial({ color: 0x1a222c, roughness: 1 }),
  pad: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.92 }),
  pipeCold: new THREE.MeshStandardMaterial({ color: 0x5cd6ff, roughness: 0.4, metalness: 0.6 }),
  pipeHot: new THREE.MeshStandardMaterial({ color: 0xff8a3d, roughness: 0.4, metalness: 0.6 }),
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

/** Corrugated wall: plane facing +z with an ISO trapezoid profile along x (crisp facets: non-indexed normals). */
function corrugatedWall(len, height, color, period = 0.278, depth = 0.036) {
  const flat = depth <= 0;
  const segs = flat ? 1 : Math.max(8, Math.round(len / period) * 4);
  let g = new THREE.PlaneGeometry(len, height, segs, 1);
  if (!flat) {
    const pos = g.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i) + len / 2;
      const ph = (x % period) / period;
      const prof = ph < 0.18 ? ph / 0.18 : ph < 0.5 ? 1 : ph < 0.68 ? 1 - (ph - 0.5) / 0.18 : 0;
      pos.setZ(i, prof * depth - depth / 2);
    }
    g = g.toNonIndexed(); g.computeVertexNormals();
  }
  const m = new THREE.Mesh(g, MAT.shell(color));
  m.castShadow = true; m.receiveShadow = true;
  return m;
}

/** Rev 1 decal: the SAI monogram + tier for the container side. Used only for configurations with lineup rev1 (history);
 *  Rev 2 configurations get the livery from livery.js. Colours here are the Rev 1 ones on purpose. */
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
    for (let k = 0; k < leds; k++) { g.fillStyle = k === 0 ? '#2BB673' : (rnd() < 0.7 ? '#4C9DFF' : '#F2C94C'); g.fillRect(88 + k * 9, y + hgt / 2 - 2, 4, 4); }
    u += size;
  }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.minFilter = THREE.LinearMipmapLinearFilter;
  return t;
}

// ----------------------------------------------------------------------------- point sprites (airflow, power pulses)
// Screen-size-clamped round points: world size with perspective, but never larger than maxPx on screen, and faded out
// close to the camera, so particles stay small, crisp dots in aisle and walkthrough views instead of out-of-focus balls.
const PT = { scale: { value: 600 }, pr: { value: 1 } };
function pointsMaterial({ color = 0xffffff, size = 0.02, maxPx = 5, opacity = 0.8, fadeNear = 0.5, vertexColors = false } = {}) {
  return new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uSize: { value: size }, uMaxPx: { value: maxPx }, uOpacity: { value: opacity }, uFadeNear: { value: fadeNear }, uScale: PT.scale, uPr: PT.pr },
    vertexColors, transparent: true, depthWrite: false,
    vertexShader: `uniform float uSize; uniform float uScale; uniform float uMaxPx; uniform float uPr; uniform float uFadeNear; varying float vFade; varying vec3 vCol;
      void main() { vec4 mv = modelViewMatrix * vec4(position, 1.0); float d = max(0.01, -mv.z);
        gl_PointSize = clamp(uSize * uScale / d, 1.0 * uPr, uMaxPx * uPr); vFade = smoothstep(uFadeNear, uFadeNear * 3.0, d);
        #ifdef USE_COLOR
        vCol = color;
        #else
        vCol = vec3(1.0);
        #endif
        gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform vec3 uColor; uniform float uOpacity; varying float vFade; varying vec3 vCol;
      void main() { float r = length(gl_PointCoord - 0.5); if (r > 0.5) discard; float a = smoothstep(0.5, 0.3, r) * uOpacity * vFade; if (a < 0.01) discard;
        gl_FragColor = vec4(uColor * vCol, a);
        #include <colorspace_fragment>
      }`,
  });
}

// ----------------------------------------------------------------------------- flow lines (power)
class Flow {
  constructor(points, { n = 14, color = C.green, size = 0.09 } = {}) {
    this.pts = points; this.n = n;
    this.len = [0]; for (let i = 1; i < points.length; i++) this.len.push(this.len[i - 1] + points[i].distanceTo(points[i - 1]));
    this.total = this.len[this.len.length - 1];
    this.s = new Float32Array(n).map((_, i) => i / n * this.total);
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    this.points = new THREE.Points(geo, pointsMaterial({ color, size: size * 0.45, maxPx: 7, opacity: 0.95, fadeNear: 0.6 }));
    this.line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.25 }));
    this.group = new THREE.Group(); this.group.add(this.line, this.points);
    this.speed = 0.6; this.active = true; this.place();
  }
  setColor(c) { this.points.material.uniforms.uColor.value.setHex(c); this.line.material.color.setHex(c); }
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

/** Procedural studio room for image-based lighting (after three's RoomEnvironment): a dim box with a few emissive panels. */
function studioRoom() {
  const env = new THREE.Scene();
  const geo = new THREE.BoxGeometry();
  const room = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ side: THREE.BackSide, color: 0x6b7480, roughness: 1 }));
  room.position.set(-0.757, 13.219, 0.717); room.scale.set(31.713, 28.305, 28.591); env.add(room);
  const boxMat = new THREE.MeshStandardMaterial({ color: 0x3a4048, roughness: 1 });
  for (const [p, s, r] of [[[-10.906, 2.009, 1.846], [2.328, 7.905, 4.651], -0.244], [[-5.607, -0.754, -0.758], [1.97, 1.534, 3.955], 0.994], [[6.167, 0.857, 7.803], [3.927, 6.285, 3.687], 0.561], [[-2.017, 0.018, 6.124], [2.002, 4.566, 2.064], 0.4]]) {
    const b = new THREE.Mesh(geo, boxMat); b.position.set(...p); b.scale.set(...s); b.rotation.y = r; env.add(b);
  }
  const light = (i) => new THREE.MeshBasicMaterial({ color: new THREE.Color(1, 1, 1).multiplyScalar(i) });
  for (const [p, s, i] of [[[-16.116, 14.37, 8.208], [0.1, 2.428, 2.739], 50], [[-16.109, 18.021, -8.207], [0.1, 2.425, 2.751], 50], [[14.904, 12.198, -1.832], [0.15, 4.265, 6.331], 17], [[-0.462, 8.89, 14.52], [4.38, 5.441, 0.088], 43], [[3.235, 11.486, -12.541], [2.5, 2.0, 0.1], 20], [[0.0, 20.0, 0.0], [1.0, 0.1, 1.0], 100]]) {
    const l = new THREE.Mesh(geo, light(i)); l.position.set(...p); l.scale.set(...s); env.add(l);
  }
  return env;
}

// ----------------------------------------------------------------------------- scene factory
export function createScene(canvas, { onSelect, caption, walkHint } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.shadowMap.autoUpdate = false;   // the sun is static: re-render the shadow map only when geometry, doors or the cutaway change
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  // Contrast first: a moderate exposure with ACES keeps whites below clipping and darks dark (high exposure + fog read as blur).
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.92;
  EQ.setAnisotropy(renderer.capabilities.getMaxAnisotropy());
  MAT.floor.map = EQ.floorTex([6, 1.2]); MAT.pad.map = EQ.concreteTex([5, 2]); MAT.linerPanel.map = EQ.linerTex([10, 1]); MAT.section.map = EQ.insulationTex();
  MAT.ground.map = EQ.gravelTex([60, 60]); MAT.ground.color.setHex(0x59606a);

  const scene = new THREE.Scene();
  // Linear fog only far away, for the ground falloff around the site; nothing inside the enclosure is ever fogged.
  scene.fog = new THREE.Fog(0x06101f, 60, 220);
  // Image-based lighting: a procedural studio room (RoomEnvironment-style) prefiltered with PMREM, so metal reads as metal.
  // Applied per material to the metal parts only (pipes, chrome, galvanised steel, castings, the shell): prefiltered env lookups
  // are expensive on software GL, and matte paint gains little from them.
  const envTex = (() => { const pm = new THREE.PMREMGenerator(renderer); const t = pm.fromScene(studioRoom(), 0.04).texture; pm.dispose(); return t; })();
  function applyEnv(root) {
    root.traverse(o => { if (!o.material) return; for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (m.isMeshStandardMaterial && !m.envMap && (m.metalness >= 0.55 || m.userData.env)) { m.envMap = envTex; m.envMapIntensity = m.userData.envI || 0.7; m.needsUpdate = true; }
    } });
  }
  const camera = new THREE.PerspectiveCamera(50, 1, 0.03, 400);
  camera.position.set(8, 5, 10);
  const orbit = new OrbitControls(camera, canvas);
  orbit.enableDamping = true; orbit.dampingFactor = 0.08; orbit.maxPolarAngle = Math.PI * 0.495; orbit.minDistance = 0.5; orbit.maxDistance = 80;
  const walk = new PointerLockControls(camera, canvas);

  // lights
  scene.add(new THREE.HemisphereLight(0xcfe0ff, 0x2a2f36, 0.7));
  const sun = new THREE.DirectionalLight(0xfff1dd, 2.4);
  sun.position.set(12, 16, 8); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -16; sun.shadow.camera.right = 16; sun.shadow.camera.top = 16; sun.shadow.camera.bottom = -16; sun.shadow.bias = -0.0005;
  scene.add(sun);
  const fill = new THREE.DirectionalLight(0x9fd8ff, 0.3); fill.position.set(-10, 6, -8); scene.add(fill);
  const back = new THREE.DirectionalLight(0xffffff, 0.2); back.position.set(6, 5, -12); scene.add(back);
  const interiorLights = new THREE.Group(); scene.add(interiorLights);

  // ground
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), MAT.ground); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const grid = new THREE.GridHelper(120, 60, 0x2a3442, 0x222a35); grid.position.y = 0.003; grid.material.transparent = true; grid.material.opacity = 0.35; scene.add(grid);

  // model state
  const G = {}; // geometry numbers for the current config
  let payload = null, state = null;
  const groups = { shell: new THREE.Group(), compute: new THREE.Group(), cooling: new THREE.Group(), power: new THREE.Group(), controls: new THREE.Group(), fx: new THREE.Group(), hl: new THREE.Group() };
  for (const g of Object.values(groups)) scene.add(g);
  const objects = {}; // key -> Object3D (rack1, cooling1, ups, battery, ats, panel, gateway, doors, drycooler1, cdu, tray, sensor:<id>)
  let pickables = [];
  const solids = [];   // interior obstacles (equipment bodies, pipes): camera clearance + walkthrough collision
  const racks = [], coolingUnits = [], dryCoolers = [], sensorMeshes = new Map(), flows = [];
  let particles = null, doorLeaves = [], roof = null, wallPos = null, wallNeg = null, decals = [];
  let livery = null;   // Rev 2 livery facts of the current build (lineup, bandText, bodyColor), exposed for tests
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

  /** Rev 2 liquid-first (BEN 300 / BEN 700): the row is config.derived().row_items at real widths (mm), door end first:
   *  switchboard, battery / UPS, CDUs, then racks with fan coils between them. No separate power bay. */
  function computeDenseLayout(cfg, d) {
    const W = { swbd: 0.915, batt: 0.6, ups: 0.85, rect: 0.6, batt800: 0.6, cdu: 0.6, fancoil: 0.3, rack: 0.6 };
    G.bayL = 0; G.unitW = 0.6; G.rackX = []; G.unitX = []; G.fcX = []; G.powerItems = []; G.wallUnits = 0;
    let x = -G.intL / 2 + 0.02, ri = 0;
    for (const k of d.row_items) {
      const w = W[k] || 0.6, cx = x + w / 2;
      if (k === 'rack') G.rackX[ri++] = cx; else if (k === 'cdu') G.unitX.push(cx); else if (k === 'fancoil') G.fcX.push(cx); else G.powerItems.push({ kind: k, x: cx, w });
      x += w;
    }
    G.inRow = G.unitX.length; G.rowEndX = x;
  }

  /** Pack racks + in-row units (or CDUs) into the row behind the power bay. */
  function computeRowLayout(cfg, d) {
    if (G.hall) return computeHallLayout(cfg, d);
    if (G.dense) return computeDenseLayout(cfg, d);
    const n = cfg.racks;
    G.bayL = G.micro ? 0 : Math.min(1.2, Math.max(0.9, G.intL * 0.18));
    let inRow = 0, unitW = 0.3;
    if (G.air && !G.micro) inRow = d.cooling_units_total;
    else if (G.liquid) { inRow = G.hd ? d.cooling_units_total : Math.min(2, d.cooling_units_total); unitW = 0.6; }
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
    // Rev 2 BEN 2000 = three BEN 700 modules on a shared yard: module 1 is built live from the module numbers (d.module), modules 2..n by
    // the same dense builders shifted across the yard, then the yard (pad-mount transformers, 15 kV switchgear, generators, lanes).
    const clusterD = p.derived.kind === 'cluster' ? p.derived : null;
    const cfg = clusterD ? { ...p.config, tier: clusterD.module_tier, racks: clusterD.module_racks, it_kw: clusterD.module_it_kw } : p.config;
    const d = clusterD ? { ...clusterD.module, geometry: clusterD.geometry, climate: clusterD.climate } : p.derived, geo = d.geometry;
    G.cluster = clusterD;
    const kind = d.kind || geo.kind || (cfg.tier === 'ben5' || cfg.tier === 'micro' ? 'cabinet' : 'module');
    const mini = kind === 'minirack';                       // Rev 2 BEN 1: indoor mini rack in an office corner
    const micro = kind === 'cabinet' || mini, hall = kind === 'hall';
    G.mini = mini; G.dense = !!d.liquid_first; G.form = cfg.form || '';
    ground.visible = grid.visible = !mini;   // BEN 1 stands in an office: no site ground under its floor
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
    if (G.dense) { G.rackD = 1.068; G.zOff = G.intW / 2 - 0.2 - G.rackD / 2; }   // GB300-class 600 x 1068 rack on a 200 mm rear plenum; rack fronts face -z, so the rack wall is +z
    if (hall) G.rackD = 1.2;
    G.aisleW = hall ? (G.intW / (G.rows + 1) - G.rackD) / 2 : (G.intW - G.rackD) / 2;
    G.coldW = G.aisleW + G.zOff; G.hotW = G.aisleW - G.zOff;
    G.pitch = G.intL / (cfg.racks + 1); // twin sensor pitch (twin frame)
    G.subs = new Set(cfg.subsystems);
    G.liquid = d.cooling_label.toLowerCase().includes('liquid') || cfg.cooling === 'dlc_cdu' || cfg.cooling === 'dlc_hd';
    G.hd = cfg.cooling === 'dlc_hd';            // high-density DLC: every CDU is a 600 mm row CDU, manifold drops on every rack
    G.dc800 = (cfg.power_architecture || 'ac480') === 'dc800';   // 800 VDC bus: rectifier / SST cabinet + DC busway instead of UPS frames
    G.water = cfg.cooling === 'rdhx_drycooler';
    G.air = !G.liquid && !G.water;
    computeRowLayout(cfg, d);
    if (!G.hall) { G.rackZ = Array.from({ length: cfg.racks }, () => G.zOff); G.rowZ = [G.zOff]; }

    for (const g of Object.values(groups)) clearGroup(g);
    for (const k of Object.keys(objects)) delete objects[k];
    racks.length = 0; coolingUnits.length = 0; dryCoolers.length = 0; sensorMeshes.clear(); flows.length = 0; doorLeaves = []; decals = []; particles = null; pickables = []; solids.length = 0; G.wallStubs = []; G.caps = []; G.wallMounted = []; G.extraModule = false; G.zoneLabels = null; solidCache = null;
    resetLivery();
    G.rev2 = (cfg.lineup || 'rev1') !== 'rev1';
    livery = G.rev2 ? { ...liveryInfo(cfg, d), bandTexture: false } : { lineup: cfg.lineup || 'rev1', bandText: '', bodyColor: null, bandTexture: false };
    clearGroup(interiorLights);

    if (G.mini) {   // BEN 1: office corner, desk or 12U cabinet, mini-rack contents, Pods; no container, no plant
      buildMinirack(cfg, d, p.sensors || []);
      buildTour(cfg, d);
      sun.shadow.camera.left = -4; sun.shadow.camera.right = 4; sun.shadow.camera.top = 4; sun.shadow.camera.bottom = -4; sun.shadow.camera.updateProjectionMatrix();
      setCamera(mode.camera, true);
      if (state) update(state);
      applyCutaway();
      renderer.shadowMap.needsUpdate = true;
      applyEnv(scene);
      return;
    }
    buildShell(cfg, d);
    buildHardening(cfg, d);
    if (G.hall) buildHallInterior(cfg, d); else buildInterior(cfg, d);
    if (G.subs.has('compute')) buildRacks(cfg, d);
    if (G.subs.has('cooling')) { if (G.hall) buildHallCooling(cfg, d); else buildCooling(cfg, d); }
    if (G.subs.has('power')) { if (G.hall) buildHallPower(cfg, d); else buildPower(cfg, d); }
    const sensorsM = clusterD ? (p.sensors || []).filter(s => { const m = /_r(\d+)/.exec(s.id); return !m || Number(m[1]) <= clusterD.module_racks; }) : (p.sensors || []);
    if (G.subs.has('controls')) buildControls(cfg, d, sensorsM);
    buildFx(cfg, d);
    if (clusterD) buildCluster(cfg, d, clusterD);
    buildZoneLabels(cfg, d);
    buildTour(cfg, d);
    const sh = G.hall ? G.extL * 1.2 : (clusterD ? clusterD.yard.site_l_m * 0.6 : G.extL);
    sun.shadow.camera.left = -sh; sun.shadow.camera.right = sh; sun.shadow.camera.top = sh; sun.shadow.camera.bottom = -sh; sun.shadow.camera.updateProjectionMatrix();
    setCamera(mode.camera, true);
    if (state) update(state);
    applyCutaway();
    renderer.shadowMap.needsUpdate = true;
    applyEnv(scene);
  }

  /** Rev 2 BEN 2000: modules 2..n with the same builders as module 1 (shifted by the yard pitch, -z = site +y), then the shared yard from
   *  config.cluster_yard(): pad-mount transformers, 15 kV switchgear, generators when fitted, the yard slab and the two lanes. Module 1 keeps
   *  the cutaway roof / walls, the sensors and the airflow particles; racks and CDUs of every module are live (twin rack i -> module floor(i / 5)). */
  function buildCluster(cfg, d, cd) {
    const keep = { roof, wallPos, wallNeg }, nStubs = G.wallStubs.length, nCaps = G.caps.length;
    G.extraModule = true;
    const pitch = cd.yard.pitch_mm / 1000;
    const sx = (x) => x / 1000 - G.extL / 2, sz = (y) => -(y / 1000 - G.extW / 2);
    for (let k = 1; k < cd.modules; k++) {
      const before = Object.fromEntries(Object.entries(groups).map(([n, g]) => [n, g.children.length]));
      buildShell(cfg, d); buildHardening(cfg, d); buildInterior(cfg, d);
      if (G.subs.has('compute')) buildRacks(cfg, d);
      if (G.subs.has('cooling')) buildCooling(cfg, d);
      if (G.subs.has('power')) buildPower(cfg, d);
      for (const [n, g] of Object.entries(groups)) for (let i = before[n]; i < g.children.length; i++) g.children[i].position.z -= k * pitch;
    }
    ({ roof, wallPos, wallNeg } = keep); G.wallStubs.length = nStubs; G.caps.length = nCaps; G.extraModule = false;
    const R = cd.yard.rects, g = groups.power;
    const fe = cd.yard.fence, slab = box((fe[2] - fe[0]) / 1000, 0.05, (fe[3] - fe[1]) / 1000, MAT.pad, (sx(fe[0]) + sx(fe[2])) / 2, -0.03, (sz(fe[1]) + sz(fe[3])) / 2);
    slab.castShadow = false; groups.shell.add(slab); objects.yard = slab;
    const asphalt = new THREE.MeshStandardMaterial({ color: 0x2b3038, roughness: 0.95 });
    for (const ln of ['LANE-W', 'LANE-E']) { const r = R[ln]; const m = box((r[2] - r[0]) / 1000, 0.04, (r[3] - r[1]) / 1000, asphalt, (sx(r[0]) + sx(r[2])) / 2, -0.02, (sz(r[1]) + sz(r[3])) / 2); m.castShadow = false; groups.shell.add(m); }
    const xfFront = new THREE.MeshStandardMaterial({ map: EQ.transformerFront(), roughness: 0.55, metalness: 0.3 });
    const mvFront = new THREE.MeshStandardMaterial({ map: EQ.mvSwitchgearFront(), roughness: 0.5, metalness: 0.3 });
    const genSide = new THREE.MeshStandardMaterial({ map: EQ.louvreTex('#3b4656', '#1b2027'), roughness: 0.6, metalness: 0.4 });
    const add = (r, h, kind, type, id, extra = {}) => {
      const w = (r[2] - r[0]) / 1000, dd = (r[3] - r[1]) / 1000, cx = (sx(r[0]) + sx(r[2])) / 2, cz = (sz(r[1]) + sz(r[3])) / 2;
      const P = new Parts(); let m;
      if (kind === 'transformer') {   // pad-mount: tank + front compartment, radiator fins on the sides, lifting lugs, on its own pad
        const tw = w * 0.62, td = dd * 0.7;
        m = new THREE.Mesh(new THREE.BoxGeometry(tw, h, td), mats6(EM.green, { '+z': xfFront, '-z': xfFront }));
        const nf = Math.max(6, Math.round(td / 0.09));
        for (const sxn of [-1, 1]) for (let k = 0; k < nf; k++) P.box(0.32, h * 0.72, 0.025, EM.green, sxn * (tw / 2 + 0.16), -h * 0.06, -td / 2 + 0.06 + k * (td - 0.12) / (nf - 1));
        for (const sxn of [-1, 1]) { P.box(0.05, 0.05, td * 0.9, EM.green, sxn * (tw / 2 + 0.16), h * 0.31, 0); P.box(0.05, 0.05, td * 0.9, EM.green, sxn * (tw / 2 + 0.16), -h * 0.42, 0); }
        for (const sxn of [-1, 1]) for (const szn of [-1, 1]) P.box(0.06, 0.08, 0.02, EM.green, sxn * tw * 0.4, h / 2 + 0.04, szn * td * 0.4);
        P.box(w, 0.15, dd, MAT.pad, 0, -h / 2 - 0.075 + 0.0, 0);
      } else if (kind === 'switchgear') {
        m = new THREE.Mesh(new THREE.BoxGeometry(w, h, dd * 0.8), mats6(EM.equipLight, { '+z': mvFront, '-z': mvFront }));
        P.box(w + 0.1, 0.08, dd * 0.8 + 0.1, EM.equipMid, 0, h / 2 + 0.04, 0); P.box(w, 0.12, dd, MAT.pad, 0, -h / 2 - 0.06, 0);
      } else {   // generator in a sound-attenuated enclosure: louvred sides, exhaust stack, base fuel tank
        m = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.82, dd), mats6(MAT.powerDark, { '+z': genSide, '-z': genSide }));
        P.box(w, h * 0.18, dd, EM.darkSteel, 0, -h * 0.41 - h * 0.09 + 0.0, 0).cyl(0.12, 0.9, EM.steel, -w * 0.3, h * 0.41 + 0.45, 0, 'y', 14);
      }
      m.position.set(cx, kind === 'generator' ? h * 0.18 + h * 0.41 : h / 2 + (kind === 'transformer' ? 0.15 : 0.12), cz); m.castShadow = m.receiveShadow = true;
      P.build(m, { cast: true });
      m.userData = { type, id, ...extra }; g.add(m); pickables.push(m); return m;
    };
    for (let k = 0; k < cd.modules; k++) {
      objects[`transformer${k + 1}`] = add(R[`T${k + 1}`], 1.9, 'transformer', 'transformer', `transformer${k + 1}`, { index: k, label: `T${k + 1} ${cd.transformer_kva.toLocaleString()} kVA, 12.47 kV–480Y/277 V (module ${k + 1})` });
      if (R[`G${k + 1}`]) objects[`generator${k + 1}`] = add(R[`G${k + 1}`], 2.6, 'generator', 'generator', `generator${k + 1}`, { index: k });
    }
    objects.mvswgr = add(R.SWGR, 2.0, 'switchgear', 'switchgear', 'mvswgr', { label: '15 kV pad-mounted switchgear, 4-way' });
  }

  function buildShell(cfg, d) {
    const { extL, extW, extH, micro, hall } = G;
    const g = groups.shell;
    // Rev 2: Shop White body (decision default, REV2_DECISION §4.3) with the Night Navy band; Rev 1: the Rev 1 paint
    const color = G.rev2 ? BODY.shop : (micro ? REV1.cab : (cfg.white_label ? REV1.wl : (hall ? REV1.hall : REV1.body)));
    if (G.rev2) livery.bodyColor = LV.shop;
    const corr = micro ? 0 : 0.036;          // ISO trapezoid corrugation on modules; outdoor cabinets have flat panels
    // concrete pad (hall: slab-on-grade for the hall, the power module and the plant yard)
    const pad = hall ? box(extL + 18, 0.12, extW + 20, MAT.pad, -5, 0.06 - 0.12, 4) : box(extL + 1.2, 0.12, extW + 1.2, MAT.pad, 0, 0.06 - 0.12, 0);
    pad.receiveShadow = true; pad.castShadow = false; g.add(pad);
    if (micro) { // skid
      g.add(box(extL + 0.2, 0.1, 0.12, MAT.casting, 0, 0.05, -extW / 2 + 0.1)); g.add(box(extL + 0.2, 0.1, 0.12, MAT.casting, 0, 0.05, extW / 2 - 0.1));
    }
    // floor slab + interior floor
    const floor = box(extL, G.floorTop, extW, MAT.shell(color), 0, G.floorTop / 2, 0); g.add(floor);
    const floorTop = new THREE.Mesh(new THREE.PlaneGeometry(G.intL, G.intW), MAT.floor); floorTop.rotation.x = -Math.PI / 2; floorTop.position.y = G.floorTop + 0.001; floorTop.receiveShadow = true; floorTop.userData = { type: 'container', id: 'container' }; g.add(floorTop);
    const tW = Math.max(0.04, (extW - G.intW) / 2), tL = Math.max(0.04, (extL - G.intL) / 2), sill = G.floorTop + 0.45;
    // roof: outer roof sheet (corrugated across the width) + ceiling liner; removed as one piece by the cutaway
    roof = new THREE.Group(); roof.userData = { type: 'container', id: 'container' };
    const roofSlab = box(extL, extH - G.ceiling, extW, MAT.shell(color), 0, (extH + G.ceiling) / 2, 0); roofSlab.userData = { type: 'container', id: 'container' }; roof.add(roofSlab); pickables.push(roofSlab);
    if (!micro) { const rc = corrugatedWall(extW - 0.2, extL - 0.3, color, 0.3, 0.02); rc.rotation.set(-Math.PI / 2, 0, Math.PI / 2); rc.position.set(0, extH + 0.012, 0); roof.add(rc); }
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(G.intL, G.intW), MAT.linerPanel); ceil.rotation.x = Math.PI / 2; ceil.position.y = G.ceiling - 0.002; roof.add(ceil);
    g.add(roof);
    // long walls: outer corrugated skin, PIR core, inner liner. The cutaway swaps the near wall for its sill stub with a cut face.
    G.wallStubs = G.wallStubs || [];
    const sectionCap = (len, thick, x, y, z, rotY = 0) => {
      const grp = new THREE.Group();
      const cap = box(len, 0.02, thick, MAT.section, 0, 0, 0); cap.castShadow = false; grp.add(cap);
      grp.add(box(len, 0.024, 0.008, MAT.casting, 0, 0.002, thick / 2), box(len, 0.024, 0.006, MAT.casting, 0, 0.002, -thick / 2));
      grp.position.set(x, y, z); grp.rotation.y = rotY; return grp;
    };
    const longWall = (side) => {
      const full = new THREE.Group();
      const outer = corrugatedWall(extL, extH, color, 0.278, corr); outer.position.set(0, extH / 2, side * (extW / 2 - corr / 2)); if (side < 0) outer.rotation.y = Math.PI;
      outer.userData = { type: 'container', id: 'container' }; pickables.push(outer); full.add(outer);
      const inner = new THREE.Mesh(new THREE.PlaneGeometry(G.intL, G.intH), MAT.linerPanel); inner.position.set(0, G.floorTop + G.intH / 2, side * G.intW / 2); inner.rotation.y = side > 0 ? Math.PI : 0; inner.receiveShadow = true; full.add(inner);
      const topCap = sectionCap(extL, tW, 0, extH + 0.01, side * (extW + G.intW) / 4); topCap.visible = false; full.add(topCap); G.caps.push(topCap);   // cut face along the top (seen once the roof is off)
      full.userData.capY = extH;
      const stub = new THREE.Group(); stub.visible = false;
      const so = corrugatedWall(extL, sill, color, 0.278, corr); so.position.set(0, sill / 2, side * (extW / 2 - corr / 2)); if (side < 0) so.rotation.y = Math.PI; stub.add(so);
      const si = new THREE.Mesh(new THREE.PlaneGeometry(G.intL, sill - G.floorTop), MAT.linerPanel); si.position.set(0, (sill + G.floorTop) / 2, side * G.intW / 2); si.rotation.y = side > 0 ? Math.PI : 0; stub.add(si);
      stub.add(sectionCap(extL, tW, 0, sill + 0.01, side * (extW + G.intW) / 4));
      g.add(full, stub); G.wallStubs.push({ full, stub, side });
      return full;
    };
    wallPos = longWall(1); wallNeg = longWall(-1);
    // far end wall
    const endWall = corrugatedWall(extW, extH, color, 0.278, corr); endWall.rotation.y = Math.PI / 2; endWall.position.set(extL / 2 - corr / 2, extH / 2, 0); g.add(endWall);
    endWall.userData = { type: 'container', id: 'container' }; pickables.push(endWall);
    const endIn = new THREE.Mesh(new THREE.PlaneGeometry(G.intW, G.intH), MAT.linerPanel); endIn.rotation.y = -Math.PI / 2; endIn.position.set(G.intL / 2, G.floorTop + G.intH / 2, 0); g.add(endIn);
    const endCap = sectionCap(extW, tL, extL / 2 - tL / 2, extH + 0.01, 0, Math.PI / 2); g.add(endCap); endCap.visible = false; G.caps.push(endCap);
    // door end: frame, corner posts, two leaves hinged at the outer edges, four lock rods with cam keepers, handles, hinges
    const doorGroup = new THREE.Group(); doorGroup.position.set(-extL / 2, 0, 0); doorGroup.userData = { type: 'doors', id: 'doors' };
    const frameMat = MAT.casting;
    doorGroup.add(box(0.12, extH, 0.12, frameMat, 0, extH / 2, -extW / 2 + 0.06), box(0.12, extH, 0.12, frameMat, 0, extH / 2, extW / 2 - 0.06), box(0.12, 0.16, extW, frameMat, 0, extH - 0.08, 0), box(0.12, 0.15, extW, frameMat, 0, 0.075, 0));
    const leafW = extW / 2 - 0.12, leafH = extH - 0.31;
    for (const side of [-1, 1]) {
      const hinge = new THREE.Group(); hinge.position.set(0, 0, side * (extW / 2 - 0.12));
      const leaf = micro ? box(0.05, leafH, leafW, MAT.shell(color), -0.03, 0.15 + leafH / 2, -side * leafW / 2) : new THREE.Mesh(new THREE.BoxGeometry(0.05, leafH, leafW), MAT.shell(color));
      if (!micro) { leaf.position.set(-0.03, 0.15 + leafH / 2, -side * leafW / 2); leaf.castShadow = leaf.receiveShadow = true; }
      leaf.userData = { type: 'doors', id: 'doors' };
      const P = new Parts();
      if (!micro) {
        for (const k of [0.22, 0.5, 0.78]) P.box(0.02, 0.07, leafW - 0.12, MAT.shell(color), -0.03, (k - 0.5) * leafH, 0);   // pressed stiffeners
        for (const k of [0.3, 0.7]) {
          const z = -side * leafW / 2 + side * k * leafW;
          P.cyl(0.016, leafH - 0.02, EM.galv, -0.06, 0, z, 'y', 10);                                   // lock rod
          for (const y of [-leafH / 2 + 0.06, leafH / 2 - 0.06]) P.box(0.05, 0.07, 0.07, EM.darkSteel, -0.05, y, z);   // cam keepers
          for (const y of [-leafH / 2 + 0.3, leafH / 2 - 0.3]) P.box(0.03, 0.03, 0.06, EM.galv, -0.05, y, z);           // rod guides
          P.box(0.03, 0.04, 0.3, EM.galv, -0.075, -leafH / 2 + 1.0, z + side * 0.13);                    // handle
          P.box(0.035, 0.08, 0.06, EM.darkSteel, -0.07, -leafH / 2 + 1.0, z + side * 0.02);              // handle hub + retainer
        }
        for (const y of [-leafH / 2 + 0.25, -leafH / 2 + leafH * 0.38, leafH / 2 - leafH * 0.38, leafH / 2 - 0.25]) P.cyl(0.03, 0.12, EM.darkSteel, -0.045, y, side * leafW / 2 - side * 0.02, 'y', 10);   // hinges
        P.box(0.003, 0.18, 0.28, EM.galv, -0.057, leafH / 2 - 0.4, 0);   // CSC plate
      } else {
        for (const k of [0.3, 0.7]) P.box(0.018, leafH - 0.3, 0.018, EM.galv, -0.04, 0, side * (k - 0.5) * leafW);
        P.box(0.03, 0.12, 0.03, EM.galv, -0.04, 0, side * leafW * 0.35);
      }
      P.build(leaf);
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
      for (const z of [-1, 1]) g.add(box(extL + 0.1, 0.1, 0.12, MAT.casting, 0, extH + 0.03, z * (extW / 2 + 0.02)));
    }
    // ISO corner castings (with their apertures), corner posts, top and bottom side rails
    if (!micro && !hall) {
      const P = new Parts();
      for (const x of [-1, 1]) for (const y of [0, 1]) for (const z of [-1, 1]) {
        const cx = x * (extL / 2 - 0.089), cy = y ? extH - 0.059 : 0.059, cz = z * (extW / 2 - 0.081);
        P.box(0.178, 0.118, 0.162, MAT.casting, cx, cy, cz);
        P.box(0.06, 0.05, 0.01, EM.black, cx, cy, z * (extW / 2 + 0.0005));        // side aperture
        P.box(0.01, 0.05, 0.06, EM.black, x * (extL / 2 + 0.0005), cy, cz);         // end aperture
        P.box(0.11, 0.01, 0.06, EM.black, cx, y ? extH + 0.0005 : -0.0005, cz);     // top / bottom aperture
      }
      for (const x of [-1, 1]) for (const z of [-1, 1]) P.box(0.12, extH - 0.236, 0.1, MAT.casting, x * (extL / 2 - 0.07), extH / 2, z * (extW / 2 - 0.06));
      for (const z of [-1, 1]) { P.box(extL - 0.36, 0.16, 0.06, MAT.casting, 0, 0.08, z * (extW / 2 - 0.01)); P.box(extL - 0.36, 0.09, 0.06, MAT.casting, 0, extH - 0.045, z * (extW / 2 - 0.01)); }
      P.box(0.06, 0.09, extW - 0.32, MAT.casting, extL / 2 - 0.02, extH - 0.045, 0);
      P.build(g, { cast: true });
    }
    // brand on both long sides. Rev 2: livery canvas over the whole side (lockup, tier, product line, data plate band);
    // H3 armour panels sit 0.12 m proud of the wall, so the livery moves onto them. Rev 1: the Rev 1 monogram decal.
    const off = (G.hardening === 'H3' && !micro) ? 0.185 : 0.035;
    if (G.rev2) {
      const tex = sideTexture(livery, extL, extH, hall ? 'hall' : (micro ? 'cabinet' : 'module'));
      for (const side of [1, -1]) {
        const dm = new THREE.Mesh(new THREE.PlaneGeometry(extL, extH), new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.6, metalness: 0.1, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
        dm.position.set(0, extH / 2, side * (extW / 2 + off)); dm.rotation.y = side > 0 ? 0 : Math.PI; dm.userData = { type: 'container', id: 'container', livery: 'side' };
        g.add(dm); decals.push(dm);
      }
      livery.bandTexture = true;
    }
    const tex = G.rev2 ? null : brandTexture(cfg.white_label ? cfg.brand : 'Schreiber AI', d.tier_label, cfg.white_label);
    const decW = Math.min(extL * 0.62, 7.5), decH = decW * 640 / 2048;
    if (!G.rev2 && decH < extH * 0.9) {
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
      const vest = box(vL, vH, vW, MAT.shell(G.rev2 ? BODY.shop : REV1.body), -extL / 2 - vL / 2 - 0.1, vH / 2, 0); vest.userData = { type: 'vestibule', id: 'vestibule' }; edges(vest, 0, 0.35); g.add(vest); pickables.push(vest); objects.vestibule = vest;
      vest.add(box(0.08, vH * 0.7, 1.0, MAT.casting, -vL / 2 - 0.02, -vH * 0.1, 0));
      vest.add(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.1, 0.1), MAT.led(C.hold)).translateX(-vL / 2 - 0.06).translateY(vH * 0.25).translateZ(0.7));
      G.vestibuleL = vL;
    }
  }

  /** BEN 2000 hall interior: `rows` rack rows with alternating cold/hot aisles, overhead busway, DLC manifolds per row. */
  function buildHallInterior(cfg, d) {
    const g = groups.shell;
    const liner = new THREE.Mesh(new THREE.BoxGeometry(G.intL, G.intH, G.intW), MAT.liner); liner.position.set(0, G.floorTop + G.intH / 2, 0); liner.visible = false; g.add(liner);
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
      const cold = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 1.2, aisleH, G.aisleW - 0.02), new THREE.MeshBasicMaterial({ color: T.cool, transparent: true, opacity: 0.07, depthWrite: false }));
      cold.position.set(0, G.floorTop + aisleH / 2, zc); cold.userData = { type: 'aisle_cold', id: 'aisle_cold', index: r }; groups.cooling.add(cold); edges(cold, T.cool, 0.2);
      const hot = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 1.2, aisleH, G.aisleW - 0.02), new THREE.MeshBasicMaterial({ color: T.warm, transparent: true, opacity: 0.07, depthWrite: false }));
      hot.position.set(0, G.floorTop + aisleH / 2, zh); hot.userData = { type: 'aisle_hot', id: 'aisle_hot', index: r }; edges(hot, T.warm, 0.2); groups.cooling.add(hot);
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
      const disp = new THREE.Mesh(new THREE.PlaneGeometry(cduW - 0.2, 0.25), MAT.led(0x4c9dff)); disp.position.set(0, cduH * 0.6, cduD / 2 + 0.003); unit.add(disp);
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
    const pmColor = G.rev2 ? BODY.shop : REV1.pm;
    const shellMat = MAT.shell(G.rev2 ? BODY.shop : (cfg.white_label ? REV1.wl : REV1.pm));
    const pm = new THREE.Group(); pm.position.set(pmX, 0, 0);
    const pmFloor = box(pmL, G.floorTop, pmW, shellMat, 0, G.floorTop / 2, 0); pm.add(pmFloor);
    const pmRoof = box(pmL, 0.2, pmW, shellMat, 0, pmH - 0.1, 0); pmRoof.userData = { type: 'powermodule', id: 'powermodule' }; pm.add(pmRoof); pickables.push(pmRoof); objects.powermodule = pmRoof;
    const pmWallPos = corrugatedWall(pmL, pmH, pmColor); pmWallPos.position.set(0, pmH / 2, pmW / 2); pm.add(pmWallPos);
    const pmWallNeg = corrugatedWall(pmL, pmH, pmColor); pmWallNeg.rotation.y = Math.PI; pmWallNeg.position.set(0, pmH / 2, -pmW / 2); pm.add(pmWallNeg);
    const pmEnd = corrugatedWall(pmW, pmH, pmColor); pmEnd.rotation.y = -Math.PI / 2; pmEnd.position.set(-pmL / 2, pmH / 2, 0); pm.add(pmEnd);
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
      ups.add(new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.16), MAT.led(0x4c9dff)).translateY(0.6).translateX(-0.502).rotateY(-Math.PI / 2));
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
    // interior extent (kept for outlines / container highlights; the visible liner is the wall panels of the shell)
    const liner = new THREE.Mesh(new THREE.BoxGeometry(G.intL, G.intH, G.intW), MAT.liner); liner.position.set(0, G.floorTop + G.intH / 2, 0); liner.visible = false; g.add(liner);
    objects.liner = liner;
    const zc = G.zOff - (G.rackD / 2 + G.coldW / 2), zRow = G.zOff;
    // ceiling LED strip luminaires (two runs: over the cold aisle and over the row), hung from the roof so the cutaway takes them off
    const P = new Parts();
    const runs = G.micro ? [0] : [zc, zRow];
    const nF = Math.max(1, Math.floor((G.intL - 0.4) / 1.25));
    const lum = EQ.led(0xf4f8ff);
    for (const z of runs) for (let i = 0; i < nF; i++) {
      const x = -G.intL / 2 + 0.2 + (i + 0.5) * (G.intL - 0.4) / nF;
      P.box(1.12, 0.035, 0.07, EM.equipLight, x, G.ceiling - 0.02, z);
      P.box(1.08, 0.004, 0.05, lum, x, G.ceiling - 0.039, z);
    }
    if (!G.micro) {
      // VESDA sampling pipe + smoke / heat detectors along the cold aisle ceiling
      P.cyl(0.0125, G.intL - 0.3, EM.red, 0, G.ceiling - 0.08, zc + 0.25, 'x', 8);
      for (let i = 0; i < Math.max(2, Math.round(G.intL / 3)); i++) { const x = -G.intL / 2 + (i + 0.5) * G.intL / Math.max(2, Math.round(G.intL / 3)); P.cyl(0.05, 0.035, EM.equipLight, x, G.ceiling - 0.02, zc - 0.2, 'y', 16); P.cyl(0.012, 0.004, EQ.led(0xff6369), x + 0.02, G.ceiling - 0.04, zc - 0.2, 'y', 8); }
    }
    P.build(roof, { cast: false });
    // area lights for the interior (module 1 only on the BEN 2000 yard: the other modules stay closed)
    if (!G.extraModule) {
      const nL = G.micro ? 1 : 2;
      for (let i = 0; i < nL; i++) {
        const pl = new THREE.PointLight(0xf2f6ff, G.micro ? 1.5 : 1.6 + G.intL * 0.08, G.micro ? 2.5 : G.intL * 0.75 + 2, 0.5); pl.position.set(-G.intL / 2 + (i + 0.5) * G.intL / nL, G.ceiling - 0.06, G.micro ? 0 : zc); interiorLights.add(pl);
      }
    }
    // aisle volumes stay as invisible extents (hover / highlight targets); the floor carries thin thermal-ramp tape lines instead of a haze
    const aisleH = G.intH - 0.05, hidden = new THREE.MeshBasicMaterial({ visible: false });
    const cold = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 0.04, aisleH, G.coldW - 0.02), hidden);
    cold.position.set(0, G.floorTop + aisleH / 2, zc); cold.userData = { type: 'aisle_cold', id: 'aisle_cold' }; groups.cooling.add(cold);
    const hot = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 0.04, aisleH, Math.max(0.05, G.hotW - 0.02)), hidden);
    hot.position.set(0, G.floorTop + aisleH / 2, G.zOff + G.rackD / 2 + G.hotW / 2); hot.userData = { type: 'aisle_hot', id: 'aisle_hot' }; groups.cooling.add(hot);
    objects.aisle_cold = cold; objects.aisle_hot = hot;
    if (!G.micro) {
      const tape = new Parts();
      tape.box(G.intL - 0.3, 0.003, 0.05, EQ.led(T.cool), 0, G.floorTop + 0.003, G.zOff - G.rackD / 2 - 0.12);
      if (G.hotW > 0.4) tape.box(G.intL - 0.3, 0.003, 0.05, EQ.led(T.warm), 0, G.floorTop + 0.003, G.zOff + G.rackD / 2 + 0.12);
      tape.build(groups.shell, { cast: false });
      for (const x of [-1, 1]) {
        if (G.hotW < 0.4) continue;   // dense tiers: a 200 mm rear plenum, no walk-in hot aisle to contain
        const door = new THREE.Mesh(new THREE.PlaneGeometry(G.hotW - 0.04, aisleH), MAT.glass); door.rotation.y = Math.PI / 2; door.position.set(x * (G.intL / 2 - 0.05), G.floorTop + aisleH / 2, G.zOff + G.rackD / 2 + G.hotW / 2); groups.cooling.add(door);
        door.userData = { type: 'containment', id: `containment${x > 0 ? 2 : 1}`, index: x > 0 ? 1 : 0 }; pickables.push(door); objects[door.userData.id] = door;
        const frame = box(0.04, aisleH, 0.04, MAT.tray, x * (G.intL / 2 - 0.05), G.floorTop + aisleH / 2, G.zOff + G.rackD / 2 + 0.02); groups.cooling.add(frame);
      }
      // clean-agent fire suppression cylinder in the blind-end corner of the cold aisle (valve, gauge, discharge pipe to a ceiling nozzle)
      // dense tiers: cold-aisle end (the rear is a 200 mm plenum); others: the hot-aisle end, out of the narrow cold aisle's sight line
      const fx = G.intL / 2 - 0.2, fz = G.hotW > 0.45 ? G.intW / 2 - 0.19 : -G.intW / 2 + 0.19, fs = new THREE.Group(); fs.position.set(fx, G.floorTop, fz);
      const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.135, 0.135, 1.15, 24), EM.red); cyl.position.y = 0.6; cyl.castShadow = true; fs.add(cyl);
      const F = new Parts();
      F.add(new THREE.SphereGeometry(0.135, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), EM.red, 0, 1.175, 0);
      F.cyl(0.045, 0.12, EM.brass, 0, 1.36, 0, 'y', 12); F.cyl(0.035, 0.02, EM.equipLight, 0.06, 1.38, -0.0, 'x', 14);
      F.cyl(0.02, G.intH - 1.48, EM.red, 0, 1.42 + (G.intH - 1.48) / 2, 0, 'y', 8);
      F.cyl(0.03, 0.06, EM.chrome, 0, G.intH - 0.06, 0, 'y', 10);
      F.box(0.06, 0.3, 0.02, EM.galv, 0, 0.6, 0.15); F.box(0.16, 0.12, 0.003, EQ.led(0xffffff), 0, 0.7, -0.136);
      F.build(fs); groups.shell.add(fs); solids.push(cyl);
    }
  }

  function buildRacks(cfg, d) {
    const g = groups.compute;
    const liquid = G.dense || G.hd || G.hall || (G.liquid && !G.micro);
    const profile = G.dense || G.hd ? 'nvl72' : 'std';
    for (let i = 0; i < cfg.racks; i++) {
      const M = EQ.rackModel({ W: G.rackW, H: G.rackH, D: G.rackD, U: G.rackU, profile, liquid, rearDoor: !G.water });
      const rack = M.group; rack.position.set(G.rackX[i], G.floorTop, G.rackZ ? G.rackZ[i] : G.zOff);
      const body = M.body; body.userData = { type: 'rack', index: i, id: `rack${i + 1}` }; pickables.push(body); solids.push(body);
      M.front.userData = body.userData; pickables.push(M.front);
      if (G.water) {   // rear-door heat exchanger: coil face + hinge frame, fed from the water loop
        const coilMat = new THREE.MeshStandardMaterial({ map: EQ.coilTex(), roughness: 0.5, metalness: 0.7 });
        const coil = faceBox(G.rackW, G.rackH - 0.12, 0.14, EM.darkSteel, coilMat, '+z'); coil.position.set(0, G.rackH / 2 + 0.04, G.rackD / 2 + 0.08);
        coil.userData = { type: 'cooling', index: Math.min(i, d.cooling_units_total - 1), id: `cooling${Math.min(i, d.cooling_units_total - 1) + 1}` }; rack.add(coil); pickables.push(coil); solids.push(coil);
      }
      rack.userData = { front: M.front, frontMat: M.frontMat, led: M.led, body };
      g.add(rack); racks.push(rack); objects[`rack${i + 1}`] = body;
    }
  }

  function coolingGapPositions(n) {
    return Array.from({ length: n }, (_, i) => G.unitX[i] === undefined ? null : G.unitX[i]);
  }

  /** Front / rear textured material set for a box (BoxGeometry face order +x, -x, +y, -y, +z, -z). */
  function mats6(body, faces) { const m = [body, body, body, body, body, body]; for (const [k, v] of Object.entries(faces)) m[{ '+x': 0, '-x': 1, '+y': 2, '-y': 3, '+z': 4, '-z': 5 }[k]] = v; return m; }
  const texMat = (t, extra = {}) => new THREE.MeshStandardMaterial({ map: t.map || t, emissiveMap: t.emissive || null, emissive: t.emissive ? 0xffffff : 0x000000, emissiveIntensity: t.emissive ? 0.9 : 0, roughness: 0.5, metalness: 0.35, ...extra });
  /** Roof / skid dry cooler: coil faces on the long sides, fan deck with guards on top, legs. Returns { unit, body, fans }. */
  function dryCoolerModel(L, H, Wd, nf, bodyUserData) {
    const unit = new THREE.Group();
    const coil = new THREE.MeshStandardMaterial({ map: EQ.coilTex(), roughness: 0.5, metalness: 0.7 });
    const body = new THREE.Mesh(new THREE.BoxGeometry(L, H, Wd), mats6(EM.equipLight, { '+z': coil, '-z': coil })); body.position.y = 0.12 + H / 2; body.castShadow = body.receiveShadow = true; body.userData = bodyUserData; unit.add(body);
    const P = new Parts(); const fans = [];
    for (const lx of [-1, 1]) for (const lz of [-1, 1]) P.box(0.06, 0.12, 0.06, EM.galv, lx * (L / 2 - 0.06), 0.06, lz * (Wd / 2 - 0.06));
    P.box(L, 0.05, 0.06, EM.galv, 0, 0.12, Wd / 2 - 0.03); P.box(L, 0.05, 0.06, EM.galv, 0, 0.12, -Wd / 2 + 0.03);
    const r = Math.min(0.42, Wd / 2 - 0.08, L / nf / 2 - 0.05);
    for (let f = 0; f < nf; f++) { const x = -L / 2 + (f + 0.5) * L / nf; P.cyl(r + 0.03, 0.08, EM.equipMid, x, 0.12 + H + 0.04, 0, 'y', 28); fans.push(EQ.fanGuard(P, unit, x, 0.12 + H + 0.09, 0, r)); }
    P.box(0.22, 0.3, 0.06, EM.equipMid, L / 2 - 0.2, 0.12 + H * 0.5, Wd / 2 + 0.03);   // EC fan control box
    P.build(unit, { cast: true });
    return { unit, body, fans };
  }

  function buildCooling(cfg, d) {
    const g = groups.cooling;
    const n = d.cooling_units_total;
    const unitW = G.unitW || 0.3;
    if (G.air && !G.micro) {
      const xs = coolingGapPositions(n);
      const front = new THREE.MeshStandardMaterial({ map: EQ.inrowFront(), roughness: 0.5, metalness: 0.35 });
      let wallIdx = 0;
      for (let i = 0; i < n; i++) {
        let x = xs[i], z = 0, w = unitW, dd = G.rackD;
        if (x === null) { x = G.intL / 2 - 0.5 - wallIdx++ * 0.7; z = G.zOff + G.rackD / 2 + G.hotW - 0.17; w = 0.6; dd = 0.3; } // wall-mounted extras
        const unit = new THREE.Group(); unit.position.set(x, G.floorTop, z + (z === 0 ? G.zOff : 0));
        const body = new THREE.Mesh(new THREE.BoxGeometry(w, G.rackH, dd), mats6(EM.equipLight, { '-z': front, '+z': front })); body.position.y = G.rackH / 2; body.castShadow = body.receiveShadow = true;
        body.userData = { type: 'cooling', index: i, id: `cooling${i + 1}` }; unit.add(body); pickables.push(body); solids.push(body);
        const strip = new THREE.Mesh(new THREE.BoxGeometry(Math.min(0.12, w - 0.06), 0.02, 0.01), EQ.led(C.green)); strip.position.set(0, G.rackH - 0.06, -dd / 2 - 0.006); unit.add(strip);
        unit.userData = { strip, body }; g.add(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = body;
      }
      // condensing units on the roof (one per in-row DX unit), on rails: the heat goes up and out
      const nc = Math.min(n, Math.max(1, Math.floor((G.extL - 0.6) / 1.15)));
      for (let i = 0; i < nc; i++) {
        const cu = dryCoolerModel(1.0, 0.55, 0.8, 1, {}); cu.unit.position.set(-G.extL / 2 + 0.7 + i * 1.15, G.extH, 0); cu.unit.userData.decor = true; g.add(cu.unit);
        cu.unit.userData.fans = cu.fans; cu.unit.userData.fanPct = 60; dryCoolers.push(cu.unit);
      }
    } else if (G.micro) {
      // cabinet DX mounted on the +z exterior side
      for (let i = 0; i < n; i++) {
        const unit = new THREE.Group(); unit.position.set(-G.extL / 2 + 0.35 + i * 0.5, 0, G.extW / 2 + 0.14);
        const body = box(0.42, G.extH * 0.7, 0.26, MAT.cooling, 0, G.extH * 0.5, 0); body.userData = { type: 'cooling', index: i, id: `cooling${i + 1}` }; unit.add(body); pickables.push(body);
        const P = new Parts(); for (const k of [1, 0.7, 0.4]) P.ring(0.15 * k, 0.005, EM.darkSteel, 0, G.extH * 0.72, 0.135, 'z', 28); P.box(0.3, 0.004, 0.01, EM.darkSteel, 0, G.extH * 0.72, 0.135); P.box(0.004, 0.3, 0.01, EM.darkSteel, 0, G.extH * 0.72, 0.135); P.build(unit);
        const fan = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.02, 24), MAT.fan); fan.rotation.x = Math.PI / 2; fan.position.set(0, G.extH * 0.72, 0.12); unit.add(fan);
        const strip = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.03, 0.02), MAT.led(C.green)); strip.position.set(0, G.extH * 0.2, 0.14); unit.add(strip);
        unit.userData = { strip, body, fan }; g.add(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = body;
      }
    } else {
      // liquid / water: CDU(s) in the row + heat rejection outside; supply / return headers along the rear with drops to each rack
      const nCdu = G.liquid ? (G.hd ? n : Math.min(2, n)) : 1;
      const cduT = EQ.cduFront(), cduMat = texMat(cduT);
      for (let k = 0; k < nCdu; k++) {
        const w = G.unitW || 0.6;
        const x = G.unitX[k] !== undefined ? G.unitX[k] : (k === 0 ? G.intL / 2 - 0.4 : -G.intL / 2 + G.bayL + 0.4);
        const cdu = new THREE.Mesh(new THREE.BoxGeometry(w - 0.01, G.rackH, G.rackD), mats6(EM.equipLight, { '-z': cduMat })); cdu.position.set(x, G.floorTop + G.rackH / 2, G.zOff); cdu.castShadow = cdu.receiveShadow = true;
        cdu.userData = { type: 'cdu', id: G.hd ? `cdu${k + 1}` : 'cdu', index: k }; g.add(cdu); pickables.push(cdu); solids.push(cdu);
        const P = new Parts(), top = G.rackH / 2;
        P.box(w - 0.02, 0.08, G.rackD - 0.04, EM.equipMid, 0, -top + 0.04, 0);   // plinth
        for (const [dx, m] of [[-0.13, EM.pipeSupply], [0.13, EM.pipeReturn]]) {   // W45 supply / return stubs: flange, isolation valve, riser
          P.cyl(0.045, 0.22, m, dx, top + 0.11, G.rackD * 0.25, 'y', 16); P.cyl(0.075, 0.02, EM.steel, dx, top + 0.02, G.rackD * 0.25, 'y', 20); P.cyl(0.075, 0.02, EM.steel, dx, top + 0.2, G.rackD * 0.25, 'y', 20);
          P.box(0.11, 0.08, 0.11, EM.darkSteel, dx, top + 0.29, G.rackD * 0.25); P.box(0.2, 0.015, 0.03, EM.red, dx + 0.07, top + 0.34, G.rackD * 0.25);
        }
        P.box(0.02, 0.18, 0.03, EM.chrome, w / 2 - 0.08, 0, -G.rackD / 2 - 0.016);   // door handle
        P.build(cdu);
        const strip = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.018, 0.006), MAT.led(C.green)); strip.position.set(0, top - 0.05, -G.rackD / 2 - 0.004); cdu.add(strip); cdu.userData.strip = strip;
        if (G.hd) objects[`cdu${k + 1}`] = cdu;
        if (k === 0) objects.cdu = cdu;
      }
      // overhead supply / return headers along the rear (dense tiers: inside the 200 mm rear plenum) with a drop to every rack
      const y = G.ceiling - 0.3, z0 = G.zOff + G.rackD / 2 + (G.dense ? 0.07 : 0.12), zs = G.dense ? 0.55 : 1, rH = G.hd ? 0.055 : 0.04;
      const H = new Parts();
      for (const [mat, dz] of [[EM.pipeSupply, 0], [EM.pipeReturn, 0.13]]) {
        const zz = z0 + dz * zs, yy = y - dz * 0.6;
        H.cyl(rH, G.intL - 0.2, mat, 0, yy, zz, 'x', 14);
        for (let k = 0; k < Math.floor((G.intL - 0.2) / 1.5); k++) H.cyl(rH + 0.01, 0.03, EM.steel, -G.intL / 2 + 0.85 + k * 1.5, yy, zz, 'x', 14);   // couplings
        for (let k = 0; k < Math.floor((G.intL - 0.2) / 1.5); k++) H.box(0.03, G.ceiling - yy, 0.03, EM.galv, -G.intL / 2 + 0.85 + k * 1.5, (yy + G.ceiling) / 2, zz);   // hangers
        for (const x of G.rackX) {
          const xd = x + (dz ? 0.21 : -0.21) * (G.dense ? 1 : 0.5), top = G.floorTop + G.rackH;
          H.cyl(rH * 0.55, yy - top + 0.02, mat, xd, (yy + top) / 2, zz, 'y', 10);
          H.box(0.05, 0.05, 0.05, EM.darkSteel, xd, top + 0.18, zz);   // ball valve
        }
      }
      H.build(g);
      const hdr = new THREE.Mesh(new THREE.BoxGeometry(G.intL - 0.2, 0.3, 0.25), new THREE.MeshBasicMaterial({ visible: false })); hdr.position.set(0, y - 0.05, z0 + 0.06); g.add(hdr); solids.push(hdr);
      if (G.hd) {
        const ghost = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: false });   // pick target only: the visible manifolds are on the rack rears
        G.rackX.forEach((x, i) => {
          const man = new THREE.Mesh(new THREE.BoxGeometry(G.rackW - 0.04, G.rackH - 0.3, 0.1), ghost); man.position.set(x, G.floorTop + G.rackH / 2, G.zOff + G.rackD / 2 + 0.06);
          man.userData = { type: 'manifold', id: `manifold${i + 1}`, index: i }; g.add(man); pickables.push(man); objects[`manifold${i + 1}`] = man;
        });
      }
      if (G.dense) { buildDenseCoolingExtras(cfg, d); return; }
      // dry coolers on the roof
      const dcW = Math.min(2.2, (G.extL - 0.6) / n - 0.2), dcL = Math.min(1.1, G.extW - 0.6);
      for (let i = 0; i < n; i++) {
        const m = dryCoolerModel(dcW, 0.62, dcL, Math.max(1, Math.round(dcW / 0.9)), { type: 'drycooler', index: i, id: `cooling${i + 1}` });
        const unit = m.unit; unit.position.set(-G.extL / 2 + 0.4 + dcW / 2 + i * (dcW + 0.2), G.extH, 0); pickables.push(m.body);
        const strip = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.03, 0.01), MAT.led(C.green)); strip.position.set(-dcW / 2 + 0.2, 0.3, dcL / 2 + 0.01); unit.add(strip);
        unit.userData = { strip, body: m.body, fans: m.fans }; g.add(unit); dryCoolers.push(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = m.body;
      }
    }
  }

  /** Rev 2 dense tiers: in-row fan coils on the 18 C trim loop, and the heat-rejection skid (W45 dry coolers + trim chiller) beside the blind end. */
  function buildDenseCoolingExtras(cfg, d) {
    const g = groups.cooling;
    const fcMat = new THREE.MeshStandardMaterial({ map: EQ.fancoilFront(), roughness: 0.5, metalness: 0.35 });
    G.fcX.forEach((x, k) => {
      const unit = new THREE.Group(); unit.position.set(x, G.floorTop, G.zOff);
      const hh = G.rackH - 0.05;
      const body = new THREE.Mesh(new THREE.BoxGeometry(0.29, hh, 1.07), mats6(EM.equipLight, { '-z': fcMat })); body.position.y = hh / 2; body.castShadow = body.receiveShadow = true;
      body.userData = { type: 'fancoil', id: `fancoil${k + 1}`, index: k }; unit.add(body); pickables.push(body); solids.push(body);
      const P = new Parts(); P.cyl(0.018, 0.2, EM.pipeSupply, -0.06, hh + 0.1, 0.3, 'y', 8); P.cyl(0.018, 0.2, EM.pipeReturn, 0.06, hh + 0.1, 0.3, 'y', 8); P.build(unit);
      const strip = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.016, 0.006), MAT.led(C.green)); strip.position.set(0, hh - 0.05, -0.539); unit.add(strip);
      unit.userData = { strip, body }; g.add(unit); objects[`fancoil${k + 1}`] = body;
    });
    // adjacent skid: concrete pad, steel skid frame, dry cooler bank (one module per CDU), trim chiller, insulated pipe bridge into the end wall
    const n = Math.max(1, d.cooling_units_n || 1), skidL = cfg.it_kw <= 300 ? 2.4 : 4.8, skidW = 2.6, sx0 = G.extL / 2 + 1.5;
    const skid = box(skidL, 0.25, skidW, MAT.casting, sx0 + skidL / 2, 0.125, 0); skid.userData = { type: 'skid', id: 'skid' }; g.add(skid); pickables.push(skid); objects.skid = skid;
    const pad = box(skidL + 0.6, 0.12, skidW + 0.6, MAT.pad, sx0 + skidL / 2, -0.06, 0); pad.castShadow = false; g.add(pad);
    const SP = new Parts();
    for (let k = 0; k <= Math.round(skidL / 0.8); k++) SP.box(0.1, 0.26, skidW, EM.galv, sx0 + k * skidL / Math.round(skidL / 0.8), 0.13, 0);
    const dcW = skidL / n - 0.1;
    for (let i = 0; i < n; i++) {
      const m = dryCoolerModel(dcW, 1.45, 1.6, Math.max(1, Math.round(dcW / 1.1)), { type: 'drycooler', index: i, id: `drycooler${i + 1}` });
      const unit = m.unit; unit.position.set(sx0 + 0.05 + dcW / 2 + i * (dcW + 0.1), 0.25, -0.35); pickables.push(m.body);
      const strip = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.03, 0.01), MAT.led(C.green)); strip.position.set(-dcW / 2 + 0.25, 0.5, 0.81); unit.add(strip);
      unit.userData = { strip, body: m.body, fans: m.fans, unit: i }; g.add(unit); dryCoolers.push(unit); if (i === 0) objects.drycooler1 = m.body;
    }
    const lv = new THREE.MeshStandardMaterial({ map: EQ.louvreTex(), roughness: 0.5, metalness: 0.3 });
    const trim = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.3, 0.8), mats6(EM.equipLight, { '+x': lv, '-x': lv, '+z': lv })); trim.position.set(sx0 + skidL - 0.6, 0.9, 0.85); trim.castShadow = trim.receiveShadow = true;
    trim.userData = { type: 'trim_chiller', id: 'trim_chiller' }; g.add(trim); pickables.push(trim); objects.trim_chiller = trim;
    const TP = new Parts(); TP.cyl(0.32, 0.06, EM.equipMid, 0, 0.68, 0, 'y', 24); const tf = EQ.fanGuard(TP, trim, 0, 0.72, 0, 0.3); TP.box(0.3, 0.4, 0.02, EM.darkSteel, -0.2, 0.1, -0.41); TP.box(0.18, 0.1, 0.005, EQ.led(0x14325a), -0.2, 0.22, -0.421); TP.build(trim);
    dryCoolers.push({ userData: { fans: [tf], fanPct: 70, decor: true } });
    // insulated supply / return from the skid header up and across into the blind end wall
    const xs = G.extL / 2, xe = sx0 + 0.3;
    for (const [mat, dz] of [[EM.pipeSupply, -0.14], [EM.pipeReturn, 0.14]]) {
      const yb = 1.05 + (dz > 0 ? 0.0 : 0.16);
      SP.cyl(0.07, xe - xs, mat, (xs + xe) / 2, yb, dz, 'x', 14);
      SP.cyl(0.07, yb - 0.25, mat, xe, (yb + 0.25) / 2, dz, 'y', 14);
      SP.add(new THREE.SphereGeometry(0.07, 14, 10), mat, xe, yb, dz);
      SP.cyl(0.11, 0.03, EM.steel, xs + 0.02, yb, dz, 'x', 18);   // wall flange
      SP.box(0.05, yb, 0.05, EM.galv, (xs + xe) / 2, yb / 2, dz);   // pipe support
    }
    SP.build(g, { cast: true });
  }

  /** Rev 2 dense tiers: the power gear stands in the row (switchboard sections, UPS frames, lithium cabinets, backed onto the rack wall). */
  function buildDensePower(cfg, d) {
    const g = groups.power, zw = G.intW / 2;   // the rack wall
    const depth = { swbd: 0.61, ups: 0.925, batt: 1.0, rect: 1.0, batt800: 1.0 };
    const upsT = EQ.upsFront(), batT = EQ.batteryFront();
    const upsMat = texMat(upsT), batMat = texMat(batT, { roughness: 0.55 });
    let nB = 0, nU = 0, nS = 0;
    for (const it of G.powerItems) {
      const dd = depth[it.kind] || 1.0, hgt = Math.min(G.intH - 0.2, it.kind === 'swbd' ? 2.29 : 2.0);
      const type = it.kind === 'swbd' ? 'switchgear' : (it.kind === 'ups' ? 'ups' : (it.kind === 'rect' ? 'rectifier' : 'battery'));
      const idx = type === 'battery' ? nB++ : type === 'ups' ? nU++ : nS++;
      const front = type === 'switchgear' ? new THREE.MeshStandardMaterial({ map: EQ.switchboardFront(idx), roughness: 0.5, metalness: 0.35 }) : type === 'battery' ? batMat : upsMat;
      const bodyMat = type === 'battery' ? EM.equipDark : EM.equipLight;
      const cab = new THREE.Mesh(new THREE.BoxGeometry(it.w - 0.02, hgt, dd), mats6(bodyMat, { '-z': front })); cab.position.set(it.x, G.floorTop + hgt / 2, zw - dd / 2); cab.castShadow = cab.receiveShadow = true;
      cab.userData = { type, id: type === 'switchgear' ? 'switchgear' : (type === 'rectifier' ? 'rectifier' : type), index: idx }; g.add(cab); pickables.push(cab); solids.push(cab);
      const P = new Parts();
      P.box(it.w - 0.03, 0.08, dd - 0.04, EM.black, 0, -hgt / 2 + 0.04, 0);   // plinth
      if (type === 'switchgear') { P.box(it.w - 0.02, 0.18, dd, EM.equipMid, 0, hgt / 2 + 0.09, 0); P.box(0.02, 0.14, 0.03, EM.chrome, it.w / 2 - 0.08, 0.1, -dd / 2 - 0.015); }
      else for (const sx of [-1, 1]) P.box(0.02, 0.16, 0.03, EM.chrome, sx * 0.05 + (type === 'battery' ? it.w * 0.3 : 0), 0.15, -dd / 2 - 0.015);
      P.build(cab);
      if (!objects[type]) objects[type] = cab;
    }
    if (!objects.ups) objects.ups = objects.rectifier || objects.battery;
    // ATS / main on the end wall outside the row; the 600 A wall panel (BEN 300) or the first switchboard section is the distribution panel
    const ats = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.9, 0.4), mats6(EM.equipLight, { '-x': new THREE.MeshStandardMaterial({ map: EQ.panelboardFront('ats'), roughness: 0.5 }) }));
    ats.position.set(G.intL / 2 - 0.11, G.floorTop + 1.55, -G.intW / 2 + 0.35); ats.castShadow = true; ats.userData = { type: 'ats', id: 'ats' }; g.add(ats); pickables.push(ats); objects.ats = ats;
    if (objects.switchgear) objects.panel = objects.switchgear;
    else {
      const panel = new THREE.Mesh(new THREE.BoxGeometry(0.25, 1.8, 0.9), mats6(EM.equipLight, { '-x': new THREE.MeshStandardMaterial({ map: EQ.panelboardFront('panel'), roughness: 0.5 }) }));
      panel.position.set(G.intL / 2 - 0.13, G.floorTop + 1.2, -G.intW / 2 + 0.55 + 0.45); panel.castShadow = true; panel.userData = { type: 'panel', id: 'panel' }; g.add(panel); pickables.push(panel); objects.panel = panel; solids.push(panel);
    }
    G.powerEndX = -G.intL / 2;
  }

  function buildPower(cfg, d) {
    const g = groups.power;
    // cable tray above the rack row (containers only)
    const tray = new THREE.Group(); tray.position.set(0, G.ceiling - 0.3, G.zOff); tray.visible = !G.micro;
    { // ladder cable tray: two side rails, rungs at 300 mm, threaded-rod hangers, a few cable bundles laid in it
      const P = new Parts(), L = G.intL - 0.1;
      P.box(L, 0.08, 0.012, EM.galv, 0, 0.02, -0.15).box(L, 0.08, 0.012, EM.galv, 0, 0.02, 0.15);
      for (let x = -L / 2 + 0.15; x < L / 2; x += 0.3) P.box(0.03, 0.015, 0.3, EM.galv, x, -0.012, 0);
      for (let x = -L / 2 + 0.6; x < L / 2; x += 1.5) for (const z of [-0.17, 0.17]) P.cyl(0.005, 0.32, EM.steel, x, 0.16, z, 'y', 6);
      for (const [z, c] of [[-0.08, EM.black], [0.0, EM.hose], [0.08, EM.black]]) P.cyl(0.022, L - 0.2, c, 0, 0.012, z, 'x', 8);
      P.build(tray, { cast: false });
    }
    const trayPick = box(G.intL - 0.1, 0.06, 0.34, new THREE.MeshBasicMaterial({ visible: false }), 0, 0, 0); trayPick.userData = { type: 'tray', id: 'tray' }; tray.add(trayPick); pickables.push(trayPick);
    g.add(tray); objects.tray = tray;

    if (G.dense) {
      buildDensePower(cfg, d);
    } else if (G.micro) {
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
      const nRect = G.dc800 ? Math.max(1, d.rectifier_cabinets || 1) : 0;
      const nCab = d.ups_modules + nBat + nRect;
      const cabW = Math.max(0.35, Math.min(0.6, (G.intW - 0.15 - 0.05 * (nCab - 1)) / nCab));
      const cabD = Math.min(0.6, G.bayL - 0.45), cabH = Math.min(1.9, G.intH - 0.35);
      const rowW = nCab * cabW + (nCab - 1) * 0.05;
      let z = -rowW / 2 + cabW / 2;
      const upsMat = texMat(EQ.upsFront()), batMat = texMat(EQ.batteryFront(), { roughness: 0.55 });
      const cab = (type, mat, bodyMat, z, ud) => {
        const m = new THREE.Mesh(new THREE.BoxGeometry(cabD, cabH, cabW), mats6(bodyMat, { '+x': mat })); m.position.set(x0 + 0.05 + cabD / 2, G.floorTop + cabH / 2, z); m.castShadow = m.receiveShadow = true;
        m.userData = ud; g.add(m); pickables.push(m); solids.push(m);
        const P = new Parts(); P.box(cabD - 0.04, 0.07, cabW - 0.02, EM.black, 0, -cabH / 2 + 0.035, 0); P.box(0.03, 0.15, 0.02, EM.chrome, cabD / 2 + 0.015, 0.1, cabW * 0.32); P.build(m);
        return m;
      };
      for (let m = 0; m < d.ups_modules; m++) {
        const ups = cab('ups', upsMat, EM.equipLight, z, { type: 'ups', id: 'ups' });
        if (m === 0) objects.ups = ups;
        z += cabW + 0.05;
      }
      for (let r = 0; r < nRect; r++) {
        // 800 VDC: SiC rectifier / SST front-end cabinet (4 x 100 kW modules each) in place of the UPS frames
        const rect = cab('rectifier', upsMat, EM.equipLight, z, { type: 'rectifier', id: 'rectifier', index: r });
        if (r === 0) { objects.rectifier = rect; objects.ups = objects.ups || rect; }
        z += cabW + 0.05;
      }
      for (let b = 0; b < nBat; b++) {
        const bat = cab('battery', batMat, EM.equipDark, z, { type: 'battery', id: 'battery' });
        if (b === 0) objects.battery = bat;
        z += cabW + 0.05;
      }
      const ats = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.9, 0.22), mats6(EM.equipLight, { '-z': new THREE.MeshStandardMaterial({ map: EQ.panelboardFront('ats'), roughness: 0.5 }) }));
      ats.position.set(x0 + 0.3, G.floorTop + 1.55, zWall - 0.11); ats.castShadow = true; ats.userData = { type: 'ats', id: 'ats' }; g.add(ats); pickables.push(ats); objects.ats = ats;
      const panel = new THREE.Mesh(new THREE.BoxGeometry(0.55, 1.0, 0.2), mats6(EM.equipLight, { '-z': new THREE.MeshStandardMaterial({ map: EQ.panelboardFront('panel'), roughness: 0.5 }) }));
      panel.position.set(x0 + Math.min(G.bayL - 0.3, 0.85), G.floorTop + 1.5, zWall - 0.1); panel.castShadow = true; panel.userData = { type: 'panel', id: 'panel' }; g.add(panel); pickables.push(panel); objects.panel = panel;
      if (G.dc800) {
        // 800 VDC busway (±400 V) over the rack row with a DC tap-off box per rack, replacing the AC feeders in the power tray
        const bwY = G.ceiling - 0.42, bwZ = G.zOff - G.rackD / 2 - 0.1, bwLen = G.intL - G.bayL - 0.3;
        const bw = box(bwLen, 0.16, 0.14, MAT.powerDark, x0 + G.bayL + bwLen / 2, bwY, bwZ); bw.userData = { type: 'dc_busway', id: 'dc_busway' }; edges(bw, C.info, 0.5); g.add(bw); pickables.push(bw); objects.dc_busway = bw;
        bw.add(new THREE.Mesh(new THREE.BoxGeometry(bwLen - 0.05, 0.02, 0.02), MAT.led(C.info)).translateY(-0.09));
        for (let i = 0; i < G.rackX.length; i++) {
          const tap = box(0.25, 0.22, 0.2, MAT.powerDark, G.rackX[i], bwY - 0.19, bwZ); tap.userData = { type: 'dc_busway', id: 'dc_busway', index: i }; edges(tap, 0, 0.35); g.add(tap); pickables.push(tap);
          tap.add(new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, 0.01), MAT.led(C.green)).translateZ(-0.105).translateY(0.05));
        }
        // feed from the rectifier cabinet to the busway end
        const rp = objects.rectifier.getWorldPosition(new THREE.Vector3());
        const feed = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, Math.hypot(x0 + G.bayL - rp.x, bwY - rp.y - 0.6), 8), MAT.powerDark);
        feed.position.set((rp.x + x0 + G.bayL) / 2, (rp.y + 0.6 + bwY) / 2, bwZ); feed.rotation.z = Math.atan2(bwY - rp.y - 0.6, x0 + G.bayL - rp.x) - Math.PI / 2; g.add(feed);
      }
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

  /** Rev 2 BEN 1: an office corner (floor, two walls) with either a desk carrying the 10-inch 8U rack and the UPS in tower
   *  orientation beside it, or the 19-inch 12U sound-damped cabinet on the floor next to the desk. Contents follow the form:
   *  desktop AI boxes / mini PC on shelves (rack10), or UPS + switch + NAS + 2U short-depth GPU server (cab12); two Pod W. */
  function buildMinirack(cfg, d, sensors) {
    const gs = groups.shell, gc = groups.compute, gp = groups.power, gk = groups.cooling, gt = groups.controls;
    const rack10 = G.form === 'rack10';
    const wallMat = new THREE.MeshStandardMaterial({ color: 0xd9dee6, roughness: 0.95 }), floorMat = new THREE.MeshStandardMaterial({ color: 0x8c7a66, roughness: 0.85 });
    const deskMat = new THREE.MeshStandardMaterial({ color: 0xb7a58c, roughness: 0.7 });
    const room = 3.2, wallH = 2.7;
    const floor = box(room, 0.02, room, floorMat, 0.6, -0.01, 0.6); floor.receiveShadow = true; floor.userData = { type: 'container', id: 'container' }; gs.add(floor); pickables.push(floor);
    const wA = box(room, wallH, 0.08, wallMat, 0.6, wallH / 2, -1.0); const wB = box(0.08, wallH, room, wallMat, -1.0, wallH / 2, 0.6);
    for (const w of [wA, wB]) { w.userData = { type: 'container', id: 'container' }; gs.add(w); pickables.push(w); }
    wallNeg = wA; wallPos = null; roof = null;
    const liner = new THREE.Group(); objects.liner = floor; gs.add(liner);
    const pl = new THREE.PointLight(0xfff4e0, 6, 6, 1.6); pl.position.set(0.5, 2.5, 0.5); interiorLights.add(pl);
    // desk (the 10-inch rack stands on it; the cabinet stands beside it)
    const deskTop = 0.74, deskX = rack10 ? 0 : 1.05;
    const desk = new THREE.Group(); desk.position.set(deskX, 0, -0.55);
    desk.add(box(1.4, 0.03, 0.7, deskMat, 0, deskTop - 0.015, 0));
    for (const sx of [-0.66, 0.66]) for (const sz of [-0.3, 0.3]) desk.add(box(0.04, deskTop - 0.03, 0.04, MAT.casting, sx, (deskTop - 0.03) / 2, sz));
    desk.add(box(0.5, 0.32, 0.03, MAT.casting, 0.3, deskTop + 0.2, 0.15));   // a monitor, for scale
    desk.userData = { type: 'desk', id: 'desk' }; gs.add(desk); objects.desk = desk;
    // the rack / cabinet
    const W = G.extL, D = G.extW, H = G.extH, baseY = rack10 ? deskTop : 0.0;
    const rx = rack10 ? -0.25 : -0.35, rz = rack10 ? -0.65 : -0.45;
    const rack = new THREE.Group(); rack.position.set(rx, baseY, rz);
    // Rev 2 livery: Night Navy powder-coat body (indoor default), lockup and S2 data plate band (brand/v2/livery/previews/ben1-*.png)
    const bodyMat = new THREE.MeshStandardMaterial({ color: BODY.night, roughness: 0.55, metalness: 0.35 });
    livery.bodyColor = LV.night;
    const glassFront = new THREE.MeshPhysicalMaterial({ color: 0x9fb3cc, transparent: true, opacity: 0.16, roughness: 0.05, metalness: 0.1, depthWrite: false });
    const body = rack10 ? box(W, H, D, bodyMat, 0, H / 2, 0) : new THREE.Mesh(new THREE.BoxGeometry(W, H, D), mats6(bodyMat, { '+z': glassFront }));
    if (!rack10) { body.position.y = H / 2; body.castShadow = body.receiveShadow = true; }
    body.userData = { type: 'rack', index: 0, id: 'rack1' }; rack.add(body); pickables.push(body);
    { // cabinet / rack hardware: door frame, handle, vented top, feet (cab12) or open 10-inch frame posts (rack10)
      const P = new Parts();
      if (rack10) { for (const sx2 of [-1, 1]) for (const sz2 of [-1, 1]) P.box(0.02, H, 0.02, EM.rackFrame, sx2 * (W / 2 - 0.01), H / 2, sz2 * (D / 2 - 0.01)); P.box(W, 0.02, D, EM.rackFrame, 0, H - 0.01, 0); P.box(W, 0.02, D, EM.rackFrame, 0, 0.01, 0); }
      else {
        const fz = D / 2 + 0.006;
        P.box(W, 0.05, 0.012, bodyMat, 0, H - 0.025, fz).box(W, 0.05, 0.012, bodyMat, 0, 0.025, fz).box(0.04, H, 0.012, bodyMat, -W / 2 + 0.02, H / 2, fz).box(0.04, H, 0.012, bodyMat, W / 2 - 0.02, H / 2, fz);
        P.box(0.015, 0.14, 0.03, EM.chrome, W / 2 - 0.045, H * 0.55, fz + 0.012);
        for (let k = 0; k < 8; k++) P.box(W * 0.6, 0.004, 0.012, EM.black, 0, H + 0.002, -D / 2 + 0.08 + k * 0.03);
        for (const sx2 of [-1, 1]) for (const sz2 of [-1, 1]) P.cyl(0.02, 0.03, EM.rubber, sx2 * (W / 2 - 0.05), -0.012, sz2 * (D / 2 - 0.05), 'y', 10);
      }
      P.build(rack);
    }
    if (rack10) { body.material = bodyMat.clone(); body.material.transparent = true; body.material.opacity = 0.22; }   // open front: see the shelves
    const tex = serverFrontTexture(G.rackU);
    const frontMat = new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: 0.4, roughness: 0.7, metalness: 0.2, transparent: true, opacity: 0.0, depthWrite: false });   // the real contents show through the open front / glass door
    const front = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.06, H - 0.1), frontMat); front.position.set(0, H / 2, D / 2 + 0.003); front.userData = body.userData; rack.add(front);

    const led = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.02, 0.01), MAT.led(C.green)); led.position.set(W / 2 - 0.08, H - 0.04, D / 2 + 0.01); rack.add(led);
    // side panels carry the stacked lockup, BEN 1, the product line and the band; rack10 adds a lockup bezel across the top
    // of the open front, cab12 the band across the foot of the glass door
    const sideTex = miniPanelTexture(livery, D, H);
    for (const sd of [1, -1]) {
      const pm = new THREE.Mesh(new THREE.PlaneGeometry(D - 0.004, H - 0.004), new THREE.MeshStandardMaterial({ map: sideTex, roughness: 0.55, metalness: 0.2 }));
      pm.position.set(sd * (W / 2 + 0.002), H / 2, 0); pm.rotation.y = sd * Math.PI / 2; pm.userData = body.userData; rack.add(pm);
    }
    if (rack10) {
      const bzH = 2 * 0.04445;
      const bz = new THREE.Mesh(new THREE.BoxGeometry(W, bzH, 0.012), [MAT.rack, MAT.rack, MAT.rack, MAT.rack, new THREE.MeshStandardMaterial({ map: bezelTexture(livery, W, bzH), roughness: 0.5 }), MAT.rack]);
      bz.position.set(0, H - bzH / 2 - 0.004, D / 2 + 0.006); bz.userData = body.userData; rack.add(bz);
    } else {
      const bh = 0.07;
      const bp = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.06, bh), new THREE.MeshStandardMaterial({ map: bandPlateTexture(livery, W - 0.06, bh), roughness: 0.5 }));
      bp.position.set(0, 0.05 + bh / 2, D / 2 + 0.012); bp.userData = body.userData; rack.add(bp);
    }
    livery.bandTexture = true;
    rack.userData = { front, frontMat, led, body };
    gc.add(rack); racks.push(rack); objects.rack1 = body; solids.push(body);
    G.rackX = [rx]; G.rackZ = [rz]; G.rowZ = [rz];
    // contents stack (bottom up), 19-inch or 10-inch wide
    const iw = rack10 ? 0.222 : 0.48, u = 0.04445; let uy = baseY + 0.03;
    const add = (type, id, nU, depth, mat, label) => {
      const bz = new THREE.MeshStandardMaterial({ map: EQ.bezelTex(type === 'ai_box' && !rack10 ? 'gpu' : type, nU, !rack10), roughness: 0.5, metalness: 0.4 });
      const m = faceBox(iw, nU * u - 0.004, depth, mat, bz, '+z'); m.position.set(rx, uy + nU * u / 2, rz + D / 2 - depth / 2 - 0.03); m.userData = { type, id, label };
      (type === 'ups' || type === 'pdu' || type === 'battery' ? gp : (type === 'edge' ? gt : gc)).add(m); pickables.push(m); objects[id] = objects[id] || m;
      uy += nU * u; return m;
    };
    const ai = cfg.profile === 'ai_training' || cfg.profile === 'ai_inference';
    if (rack10) {
      add('pdu', 'pdu', 1, 0.12, MAT.powerDark); add('switch', 'switch', 1, 0.12, MAT.gateway);
      const nAi = ai ? Math.max(1, Math.floor(cfg.it_kw * 1000 * 0.7 / 200)) : 0;
      for (let k = 0; k < nAi; k++) add('ai_box', k ? `ai_box${k + 1}` : 'ai_box', 2, 0.15, new THREE.MeshStandardMaterial({ color: 0xb08d57, roughness: 0.4, metalness: 0.8 }));
      if (!ai) add('ai_box', 'ai_box', 2, 0.18, MAT.powerDark);
      add('edge', 'edge', 1, 0.12, MAT.gateway);
      // the 2U 19-inch UPS cannot sit on 10-inch rails: it stands beside the rack in tower orientation
      const ups = box(0.09, 0.44, 0.43, MAT.power, rx + W / 2 + 0.12, deskTop + 0.22, rz); ups.userData = { type: 'ups', id: 'ups' }; edges(ups, 0, 0.35); gp.add(ups); pickables.push(ups); objects.ups = ups;
    } else {
      add('ups', 'ups', 2, 0.47, MAT.power); for (let k = 0; k < (d.ups_battery_packs || 0); k++) add('battery', 'battery', 2, 0.47, MAT.battery);
      add('switch', 'switch', 1, 0.2, MAT.gateway); add('nas', 'nas', 1, 0.47, MAT.powerDark);
      add('ai_box', 'ai_box', ai ? 2 : 1, 0.47, ai ? new THREE.MeshStandardMaterial({ color: 0x2c3a52, roughness: 0.5, metalness: 0.6 }) : MAT.powerDark);
      add('edge', 'edge', 1, 0.12, MAT.gateway); add('patch', 'patch', 1, 0.06, MAT.casting);
      // N+1 extraction fans in the rear top of the cabinet (sound-damped, filtered path)
      for (let i = 0; i < d.cooling_units_total; i++) {
        const unit = new THREE.Group(); unit.position.set(rx - 0.12 + i * 0.24, H - 0.02, rz - D / 2 + 0.15);
        const fb = box(0.2, 0.04, 0.2, MAT.coolingDark, 0, 0, 0); fb.userData = { type: 'cooling', index: i, id: `cooling${i + 1}` }; unit.add(fb); pickables.push(fb);
        const fan = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.01, 20), MAT.fan); fan.position.y = 0.03; unit.add(fan);
        const strip = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.01, 0.01), MAT.led(C.green)); strip.position.set(0, 0.03, 0.1); unit.add(strip);
        unit.userData = { strip, body: fb, fan }; gk.add(unit); coolingUnits.push(unit); objects[`cooling${i + 1}`] = fb;
      }
    }
    // two Pod W: inlet (front rail) and exhaust (rear rail)
    for (const [k, z, label] of [[1, D / 2 - 0.02, 'inlet'], [2, -D / 2 + 0.02, 'exhaust']]) {
      const pod = box(0.06, 0.09, 0.03, MAT.gateway, rx - W / 2 + 0.05, baseY + H * (k === 1 ? 0.5 : 0.7), rz + z); pod.userData = { type: 'pod', id: `pod${k}`, label }; edges(pod, 0x4c9dff, 0.5); gt.add(pod); pickables.push(pod); objects[`pod${k}`] = pod;
    }
    objects.controller = objects.edge; objects.gateway = objects.edge;
    // sensors: inlet probes on the front, outlet on the rear, room channels near the inlet Pod
    const geo = new THREE.SphereGeometry(0.012, 10, 8);
    for (const s of sensors) {
      const out = /^T_out/.test(s.id), inl = /^T_in/.test(s.id);
      const p = new THREE.Vector3(rx + (inl || out ? (s.location_m[2] - 1.2) * 0.05 : -W / 2 + 0.1), baseY + (inl || out ? Math.min(H - 0.05, 0.05 + (s.location_m[2] / 2.0) * H) : H * 0.4),
        rz + (out ? -D / 2 - 0.02 : D / 2 + 0.02));
      if (!inl && !out) p.x += 0.04 * (sensorMeshes.size % 4);
      const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x9fb3cc, emissive: 0x9fb3cc, emissiveIntensity: 0.6, roughness: 0.4 }));
      m.position.copy(p); m.userData = { type: 'sensor', id: s.id, spec: s }; gt.add(m); pickables.push(m); sensorMeshes.set(s.id, m); objects[`sensor:${s.id}`] = m;
    }
    // the plug-in power path: wall outlet -> UPS -> PDU -> IT (pulses colour on battery like the module tiers)
    const outlet = box(0.08, 0.12, 0.03, MAT.casting, -0.6, 0.35, -0.95); outlet.userData = { type: 'utility', id: 'utility' }; gs.add(outlet); pickables.push(outlet); objects.utility = outlet; objects.ats = outlet;
    objects.panel = objects.pdu || objects.ups;
    const upsPos = objects.ups.getWorldPosition(new THREE.Vector3());
    flows.push(Object.assign(new Flow([outlet.position.clone(), new THREE.Vector3(-0.6, 0.05, -0.9), new THREE.Vector3(upsPos.x, 0.05, -0.9), upsPos], { n: 6, size: 0.03 }), { role: 'utility' }));
    flows.push(Object.assign(new Flow([upsPos, new THREE.Vector3(rx, baseY + H * 0.5, rz)], { n: 3, size: 0.025 }), { role: 'rack', index: 0 }));
    for (const f of flows) gp.add(f.group);
  }

  const sensorClip = new THREE.BoxGeometry(0.016, 0.03, 0.012).translate(0, -0.026, 0);
  function buildControls(cfg, d, sensors) {
    const g = groups.controls;
    // gateway / network cabinet on the cold-aisle wall at the door end
    const gw = box(0.45, 0.55, 0.18, MAT.gateway, -G.intL / 2 + (G.micro ? 0.2 : 0.5), G.floorTop + (G.micro ? 1.2 : 1.7), -(G.intW / 2 - 0.09));
    gw.userData = { type: 'controller', id: 'controller' }; g.add(gw); pickables.push(gw); objects.controller = gw; objects.gateway = gw;
    gw.material = mats6(MAT.gateway, { '+z': new THREE.MeshStandardMaterial({ map: EQ.bezelTex('edge', 4, false), roughness: 0.5, metalness: 0.4 }) });
    G.wallMounted = [{ obj: gw, side: -1 }];   // hangs on the cold-side long wall: goes with it when the cutaway takes that wall off
    for (let k = 0; k < 4; k++) gw.add(new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.03, 0.01), MAT.led(k % 2 ? C.cyan : C.green)).translateX(-0.15 + k * 0.08).translateY(0.2).translateZ(0.115));
    // leak-detection rope along the floor under the rack row (BEN Pod leak input)
    const ropeMat = new THREE.MeshStandardMaterial({ color: 0xf2c94c, roughness: 0.8 });
    for (let r = 0; r < (G.rowZ || [G.zOff]).length; r++) {
      const rope = new THREE.Mesh(new THREE.BoxGeometry(G.intL - (G.hall ? 1.4 : 0.3), 0.015, 0.04), ropeMat);
      rope.position.set(0, G.floorTop + 0.01, (G.rowZ ? G.rowZ[r] : G.zOff) + G.rackD / 2 + 0.06); rope.userData = { type: 'leak_rope', id: 'leak_rope', index: r }; g.add(rope); pickables.push(rope); if (r === 0) objects.leak_rope = rope;
    }
    // sensors as small spheres (clamped into the interior)
    const r = G.micro ? 0.015 : 0.018;
    const geo = new THREE.SphereGeometry(r, 12, 10);
    for (const s of sensors) {
      const rm = /_r(\d+)(_|$)/.exec(s.id);
      const p = toThree(s.location_m, rm ? +rm[1] - 1 : undefined);
      p.x = THREE.MathUtils.clamp(p.x, -G.intL / 2 + 0.08, G.intL / 2 - 0.08);
      p.z = THREE.MathUtils.clamp(p.z, -G.intW / 2 + 0.08, G.intW / 2 - 0.08);
      p.y = THREE.MathUtils.clamp(p.y + G.floorTop, G.floorTop + 0.03, G.ceiling - 0.08);
      const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x9fb3cc, emissive: 0x9fb3cc, emissiveIntensity: 0.6, roughness: 0.4 }));
      m.add(new THREE.Mesh(sensorClip, EM.equipDark));   // probe clip / housing
      m.position.copy(p); m.userData = { type: 'sensor', id: s.id, spec: s }; g.add(m); pickables.push(m); sensorMeshes.set(s.id, m); objects[`sensor:${s.id}`] = m;
    }
  }

  function buildFx(cfg, d) {
    if (!G.subs.has('cooling')) return;
    const n = Math.min(720, Math.max(160, (G.racks || 1) * 90));
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const mat = pointsMaterial({ size: G.micro ? 0.008 : 0.014, maxPx: 4, opacity: 0.75, fadeNear: G.micro ? 0.3 : 0.8, vertexColors: true });
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
    if (G.hd && st.loop) for (let k = 0; objects[`cdu${k + 1}`]; k++) { const c = objects[`cdu${k + 1}`]; const pump = (st.loop.pumps || [])[k]; if (c.userData.strip) c.userData.strip.material = MAT.led(pump && !pump.ok ? C.red : (st.loop.flow_low ? C.hold : C.green)); }
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
      else if (s.kind === 'contact') color = st.door_open ? C.hold : C.green;
      else if (s.kind === 'power') color = p.utility_ok ? C.green : C.red;
      else color = C.info;
      m.material.color.setHex(color); m.material.emissive.setHex(color);
    }
    // power flows
    const lost = !p.utility_ok, battery = p.ups_on_battery, low = p.ups_soc_pct < 30;
    const flowColor = lost && low ? C.red : (battery ? C.hold : C.green);
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
      if (highlights.has(k)) { highlights.get(k).material.color.setHex(w.sev >= 2 ? C.red : C.hold); continue; }
      const o = makeOutline(w.obj, w.sev >= 2 ? C.red : C.hold); if (o) { groups.hl.add(o); highlights.set(k, o); }
    }
  }
  function alarmTargetLocal(a) {
    let m;
    if ((m = /^rack(\d+)_/.exec(a.id))) return { type: 'rack', index: +m[1] - 1, id: `rack${m[1]}` };
    if ((m = /^cool(\d+)_/.exec(a.id))) return { type: 'cooling', index: +m[1] - 1, id: `cooling${m[1]}` };
    if (a.id === 'utility_loss') return { type: 'ats', id: 'ats' };
    if (a.id === 'ups_low') return G.dc800 ? { type: 'battery', id: 'battery' } : { type: 'ups', id: 'ups' };
    if (a.id === 'dc_ground_fault' || a.id === 'dc_bus_voltage' || a.id === 'dc_arc') return { type: 'dc_busway', id: 'dc_busway' };
    if (/^cdu_pump\d+_fail$/.test(a.id) || a.id === 'loop_flow_low' || a.id === 'loop_supply_high') return { type: 'cdu', id: G.hd ? 'cdu1' : 'cdu' };
    if (a.id === 'loop_isolated') return { type: 'manifold', id: 'manifold1', index: 0 };
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
  // cdu<k> / manifold<k> ids (dlc_hd) are already unique per object; dc_busway tap-offs share one key with the busway
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
    const order = { container: 0, doors: 1, vestibule: 1.5, rack: 2, ai_box: 2.1, nas: 2.2, switch: 2.3, pdu: 2.4, cooling: 3, fancoil: 3.2, fanwall: 3.5, drycooler: 4, trim_chiller: 4.2, skid: 4.3, cdu: 5, manifold: 5.2, powermodule: 5.5, transformer: 5.7, switchgear: 5.8, ups: 6, rectifier: 6.1, dc_busway: 6.2, battery: 7, ats: 8, panel: 9, utility: 10, generator: 11, controller: 12, tray: 13, containment: 14, leak_rope: 15, plinth: 15.5, armour: 15.6, sensor: 16 };
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
  /** Distance at which a span of `w` metres (and `h` metres tall) fills the view with a margin. */
  function fitSpan(w, h = 0) {
    const vfov = THREE.MathUtils.degToRad(camera.fov), hfov = 2 * Math.atan(Math.tan(vfov / 2) * Math.max(0.5, camera.aspect || 1));
    return Math.max(w / 2 / Math.tan(hfov / 2), h / 2 / Math.tan(vfov / 2)) * 1.12;
  }
  // ---- clearance: bounding boxes of everything a camera or a walker must not sit in (racks, CDUs, power gear, pipes, walls)
  let solidCache = null;
  function solidBoxes() {
    if (!solidCache) solidCache = solids.filter(o => o.parent).map(o => { o.updateWorldMatrix(true, false); return new THREE.Box3().setFromObject(o); }).filter(b => !b.isEmpty());
    return solidCache;
  }
  const inContainer = (p, pad = 0) => !G.mini && Math.abs(p.x) < G.extL / 2 + pad && Math.abs(p.z) < G.extW / 2 + pad && p.y < G.extH + pad && p.y > 0;
  const _ray = new THREE.Ray(), _hit = new THREE.Vector3(), _bb = new THREE.Box3();
  function poseClear(p, look) {
    if (inContainer(p)) {   // inside: off the walls, floor and ceiling
      if (Math.abs(p.x) > G.intL / 2 - 0.15 || Math.abs(p.z) > G.intW / 2 - 0.15 || p.y > G.ceiling - 0.12 || p.y < G.floorTop + 0.3) return false;
    }
    const dir = new THREE.Vector3().subVectors(look, p).normalize();
    _ray.set(p, dir);
    for (const b of solidBoxes()) {
      if (_bb.copy(b).expandByScalar(0.18).containsPoint(p)) return false;
      if (_ray.intersectBox(b, _hit) && _hit.distanceTo(p) < 0.75) return false;   // nothing filling the frame right in front of the lens
    }
    return true;
  }
  /** Nudge a preset camera until it is clear of geometry: back along the view line first, then up / sideways. */
  function clearPose(pos, look) {
    const p = new THREE.Vector3(...pos), l = new THREE.Vector3(...look);
    if (poseClear(p, l)) return p.toArray();
    const back = new THREE.Vector3().subVectors(p, l).setY(0).normalize(), side = new THREE.Vector3(-back.z, 0, back.x), up = new THREE.Vector3(0, 1, 0);
    const dirs = [back, up, side, side.clone().negate(), up.clone().negate(), back.clone().add(up).normalize(), back.clone().add(side).normalize(), back.clone().sub(side).normalize()];
    const inside = inContainer(p);   // never push an interior camera through a wall (or an exterior one into the module)
    for (const s of [0.12, 0.25, 0.4, 0.6, 0.85, 1.2]) for (const dv of dirs) { const c = p.clone().addScaledVector(dv, s); if (inContainer(c) === inside && poseClear(c, l)) return c.toArray(); }
    return pos;
  }
  function rowSpan(xs, pad = 0.3) { return xs.length ? [Math.min(...xs) - pad, Math.max(...xs) + pad] : [-G.intL / 2, G.intL / 2]; }
  function presetPose(name) {
    const { extL, extW, extH, intL, intW, rackD, floorTop } = G;
    const eye = floorTop + 1.6;
    const zc = G.zOff - (rackD / 2 + G.coldW / 2), zh = G.zOff + rackD / 2 + G.hotW / 2;
    const outdoor = G.hall ? 22 : (objects.generator ? 2.6 : 0) + (objects.skid ? 5.5 : 2.2); // utility pedestal / generator / skid outside the ends (hall: power module + yards)
    const R = 0.5 * Math.hypot(extL + outdoor, extW + (G.hall ? 16 : 1.2), extH + 0.9);
    const centre = [G.hall ? -4 : (objects.skid ? 1.6 : (objects.generator ? 0 : -0.6)), extH * 0.45, G.hall ? 1.5 : 0];
    if (G.cluster && (name === 'exterior_iso' || name === 'roof')) {   // the whole yard: modules, skids, transformers, lanes
      const y = G.cluster.yard, site = y.site;
      const cx = ((site[0] + site[2]) / 2) / 1000 - extL / 2, cz = -(((site[1] + site[3]) / 2) / 1000 - extW / 2);
      const Rc = 0.5 * Math.hypot(y.site_l_m, y.site_w_m, extH);
      const v = name === 'roof' ? new THREE.Vector3(-0.2, 1.0, 0.6) : new THREE.Vector3(-0.7, 0.5, 0.95);
      const dd = fitDistance(Rc * (name === 'roof' ? 0.62 : 0.66)); v.normalize().multiplyScalar(dd);
      return { pos: [cx + v.x, extH * 0.4 + v.y, cz + v.z], look: [cx, extH * 0.3, cz], cutaway: false };
    }
    if (G.hall) {
      const z0 = G.rowZ[0], zc0 = z0 - (rackD / 2 + G.aisleW / 2), zh0 = z0 + rackD / 2 + G.aisleW / 2;
      switch (name) {
        case 'cold_aisle': return { pos: [-intL / 2 + 0.9, eye, zc0], look: [intL / 2, eye - 0.45, zc0 + 0.3], cutaway: false };
        case 'hot_aisle': return { pos: [intL / 2 - 0.9, eye, zh0], look: [-intL / 2, eye - 0.45, zh0 - 0.3], cutaway: false };
        case 'power_room': { const pm = objects.pm ? objects.pm.position.x : -extL / 2 - 6; return { pos: [pm - 7, extH + 4, -10], look: [pm, 1.2, 0], cutaway: true }; }
        case 'roof': { const d = fitDistance(R * 0.6), v = new THREE.Vector3(-0.2, 1.0, 0.6).normalize().multiplyScalar(d); return { pos: [centre[0] + v.x, extH + v.y, centre[2] + v.z], look: [centre[0], extH, centre[2]], cutaway: false }; }
        default: { const d = fitDistance(R * 0.95), v = new THREE.Vector3(-0.7, 0.42, 0.95).normalize().multiplyScalar(d); return { pos: [centre[0] + v.x, centre[1] + v.y, centre[2] + v.z], look: centre, cutaway: false }; }
      }
    }
    if (G.mini) { // BEN 1 in an office corner: every preset looks at the rack from the room
      const rx = G.rackX[0], rz = G.rackZ[0], ry = G.form === 'rack10' ? 0.74 : 0, cy = ry + extH / 2, W = extL, D = extW, H = extH;
      if (name === 'hot_aisle') { const sx = G.form === 'rack10' ? -1 : 1; return { pos: [rx + sx * (W / 2 + 0.6), ry + H + 0.6, rz - D / 2 + 0.1], look: [rx, ry + H * 0.55, rz - D / 2], cutaway: false }; }   // over the shoulder at the exhaust side (rack10: away from the UPS tower)
      if (name === 'power_room') return { pos: [rx + 0.5, ry + 0.55, rz + D / 2 + 0.85], look: [rx + (G.form === 'rack10' ? W / 2 + 0.12 : 0), ry + 0.15, rz + D / 4], cutaway: false };
      if (name === 'cold_aisle') return { pos: [rx + 0.25, ry + H * 0.6 + 0.3, rz + D / 2 + 1.0], look: [rx, ry + H * 0.5, rz + D / 2], cutaway: false };
      if (name === 'roof') return { pos: [rx + 0.5, ry + H + 1.0, rz + 0.75], look: [rx, ry + H, rz], cutaway: false };
      return { pos: [2.1, 1.7, 2.3], look: [0, 0.7, -0.4], cutaway: false };
    }
    if (G.micro && name !== 'exterior_iso' && name !== 'roof') { // a cabinet: look in from outside with the shell cut open
      const side = name === 'hot_aisle' ? 1 : -1;
      if (name === 'power_room') return { pos: [-extL / 2 - 1.6, extH * 0.9, -extW * 0.9], look: [-intL / 2 + 0.3, floorTop + 0.45, 0], cutaway: true, doors: true };
      return { pos: [extL * 0.35, extH * 1.05, side * (extW / 2 + 1.5)], look: [0, floorTop + G.rackH * 0.5, 0], cutaway: true };
    }
    const [r0, r1] = rowSpan(G.rackX), rcx = (r0 + r1) / 2;
    const zFront = G.zOff - rackD / 2;
    // BEN 2000: the next module stands on the -z side, so section views from that side look down steeply from the gap between modules
    const gapNeg = G.cluster ? Math.max(1.0, G.cluster.yard.pitch_mm / 1000 - extW) : 99;
    const negSide = (dist, x, lookY, lookZ, y) => gapNeg < dist ? { pos: [x, extH + 2.6, -extW / 2 - gapNeg * 0.5], look: [x, lookY, lookZ] } : { pos: [x, y, -intW / 2 - dist], look: [x, lookY, lookZ] };
    switch (name) {
      case 'cold_aisle': {   // in the aisle, rack fronts running away on the side
        // stand close to the cold-side wall a little before the first rack and look diagonally down the row of fronts
        const x0 = G.dense ? Math.max(-intL / 2 + 0.5, r0 - 1.9) : -intL / 2 + Math.max(0.75, G.bayL - 0.2);
        const z0 = Math.min(zc, -intW / 2 + 0.24);
        return { pos: [x0, eye, z0], look: [Math.min(intL / 2 - 0.3, r1 + 0.4), eye - 0.6, zFront - Math.min(0.12, G.coldW * 0.2)], cutaway: false };
      }
      case 'hot_aisle': {
        if (G.hotW < 0.95) {   // a 200 mm rear plenum (dense) or a sub-metre hot aisle: take the near wall off and look at the rack rears, manifolds and hoses
          const dist = Math.max(3.2, fitSpan(r1 - r0 + 0.6, 2.2) * 0.95);
          return { pos: [rcx - 0.3, floorTop + 2.1, intW / 2 + Math.max(2.4, dist)], look: [rcx, floorTop + 1.15, G.zOff + rackD / 2], cutaway: true };
        }
        return { pos: [intL / 2 - 0.3, eye, Math.max(zh, intW / 2 - 0.22)], look: [r0 - 0.2, eye - 0.65, G.zOff + rackD / 2 + 0.05], cutaway: false };
      }
      case 'power_room': {
        if (G.dense) {   // switchboard sections, UPS frames and lithium cabinets face the cold aisle: section view from the aisle side
          const [p0, p1] = rowSpan(G.powerItems.map(it => it.x), 0.55), pcx = (p0 + p1) / 2;
          const dist = Math.max(3.0, fitSpan(p1 - p0, 2.4)) * 0.82, v = negSide(dist, pcx, floorTop + 1.0, intW / 2 - 0.6, floorTop + 2.3);
          return { pos: [v.pos[0] + 0.35, v.pos[1], v.pos[2]], look: v.look, cutaway: true };
        }
        return { pos: [-intL / 2 + G.bayL + 2.3, extH + 1.2, -(intW / 2 + 1.5)], look: [-intL / 2 + G.bayL * 0.55, floorTop + 0.8, 0.05], cutaway: true };   // power bay with the first racks beside it
      }
      case 'compute': {   // tour: rack fronts in section from the cold-aisle side
        const dist = Math.max(2.8, fitSpan(r1 - r0 + 0.4, 2.4)) * 0.85, v = negSide(dist, rcx, floorTop + 1.1, G.zOff, floorTop + 2.4);
        return { pos: [v.pos[0] - 0.4, v.pos[1], v.pos[2]], look: v.look, cutaway: true };
      }
      case 'roof': {
        if (objects.skid) {   // dense: the roof is clean, the heat goes to the skid beside the blind end
          const sk = objects.skid.position, v = new THREE.Vector3(0.25, 0.9, 0.85).normalize().multiplyScalar(fitDistance(4.4));
          return { pos: [sk.x - 1.4 + v.x, v.y, v.z], look: [sk.x - 1.4, 1.0, 0], cutaway: false };
        }
        const d = fitDistance(Math.max(2.6, extL * 0.58)), v = new THREE.Vector3(-0.3, 0.95, 0.8).normalize().multiplyScalar(d);
        return { pos: [v.x, extH + v.y, v.z], look: [0, extH + 0.3, 0], cutaway: false };
      }
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
    const pos = clearPose(pose.pos, pose.look);
    flyTo(new THREE.Vector3(...pos), new THREE.Vector3(...pose.look), instant || reduce ? 0 : 0.9);
    applyCutaway();
    notify();
  }
  function flyTo(pos, look, dur) {
    orbit.enabled = true;
    if (dur <= 0) { camera.position.copy(pos); orbit.target.copy(look); camera.lookAt(look); orbit.update(); camTween = null; applyCutaway(); return; }
    camTween = { p0: camera.position.clone(), l0: orbit.target.clone(), p1: pos, l1: look, t0: performance.now(), dur };
  }
  function ghost(mesh, on) { // hall power module: transparent but still casting shadows
    if (!mesh) return;
    const m = mesh.material; m.transparent = true; m.opacity = on ? 0.06 : 1; m.depthWrite = !on; mesh.renderOrder = on ? 5 : 0;
  }
  /** Architectural section: the roof (with its luminaires) comes off and the long wall nearest the camera is cut down to a sill
   *  showing the wall build-up (steel skin, PIR core, liner); zone labels name what you are looking at. Inside, nothing is cut. */
  function applyCutaway() {
    if (G.mini) return;
    const c = camera.position;
    const inside = Math.abs(c.z) < G.extW / 2 && Math.abs(c.x) < G.extL / 2 && c.y < G.extH;
    const cut = mode.cutaway && !inside;
    if (roof) roof.visible = !cut;
    for (const cap of G.caps || []) cap.visible = cut;
    if (G.hall && G.pmRoof) { ghost(G.pmRoof, cut); for (const w of G.pmWalls || []) ghost(w, cut && c.y > G.extH * 0.6); }
    const nearSide = c.z >= 0 ? 1 : -1;
    for (const w of G.wallStubs || []) { const isNear = cut && w.side === nearSide; w.full.visible = !isNear; w.stub.visible = isNear; }
    for (const w of G.wallMounted || []) w.obj.visible = !(cut && w.side === nearSide);
    for (const dcl of decals) dcl.visible = !(cut && ((dcl.position.z > 0) === (c.z >= 0)));
    if (G.zoneLabels) G.zoneLabels.visible = cut && !mode.walk;
    const sig = `${cut}|${nearSide}`; if (sig !== cutSig) { cutSig = sig; renderer.shadowMap.needsUpdate = true; }
  }
  let cutSig = '';
  function toggleCutaway() { mode.cutaway = !mode.cutaway; applyCutaway(); notify(); return mode.cutaway; }
  function toggleDoors() { mode.doors = !mode.doors; if (state) update(state); notify(); return mode.doors; }
  function notify() { api.onModeChange && api.onModeChange({ ...mode }); }
  /** Floating zone tags for the section view. */
  function buildZoneLabels(cfg, d) {
    if (G.mini || G.micro || G.hall) return;
    const grp = new THREE.Group(); grp.visible = false;
    const yA = G.ceiling + 0.35, yB = G.ceiling + 0.95;
    const add = (title, sub, color, x, y, z) => { const sp = EQ.zoneLabel(title, sub, color); sp.position.set(x, y, z); grp.add(sp); };
    const avg = (xs) => xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length);
    const [r0, r1] = rowSpan(G.rackX, 0);
    if (G.dense) {
      add('POWER', d.swbd_sections ? 'switchboard · UPS · batteries' : 'UPS · lithium batteries', '#2BB673', avg(G.powerItems.map(i => i.x)), yA, 0.2);
      add('COOLING', 'CDUs · fan coils', '#5CD6FF', avg(G.unitX), yB, 0.2);
      add('IT', `${cfg.racks} × liquid racks`, '#4C9DFF', (r0 + r1) / 2, yA, 0.2);
      if (objects.skid) add('HEAT REJECTION', 'dry coolers · trim chiller', '#FF8A3D', objects.skid.position.x, 2.4, 0);
    } else {
      add('POWER', 'UPS · batteries · ATS', '#2BB673', -G.intL / 2 + Math.max(0.4, G.bayL / 2), yA, 0);
      add('IT', `${cfg.racks} racks`, '#4C9DFF', (r0 + r1) / 2, yA, 0);
      const cool = G.air ? 'in-row coolers' : G.water ? 'rear-door coils' : 'CDU · manifolds';
      add('COOLING', cool, '#5CD6FF', G.unitX.length ? avg(G.unitX) : (r0 + r1) / 2 + 0.8, yB, 0);
      add('HEAT REJECTION', G.air ? 'roof condensers' : 'roof dry coolers', '#FF8A3D', 0.6, G.extH + 1.25, 0);
    }
    groups.fx.add(grp); G.zoneLabels = grp;
  }

  // --------------------------------------------------------------------------- walkthrough
  const keys = new Set(); const walkPos = new THREE.Vector3();
  document.addEventListener('keydown', (e) => { if (mode.walk) keys.add(e.code); });
  document.addEventListener('keyup', (e) => keys.delete(e.code));
  walk.addEventListener('unlock', () => { if (mode.walk && !walkNoLock) exitWalk(); });
  // own mouse look (the vendored control's handler is detached): ignores the spurious jump some browsers send right after the
  // lock, clamps per-event deltas, and also works as click-drag look when the pointer is not locked
  canvas.ownerDocument.removeEventListener('mousemove', walk._onMouseMove);
  const look = { yaw: 0, pitch: 0, ignoreUntil: 0, drag: null };
  const _eul = new THREE.Euler(0, 0, 0, 'YXZ');
  function syncLook() { _eul.setFromQuaternion(camera.quaternion, 'YXZ'); look.yaw = _eul.y; look.pitch = _eul.x; }
  walk.addEventListener('lock', () => { look.ignoreUntil = performance.now() + 180; syncLook(); });
  document.addEventListener('mousemove', (e) => {
    if (!mode.walk) return;
    let dx, dy;
    if (walk.isLocked) { if (performance.now() < look.ignoreUntil) return; dx = e.movementX; dy = e.movementY; }
    else if (look.drag) { dx = e.clientX - look.drag[0]; dy = e.clientY - look.drag[1]; look.drag = [e.clientX, e.clientY]; }
    else return;
    dx = THREE.MathUtils.clamp(dx || 0, -60, 60); dy = THREE.MathUtils.clamp(dy || 0, -60, 60);
    look.yaw -= dx * 0.0022; look.pitch = THREE.MathUtils.clamp(look.pitch - dy * 0.0022, -1.25, 1.25);
    _eul.set(look.pitch, look.yaw, 0, 'YXZ'); camera.quaternion.setFromEuler(_eul);
  });
  canvas.addEventListener('pointerdown', (e) => { if (mode.walk && !walk.isLocked) { look.drag = [e.clientX, e.clientY]; if (!walkNoLock) { try { walk.lock(); } catch (_) { /* headless */ } } } });
  document.addEventListener('pointerup', () => { look.drag = null; });
  let walkNoLock = false;
  const EYE = 1.6;
  function enterWalk({ lock = true } = {}) {
    if (!payload) return; tour.stop(false); setHover(null); camTween = null;
    mode.walk = true; mode.cutaway = true; orbit.enabled = false; walkNoLock = !lock;
    const eye = (G.micro || G.mini ? 0 : G.floorTop) + EYE;
    if (G.mini) { camera.position.set(1.6, eye, 1.7); camera.lookAt(G.rackX[0], 0.9, G.rackZ[0]); }
    else if (G.micro) { camera.position.set(-G.extL / 2 - 2.3, eye, 0.4); camera.lookAt(0, G.floorTop + 0.8, 0); }
    else {
      // just inside the door, in the (first) cold aisle, looking down it toward the far end
      const zc = G.hall ? G.rowZ[0] - (G.rackD / 2 + G.aisleW / 2) : G.zOff - (G.rackD / 2 + G.coldW / 2);
      const p = new THREE.Vector3(-G.intL / 2 + 0.45, eye, zc);
      for (let k = 0; k < 40 && !collide(p.clone()); k++) p.x += 0.15;
      camera.position.copy(p); camera.lookAt(G.intL / 2, eye - 0.15, zc + (G.hall ? 0.15 : 0.1));
    }
    syncLook();
    if (lock) { try { walk.lock(); } catch (_) { /* headless */ } }
    if (walkHint) walkHint.hidden = false;
    applyCutaway(); notify();
  }
  function exitWalk() {
    if (!mode.walk) return;
    mode.walk = false; keys.clear(); look.drag = null; if (walk.isLocked) walk.unlock();
    orbit.enabled = true; orbit.target.copy(camera.position).add(camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(3)); orbit.update();
    if (walkHint) walkHint.hidden = true;
    applyCutaway(); notify();
  }
  function toggleWalk() { mode.walk ? exitWalk() : enterWalk(); }
  /** Collision: interior walls, then the footprint of every solid that reaches below head height (overhead pipes and trays pass). */
  function collide(p) {
    const m = 0.25;
    if (G.mini) { p.x = THREE.MathUtils.clamp(p.x, -0.75, 2.1); p.z = THREE.MathUtils.clamp(p.z, -0.05, 2.1); const rx = G.rackX[0], rz = G.rackZ[0]; return !(Math.abs(p.x - rx) < G.extL / 2 + 0.35 && Math.abs(p.z - rz) < G.extW / 2 + 0.35) && !(p.x > 0.2 && p.z < 0.05); }
    if (G.micro) { // outdoor cabinet: walk the pad, the cabinet is the obstacle
      p.x = THREE.MathUtils.clamp(p.x, -4, 4); p.z = THREE.MathUtils.clamp(p.z, -4, 4);
      return !(Math.abs(p.x) < G.extL / 2 + 0.7 && Math.abs(p.z) < G.extW / 2 + 0.7);
    }
    // body radius: 0.25 m, less in a narrow aisle (a 20 ft module's cold aisle is about 0.5 m) so the walker still fits
    const aisle = G.hall ? G.aisleW : G.coldW, mw = Math.min(m, aisle / 2 - 0.04), me = Math.min(0.22, aisle / 2 - 0.08);
    if (Math.abs(p.x) > G.intL / 2 - mw || Math.abs(p.z) > G.intW / 2 - mw) return false;
    const lo = G.floorTop + 0.05, hi = G.floorTop + EYE + 0.15;
    for (const b of solidBoxes()) {
      if (b.max.y < lo || b.min.y > hi) continue;
      if (p.x > b.min.x - me && p.x < b.max.x + me && p.z > b.min.z - me && p.z < b.max.z + me) return false;
    }
    return true;
  }
  function stepWalk(dt) {
    const run = keys.has('ShiftLeft') || keys.has('ShiftRight');
    const sp = (run ? 3.0 : 1.4);
    const f = (keys.has('KeyW') || keys.has('ArrowUp') ? 1 : 0) - (keys.has('KeyS') || keys.has('ArrowDown') ? 1 : 0);
    const r = (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) - (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0);
    camera.position.y = (G.micro || G.mini ? 0 : G.floorTop) + EYE;
    if (!f && !r) return;
    const dir = camera.getWorldDirection(new THREE.Vector3()); dir.y = 0; dir.normalize();
    const right = new THREE.Vector3().crossVectors(dir, new THREE.Vector3(0, 1, 0));
    const mv = new THREE.Vector3().addScaledVector(dir, f).addScaledVector(right, r); if (mv.lengthSq() > 1) mv.normalize(); mv.multiplyScalar(sp * dt);
    // slide along obstacles: try the full move, then each axis on its own
    for (const t of [mv, new THREE.Vector3(mv.x, 0, 0), new THREE.Vector3(0, 0, mv.z)]) {
      walkPos.copy(camera.position).add(t);
      if (collide(walkPos)) { camera.position.x = walkPos.x; camera.position.z = walkPos.z; break; }
    }
  }

  // --------------------------------------------------------------------------- guided tour
  // Each stop holds its framing for most of its slot. Between two outside stops the camera flies (lifted over the module);
  // into or out of the enclosure it dips to the background colour and cuts, so no frame ever shows the inside of a wall.
  let tourWantsDoors = false;
  const fadeEl = (() => { const el = document.createElement('div'); el.className = 'tour-fade'; el.style.cssText = 'position:absolute;inset:0;background:#06101f;opacity:0;pointer-events:none;'; canvas.insertAdjacentElement('afterend', el); return el; })();
  const smooth = (x) => x * x * (3 - 2 * x);
  const tour = { running: false, t: 0, total: 0, stops: [],
    start() { if (!payload) return; exitWalk(); camTween = null; orbit.enabled = false; this.running = true; this.t = 0; mode.tour = true; mode.cutaway = true; this.apply(0); notify(); },
    stop(doNotify = true) { fadeEl.style.opacity = 0; if (!this.running) { tourWantsDoors = false; return; } this.running = false; mode.tour = false; tourWantsDoors = false; if (caption) caption.hidden = true; orbit.enabled = true; orbit.target.copy(camera.position).add(camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(4)); orbit.update(); if (state) update(state); if (doNotify) notify(); },
    toggle() { this.running ? this.stop() : this.start(); },
    seek(frac) { if (!this.running) this.start(); this.t = THREE.MathUtils.clamp(frac, 0, 0.9999) * this.total; this.apply(this.t); },
    apply(t) {
      const n = this.stops.length; if (!n) return;
      const u = THREE.MathUtils.clamp(this.total ? t / this.total : 0, 0, 0.99999) * n, k = Math.floor(u), f = u - k;
      const s = this.stops[k], nx = this.stops[Math.min(n - 1, k + 1)];
      let pos = s.pos, lk = s.look, fade = 0;
      const prev = this.stops[Math.max(0, k - 1)];
      if (!reduce && k < n - 1 && nx !== s) {
        if (s.inside || nx.inside) { if (f > 0.95) fade = (f - 0.95) / 0.05; }
        else if (f > 0.6) {
          const e = smooth((f - 0.6) / 0.4);
          pos = new THREE.Vector3().lerpVectors(s.pos, nx.pos, e); lk = new THREE.Vector3().lerpVectors(s.look, nx.look, e);
          // lift the path over the module when the straight line would cut through it
          const mid = new THREE.Vector3().lerpVectors(s.pos, nx.pos, 0.5);
          if (inContainer(mid, 1.2)) pos.y += Math.sin(Math.PI * e) * (G.extH + 2.5 - Math.min(s.pos.y, nx.pos.y) * 0.5);
        }
      }
      if (!reduce && k > 0 && (s.inside || prev.inside) && f < 0.05) fade = 1 - f / 0.05;
      camera.position.copy(pos); camera.lookAt(lk);
      fadeEl.style.opacity = fade.toFixed(3);
      tourWantsDoors = !!s.doors;
      if (caption) { caption.hidden = false; caption.innerHTML = `<b>${k + 1} / ${n} · ${s.title}</b>${s.text}`; }
      applyCutaway();
    },
    step(dt) { if (!this.running) return; this.t += dt; if (this.t >= this.total) { this.stop(); return; } this.apply(this.t); },
  };
  function finishTour(stops) {
    for (const s of stops) { const p = clearPose(s.pos.toArray(), s.look.toArray()); s.pos.fromArray(p); s.inside = inContainer(s.pos); }
    tour.stops = stops;
    tour.total = reduce ? stops.length * 4 : 7.5 * stops.length;
  }
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
      finishTour(stops);
      return;
    }
    if (G.mini) {
      const rx = G.rackX[0], rz = G.rackZ[0], ry = G.form === 'rack10' ? 0.74 : 0;
      const stops = [
        { title: `${d.tier_label} · ${d.form_label}`, text: `${cfg.it_kw} kW IT for a small business, on a 120 V plug: ${d.outlet_circuit}. ${d.room_cooling_note.split('.')[0]}.`, pos: [2.2, 1.9, 2.4], look: [rx, ry + extH / 2, rz] },
        { title: 'The IT', text: G.form === 'rack10' ? `Desktop AI boxes on 2U shelves in a 10-inch 8U rack, a managed switch and a 10-inch PDU; the 2U lithium UPS stands beside it.` : `A 2U short-depth GPU server, NAS, switch and 2U lithium UPS in a sound-damped 12U cabinet (${d.geometry.insertion_loss_db} dB).`, pos: [rx + 0.4, ry + extH * 0.8, rz + 1.2], look: [rx, ry + extH / 2, rz] },
        { title: 'Air and noise', text: `Office air in at the front, out at the back${G.form === 'cab12' ? ' through the N+1 extraction fans' : ''}; estimated ${d.noise_dba_est} dBA at 1 m (target ${d.noise_dba_target}). All ${d.heat_to_room_w} W stays in the room.`, pos: [rx + extL / 2 + 0.6, ry + extH + 0.6, rz - extW / 2 + 0.1], look: [rx, ry + extH * 0.55, rz - extW / 2] },
        { title: 'BEN Controls Mini', text: `Two BEN Pods (inlet and exhaust) on the BEN Mesh; the BEN Care agent runs on ${G.form === 'rack10' ? 'a fanless edge box on the top shelf' : 'the edge computer in the cabinet'} or the customer's own box.`, pos: [rx + 0.15, ry + extH * 0.7 + 0.2, rz + extW / 2 + 0.7], look: [rx - extL / 4, ry + extH * 0.6, rz + extW / 2] },
      ].map(s => ({ ...s, pos: new THREE.Vector3(...s.pos), look: new THREE.Vector3(...s.look) }));
      finishTour(stops);
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
    if (!G.micro) {   // frame real equipment at every stop (same presets as the camera buttons, plus a few tour-only views)
      const P = (n) => presetPose(n), V = (a) => new THREE.Vector3(...a);
      const zc = G.zOff - (rackD / 2 + G.coldW / 2);
      const heat = objects.skid ? { pos: [objects.skid.position.x + 3.2, 3.6, 5.6], look: [objects.skid.position.x - 0.6, 1.0, 0] } : P('roof');
      const views = [P('exterior_iso'),
        { pos: [-extL / 2 - 3.4, eye + 0.4, -extW * 0.55], look: [-extL / 2 + 1.2, floorTop + 1.1, 0.1] },
        P('cold_aisle'), P('compute'), P('hot_aisle'), P('power_room'),
        { pos: [-intL / 2 + 2.0, eye, zc + 0.2], look: [-intL / 2 + 0.45, floorTop + 1.45, -intW / 2] },
        heat,
        { pos: [extL * 0.55, extH * 1.2 + 1.2, -(extW * 1.6 + extL * 0.35 + 2.5)], look: [0.8, extH * 0.4, 0] }];
      stops.forEach((s, i) => { if (views[i]) { s.pos = V(views[i].pos); s.look = V(views[i].look); } });
    }
    finishTour(stops);
    void st;
  }

  // --------------------------------------------------------------------------- loop
  const clock = new THREE.Clock();
  function resize() {
    const parent = canvas.parentElement; const w = parent.clientWidth || 800, hgt = parent.clientHeight || 500;
    if (canvas.width !== Math.round(w * renderer.getPixelRatio()) || canvas.height !== Math.round(hgt * renderer.getPixelRatio())) { renderer.setSize(w, hgt, false); camera.aspect = w / hgt; camera.updateProjectionMatrix(); }
    PT.scale.value = canvas.height / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2)); PT.pr.value = renderer.getPixelRatio();
  }
  new ResizeObserver(resize).observe(canvas.parentElement);
  let pulse = 0;
  function frame() {
    const dt = Math.min(0.1, clock.getDelta());
    resize();
    if (camTween) { const k = Math.min(1, (performance.now() - camTween.t0) / 1000 / camTween.dur), e = k * k * (3 - 2 * k); camera.position.lerpVectors(camTween.p0, camTween.p1, e); orbit.target.lerpVectors(camTween.l0, camTween.l1, e); if (k >= 1) camTween = null; }
    if (mode.walk) stepWalk(dt); else if (tour.running) tour.step(dt); else orbit.update();
    // doors
    for (const l of doorLeaves) { const target = (l.target || 0) * THREE.MathUtils.degToRad(125) * -l.side; const cur = l.hinge.rotation.y; if (Math.abs(target - cur) > 1e-3) renderer.shadowMap.needsUpdate = true; l.hinge.rotation.y = reduce ? target : cur + (target - cur) * Math.min(1, dt * 3); }
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
    rowCount: () => (G.rowZ || []).length,
    // Rev 2 livery of the current build: { lineup, bandText, bodyColor, bandTexture, productLine, whiteLabel, brand }
    livery: () => livery && { lineup: livery.lineup, bandText: livery.bandText, bodyColor: livery.bodyColor, bandTexture: !!livery.bandTexture, productLine: livery.productLine || '', whiteLabel: !!livery.whiteLabel, brand: livery.brand || '' },
    // Rev 2: counts of the dense-row parts and the BEN 1 contents, for tests and the tour
    rev2Objects: () => { const n = (t) => pickables.filter(o => o.userData && o.userData.type === t).length; return { mini: !!G.mini, form: G.form, dense: !!G.dense, fancoils: n('fancoil'), cdus: n('cdu'), ups: n('ups'), batteries: n('battery'), switchgear: n('switchgear'), skid: !!objects.skid, aiBoxes: n('ai_box'), pods: n('pod'), desk: !!objects.desk, fans: n('cooling') }; }, clusterObjects: () => ({ cluster: !!G.cluster, modules: G.cluster ? G.cluster.modules : 0, transformers: pickables.filter(o => o.userData && o.userData.type === 'transformer').length, mvswgr: !!objects.mvswgr, yard: !!objects.yard, skids: pickables.filter(o => o.userData && o.userData.type === 'skid').length, cdus: pickables.filter(o => o.userData && o.userData.type === 'cdu').length }),
    hallObjects: () => ({ powermodule: !!objects.pm, transformers: pickables.filter(o => o.userData && o.userData.type === 'transformer').length, generators: pickables.filter(o => o.userData && o.userData.type === 'generator').length, fanwalls: pickables.filter(o => o.userData && o.userData.type === 'fanwall').length, plinth: !!objects.plinth, vestibule: !!objects.vestibule }),
    mode, camera, objects, G, renderer, three: scene, solidBoxes: () => solidBoxes().map(b => [b.min.toArray(), b.max.toArray()]),
    focus(sel) { // orbit camera to an object
      const obj = targetObject(sel); if (!obj) return; const c = new THREE.Box3().setFromObject(obj).getCenter(new THREE.Vector3());
      mode.cutaway = true; applyCutaway(); const dir = new THREE.Vector3(0.6, 0.5, -1).normalize(); exitWalk(); tour.stop(false);
      flyTo(c.clone().addScaledVector(dir, 3), c, reduce ? 0 : 0.8); setSelection(sel); notify();
    },
  });
  return api;
}
