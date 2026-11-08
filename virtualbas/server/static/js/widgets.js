/* =============================================================================
 * widgets.js - small live display elements shared by the IEQ, weather and
 * equipment pages. Like the value bindings in core.js they are built once as
 * HTML and refreshed in place by refreshWidgets() after every snapshot:
 *
 *   scale(key, pid)        threshold scale (coloured bands + value marker,
 *                          violet truth marker in truth mode)
 *   gaugeRow(key, pid, ..) label | value | scale | status chip | sparkline
 *   lamp(pid, label, type) status lamp (type 'alarm' = red when on, 'run' = green)
 *   pbar(pid, max)         thin horizontal bar (0..max)
 *   kvRows([[label, pid]]) <dt>/<dd> rows, silently skipping missing points
 * ========================================================================== */
import { S, esc, pv, val, truthVal, has, evalPoint } from './core.js';

const BIG = 1e9;
/**
 * Threshold definitions. bands: [from, to, level, label]; levels map to colours
 * (good / mod / warn / poor / cool / cold / warm / hot / low).
 */
export const SCALES = {
  co2: { min: 400, max: 1600, ticks: [800, 1100], bands: [[-BIG, 800, 'good', 'Good'], [800, 1000, 'mod', 'Fair'], [1000, 1100, 'warn', 'Elevated'], [1100, BIG, 'poor', 'Poor']] },
  pm25: { min: 0, max: 60, ticks: [12, 35], bands: [[-BIG, 12, 'good', 'Good'], [12, 15, 'mod', 'Fair (WELL 15)'], [15, 35, 'warn', 'Elevated'], [35, BIG, 'poor', 'Poor']] },
  pm10: { min: 0, max: 150, ticks: [50, 100], bands: [[-BIG, 50, 'good', 'Good'], [50, 100, 'warn', 'Elevated'], [100, BIG, 'poor', 'Poor']] },
  tvoc: { min: 0, max: 1000, ticks: [300, 500], bands: [[-BIG, 300, 'good', 'Good'], [300, 500, 'mod', 'Fair'], [500, BIG, 'poor', 'Poor']] },
  rh: { min: 0, max: 100, ticks: [30, 60], bands: [[-BIG, 30, 'mod', 'Dry'], [30, 60, 'good', 'Good'], [60, 70, 'mod', 'Humid'], [70, BIG, 'poor', 'Too humid']] },
  lux: { min: 0, max: 1200, ticks: [300, 750], bands: [[-BIG, 300, 'low', 'Low'], [300, 750, 'good', 'Good'], [750, BIG, 'mod', 'Bright']] },
  dba: { min: 20, max: 70, ticks: [40, 50], bands: [[-BIG, 40, 'good', 'Quiet'], [40, 50, 'mod', 'Moderate'], [50, BIG, 'poor', 'Noisy']] },
  pmv: { min: -3, max: 3, ticks: [-2, -1, 0, 1, 2], bands: [[-BIG, -2, 'cold', 'Cold'], [-2, -1, 'cool', 'Cool'], [-1, -0.5, 'mod', 'Slightly cool'], [-0.5, 0.5, 'good', 'Neutral'], [0.5, 1, 'mod', 'Slightly warm'], [1, 2, 'warm', 'Warm'], [2, BIG, 'hot', 'Hot']] },
  vote: { min: -3, max: 3, ticks: [-2, -1, 0, 1, 2], bands: [[-BIG, -2, 'cold', 'Cold'], [-2, -1, 'cool', 'Cool'], [-1, -0.5, 'mod', 'Slightly cool'], [-0.5, 0.5, 'good', 'Neutral'], [0.5, 1, 'mod', 'Slightly warm'], [1, 2, 'warm', 'Warm'], [2, BIG, 'hot', 'Hot']] },
  ppd: { min: 0, max: 50, ticks: [10, 20], bands: [[-BIG, 10, 'good', 'Cat. A/B'], [10, 20, 'mod', 'Cat. C'], [20, BIG, 'poor', 'Out of range']] },
  // ISO 10816-3 vibration severity (rigid mount, 15-300 kW)
  vib: { min: 0, max: 10, ticks: [2.3, 4.5, 7.1], bands: [[-BIG, 2.3, 'good', 'Zone A/B'], [2.3, 4.5, 'mod', 'Zone C'], [4.5, 7.1, 'warn', 'Zone C/D'], [7.1, BIG, 'poor', 'Zone D']] },
  // outdoor PM: US EPA AQI breakpoints (24 h), used as a live indication
  aqi25: { min: 0, max: 160, ticks: [12, 35, 55, 150], bands: [[-BIG, 12.05, 'good', 'Good'], [12.05, 35.45, 'mod', 'Moderate'], [35.45, 55.45, 'warn', 'Unhealthy (sensitive)'], [55.45, 150.45, 'poor', 'Unhealthy'], [150.45, BIG, 'hot', 'Very unhealthy']] },
  aqi10: { min: 0, max: 300, ticks: [54, 154, 254], bands: [[-BIG, 54.5, 'good', 'Good'], [54.5, 154.5, 'mod', 'Moderate'], [154.5, 254.5, 'warn', 'Unhealthy (sensitive)'], [254.5, BIG, 'poor', 'Unhealthy']] },
};

/** {level, label} of value v on scale key (level 'na' if no value). */
export function classify(key, v) {
  const d = SCALES[key];
  if (!d || v === null || v === undefined || Number.isNaN(v)) return { level: 'na', label: 'No data' };
  for (const [, to, level, label] of d.bands) if (v < to) return { level, label };
  const b = d.bands[d.bands.length - 1];
  return { level: b[2], label: b[3] };
}

