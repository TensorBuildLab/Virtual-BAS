/* =============================================================================
 * Central plant page - condenser water loop with cooling tower, two
 * water-cooled chillers, chilled-water distribution and the hot-water plant.
 * ========================================================================== */
import { S, $, esc, pv, pmap, svgBox, val, has, equipOfType } from '../core.js';
import { TrendChart, loadSeries } from '../chart.js';
import { lamp, pbar, kvRows, scale } from '../widgets.js';

let chart = null, timer = null;

/** Pipe path (+ animated flow overlay) of a loop. */
const pipe = (cls, d) => `<path class="pipe pipe-${cls}" d="${d}"/><path class="pflow pf-${cls}" d="${d}"/>`;
/** Centrifugal pump symbol. */
const pump = (id, x, y, rot = 0) => `<g class="pump" id="${id}" transform="rotate(${rot} ${x} ${y})"><circle cx="${x}" cy="${y}" r="16"/><path d="M${x - 9} ${y + 10}L${x} ${y - 13}L${x + 9} ${y + 10}"/></g>`;

/** One chiller: condenser shell (top), compressor, evaporator shell (bottom). */
function chiller(id, y0) {
  return `<g class="equip chiller" id="eq-${id}">
    <rect class="shell cond" x="440" y="${y0}" width="200" height="50" rx="22"/>
    <rect class="shell evap" x="440" y="${y0 + 88}" width="200" height="50" rx="22"/>
    <path class="comp-link" d="M520 ${y0 + 50}V${y0 + 88}M560 ${y0 + 50}V${y0 + 88}"/>
    <circle class="compressor" cx="540" cy="${y0 + 69}" r="15"/><text class="comp-sym" x="540" y="${y0 + 74}" text-anchor="middle">C</text>
    <text class="eq-name" x="456" y="${y0 + 74}">${id}</text>
    <text class="shell-lbl" x="540" y="${y0 + 30}" text-anchor="middle">condenser</text>
    <text class="shell-lbl" x="540" y="${y0 + 118}" text-anchor="middle">evaporator</text>
  </g>`;
}

