/* =============================================================================
 * Weather & energy - rooftop weather station (psychrometrics, wind rose, sky,
 * solar), outdoor air quality, 48 h weather forecast (vs. realised weather in
 * truth mode), utility / grid signals with demand-response banner, and the
 * building meters: demand, peaks, end-use breakdown, gas, water, totalisers.
 * ========================================================================== */
import { S, $, esc, api, pv, val, has, fmtDT, parseT, refreshBindings } from '../core.js';
import { TrendChart, loadSeries, fetchTrend, sparkline, SERIES_COLORS } from '../chart.js';
import { gaugeRow, lamp, kvRows, classify } from '../widgets.js';

let fcChart = null, gridChart = null, dmdChart = null, timer = null, fcTimer = null;

const ELEC = [
  ['Interior lighting', 'MTR/LIGHT-KW', '#c98500'], ['Plug loads', 'MTR/PLUG-KW', '#9085e9'], ['Chillers', 'MTR/CLG-ELEC-KW', '#3987e5'],
  ['Fans', 'MTR/FAN-ELEC-KW', '#199e70'], ['Pumps', 'MTR/PUMP-ELEC-KW', '#2fae2f'], ['Heat rejection', 'MTR/HREJ-ELEC-KW', '#29c7d8'],
  ['Exterior lighting', 'MTR/EXT-LIGHT-KW', '#d55181'], ['Elevators', 'MTR/ELEV-KW', '#a3b3ca'],
];
const GAS = [['Space heating', 'MTR/HTG-GAS-KW', '#d95926'], ['Service hot water', 'MTR/DHW-GAS-KW', '#e66767']];
const DIRS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
const cardinal = (d) => DIRS[Math.round(((d % 360) + 360) % 360 / 22.5) % 16];

const kv = (rows, cls = '') => { const h = kvRows(rows); return h ? `<dl class="kvlist ${cls}">${h}</dl>` : ''; };
const ebars = (list, id) => list.filter(([, pid]) => has(pid)).map(([label, pid, c]) => `<div class="ebar" data-epid="${esc(pid)}" data-grp="${id}">
    <span class="eb-lbl">${esc(label)}</span><span class="eb-track"><i style="background:${c}"></i></span><span class="eb-val">${pv(pid)}</span><span class="eb-pct">-</span></div>`).join('');

// ---------------------------------------------------------------- SVG pieces
function compass() {
  let ticks = '';
  for (let i = 0; i < 72; i++) {
    const a = (i * 5 * Math.PI) / 180, r1 = i % 18 === 0 ? 60 : i % 2 === 0 ? 64 : 66;
    ticks += `M${(80 + r1 * Math.sin(a)).toFixed(1)} ${(80 - r1 * Math.cos(a)).toFixed(1)}L${(80 + 69 * Math.sin(a)).toFixed(1)} ${(80 - 69 * Math.cos(a)).toFixed(1)}`;
  }
  return `<svg class="compass" viewBox="0 0 160 160" role="img" aria-label="Wind direction">
    <circle class="cp-ring" cx="80" cy="80" r="70"/><circle class="cp-in" cx="80" cy="80" r="44"/><circle class="cp-in" cx="80" cy="80" r="22"/>
    <g id="wx-rose"></g>
    <path class="cp-ticks" d="${ticks}"/>
    <text class="cp-c" x="80" y="20" text-anchor="middle">N</text><text class="cp-c" x="146" y="84" text-anchor="middle">E</text>
    <text class="cp-c" x="80" y="150" text-anchor="middle">S</text><text class="cp-c" x="14" y="84" text-anchor="middle">W</text>
    <g id="wx-arrow" class="cp-arrow"><path d="M80 14L88 30H83V96H77V30H72Z"/></g>
    <circle class="cp-hub" cx="80" cy="80" r="17"/>
    <text id="wx-spd" class="cp-spd" x="80" y="80" text-anchor="middle">-</text><text id="wx-dir" class="cp-dir" x="80" y="92" text-anchor="middle">-</text>
  </svg>`;
}
function skyIcon() {
  return `<svg class="sky" viewBox="0 0 60 60" role="img" aria-label="Sky cover"><circle class="sky-bg" cx="30" cy="30" r="24"/><path id="sky-pie" class="sky-pie" d=""/><circle class="sky-ring" cx="30" cy="30" r="24"/></svg>`;
}

