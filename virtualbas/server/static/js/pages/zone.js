/* =============================================================================
 * Zones & IEQ - building IEQ heat-map (all zones colour-coded by a selectable
 * metric) and an indoor-environment dashboard for one zone: thermal comfort,
 * air quality, light & sound, occupancy & occupant feedback, energy and the
 * serving VAV terminal, with sparklines and a 24 h trend.
 * URL: #zone/ZN-Perimeter_mid_ZN_1?m=co2
 * ========================================================================== */
import { S, $, $$, esc, pv, pmap, val, truthVal, has, zoneLabel, fmtVal, unitLabel, equipOfType } from '../core.js';
import { TrendChart, loadSeries, sparkline, fetchTrend } from '../chart.js';
import { gaugeRow, lamp, pbar, kvRows, classify } from '../widgets.js';

let zid = null, chart = null, timer = null;
let metric = 'tdev';

/** Heat-map metrics: point name, scale key (null = custom), label. */
const METRICS = {
  tdev: { name: 'ZN-T', label: 'Temperature vs set points' },
  co2: { name: 'ZN-CO2', sc: 'co2', label: 'CO₂' },
  pm25: { name: 'ZN-PM25', sc: 'pm25', label: 'PM2.5' },
  tvoc: { name: 'ZN-TVOC', sc: 'tvoc', label: 'TVOC' },
  pmv: { name: 'PMV', sc: 'pmv', label: 'PMV' },
  lux: { name: 'ZN-LUX', sc: 'lux', label: 'Illuminance' },
};
const LEGENDS = {
  tdev: [['cold', '< −1.5 K'], ['cool', '−1.5…−0.5'], ['mod', '±0.5 K outside'], ['good', 'in band'], ['warm', '+0.5…+1.5'], ['hot', '> +1.5 K']],
  co2: [['good', '< 800 ppm'], ['mod', '800–1000'], ['warn', '1000–1100'], ['poor', '> 1100']],
  pm25: [['good', '< 12 µg/m³'], ['mod', '12–15 (WELL)'], ['warn', '15–35'], ['poor', '> 35']],
  tvoc: [['good', '< 300 µg/m³'], ['mod', '300–500'], ['poor', '> 500']],
  pmv: [['cold', '< −2'], ['cool', '−2…−1'], ['mod', '±0.5…1'], ['good', '−0.5…+0.5'], ['warm', '+1…+2'], ['hot', '> +2']],
  lux: [['off', 'unoccupied'], ['low', '< 300 lux'], ['good', '300–750'], ['mod', '> 750']],
};

// ---------------------------------------------------------------- zone grouping
const FLOOR_RANK = (name) => (/_top$|_top_/.test(name) ? 0 : /_mid$|_mid_/.test(name) ? 1 : /_bot$|_bot_|_bottom$/.test(name) ? 2 : /Basement/i.test(name) ? 3 : 9);
const FLOOR_NAME = ['Floor 12 (top)', 'Floors 2–11 (mid ×10)', 'Floor 1 (ground)', 'Basement'];
function zoneGroups() {
  const zones = equipOfType('Zone');
  const groups = new Map();
  for (const z of zones) {
    const key = z.meta?.ahu || 'other';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(z);
  }
  const out = Array.from(groups, ([ahu, list]) => {
    list.sort((a, b) => (a.eplus_name.startsWith('Core') ? 1 : 0) - (b.eplus_name.startsWith('Core') ? 1 : 0) || a.eplus_name.localeCompare(b.eplus_name));
    const rank = Math.min(...list.map((z) => FLOOR_RANK(z.eplus_name)));
    return { ahu, list, rank, title: FLOOR_NAME[rank] || (ahu === 'other' ? 'Other zones' : ahu) };
  });
  out.sort((a, b) => a.rank - b.rank || a.ahu.localeCompare(b.ahu));
  return out;
}
const vavOf = (z) => (z.parent && S.equipById[z.parent]?.type === 'VAV' ? z.parent : null);