function schematic() {
  const P = (eq, n, x, y, o) => svgBox(pmap(eq)[n], x, y, o);
  const ch = (id, y0) => `${chiller(id, y0)}
    ${P(id, 'KW', 440, y0 - 54, { label: 'Power' })}${P(id, 'LOAD', 542, y0 - 54, { label: 'Cooling load' })}${P(id, 'STS', 644, y0 - 54, { label: 'Run status' })}
    ${P(id, 'CDW-EWT', 340, y0 - 50, { label: 'Cond. entering' })}${P(id, 'CDW-LWT', 340, y0 + 50, { label: 'Cond. leaving' })}
    ${P(id, 'CHW-EWT', 650, y0 + 46, { label: 'Evap. entering' })}${P(id, 'CHW-LWT', 650, y0 + 136, { label: 'Evap. leaving' })}
    ${P(id, 'COP', 340, y0 + 104, { label: 'COP (truth)', w: 90 })}`;
  const y1 = 70, y2 = 330;
  return `<svg class="schem plant-svg" id="plant-svg" viewBox="0 0 1300 650" role="img" aria-label="Central plant schematic">
  <text class="sec-lbl" x="20" y="16">CONDENSER WATER</text><text class="sec-lbl" x="340" y="16">CHILLERS</text>
  <text class="sec-lbl" x="812" y="16">CHILLED WATER</text><text class="sec-lbl" x="1062" y="16">HEATING HOT WATER</text>
  <path class="sep" d="M1030 24V640"/>

  <!-- ===== condenser loop ===== -->
  <g id="loop-cw">
    ${pipe('cws', 'M140 180V600H300V85H440 M300 345H440')}
    ${pipe('cwr', 'M440 105H320V30H200V62 M440 365H320V105')}
  </g>
  <g class="equip tower" id="eq-CT-1">
    <path class="tower-body" d="M50 62L230 62L212 180L68 180Z"/>
    <path class="tower-fill" d="M70 100H210M74 120H206M77 140H203M80 160H200"/>
    <rect class="tower-stack" x="104" y="44" width="72" height="18"/>
    <g class="fan-blades tower-fan"><ellipse cx="140" cy="53" rx="30" ry="5"/></g>
    <text class="eq-name" x="140" y="200" text-anchor="middle">CT-1</text>
  </g>
  ${P('CT-1', 'LWT', 30, 210, { label: 'Tower leaving' })}${P('CT-1', 'EWT', 154, 210, { label: 'Tower entering' })}
  ${P('CT-1', 'FAN-KW', 30, 264, { label: 'Fan power' })}${P('CT-1', 'FAN-STS', 154, 264, { label: 'Fan status' })}
  ${P('CW-SYS', 'CW-ST', 30, 318, { label: 'CW supply' })}${P('CW-SYS', 'CW-RT', 154, 318, { label: 'CW return' })}
  ${P('CW-SYS', 'CW-ST-SP', 30, 372, { label: 'CW supply SP' })}${P('CW-SYS', 'CW-F', 154, 372, { label: 'CW flow' })}
  ${P('CW-SYS', 'CW-DP', 30, 426, { label: 'CW diff. press.' })}
  ${P('CWP-1', 'KW', 30, 480, { label: 'CWP-1 power' })}${P('CWP-1', 'SPD', 154, 480, { label: 'CWP-1 speed' })}
  ${P('CWP-1', 'STS', 30, 534, { label: 'CWP-1 status' })}
  ${pump('pmp-cw', 140, 600, 0)}<text class="eq-name" x="164" y="590">CWP-1</text>

  <!-- ===== chillers ===== -->
  ${ch('CH-1', y1)}${ch('CH-2', y2)}

  <!-- ===== chilled water distribution ===== -->
  <g id="loop-chw">
    ${pipe('chws', `M640 ${y1 + 125}H800V${y2 + 125}H640 M800 ${y2 + 125}V600H860`)}
    ${pipe('chwr', `M960 600H1010V40H770V${y1 + 100}H640 M770 ${y1 + 100}V${y2 + 100}H640`)}
  </g>
  ${pump('pmp-chw', 800, 540, 180)}<text class="eq-name" x="820" y="520">CHWP-1</text>
  <rect class="load-box" x="860" y="575" width="100" height="50" rx="4"/><text class="load-lbl" x="910" y="596" text-anchor="middle">AHU-1…4</text><text class="load-lbl" x="910" y="612" text-anchor="middle">cooling coils</text>
  ${P('CHW-SYS', 'CHW-ST', 812, 56, { label: 'CHW supply' })}${P('CHW-SYS', 'CHW-RT', 910, 56, { label: 'CHW return', w: 92 })}
  ${P('CHW-SYS', 'CHW-ST-SP', 812, 110, { label: 'CHW supply SP' })}${P('CHW-SYS', 'CHW-F', 910, 110, { label: 'CHW flow', w: 92 })}
  ${P('CHW-SYS', 'CHW-DP', 812, 164, { label: 'CHW diff. press.' })}
  ${P('CHWP-1', 'KW', 812, 380, { label: 'CHWP-1 power' })}${P('CHWP-1', 'SPD', 910, 380, { label: 'CHWP-1 speed', w: 92 })}
  ${P('CHWP-1', 'STS', 812, 434, { label: 'CHWP-1 status' })}

  <!-- ===== hot water plant ===== -->
  <g id="loop-hw">
    ${pipe('hws', 'M1240 80H1285V630H1180')}
    ${pipe('hwr', 'M1080 630H1045V150H1062')}
  </g>
  <g class="equip boiler" id="eq-BLR-1">
    <rect class="boiler-body" x="1062" y="50" width="178" height="120" rx="6"/>
    <path class="flame" d="M1110 150C1094 130 1108 116 1112 100C1118 116 1124 112 1122 96C1138 116 1136 140 1126 150Z"/>
    <text class="eq-name" x="1150" y="100">BLR-1</text><text class="shell-lbl" x="1150" y="118">gas boiler</text>
  </g>
  <rect class="load-box hw" x="1080" y="608" width="100" height="40" rx="4"/><text class="load-lbl" x="1130" y="624" text-anchor="middle">preheat + VAV</text><text class="load-lbl" x="1130" y="639" text-anchor="middle">reheat coils</text>
  ${P('BLR-1', 'LOAD', 1062, 182, { label: 'Boiler output' })}${P('BLR-1', 'GAS-KW', 1170, 182, { label: 'Gas input' })}
  ${P('BLR-1', 'HW-LWT', 1062, 236, { label: 'Boiler leaving' })}${P('BLR-1', 'HW-EWT', 1170, 236, { label: 'Boiler entering' })}
  ${P('BLR-1', 'STS', 1062, 290, { label: 'Firing status' })}${P('BLR-1', 'PLR', 1170, 290, { label: 'PLR (truth)' })}
  ${P('HW-SYS', 'HW-ST', 1062, 344, { label: 'HW supply' })}${P('HW-SYS', 'HW-RT', 1170, 344, { label: 'HW return' })}
  ${P('HW-SYS', 'HW-ST-SP', 1062, 398, { label: 'HW supply SP' })}${P('HW-SYS', 'HW-F', 1170, 398, { label: 'HW flow' })}
  ${P('HW-SYS', 'HW-DP', 1062, 452, { label: 'HW diff. press.' })}${P('HWP-1', 'STS', 1170, 452, { label: 'HWP-1 status' })}
  ${P('HWP-1', 'KW', 1062, 506, { label: 'HWP-1 power' })}${P('HWP-1', 'SPD', 1170, 506, { label: 'HWP-1 speed' })}
  ${pump('pmp-hw', 1045, 580, 0)}<text class="eq-name" x="1062" y="572" text-anchor="start">HWP-1</text>
  </svg>`;
}