// ---------------------------------------------------------------- page
export function render(main) {
  const wx = has('WX/OA-T'), grid = has('GRID/PRICE'), mtr = has('MTR/BLDG-ELEC-KW');
  main.innerHTML = `
  <div class="page-head"><h1>Weather, grid &amp; energy</h1><span class="crumb">rooftop weather station · outdoor air quality · forecast feed · utility signals · meters</span></div>
  <div class="dr-banner" id="dr-banner" hidden></div>
  <div class="aq-banner" id="aq-banner" hidden></div>
  <div class="wx-grid">
    ${wx ? `<section class="card wx-station">
      <div class="card-h"><b>Weather station</b><small>${esc(S.equipById.WX?.description || '')}</small></div>
      <div class="wx-cols">
        <div class="wx-main">
          <div class="wx-big">${pv('WX/OA-T', { cls: 'pv-big' })}</div>
          <div class="wx-big2">${pv('WX/OA-RH', { cls: 'pv-mid' })} <small>RH</small></div>
          ${kv([['Wet bulb', 'WX/OA-WB'], ['Dew point', 'WX/OA-DP'], ['Enthalpy', 'WX/OA-H'], ['Humidity ratio', 'WX/OA-W'], ['Barometric pressure', 'WX/BARO'], ['Sky temperature', 'WX/SKY-T']])}
        </div>
        <div class="wx-wind">${has('WX/WIND-DIR') || has('WX/WIND') ? compass() : ''}
          <div class="wx-cap">${has('WX/WIND') ? `Wind ${pv('WX/WIND')}` : ''} ${has('WX/WIND-DIR') ? `from ${pv('WX/WIND-DIR')}` : ''}<br><small>petals: 24 h direction frequency</small></div></div>
        <div class="wx-sky">
          <div class="sky-row">${has('WX/SKY-COVER') ? skyIcon() : ''}<div><span class="k">Sky cover</span><br>${pv('WX/SKY-COVER', { cls: 'pv-mid' })}</div></div>
          <div class="lamps">${lamp('WX/RAIN', 'Rain sensor', 'info')}</div>
          ${kv([['Precipitation', 'WX/PRECIP'], ['Outdoor illuminance', 'WX/OA-LUX']])}
          <div class="sol">${[['GHI', 'WX/SOLAR'], ['DNI', 'WX/DNI'], ['DHI', 'WX/DHI']].filter(([, p]) => has(p)).map(([l, p]) => `<div class="sol-r"><span class="k">${l}</span><span class="eb-track"><i class="sol-i" data-sol="${p}"></i></span>${pv(p)}</div>`).join('')}</div>
        </div>
      </div>
    </section>` : ''}
    <section class="card wx-aq">
      <div class="card-h"><b>Outdoor air quality</b><small>US EPA AQI categories</small></div>
      <div class="aqi-big" id="aqi-big"><span class="aqi-cat">-</span><small>PM2.5 category</small></div>
      ${gaugeRow('aqi25', 'WX/OA-PM25', 'PM2.5', { spark: true })}${gaugeRow('aqi10', 'WX/OA-PM10', 'PM10', { spark: true })}
      <p class="hint">Wildfire smoke or traffic events raise outdoor PM; the economizer and minimum-OA logic only see these values if the BAS has an outdoor PM sensor (next-gen tier).</p>
    </section>

    <section class="card wx-fc">
      <div class="card-h"><b>48 h weather forecast</b><small id="fc-issued">-</small><span class="spacer"></span><span class="truth-only small">dashed = realised weather (truth)</span></div>
      <div id="fc-chart" class="chart-box" style="height:290px"></div>
      <div class="fc-tiles">${[['+1 h', 'WX/OA-T-FC1H', 'WX/GHI-FC1H'], ['+6 h', 'WX/OA-T-FC6H', 'WX/GHI-FC6H'], ['+24 h', 'WX/OA-T-FC24H', 'WX/GHI-FC24H']]
        .filter(([, a]) => has(a)).map(([l, a, b]) => `<div class="fc-tile"><span class="k">Forecast ${l}</span>${pv(a)}${has(b) ? `<small>${pv(b)}</small>` : ''}</div>`).join('')}</div>
    </section>
    ${grid ? `<section class="card wx-grid-card">
      <div class="card-h"><b>Grid &amp; tariff</b><small>${esc(S.equipById.GRID?.description || '')}</small></div>
      <div class="grid-top">
        <div><span class="k">Energy price</span>${pv('GRID/PRICE', { cls: 'pv-mid' })}</div>
        <div><span class="k">TOU period</span><span class="tou" id="tou">${pv('GRID/TOU-PERIOD')}</span></div>
        <div><span class="k">Carbon intensity</span>${pv('GRID/CO2-INT', { cls: 'pv-mid' })}</div>
      </div>
      <div class="lamps">${lamp('GRID/DR-EVENT', 'Demand response', 'alarm')}</div>
      ${kv([['Requested shed', 'GRID/DR-SHED-KW'], ['Energy cost today', 'GRID/COST-TODAY'], ['Emissions today', 'GRID/CO2-TODAY']])}
      <div id="grid-chart" class="chart-box" style="height:170px"></div>
    </section>` : ''}

    ${mtr ? `<section class="card wx-dmd">
      <div class="card-h"><b>Electric demand &amp; end uses</b><small>utility meter and sub-meters</small></div>
      <div class="dmd-top">
        <div class="dmd-big"><span class="k">Building demand</span>${pv('MTR/BLDG-ELEC-KW', { cls: 'pv-big' })}</div>
        <div class="dmd-kv">${kv([['15-min demand', 'MTR/BLDG-DMD-15'], ['Peak today', 'MTR/PEAK-DMD-DAY'], ['Peak this month', 'MTR/PEAK-DMD-MONTH'], ['HVAC electricity', 'MTR/HVAC-ELEC-KW']])}
          ${has('MTR/PEAK-DMD-MONTH') ? `<div class="dmd-bar" title="15-min demand vs. monthly peak"><span class="eb-track"><i id="dmd-i"></i></span><small id="dmd-pct">-</small></div>` : ''}</div>
      </div>
      <div class="ebars">${ebars(ELEC, 'e')}<div class="ebar ebar-rest" id="eb-rest"><span class="eb-lbl">Other / unmetered</span><span class="eb-track"><i></i></span><span class="eb-val">-</span><span class="eb-pct">-</span></div></div>
      <div id="dmd-chart" class="chart-box" style="height:170px"></div>
    </section>
    <section class="card wx-util">
      <div class="card-h"><b>Gas, water &amp; totalisers</b></div>
      <div class="dmd-big"><span class="k">Natural gas</span>${pv('MTR/BLDG-GAS-KW', { cls: 'pv-mid' })}</div>
      <div class="ebars">${ebars(GAS, 'g')}</div>
      <h5 class="sub-h">Water</h5>
      ${kv([['Domestic water', 'MTR/WATER-F'], ['Cooling-tower make-up', 'MTR/TOWER-WATER-F'], ['Service hot water use', 'DHW-1/USE-F']])}
      <h5 class="sub-h">Totalisers <small>since start of run</small></h5>
      ${kv([['Electricity', 'MTR/BLDG-ELEC-KWH'], ['Natural gas', 'MTR/BLDG-GAS-KWH'], ['Water', 'MTR/WATER-M3']])}
      <h5 class="sub-h">Today</h5>
      ${kv([['Heating degree-days', 'WX/HDD-TODAY'], ['Cooling degree-days', 'WX/CDD-TODAY'], ['Building occupancy', 'BLDG/OCC-COUNT'], ['Energy cost', 'GRID/COST-TODAY'], ['Emissions', 'GRID/CO2-TODAY']])}
    </section>` : ''}
  </div>`;
  if ($('#fc-chart', main)) fcChart = new TrendChart($('#fc-chart', main));
  if ($('#grid-chart', main)) gridChart = new TrendChart($('#grid-chart', main));
  if ($('#dmd-chart', main)) dmdChart = new TrendChart($('#dmd-chart', main));
  loadCharts();
  loadForecast();
  timer = setInterval(loadCharts, 30000);
  fcTimer = setInterval(loadForecast, 20000);
}