// ---------------------------------------------------------------- heat map
function hmTile(z) {
  const m = pmap(z.id);
  const mult = z.meta?.multiplier ?? 1;
  return `<a class="hm-tile${z.id === zid ? ' sel' : ''}" href="#zone/${esc(z.id)}" data-z="${esc(z.id)}" title="${esc(z.eplus_name)}">
    <div class="hm-h"><span class="hm-name">${esc(zoneLabel(z.eplus_name))}</span>${mult > 1 ? `<span class="mult">×${mult}</span>` : ''}</div>
    <div class="hm-v"><b class="hm-val">---</b><small class="hm-u"></small></div>
    <div class="hm-sub"><span class="hm-lbl">-</span><span class="hm-t truth-ink truth-only"></span></div>
    <div class="hm-foot">${has(m['OCC-COUNT']) ? `<span title="people counter">👤 <span class="hm-ppl">-</span></span>` : ''}</div>
  </a>`;
}

/** {text, unit, level, label, truthText} for the heat-map metric of zone z. */
function metricOf(z, key) {
  const m = pmap(z.id);
  const M = METRICS[key];
  const pid = m[M.name];
  if (!has(pid)) return { text: 'n/a', unit: '', level: 'na', label: 'not measured', tt: '' };
  const p = S.pointById[pid];
  const v = val(pid), t = truthVal(pid);
  const unit = unitLabel(p.unit);
  const tt = S.truth && t !== null && t !== undefined ? 'E+ ' + fmtVal(p, t) : '';
  if (key === 'tdev') {
    const h = val(m['HTG-SP']), c = val(m['CLG-SP']);
    if (v === null || h === null || c === null) return { text: fmtVal(p, v), unit, level: 'na', label: 'no data', tt };
    const dev = v < h ? v - h : v > c ? v - c : 0;
    const level = dev < -1.5 ? 'cold' : dev < -0.5 ? 'cool' : dev < 0 ? 'mod' : dev === 0 ? 'good' : dev <= 0.5 ? 'mod' : dev <= 1.5 ? 'warm' : 'hot';
    const label = dev === 0 ? `in band ${h.toFixed(1)}–${c.toFixed(1)}` : `Δ ${dev > 0 ? '+' : '−'}${Math.abs(dev).toFixed(1)} K ${dev > 0 ? 'above clg' : 'below htg'} SP`;
    return { text: fmtVal(p, v), unit, level, label, tt };
  }
  const c = classify(M.sc, v);
  if (key === 'lux' && (val(m['OCC-MODE']) ?? 1) < 0.5 && v !== null && v < 300) return { text: fmtVal(p, v), unit, level: 'off', label: 'unoccupied', tt };
  return { text: fmtVal(p, v), unit, level: c.level, label: c.label, tt };
}

function updateHeatmap() {
  for (const el of $$('.hm-tile[data-z]')) {
    const z = S.equipById[el.dataset.z];
    const r = metricOf(z, metric);
    el.querySelector('.hm-val').textContent = r.text;
    el.querySelector('.hm-u').textContent = r.unit;
    el.querySelector('.hm-lbl').textContent = r.label;
    el.querySelector('.hm-t').textContent = r.tt;
    const ppl = el.querySelector('.hm-ppl');
    if (ppl) { const n = val(`${z.id}/OCC-COUNT`); ppl.textContent = n === null ? '-' : String(Math.round(n)); }
    if (el.dataset.lv !== r.level) {
      el.classList.remove('lv-' + el.dataset.lv);
      el.classList.add('lv-' + r.level);
      el.dataset.lv = r.level;
    }
  }
  const lg = $('#hm-legend');
  if (lg && lg.dataset.m !== metric) {
    lg.dataset.m = metric;
    lg.innerHTML = (LEGENDS[metric] || []).map(([lv, t]) => `<span class="hm-lc lv-${lv}">${esc(t)}</span>`).join('');
  }
}