// ---------------------------------------------------------------- equipment detail panels
const kv = (rows) => { const h = kvRows(rows); return h ? `<dl class="kvlist kv2">${h}</dl>` : ''; };
/** Calculated difference / ratio shown in a detail panel, refreshed in update(). */
const calc = (a, b, op = 'sub', unit = 'K', dec = 1) => (has(a) && has(b) ? `<span class="calc" data-a="${esc(a)}" data-b="${esc(b)}" data-op="${op}" data-u="${unit}" data-d="${dec}">---</span>` : null);
const crow = (label, html) => (html ? [label, null, html] : [label, undefined]);
function panel(e, head, body) {
  return `<section class="card eqd"><div class="card-h"><b>${esc(e.id)}</b><small>${esc(e.description)}</small></div>${head ? `<div class="lamps">${head}</div>` : ''}${body}</section>`;
}
const big = (label, pid, max, cls = '') => (has(pid) ? `<div class="eqd-big"><span class="k">${label}</span>${pv(pid, { cls: 'pv-mid' })}${pbar(pid, max, cls)}</div>` : '');

function chillerPanel(e) {
  const m = pmap(e.id);
  return panel(e, lamp(m.STS, 'Run', 'run') + lamp(m.ALM, 'Alarm', 'alarm'),
    `<div class="eqd-bigs">${big('% RLA', m['PCT-RLA'], 100)}${big('Power', m.KW, (S.equipById[e.id]?.meta?.capacity_kw || 1000) / 5)}${has(m['KW-TON']) ? `<div class="eqd-big"><span class="k">Efficiency</span>${pv(m['KW-TON'], { cls: 'pv-mid' })}</div>` : ''}</div>`
    + kv([['Load (tons)', m['LOAD-TONS']], ['Evaporator load', m.LOAD], ['Enable command', m['EN-CMD']], ['PLR (truth)', m.PLR], ['COP (truth)', m.COP],
      ['Evap. entering', m['CHW-EWT']], ['Evap. leaving', m['CHW-LWT']], ['Evap. water flow', m['CHW-F']], ['Cond. water flow', m['CDW-F']],
      ['Cond. entering', m['CDW-EWT']], ['Cond. leaving', m['CDW-LWT']], ['Evap. sat. temp', m['EVAP-SAT-T']], ['Cond. sat. temp', m['COND-SAT-T']],
      ['Evap. pressure', m['EVAP-P']], ['Cond. pressure', m['COND-P']],
      crow('Lift (sat.)', calc(m['COND-SAT-T'], m['EVAP-SAT-T'])), crow('Evap. approach', calc(m['CHW-LWT'], m['EVAP-SAT-T'])),
      crow('Cond. approach', calc(m['COND-SAT-T'], m['CDW-LWT'])), crow('Evap. ΔT', calc(m['CHW-EWT'], m['CHW-LWT'])),
      ['Run hours', m.RUNHRS], ['Starts', m.STARTS]]));
}
function boilerPanel(e) {
  const m = pmap(e.id);
  return panel(e, lamp(m.STS, 'Firing', 'run') + lamp(m.ALM, 'Alarm', 'alarm'),
    `<div class="eqd-bigs">${big('Firing rate', m['FIRE-RATE'], 100, 'pb-hot')}${big('Flue gas', m['FLUE-T'], 250, 'pb-hot')}</div>`
    + kv([['Heat output', m.LOAD], ['Gas input', m['GAS-KW']], crow('Efficiency (calc.)', calc(m.LOAD, m['GAS-KW'], 'div', '%', 0)), ['Efficiency (truth)', m.EFF],
      ['HW leaving', m['HW-LWT']], ['HW entering', m['HW-EWT']], ['HW flow', m['HW-F']], ['Enable command', m['EN-CMD']], ['PLR (truth)', m.PLR],
      ['Run hours', m.RUNHRS], ['Starts', m.STARTS]]));
}
function towerPanel(e) {
  const m = pmap(e.id);
  return panel(e, lamp(m['FAN-STS'], 'Fan', 'run') + lamp(m.ALM, 'Alarm', 'alarm'),
    `<div class="eqd-bigs">${big('Fan speed', m['FAN-SPD'], 100)}${has(m.APPROACH) ? `<div class="eqd-big"><span class="k">Approach</span>${pv(m.APPROACH, { cls: 'pv-mid' })}</div>` : ''}${has(m.RANGE) ? `<div class="eqd-big"><span class="k">Range</span>${pv(m.RANGE, { cls: 'pv-mid' })}</div>` : ''}</div>`
    + kv([['Fan power', m['FAN-KW']], ['Entering water', m.EWT], ['Leaving water', m.LWT], ['OA wet bulb', has('WX/OA-WB') ? 'WX/OA-WB' : undefined],
      ['Make-up water', m['MAKEUP-F']], ['Evaporation (truth)', m['EVAP-F']], ['Heat rejected (truth)', m['Q-REJ']], ['Fan run hours', m['FAN-RUNHRS']], ['Fan starts', m['FAN-STARTS']]]));
}
function loopPanel(e) {
  const m = pmap(e.id);
  const st = Object.keys(m).find((n) => /-ST$/.test(n));
  const pre = st ? st.slice(0, -3) : '';
  const tons = m['CHW-TONS'], kwt = m['PLANT-KW-TON'];
  return panel(e, '',
    `<div class="eqd-bigs">${has(tons) ? `<div class="eqd-big"><span class="k">Plant load</span>${pv(tons, { cls: 'pv-mid' })}</div>` : ''}${has(kwt) ? `<div class="eqd-big"><span class="k">Plant efficiency</span>${pv(kwt, { cls: 'pv-mid' })}</div>` : ''}${has(m[pre + '-DT']) ? `<div class="eqd-big"><span class="k">Loop ΔT</span>${pv(m[pre + '-DT'], { cls: 'pv-mid' })}</div>` : ''}</div>`
    + kv([['Supply temp', m[pre + '-ST']], ['Return temp', m[pre + '-RT']], ['Supply set point', m[pre + '-ST-SP']], ['Flow', m[pre + '-F']], ['Differential pressure', m[pre + '-DP']]]));
}
function dhwPanel(e) {
  const m = pmap(e.id);
  return panel(e, lamp(m.STS, 'Burner', 'run'), kv([['Tank temperature', m['TANK-T']], ['Gas input', m['GAS-KW']], ['Hot-water use', m['USE-F']]]));
}
function pumpTable(pumps) {
  if (!pumps.length) return '';
  const td = (pid) => `<td>${has(pid) ? pv(pid) : '<span class="muted">-</span>'}</td>`;
  return `<section class="card eqd eqd-wide"><div class="card-h"><b>Pumps</b><small>${pumps.length} · VFD frequency, vibration (ISO 10816) and run statistics</small></div>
    <table class="tbl"><thead><tr><th>Pump</th><th>Status</th><th>Speed</th><th>VFD Hz</th><th>Power</th><th>Vibration</th><th>Run hours</th><th>Starts</th></tr></thead>
    <tbody>${pumps.map((e) => { const m = pmap(e.id); return `<tr><td><b>${esc(e.id)}</b><small class="sub">${esc(e.parent || '')}</small></td><td>${lamp(m.STS, '', 'run')}</td>${td(m.SPD)}${td(m.HZ)}${td(m.KW)}
      <td class="vibcell">${has(m.VIB) ? `${pv(m.VIB)}${scale('vib', m.VIB)}` : '-'}</td>${td(m.RUNHRS)}${td(m.STARTS)}</tr>`; }).join('')}</tbody></table></section>`;
}
function details() {
  const html = [
    ...equipOfType('PlantLoop').map(loopPanel),
    ...equipOfType('Chiller').map(chillerPanel),
    ...equipOfType('CoolingTower').map(towerPanel),
    ...equipOfType('Boiler').map(boilerPanel),
    ...equipOfType('WaterHeater').map(dhwPanel),
  ].join('');
  return `<div class="plant-details">${html}${pumpTable(equipOfType('Pump'))}</div>`;
}