function loadCharts() {
  const n = Math.round(86400 / (S.info.timestep_s || 300));
  if (gridChart) {
    const pids = ['GRID/PRICE', 'GRID/CO2-INT'].filter(has);
    loadSeries(pids, n, { pointById: S.pointById, labels: ['Price', 'Carbon intensity'], colors: [SERIES_COLORS[3], SERIES_COLORS[2]] })
      .then(({ times, series }) => gridChart?.setData(times, series)).catch(() => {});
  }
  if (dmdChart) {
    const pids = ['MTR/BLDG-ELEC-KW', 'MTR/BLDG-DMD-15', 'MTR/HVAC-ELEC-KW'].filter(has);
    loadSeries(pids, n, { truth: S.truth, pointById: S.pointById, labels: ['Building', '15-min demand', 'HVAC'] })
      .then(({ times, series }) => dmdChart?.setData(times, series)).catch(() => {});
  }
  // wind rose (direction frequency weighted by speed) and AQ sparklines
  const sp = [...document.querySelectorAll('svg.spark[data-spark]')].map((s) => s.dataset.spark);
  fetchTrend(['WX/WIND-DIR', 'WX/WIND', ...sp].filter(has), n).then(({ data }) => {
    for (const s of document.querySelectorAll('svg.spark[data-spark]')) sparkline(s, data[s.dataset.spark]);
    drawRose(data['WX/WIND-DIR'], data['WX/WIND']);
  }).catch(() => {});
}

