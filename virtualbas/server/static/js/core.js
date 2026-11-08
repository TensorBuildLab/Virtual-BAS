/* =============================================================================
 * core.js - shared state, REST helpers, value formatting, observed-vs-truth
 * comparison and the live "binding" mechanism.
 *
 * Every element that shows a point value carries `data-pid="<point id>"`.
 * After each snapshot, refreshBindings() walks those elements and fills
 *   .v  - present (observed) value          .u  - engineering unit
 *   .tv - EnergyPlus ground truth (only visible when the truth toggle is on)
 * and sets status classes: st-missing, st-warn, st-alarm, st-ovr (override).
 * Pages are therefore built once and only their text/classes change.
 * ========================================================================== */

/** Global application state. */
export const S = {
  info: null,          // /api/info
  equip: [],           // /api/equipment
  equipById: {},
  points: [],          // /api/points
  pointById: {},
  pointsByEquip: {},
  catalog: [],         // /api/faults/catalog
  snap: null,          // latest /api/snapshot?truth=1
  truth: false,        // ground-truth (inner space) toggle
  conn: 'connecting',  // ws | poll | offline
};

/** Software points (BAS-internal values) can be written through /api/write. */
export const SOFT_KINDS = new Set(['setpoint', 'command', 'virtual', 'status']);

// --------------------------------------------------------------------- DOM helpers
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ESC[c]);

// --------------------------------------------------------------------- REST
export async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  const txt = await r.text();
  let body = null;
  try { body = txt ? JSON.parse(txt) : null; } catch { body = txt; }
  if (!r.ok) {
    const msg = body && body.detail ? (typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)) : txt;
    throw new Error(`${r.status}: ${msg}`);
  }
  return body;
}
export const post = (path, body) => api(path, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
});
export const del = (path) => api(path, { method: 'DELETE' });