export function render(main) {
  const c1 = pmap('CH-1'), c2 = pmap('CH-2');
  main.innerHTML = `
  <div class="page-head"><h1>Central plant</h1><span class="crumb">chilled water · condenser water · heating hot water</span></div>
  <div class="eq-grid">
    <section class="card schem-card">${schematic()}</section>
    <aside class="card status-card">
      <div class="card-h"><b>Plant summary</b></div>
      <dl class="kvlist big">
        <dt>Chiller power (meter)</dt><dd>${pv('MTR/CLG-ELEC-KW')}</dd>
        <dt>Pump power (meter)</dt><dd>${pv('MTR/PUMP-ELEC-KW')}</dd>
        <dt>Heat rejection (meter)</dt><dd>${pv('MTR/HREJ-ELEC-KW')}</dd>
        <dt>Heating gas (meter)</dt><dd>${pv('MTR/HTG-GAS-KW')}</dd>
        <dt>Plant kW/ton (calc.)</dt><dd><span id="kwton">-</span></dd>
        ${kvRows([['Plant kW/ton (BAS)', 'CHW-SYS/PLANT-KW-TON'], ['CHW plant load', 'CHW-SYS/CHW-TONS'], ['CHW loop ΔT', 'CHW-SYS/CHW-DT']])}
        <dt>CH-1 enable cmd</dt><dd>${pv(c1['EN-CMD'])}</dd>
        <dt>CH-2 enable cmd</dt><dd>${pv(c2['EN-CMD'])}</dd>
        <dt>Boiler enable cmd</dt><dd>${pv(pmap('BLR-1')['EN-CMD'])}</dd>
        <dt class="truth-only">CH-1 PLR / COP</dt><dd class="truth-only">${pv('CH-1/PLR')} / ${pv('CH-1/COP')}</dd>
        <dt class="truth-only">CH-2 PLR / COP</dt><dd class="truth-only">${pv('CH-2/PLR')} / ${pv('CH-2/COP')}</dd>
      </dl>
      <div class="card-h"><b>Design data</b></div>
      <dl class="kvlist">
        <dt>Chiller capacity</dt><dd>2 × ${Math.round(S.equipById['CH-1']?.meta?.capacity_kw || 0)} kW</dd>
        <dt>Boiler capacity</dt><dd>${Math.round(S.equipById['BLR-1']?.meta?.capacity_kw || 0)} kW</dd>
        <dt>CHW design flow</dt><dd>${((S.equipById['CHW-SYS']?.meta?.design_flow_m3s || 0) * 1000).toFixed(0)} L/s</dd>
        <dt>CW design flow</dt><dd>${((S.equipById['CW-SYS']?.meta?.design_flow_m3s || 0) * 1000).toFixed(0)} L/s</dd>
      </dl>
    </aside>
  </div>
  <section class="card chart-card"><div class="card-h"><b>Last 24 h</b><small>loop temperatures and chiller power</small></div>
    <div id="plant-chart" class="chart-box" style="height:260px"></div></section>
  <div class="page-sub"><h2>Equipment details</h2><span class="crumb">chiller panels, boiler, tower, loops, pumps${equipOfType('WaterHeater').length ? ', service hot water' : ''}</span></div>
  ${details()}`;
  chart = new TrendChart($('#plant-chart', main));
  loadChart();
  timer = setInterval(loadChart, 30000);
}