function drawRose(dirs, spd) {
  const g = document.getElementById('wx-rose');
  if (!g || !dirs) return;
  const bins = new Array(16).fill(0);
  dirs.forEach((d, i) => { if (d !== null) bins[Math.round(((d % 360) + 360) % 360 / 22.5) % 16] += Math.max(0.2, spd?.[i] ?? 1); });
  const mx = Math.max(...bins);
  if (!mx) { g.innerHTML = ''; return; }
  let html = '';
  bins.forEach((b, k) => {
    if (!b) return;
    const r = 18 + 50 * Math.sqrt(b / mx);
    const a0 = ((k * 22.5 - 9) * Math.PI) / 180, a1 = ((k * 22.5 + 9) * Math.PI) / 180;
    const P = (a, rr) => `${(80 + rr * Math.sin(a)).toFixed(1)} ${(80 - rr * Math.cos(a)).toFixed(1)}`;
    html += `<path class="rose-p" d="M${P(a0, 18)}L${P(a0, r)}A${r.toFixed(1)} ${r.toFixed(1)} 0 0 1 ${P(a1, r)}L${P(a1, 18)}Z"/>`;
  });
  g.innerHTML = html;
}

async function loadForecast() {
  if (!fcChart) return;
  try {
    const n = Math.round(86400 / (S.info.timestep_s || 300));
    const [fc, past] = await Promise.all([api(`/api/forecast?hours=48${S.truth ? '&truth=1' : ''}`), fetchTrend(['WX/OA-T', 'WX/SOLAR'].filter(has), n)]);
    const rows = fc.rows || [];
    $('#fc-issued').textContent = fc.issued ? `issued ${fmtDT(fc.issued)} · hourly · error grows with lead time` : 'no forecast feed';
    // shared time axis: observed history (15-min) followed by the hourly forecast
    const hist = [];
    for (let i = 0; i < past.times.length; i += 3) hist.push(i);
    const tPast = hist.map((i) => past.times[i]);
    const tFc = rows.map((r) => parseT(r.time).getTime());
    const times = tPast.concat(tFc);
    const nP = tPast.length, nF = tFc.length;
    const padF = new Array(nF).fill(null), padP = new Array(nP).fill(null);
    const obsT = past.data['WX/OA-T'], obsG = past.data['WX/SOLAR'];
    const C = SERIES_COLORS;
    const series = [];
    if (obsT) series.push({ id: 'oT', label: 'OA temp (station)', color: '#a3b3ca', unit: 'degC', values: hist.map((i) => obsT[i]).concat(padF) });
    series.push({ id: 'fT', label: 'OA temp forecast', color: C[1], unit: 'degC', values: padP.concat(rows.map((r) => r.oa_t ?? null)) });
    if (S.truth && rows.some((r) => r.truth_oa_t !== undefined)) series.push({ id: 'tT', label: 'OA temp realised (truth)', color: C[1], unit: 'degC', dashed: true, values: padP.concat(rows.map((r) => r.truth_oa_t ?? null)) });
    if (obsG) series.push({ id: 'oG', label: 'GHI (station)', color: '#71839e', unit: 'W/m2', values: hist.map((i) => obsG[i]).concat(padF) });
    series.push({ id: 'fG', label: 'GHI forecast', color: C[3], unit: 'W/m2', values: padP.concat(rows.map((r) => r.ghi ?? null)) });
    if (S.truth && rows.some((r) => r.truth_ghi !== undefined)) series.push({ id: 'tG', label: 'GHI realised (truth)', color: C[3], unit: 'W/m2', dashed: true, values: padP.concat(rows.map((r) => r.truth_ghi ?? null)) });
    fcChart.markers = [{ t: parseT(S.snap.time).getTime(), label: 'now' }];
    fcChart.setData(times, series);
  } catch { /* forecast feed unavailable */ }
}
export function onTruth() { loadCharts(); loadForecast(); }