/** Small transient notification in the lower right corner. */
export function toast(msg, kind = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${kind}`;
  el.textContent = msg;
  $('#toasts').appendChild(el);
  setTimeout(() => el.classList.add('out'), 3800);
  setTimeout(() => el.remove(), 4400);
}

// --------------------------------------------------------------------- units & formatting
const UNIT_LABEL = { degC: '°C', 'm3/s': 'm³/s', 'W/m2': 'W/m²', '-': '', people: 'people' };
export const unitLabel = (u) => (u in UNIT_LABEL ? UNIT_LABEL[u] : (u || ''));

const DECIMALS = { degC: 1, '%RH': 0, '%': 0, ppm: 0, 'm3/s': 2, 'L/s': 1, kW: 1, Pa: 0, kPa: 1, 'W/m2': 0, 'm/s': 1, people: 0, '-': 2 };

/** Enumerated / binary points get text states, as in a commercial BAS. */
function enumText(p, v) {
  const n = p.name;
  if (n === 'OCC-MODE') {
    if (p.equip_type === 'AHU') return ({ 0: 'OFF', 1: 'NIGHT CYCLE', 2: 'OCCUPIED' })[Math.round(v)] ?? String(v);
    return v >= 0.5 ? 'OCC' : 'UNOCC';
  }
  if (n === 'ECON-EN') return v >= 0.5 ? 'ENABLED' : 'DISABLED';
  if (n === 'ZN-OCC') return v >= 0.5 ? 'OCCUPIED' : 'VACANT';
  if (/(^|-)STS$/.test(n)) return v >= 0.5 ? 'ON' : 'OFF';
  if (/(^|-)CMD$/.test(n) && p.unit === '-') return v >= 0.5 ? 'ON' : 'OFF';
  return null;
}

/** Format a value of point `p` (point object) for display (without unit). */
export function fmtVal(p, v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '---';
  if (p) {
    const e = enumText(p, v);
    if (e !== null) return e;
  }
  const u = p ? p.unit : '';
  let d = DECIMALS[u] ?? 1;
  const a = Math.abs(v);
  if (u === 'kW' && a >= 100) d = 0;
  if (u === 'm3/s' && a >= 10) d = 1;
  if (u === 'L/s' && a >= 100) d = 0;
  return v.toFixed(d);
}
export const isEnum = (p) => p && enumText(p, 0) !== null;

/** Format with unit, e.g. "12.8 °C". */
export function fmtFull(pid, v) {
  const p = S.pointById[pid];
  const t = fmtVal(p, v);
  if (!p || isEnum(p) || t === '---') return t;
  const u = unitLabel(p.unit);
  return u ? `${t} ${u}` : t;
}

// --------------------------------------------------------------------- observed vs truth
/**
 * Tolerance used to flag a discrepancy between an observed value and the
 * EnergyPlus truth. tol = max(absolute, relative * |truth|).
 */
const TOL = {
  degC: [1.0, 0], '%RH': [6, 0], ppm: [100, 0], '%': [5, 0], 'm3/s': [0.05, 0.08], 'L/s': [0.5, 0.08],
  kW: [1, 0.08], Pa: [20, 0.15], kPa: [6, 0.12], 'W/m2': [40, 0.12], 'm/s': [1.0, 0], '-': [0.5, 0],
};
export function tolerance(p, truth) {
  const [a, r] = TOL[p.unit] ?? [0, 0.1];
  return Math.max(a, r * Math.abs(truth ?? 0));
}

/** Observed value [v, stale] of a point in the latest snapshot (undefined if not an observed point). */
export function obs(pid) { return S.snap?.points?.[pid]; }
/** Numeric present value (observed, or truth for truth-only points). */
export function val(pid) {
  const o = obs(pid);
  if (o) return o[0];
  const t = S.snap?.truth?.[pid];
  return t === undefined ? null : t;
}
export function truthVal(pid) { return S.snap?.truth?.[pid]; }

/**
 * Evaluate a point: present value, truth, deviation and status level.
 * level: 'ok' | 'warn' | 'alarm' | 'missing' | 'none'
 */
export function evalPoint(pid) {
  const p = S.pointById[pid];
  const o = obs(pid);
  const t = truthVal(pid);
  const res = { p, v: null, stale: false, truth: t, hasTruth: t !== undefined, dev: null, level: 'none', ovr: false, truthOnly: false };
  if (!p) return res;
  if (p.kind === 'truth') {
    res.truthOnly = true;
    res.v = t ?? null;
    return res;
  }
  if (o) { res.v = o[0]; res.stale = !!o[1]; }
  res.ovr = !!(S.snap?.overrides?.[pid] && Object.keys(S.snap.overrides[pid]).length);
  const measured = p.kind === 'sensor' || p.kind === 'meter';
  if (measured && (res.v === null || res.stale)) res.level = 'missing';
  else if (measured && res.hasTruth && t !== null && res.v !== null) {
    res.dev = res.v - t;
    const tol = tolerance(p, t);
    const ad = Math.abs(res.dev);
    res.level = ad > 2.5 * tol ? 'alarm' : ad > tol ? 'warn' : 'ok';
  } else if (measured) res.level = 'ok';
  return res;
}

/** Signed deviation text, e.g. "Δ+1.3". */
export function devText(r) {
  if (r.dev === null) return '';
  if (isEnum(r.p)) return '≠ E+';   // binary/enum disagreement
  const d = DECIMALS[r.p.unit] ?? 1;
  const s = r.dev >= 0 ? '+' : '−';
  return `Δ${s}${Math.abs(r.dev).toFixed(Math.min(d + 1, 3))}`;
}

// --------------------------------------------------------------------- binding markup
/**
 * HTML for a live value: <span class="pv" data-pid=..>value unit [truth] [badge]</span>
 * opts.unit=false hides the unit.
 */
export function pv(pid, opts = {}) {
  const p = S.pointById[pid];
  const cls = ['pv'];
  if (p && p.kind === 'truth') cls.push('truth-only');
  if (opts.cls) cls.push(opts.cls);
  const u = opts.unit === false || !p || isEnum(p) ? '' : unitLabel(p.unit);
  return `<span class="${cls.join(' ')}" data-pid="${esc(pid)}" title="${esc(pid)}"><span class="v">---</span>`
    + (u ? `<span class="u">${esc(u)}</span>` : '')
    + `<span class="tv"></span><span class="dbadge"></span></span>`;
}

/**
 * SVG "value box" (label + value + truth line) at x,y - the typical
 * BAS-graphic data tag next to a sensor or actuator.
 */
export function svgBox(pid, x, y, opts = {}) {
  const p = S.pointById[pid];
  const w = opts.w ?? 96;
  const label = opts.label ?? (p ? p.name : pid);
  const anchor = opts.anchor ?? 'start';
  const tx = anchor === 'middle' ? w / 2 : 6;
  const truthOnly = p && p.kind === 'truth' ? ' truth-only' : '';
  if (!p) return `<g class="vbox vbox-na" transform="translate(${x},${y})"><rect class="bg" width="${w}" height="34" rx="3"/><text class="lbl" x="${tx}" y="12" text-anchor="${anchor}">${esc(label)}</text><text class="v" x="${tx}" y="28" text-anchor="${anchor}">n/a</text></g>`;
  return `<g class="vbox${truthOnly}" data-pid="${esc(pid)}" transform="translate(${x},${y})">`
    + `<title>${esc(pid)} - ${esc(p.description)}</title>`
    + `<rect class="bg" width="${w}" height="34" rx="3"/>`
    + `<text class="lbl" x="${tx}" y="12" text-anchor="${anchor}">${esc(label)}</text>`
    + `<text class="v" x="${tx}" y="28" text-anchor="${anchor}">---</text>`
    + `<g class="tgrp"><rect class="tbg" y="35" width="${w}" height="15" rx="2"/><text class="tv" x="${tx}" y="46" text-anchor="${anchor}"></text></g>`
    + `</g>`;
}

/**
 * Refresh every bound element under root (default: whole document) from the
 * current snapshot. Cheap enough to run every second for ~1500 elements.
 */
export function refreshBindings(root = document) {
  if (!S.snap) return;
  const truthOn = S.truth;
  for (const el of root.querySelectorAll('[data-pid]')) {
    const r = evalPoint(el.dataset.pid);
    const p = r.p;
    const vEl = el.querySelector('.v');
    if (!vEl) continue;
    const isSvg = el instanceof SVGElement;
    let text = fmtVal(p, r.v);
    if (isSvg && p && !isEnum(p) && text !== '---') text += ' ' + unitLabel(p.unit);
    if (vEl.textContent !== text) vEl.textContent = text;
    const uEl = el.querySelector('.u');
    if (uEl && !uEl.textContent && p) uEl.textContent = unitLabel(p.unit);

    // truth text; binary/enum truth is only worth showing when it disagrees
    let tt = '';
    if (truthOn && r.hasTruth && !r.truthOnly && !(isEnum(p) && r.level === 'ok' && el.tagName !== 'TR')) {
      tt = (isSvg ? 'E+ ' : '') + fmtVal(p, r.truth);
      if (isSvg && r.dev !== null) tt += '  ' + devText(r);
    }
    const tEl = el.querySelector('.tv');
    if (tEl && tEl.textContent !== tt) tEl.textContent = tt;
    const bEl = el.querySelector('.dbadge');
    if (bEl) {
      let bt = '';
      if (r.level === 'missing') bt = r.stale ? 'STALE' : 'MISSING';
      else if (truthOn && (r.level === 'warn' || r.level === 'alarm')) bt = devText(r);
      if (bEl.textContent !== bt) bEl.textContent = bt;
      bEl.className = 'dbadge' + (bt ? ` lvl-${r.level}` : '');
    }
    const cl = el.classList;
    cl.toggle('st-missing', r.level === 'missing');
    cl.toggle('st-warn', truthOn && r.level === 'warn');
    cl.toggle('st-alarm', truthOn && r.level === 'alarm');
    cl.toggle('st-ovr', r.ovr);
    cl.toggle('has-truth', tt !== '');
  }
}

// --------------------------------------------------------------------- time helpers
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
/** Parse a naive ISO timestamp from the simulation as local wall-clock time. */
export const parseT = (s) => (s ? new Date(String(s).replace(' ', 'T')) : null);
const p2 = (n) => String(n).padStart(2, '0');
export const fmtHM = (d) => `${p2(d.getHours())}:${p2(d.getMinutes())}`;
export const fmtDate = (d) => `${DOW[d.getDay()]} ${d.getDate()} ${MON[d.getMonth()]} ${d.getFullYear()}`;
export const fmtDT = (s) => {
  const d = typeof s === 'string' ? parseT(s) : s;
  return d ? `${d.getDate()} ${MON[d.getMonth()]} ${fmtHM(d)}` : '-';
};
export const shortDay = (d) => `${DOW[d.getDay()]} ${d.getDate()} ${MON[d.getMonth()]}`;

// --------------------------------------------------------------------- hash routing
/** Parse "#page/arg?k=v&k2=v2" into {page, arg, q}. */
export function parseHash() {
  const raw = decodeURIComponent(location.hash.replace(/^#/, ''));
  const [path, query = ''] = raw.split('?');
  const [page, ...rest] = path.split('/');
  const q = {};
  for (const kv of query.split('&')) {
    if (!kv) continue;
    const i = kv.indexOf('=');
    q[i < 0 ? kv : kv.slice(0, i)] = i < 0 ? '1' : kv.slice(i + 1);
  }
  return { page: page || 'overview', arg: rest.join('/'), q };
}

// --------------------------------------------------------------------- equipment helpers
export const equipOfType = (t) => S.equip.filter((e) => e.type === t);
/** Short, readable zone label: "Perimeter_mid_ZN_1" -> "South · P1" (DOE orientation). */
const ORIENT = { 1: 'South', 2: 'East', 3: 'North', 4: 'West' };
export function zoneLabel(zone) {
  const m = /^Perimeter_(\w+?)_ZN_(\d)$/.exec(zone);
  if (m) return `${ORIENT[m[2]] ?? ''} · P${m[2]}`;
  if (zone.startsWith('Core')) return 'Core';
  return zone;
}
/** Points of an equipment as {NAME: pid}. */
export function pmap(eid) {
  const out = {};
  for (const p of S.pointsByEquip[eid] || []) out[p.name] = p.id;
  return out;
}