function loadChart() {
  const pids = ['CHW-SYS/CHW-ST', 'CHW-SYS/CHW-RT', 'CW-SYS/CW-ST', 'CH-1/KW', 'CH-2/KW'];
  const n = Math.round(86400 / (S.info.timestep_s || 300));
  loadSeries(pids, n, { truth: S.truth, pointById: S.pointById, labels: ['CHW supply', 'CHW return', 'CW supply', 'CH-1 power', 'CH-2 power'] })
    .then(({ times, series }) => chart?.setData(times, series)).catch(() => {});
}
export function onTruth() { loadChart(); }

export function update() {
  const svg = document.getElementById('plant-svg');
  if (!svg) return;
  const on = (pid) => (val(pid) ?? 0) >= 0.5;
  const st = {
    'eq-CH-1': on('CH-1/STS'), 'eq-CH-2': on('CH-2/STS'), 'eq-CT-1': on('CT-1/FAN-STS'), 'eq-BLR-1': on('BLR-1/STS'),
    'pmp-cw': on('CWP-1/STS'), 'pmp-chw': on('CHWP-1/STS'), 'pmp-hw': on('HWP-1/STS'),
  };
  for (const [id, v] of Object.entries(st)) document.getElementById(id)?.classList.toggle('on', v);
  // loops flow when their pump runs and measured flow is non-trivial
  svg.querySelector('#loop-cw')?.classList.toggle('running', st['pmp-cw'] && (val('CW-SYS/CW-F') ?? 0) > 0.5);
  svg.querySelector('#loop-chw')?.classList.toggle('running', st['pmp-chw'] && (val('CHW-SYS/CHW-F') ?? 0) > 0.5);
  svg.querySelector('#loop-hw')?.classList.toggle('running', st['pmp-hw'] && (val('HW-SYS/HW-F') ?? 0) > 0.05);
  const kw = (val('CH-1/KW') ?? 0) + (val('CH-2/KW') ?? 0) + (val('CHWP-1/KW') ?? 0) + (val('CWP-1/KW') ?? 0) + (val('CT-1/FAN-KW') ?? 0);
  const q = (val('CH-1/LOAD') ?? 0) + (val('CH-2/LOAD') ?? 0);
  for (const c of document.querySelectorAll('.calc[data-a]')) {
    const a = val(c.dataset.a), b = val(c.dataset.b);
    let t = '---';
    if (a !== null && b !== null) {
      if (c.dataset.op === 'div') t = b > 1 ? `${(100 * a / b).toFixed(+c.dataset.d)} ${c.dataset.u}` : 'n/a';
      else t = `${(a - b).toFixed(+c.dataset.d)} ${c.dataset.u}`;
    }
    if (c.textContent !== t) c.textContent = t;
  }
  const el = document.getElementById('kwton');
  if (el) el.textContent = q > 50 ? `${(kw / (q / 3.517)).toFixed(2)} kW/ton` : 'n/a (no load)';
}

export function destroy() { clearInterval(timer); chart?.destroy(); chart = null; }