export function update() {
  // wind arrow (meteorological: direction the wind blows FROM -> arrow points downwind)
  const dir = val('WX/WIND-DIR'), spd = val('WX/WIND');
  const ar = document.getElementById('wx-arrow');
  if (ar) {
    ar.setAttribute('transform', `rotate(${((dir ?? 0) + 180) % 360} 80 80)`);
    ar.style.display = dir === null ? 'none' : '';
    $('#wx-spd').textContent = spd === null ? '-' : spd.toFixed(1);
    $('#wx-dir').textContent = dir === null ? 'm/s' : `m/s ${cardinal(dir)}`;
  }
  // sky cover pie (tenths)
  const pie = document.getElementById('sky-pie');
  if (pie) {
    const f = Math.max(0, Math.min(1, (val('WX/SKY-COVER') ?? 0) / 10));
    if (f >= 0.999) pie.setAttribute('d', 'M30 6A24 24 0 1 1 29.99 6Z');
    else if (f <= 0.001) pie.setAttribute('d', '');
    else {
      const a = 2 * Math.PI * f;
      pie.setAttribute('d', `M30 30L30 6A24 24 0 ${f > 0.5 ? 1 : 0} 1 ${(30 + 24 * Math.sin(a)).toFixed(2)} ${(30 - 24 * Math.cos(a)).toFixed(2)}Z`);
    }
  }
  for (const el of document.querySelectorAll('.sol-i[data-sol]')) el.style.width = `${Math.max(0, Math.min(100, (val(el.dataset.sol) ?? 0) / 10)).toFixed(1)}%`;
  // TOU colour
  const tou = document.getElementById('tou');
  if (tou) tou.dataset.p = String(Math.round(val('GRID/TOU-PERIOD') ?? -1));
  // AQI headline
  const aq = document.getElementById('aqi-big');
  const pm = val('WX/OA-PM25');
  if (aq) {
    const c = classify('aqi25', pm);
    aq.className = 'aqi-big lv-' + c.level;
    aq.querySelector('.aqi-cat').textContent = c.label;
  }
  // banners
  const inj = S.snap.injections || [];
  const dr = document.getElementById('dr-banner');
  if (dr) {
    const on = (val('GRID/DR-EVENT') ?? 0) >= 0.5;
    dr.hidden = !on;
    if (on) {
      const shed = val('GRID/DR-SHED-KW'), d15 = val('MTR/BLDG-DMD-15'), kw = val('MTR/BLDG-ELEC-KW');
      const ev = inj.find((i) => i.type === 'demand_response' && i.severity > 0);
      const html = `<b>⚡ DEMAND RESPONSE EVENT ACTIVE</b><span>Utility requests a load shed of <b>${shed === null ? '-' : Math.round(shed)} kW</b>${ev?.end ? ` until ${esc(fmtDT(ev.end))}` : ''}.</span>`
        + `<span>Building demand ${kw === null ? '-' : Math.round(kw)} kW · 15-min ${d15 === null ? '-' : Math.round(d15)} kW · price ${pv('GRID/PRICE')}</span>`;
      if (dr.dataset.h !== html) { dr.innerHTML = html; dr.dataset.h = html; refreshBindings(dr); }
    }
  }
  const ab = document.getElementById('aq-banner');
  if (ab) {
    const bad = pm !== null && pm > 35.45;
    ab.hidden = !bad;
    if (bad) {
      const smoke = inj.find((i) => i.type === 'wildfire_smoke' && i.severity > 0);
      const html = `<b>⚠ OUTDOOR AIR QUALITY ALERT</b><span>PM2.5 ${pm.toFixed(0)} µg/m³ - ${esc(classify('aqi25', pm).label)}${smoke ? ' (wildfire smoke)' : ''}.</span><span>Consider minimum outdoor air, high-efficiency filtration and re-circulation; check zone PM2.5 on the <a href="#zone?m=pm25">IEQ heat-map</a>.</span>`;
      if (ab.dataset.h !== html) { ab.innerHTML = html; ab.dataset.h = html; }
    }
  }
  // end-use bars, scaled to the building meter
  const tot = val('MTR/BLDG-ELEC-KW');
  let sum = 0;
  for (const el of document.querySelectorAll('.ebar[data-epid]')) {
    const v = val(el.dataset.epid);
    const ref = el.dataset.grp === 'g' ? val('MTR/BLDG-GAS-KW') : tot;
    if (el.dataset.grp === 'e') sum += v ?? 0;
    const ok = v !== null && ref !== null && ref > 0.5;
    const f = ok ? Math.max(0, Math.min(1, v / ref)) : 0;
    el.querySelector('.eb-track i').style.width = `${(100 * f).toFixed(1)}%`;
    el.querySelector('.eb-pct').textContent = ok ? `${Math.round(100 * f)} %` : '-';
  }
  const rest = document.getElementById('eb-rest');
  if (rest) {
    const r = tot === null ? null : Math.max(0, tot - sum);
    rest.querySelector('.eb-track i').style.width = r === null || !tot ? '0' : `${Math.min(100, (100 * r) / tot).toFixed(1)}%`;
    rest.querySelector('.eb-val').textContent = r === null ? '-' : `${r.toFixed(r >= 100 ? 0 : 1)} kW`;
    rest.querySelector('.eb-pct').textContent = r === null || !tot ? '-' : `${Math.round((100 * r) / tot)} %`;
  }
  const di = document.getElementById('dmd-i');
  if (di) {
    const d = val('MTR/BLDG-DMD-15'), pk = val('MTR/PEAK-DMD-MONTH');
    const f = d !== null && pk ? Math.min(1, d / pk) : 0;
    di.style.width = `${(100 * f).toFixed(1)}%`;
    di.className = f > 0.95 ? 'hot' : '';
    $('#dmd-pct').textContent = pk ? `${Math.round(100 * f)} % of monthly peak` : '-';
  }
}

export function destroy() {
  clearInterval(timer); clearInterval(fcTimer);
  for (const c of [fcChart, gridChart, dmdChart]) c?.destroy();
  fcChart = gridChart = dmdChart = null;
}