// ---------------------------------------------------------------- detail cards
const card = (title, sub, body, cls = '') => `<section class="card ieq-card ${cls}"><div class="card-h"><b>${title}</b>${sub ? `<small>${sub}</small>` : ''}</div>${body}</section>`;
const kv = (rows) => { const h = kvRows(rows); return h ? `<dl class="kvlist">${h}</dl>` : ''; };

function detail(z) {
  const m = pmap(z.id);
  const vid = vavOf(z), vm = vid ? pmap(vid) : {};
  const ahu = z.meta?.ahu;
  const mult = z.meta?.multiplier ?? 1;

  const thermal = `
    <div class="ieq-big">${pv(m['ZN-T'], { cls: 'pv-big' })}<div class="ieq-big-s">
      <span class="k">Operative</span> ${pv(m['ZN-OPT'])}<br><span class="k">Radiant (MRT)</span> ${pv(m['ZN-MRT'])}</div></div>
    ${has(m['ZN-T']) && has(m['HTG-SP']) && has(m['CLG-SP']) ? `<div class="tband" id="tband"><div class="tb-track"><i class="tb-band"></i><span class="mk"></span><span class="mk-t truth-only"></span></div>
      <div class="tb-lbl"><span id="tb-lo">-</span><span class="muted">heating SP · comfort band · cooling SP</span><span id="tb-hi">-</span></div></div>` : ''}
    ${gaugeRow('pmv', m['PMV'], 'PMV')}${gaugeRow('ppd', m['PPD'], 'PPD')}${gaugeRow('rh', m['ZN-RH'], 'Humidity', { spark: true })}
    ${kv([['Dew point', m['ZN-DP']], ['Active heating / cooling SP', m['HTG-SP'], has(m['CLG-SP']) ? ` / ${pv(m['CLG-SP'])}` : ''], ['Occupied heating / cooling SP', m['OCC-HTG-SP'], has(m['OCC-CLG-SP']) ? ` / ${pv(m['OCC-CLG-SP'])}` : ''], ['Occupant SP adjust', m['ZN-T-ADJ']], ['Occupancy mode', m['OCC-MODE']]])}`;

  const oa25 = has('WX/OA-PM25') ? `<div class="io-ratio"><span class="k">Outdoor PM2.5</span> ${pv('WX/OA-PM25')} <span class="k">I/O ratio</span> <b id="io-ratio">-</b>${has(`${ahu}/SA-PM25`) ? `<span class="truth-only"> <span class="k">Supply air (truth)</span> ${pv(`${ahu}/SA-PM25`)}</span>` : ''}</div>` : '';
  const aq = `${gaugeRow('co2', m['ZN-CO2'], 'CO₂', { spark: true })}${gaugeRow('pm25', m['ZN-PM25'], 'PM2.5', { spark: true })}
    ${gaugeRow('pm10', m['ZN-PM10'], 'PM10', { spark: true })}${gaugeRow('tvoc', m['ZN-TVOC'], 'TVOC', { spark: true })}${oa25}
    <p class="hint">Thresholds: CO₂ 1000 / 1100 ppm · PM2.5 12 / 35 µg/m³ (WELL 15) · PM10 50 µg/m³ · TVOC 500 µg/m³.</p>`;

  const light = `${gaugeRow('lux', m['ZN-LUX'], 'Illuminance', { spark: true })}
    ${has(m['LIGHT-LVL']) ? `<div class="grow-plain"><span class="g-lv"><span class="g-lbl">Lighting level</span><span class="g-val">${pv(m['LIGHT-LVL'])}</span></span>${pbar(m['LIGHT-LVL'], 100, 'pb-light')}</div>` : ''}
    ${has(m['DAYLIGHT-LUX']) ? `<div class="grow-plain truth-only"><span class="g-lv"><span class="g-lbl">Daylight (truth)</span><span class="g-val">${pv(m['DAYLIGHT-LUX'])}</span></span><span class="pbar pb-day"><i id="dl-bar"></i></span><span class="lvchip lv-na" id="dl-share">-</span></div>` : ''}
    ${gaugeRow('dba', m['ZN-DBA'], 'Sound level', { spark: true })}`;

  const occ = `<div class="occ-tiles">
      ${has(m['OCC-COUNT']) ? `<div class="otile"><span class="k">People counter</span>${pv(m['OCC-COUNT'], { cls: 'pv-mid' })}</div>` : ''}
      ${has(m['OCCUPANTS']) ? `<div class="otile truth-only"><span class="k">True occupants</span>${pv(m['OCCUPANTS'], { cls: 'pv-mid' })}</div>` : ''}
      ${has(m['HOT-CALLS']) ? `<div class="otile"><span class="k">Hot calls</span>${pv(m['HOT-CALLS'], { cls: 'pv-mid hot' })}</div>` : ''}
      ${has(m['COLD-CALLS']) ? `<div class="otile"><span class="k">Cold calls</span>${pv(m['COLD-CALLS'], { cls: 'pv-mid cold' })}</div>` : ''}
    </div>
    <div class="lamps">${lamp(m['ZN-OCC'], 'Occupancy (PIR)', 'run')}${lamp(m['WIN-STS'], 'Window', 'info')}</div>
    ${gaugeRow('vote', m['TS-VOTE'], 'Thermal vote')}
    <p class="hint">Thermal vote = mean occupant sensation vote (−3 cold … +3 hot) from a feedback app; empty when nobody has voted.</p>`;

  const energy = kv([['Lighting power', m['LIGHT-KW']], ['Plug loads', m['PLUG-KW']], ['Internal gains', m['INT-GAIN-KW']], ['Window solar gain', m['WIN-SOL-KW']],
    ['Window heat gain', m['WIN-Q-KW']], ['Infiltration', m['INFIL-ACH']], ['HVAC sensible cooling', m['SYS-CLG-KW']], ['HVAC sensible heating', m['SYS-HTG-KW']]])
    + (mult > 1 ? `<p class="hint">Zone represents ${mult} identical floors; values are per modelled zone.</p>` : '')
    + `<p class="hint truth-only">Violet rows are the EnergyPlus zone heat balance (inner space) - not measurable by a BAS.</p>`;

  const term = vid ? kv([['Airflow', vm['DA-F']], ['Airflow set point', vm['DA-F-SP']], ['Discharge air temp', vm['DA-T']], ['Damper position', vm['DMPR-POS']],
    ['Reheat valve', vm['RHV-POS']], ['Terminal mode', vm['ZN-MODE']], ['Cooling loop', vm['CLG-LOOP']], ['Heating loop', vm['HTG-LOOP']]])
    + `<div class="lamps">${lamp(vm['LOW-FLOW-ALM'], 'Low flow', 'alarm')}</div>
       <div class="form-row"><a class="btn" href="#vav/${esc(vid)}">Open ${esc(vid)} →</a>${ahu ? `<a class="btn btn-ghost" href="#ahu/${esc(ahu)}">${esc(ahu)}</a>` : ''}</div>`
    : '<p class="muted">No VAV terminal mapped to this zone.</p>';

  return `<div class="zone-head card">
      <div><div class="zh-name">${esc(zoneLabel(z.eplus_name))} <small>${esc(z.eplus_name)}</small>${mult > 1 ? ` <span class="mult">×${mult} floors</span>` : ''}</div>
      <div class="zh-sub">${esc(z.description)}${vid ? ` · served by <a href="#vav/${esc(vid)}">${esc(vid)}</a>` : ''}${ahu ? ` › <a href="#ahu/${esc(ahu)}">${esc(ahu)}</a>` : ''}</div></div>
      <span class="spacer"></span>
      <div class="zh-chips" id="zh-chips"></div>
    </div>
    <div class="ieq-grid">
      ${card('Thermal comfort', 'temperature, radiant, humidity, PMV / PPD', thermal)}
      ${card('Indoor air quality', 'last 24 h sparklines', aq)}
      ${card('Light &amp; sound', '', light)}
      ${card('Occupancy &amp; feedback', '', occ)}
      ${card('Energy &amp; heat balance', '', energy)}
      ${card('VAV terminal', vid ? esc(vid) : '', term)}
    </div>
    <section class="card chart-card"><div class="card-h"><b>Last 24 h</b><small>temperature with set points, CO₂, particulates / TVOC, illuminance</small><span class="spacer"></span><span class="truth-only small">dashed = EnergyPlus truth</span></div>
      <div id="zn-chart" class="chart-box" style="height:330px"></div></section>`;
}