const pct = (d, v) => Math.max(0, Math.min(100, (100 * (v - d.min)) / (d.max - d.min)));

/** Threshold scale for point pid (empty string if the point does not exist). */
export function scale(key, pid) {
  const d = SCALES[key];
  if (!d || !has(pid)) return '';
  const seg = d.bands.map(([a, b, lv]) => {
    const lo = Math.max(a, d.min), hi = Math.min(b, d.max);
    return hi > lo ? `<i class="b-${lv}" style="width:${(pct(d, hi) - pct(d, lo)).toFixed(2)}%"></i>` : '';
  }).join('');
  const ticks = (d.ticks || []).map((t) => `<em style="left:${pct(d, t).toFixed(2)}%">${t}</em>`).join('');
  return `<div class="scale" data-sc="${key}" data-spid="${esc(pid)}"><div class="sc-bands">${seg}</div>`
    + `<span class="mk"></span><span class="mk-t truth-only"></span><div class="sc-ticks">${ticks}</div></div>`;
}

/** One gauge row: label, live value, threshold scale, status chip and optional sparkline. */
export function gaugeRow(key, pid, label, { spark = false } = {}) {
  if (!has(pid)) return '';
  const tOnly = S.pointById[pid].kind === 'truth' ? ' truth-only' : '';
  return `<div class="grow${tOnly}${spark ? '' : ' no-spark'}" data-sc="${key}" data-spid="${esc(pid)}">
    <span class="g-lv"><span class="g-lbl">${esc(label)}</span><span class="g-val">${pv(pid)}</span></span>
    ${scale(key, pid)}<span class="lvchip lv-na">-</span>
    ${spark ? `<svg class="spark" data-spark="${esc(pid)}" viewBox="0 0 100 24" preserveAspectRatio="none"><path/></svg>` : ''}</div>`;
}

/** Status lamp bound to a binary point. type: 'alarm' (red when on) | 'run' (green) | 'info' (amber). */
export function lamp(pid, label = '', type = 'alarm') {
  if (!has(pid)) return '';
  return `<span class="lamp lamp-${type}" data-lpid="${esc(pid)}" data-pid="${esc(pid)}" title="${esc(pid)}"><i></i>`
    + (label ? `<b>${esc(label)}</b>` : '') + `<span class="v">---</span><span class="tv"></span></span>`;
}

/** Thin bar 0..max bound to a point (max may be a number or a point id). */
export function pbar(pid, max = 100, cls = '') {
  if (!has(pid)) return '';
  return `<span class="pbar ${cls}" data-bpid="${esc(pid)}" data-max="${esc(String(max))}"><i></i></span>`;
}

/**
 * <dt>/<dd> rows for a kvlist. Each row: [label, pid] or [label, pid, extraHtml]
 * or [label, null, html]. Rows whose point does not exist are skipped; truth
 * points are wrapped so they only show in truth mode.
 */
export function kvRows(rows) {
  return rows.map(([label, pid, extra = '']) => {
    if (pid === null) return `<dt>${esc(label)}</dt><dd>${extra}</dd>`;
    if (!has(pid)) return '';
    const t = S.pointById[pid].kind === 'truth' ? ' class="truth-only"' : '';
    return `<dt${t}>${esc(label)}</dt><dd${t}>${pv(pid)}${extra}</dd>`;
  }).join('');
}

/** Refresh all widgets under root from the latest snapshot. */
export function refreshWidgets(root = document) {
  if (!S.snap) return;
  for (const el of root.querySelectorAll('.scale[data-sc]')) {
    const d = SCALES[el.dataset.sc];
    const pid = el.dataset.spid;
    const v = evalPoint(pid).v;   // respects sparse / stale handling
    const mk = el.querySelector('.mk');
    if (mk) {
      mk.style.display = v === null || v === undefined ? 'none' : '';
      if (v !== null && v !== undefined) mk.style.left = pct(d, v).toFixed(2) + '%';
    }
    const mt = el.querySelector('.mk-t');
    if (mt) {
      const t = truthVal(pid);
      const show = S.truth && t !== null && t !== undefined && S.pointById[pid]?.kind !== 'truth';
      mt.style.display = show ? '' : 'none';
      if (show) mt.style.left = pct(d, t).toFixed(2) + '%';
    }
  }
  for (const el of root.querySelectorAll('.grow[data-sc]')) {
    const c = classify(el.dataset.sc, evalPoint(el.dataset.spid).v);
    const chip = el.querySelector('.lvchip');
    if (chip && chip.textContent !== c.label) { chip.textContent = c.label; chip.className = 'lvchip lv-' + c.level; }
    if (el.dataset.lv !== c.level) {
      el.classList.remove('lv-' + el.dataset.lv);
      el.classList.add('lv-' + c.level);
      el.dataset.lv = c.level;
    }
  }
  for (const el of root.querySelectorAll('.lamp[data-lpid]')) {
    el.classList.toggle('on', (val(el.dataset.lpid) ?? 0) >= 0.5);
    el.classList.toggle('na', val(el.dataset.lpid) === null);
  }
  for (const el of root.querySelectorAll('.pbar[data-bpid]')) {
    const m = el.dataset.max;
    const max = Number.isNaN(+m) ? val(m) : +m;
    const v = val(el.dataset.bpid);
    const w = v === null || !max ? 0 : Math.max(0, Math.min(100, (100 * v) / max));
    const i = el.firstElementChild;
    if (i) i.style.width = w.toFixed(1) + '%';
  }
}