// ---------------------------------------------------------------- page
export function render(main, { arg, q }) {
  const zones = equipOfType('Zone');
  if (!zones.length) { main.innerHTML = '<div class="loading">This building has no thermal zones in the point catalog.</div>'; return; }
  zid = S.equipById[arg]?.type === 'Zone' ? arg : (S.equipById['ZN-Core_mid'] ? 'ZN-Core_mid' : zones[0].id);
  if (q?.m && METRICS[q.m]) metric = q.m;
  const z = S.equipById[zid];
  const groups = zoneGroups();
  main.innerHTML = `
  <div class="page-head"><h1>Zones &amp; indoor environment</h1>
    <select id="zn-sel" class="sel">${groups.map((g) => `<optgroup label="${esc(g.title)}">${g.list.map((x) => `<option value="${esc(x.id)}" ${x.id === zid ? 'selected' : ''}>${esc(x.id)}</option>`).join('')}</optgroup>`).join('')}</select>
    <span class="crumb">${zones.length} zones · IEQ = thermal, air quality, light, acoustics, occupancy</span></div>
  <section class="card hm-card">
    <div class="card-h"><b>IEQ heat-map</b><small>all zones, live</small><span class="spacer"></span>
      <div class="seg" id="hm-metric">${Object.entries(METRICS).map(([k, d]) => `<button data-m="${k}" class="${k === metric ? 'on' : ''}">${d.label}</button>`).join('')}</div></div>
    <div class="hm-legend" id="hm-legend"></div>
    <div class="hm-grid">${groups.map((g) => `<div class="hm-row"><div class="hm-row-lbl"><b>${esc(g.title)}</b>${g.ahu !== 'other' ? `<a href="#ahu/${esc(g.ahu)}" class="ahu-link">${esc(g.ahu)}</a>` : ''}</div>
      <div class="hm-tiles" style="--cols:${Math.min(8, Math.max(...groups.map((x) => x.list.length)))}">${g.list.map(hmTile).join('')}</div></div>`).join('')}</div>
  </section>
  ${detail(z)}`;
  $('#zn-sel', main).onchange = (e) => { location.hash = `#zone/${e.target.value}`; };
  for (const b of $$('#hm-metric button', main)) {
    b.onclick = () => {
      metric = b.dataset.m;
      $$('#hm-metric button').forEach((x) => x.classList.toggle('on', x === b));
      updateHeatmap();
    };
  }
  chart = new TrendChart($('#zn-chart', main));
  loadChart();
  timer = setInterval(loadChart, 30000);
}

function loadChart() {
  const m = pmap(zid);
  const names = ['ZN-T', 'HTG-SP', 'CLG-SP', 'ZN-CO2', 'ZN-PM25', 'ZN-TVOC', 'ZN-LUX'].filter((n) => has(m[n]));
  const n = Math.round(86400 / (S.info.timestep_s || 300));
  loadSeries(names.map((x) => m[x]), n, { truth: S.truth, pointById: S.pointById, labels: names })
    .then(({ times, series }) => chart?.setData(times, series)).catch(() => {});
  // sparklines
  const sp = $$('svg.spark[data-spark]');
  fetchTrend(sp.map((s) => s.dataset.spark), n).then(({ data }) => {
    for (const s of sp) sparkline(s, data[s.dataset.spark]);
  }).catch(() => {});
}
export function onTruth() { loadChart(); updateHeatmap(); }

export function update() {
  updateHeatmap();
  const m = pmap(zid);
  // temperature band: heating SP .. cooling SP with the zone temperature marker
  const tb = document.getElementById('tband');
  if (tb) {
    const t = val(m['ZN-T']), h = val(m['HTG-SP']), c = val(m['CLG-SP']), tt = truthVal(m['ZN-T']);
    if (h !== null && c !== null) {
      const lo = Math.min(h, t ?? h) - 2, hi = Math.max(c, t ?? c) + 2;
      const P = (x) => `${Math.max(0, Math.min(100, (100 * (x - lo)) / (hi - lo))).toFixed(1)}%`;
      const band = tb.querySelector('.tb-band');
      band.style.left = P(h);
      band.style.width = `calc(${P(c)} - ${P(h)})`;
      const mk = tb.querySelector('.mk');
      mk.style.display = t === null ? 'none' : '';
      if (t !== null) mk.style.left = P(t);
      const mt = tb.querySelector('.mk-t');
      mt.style.display = S.truth && tt !== undefined && tt !== null ? '' : 'none';
      if (tt !== undefined && tt !== null) mt.style.left = P(tt);
      tb.classList.toggle('out-hot', t !== null && t > c + 0.5);
      tb.classList.toggle('out-cold', t !== null && t < h - 0.5);
      $('#tb-lo').textContent = `${h.toFixed(1)} °C`;
      $('#tb-hi').textContent = `${c.toFixed(1)} °C`;
    }
  }
  // daylight share (truth)
  const dl = document.getElementById('dl-bar');
  if (dl) {
    const d = val(m['DAYLIGHT-LUX']), tot = truthVal(m['ZN-LUX']) ?? val(m['ZN-LUX']);
    const share = d !== null && tot ? Math.max(0, Math.min(1, d / tot)) : null;
    dl.style.width = share === null ? '0' : `${(100 * share).toFixed(0)}%`;
    const ch = $('#dl-share');
    ch.textContent = share === null ? '-' : `${Math.round(100 * share)} % daylight`;
    ch.className = 'lvchip ' + (share === null ? 'lv-na' : share > 0.5 ? 'lv-good' : 'lv-mod');
  }
  // indoor/outdoor PM2.5 ratio
  const io = document.getElementById('io-ratio');
  if (io) {
    const a = val(m['ZN-PM25']), b = val('WX/OA-PM25');
    io.textContent = a !== null && b ? (a / b).toFixed(2) : '-';
  }
  // summary chips in the zone header
  const chips = document.getElementById('zh-chips');
  if (chips) {
    const z = S.equipById[zid];
    const items = [['Thermal', metricOf(z, 'tdev')], ['Comfort', metricOf(z, 'pmv')], ['CO₂', metricOf(z, 'co2')], ['PM2.5', metricOf(z, 'pm25')], ['TVOC', metricOf(z, 'tvoc')], ['Light', metricOf(z, 'lux')]]
      .filter(([, r]) => r.text !== 'n/a');
    const html = items.map(([k, r]) => `<span class="zchip lv-${r.level}"><span class="k">${k}</span><b>${esc(r.text)}</b><small>${esc(r.label)}</small></span>`).join('');
    if (chips.dataset.h !== html) { chips.innerHTML = html; chips.dataset.h = html; }
  }
}

export function destroy() { clearInterval(timer); chart?.destroy(); chart = null; }
