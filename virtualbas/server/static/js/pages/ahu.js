/* =============================================================================
 * AHU page - SVG schematic of a VAV air-handling unit with economizer,
 * filter, HW preheat coil, CHW cooling coil and VFD supply fan, plus the
 * served VAV boxes and a 24 h trend.
 * ========================================================================== */
import { S, $, esc, pv, pmap, svgBox, val, has, zoneLabel } from '../core.js';
import { TrendChart, loadSeries } from '../chart.js';
import { lamp, pbar, kvRows, gaugeRow } from '../widgets.js';

let eid = null, chart = null, timer = null;

// ---------------------------------------------------------------- SVG pieces
/** Damper with three blades; `vertical` = duct runs vertically. */
function damper(id, cx, cy, vertical) {
  const offs = [-25, 0, 25];
  const blades = offs.map((o) => {
    const x = vertical ? cx + o : cx, y = vertical ? cy : cy + o;
    const d = vertical ? `M${x} ${y - 11}V${y + 11}` : `M${x - 11} ${y}H${x + 11}`;
    return `<g class="blade" data-cx="${x}" data-cy="${y}"><path d="${d}"/><circle cx="${x}" cy="${y}" r="2"/></g>`;
  }).join('');
  const frame = vertical ? `<rect class="dmp-frame" x="${cx - 40}" y="${cy - 14}" width="80" height="28"/>` : `<rect class="dmp-frame" x="${cx - 14}" y="${cy - 40}" width="28" height="80"/>`;
  return `<g class="damper" id="${id}">${frame}${blades}</g>`;
}
/** Water coil: framed rectangle with serpentine tubes. */
function coil(id, x, cls, label) {
  let d = '';
  for (let i = 0; i < 6; i++) { const y = 298 + i * 12; d += `M${x + 3} ${y}H${x + 27}`; }
  return `<g class="coil ${cls}" id="${id}"><rect class="coil-fill" x="${x}" y="290" width="30" height="80"/><rect class="coil-frame" x="${x}" y="290" width="30" height="80"/><path class="coil-tubes" d="${d}"/>`
    + `<text class="comp-lbl" x="${x + 15}" y="282" text-anchor="middle">${label}</text></g>`;
}
/** Two-way control valve (bow-tie) on a vertical pipe. */
function valve(id, x, y) {
  return `<g class="valve" id="${id}"><path class="valve-body" d="M${x - 9} ${y - 7}L${x + 9} ${y + 7}V${y - 7}L${x - 9} ${y + 7}Z"/><path class="valve-stem" d="M${x} ${y}H${x + 14}M${x + 14} ${y - 6}V${y + 6}"/></g>`;
}
/** Safety device lamp drawn inside the duct (freeze-stat, smoke detector). */
function safety(pid, x, y, label) {
  if (!has(pid)) return '';
  return `<g class="slamp" id="sl-${esc(pid.split('/')[1])}" data-pid="${esc(pid)}"><title>${esc(pid)} - ${esc(S.pointById[pid].description)}</title>`
    + `<rect class="sl-bg" x="${x - 20}" y="${y - 10}" width="40" height="30" rx="3"/><circle class="sl-dot" cx="${x}" cy="${y + 10}" r="5"/>`
    + `<text class="sl-lbl" x="${x}" y="${y + 1}" text-anchor="middle">${label}</text></g>`;
}
/** Sensor bulb on the duct with a leader line to its value box. */
const sensor = (x, y, x2, y2) => `<path class="leader" d="M${x} ${y}L${x2} ${y2}"/><circle class="sensor" cx="${x}" cy="${y}" r="5"/>`;

function schematic(a) {
  const m = pmap(a.id);
  const B = (name, x, y, o = {}) => svgBox(m[name], x, y, o);
  return `<svg class="schem ahu-svg" id="ahu-svg" viewBox="0 0 1180 520" role="img" aria-label="Air handling unit schematic">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="arrowhead"/></marker>
    <pattern id="louver" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V8" class="louver-line"/></pattern>
  </defs>
  <!-- ducts: stroked layer then fill layer hides internal seams -->
  <g class="duct-edge"><rect x="60" y="70" width="1060" height="80"/><rect x="250" y="70" width="80" height="300"/><rect x="60" y="290" width="1060" height="80"/></g>
  <g class="duct-fill"><rect x="60" y="70" width="1060" height="80"/><rect x="250" y="70" width="80" height="300"/><rect x="60" y="290" width="1060" height="80"/></g>
  <!-- animated air flow -->
  <path class="flow flow-ret" d="M1110 110H290V330"/>
  <path class="flow flow-rel" d="M250 110H64"/>
  <path class="flow flow-oa" d="M64 330H1110"/>
  <!-- louvres -->
  <rect x="44" y="70" width="16" height="80" fill="url(#louver)" class="louver"/><rect x="44" y="290" width="16" height="80" fill="url(#louver)" class="louver"/>
  <text class="io-lbl" x="44" y="58">RELIEF AIR</text>
  <path class="io-arrow" d="M44 110H6" marker-end="url(#arr)"/>
  <text class="io-lbl" x="6" y="278">OUTDOOR AIR</text>
  <path class="io-arrow" d="M6 330H40" marker-end="url(#arr)"/>
  <text class="io-lbl" x="1176" y="58" text-anchor="end">RETURN AIR ← zones</text>
  <path class="io-arrow" d="M1176 110H1124" marker-end="url(#arr)"/>
  <text class="io-lbl" x="1176" y="392" text-anchor="end">SUPPLY AIR → VAV</text>
  <path class="io-arrow" d="M1122 330H1176" marker-end="url(#arr)"/>

  <!-- dampers -->
  ${damper('d-rel', 140, 110, false)}<text class="comp-lbl" x="140" y="166" text-anchor="middle">RELIEF DMPR</text>
  ${damper('d-oa', 140, 330, false)}<text class="comp-lbl" x="140" y="282" text-anchor="middle">OA DAMPER</text>
  ${damper('d-ret', 290, 220, true)}<text class="comp-lbl" x="338" y="224">RETURN DMPR</text>
  <!-- OA flow station -->
  <g class="afms"><path d="M205 292V368M213 292V368M221 292V368"/></g><text class="comp-lbl" x="213" y="282" text-anchor="middle">AFMS</text>
  <text class="comp-lbl" x="290" y="282" text-anchor="middle">MIXING</text>
  <!-- filter -->
  <path class="filter" d="M400 290L430 303L400 316L430 329L400 342L430 355L400 368"/><rect class="filter-frame" x="398" y="290" width="34" height="80"/>
  <text class="comp-lbl" x="415" y="282" text-anchor="middle">FILTER</text>
  <!-- coils + piping -->
  ${coil('c-hc', 470, 'hw', 'PREHEAT')}${coil('c-cc', 590, 'chw', 'COOLING')}
  <path class="pipe pipe-hws" d="M477 370V500"/><path class="pipe pipe-hwr" d="M493 370V500"/>
  <path class="pipe pipe-chws" d="M597 370V500"/><path class="pipe pipe-chwr" d="M613 370V500"/>
  ${valve('v-hc', 493, 396)}${valve('v-cc', 613, 396)}
  <text class="pipe-lbl" x="485" y="514" text-anchor="middle">HWS HWR</text>
  <text class="pipe-lbl" x="605" y="514" text-anchor="middle">CHWS CHWR</text>
  <!-- supply fan -->
  <g class="fan" id="fan"><circle class="fan-housing" cx="740" cy="330" r="34"/>
    <g class="fan-blades"><path d="M740 330L740 302A10 10 0 0 1 752 312Z M740 330L768 330A10 10 0 0 1 758 342Z M740 330L740 358A10 10 0 0 1 728 348Z M740 330L712 330A10 10 0 0 1 722 318Z"/><circle cx="740" cy="330" r="5"/></g></g>
  <text class="comp-lbl" x="740" y="282" text-anchor="middle">SUPPLY FAN (VFD)</text>
  <!-- duct static pressure tap + supply flow station -->
  <g class="afms"><path d="M985 292V368M993 292V368M1001 292V368"/></g>

  <!-- sensors + value boxes -->
  ${sensor(810, 110, 808, 42)}${sensor(910, 110, 912, 42)}
  ${B('RA-T', 760, 8, { label: 'Return air temp' })}${B('RA-RH', 864, 8, { label: 'Return air RH' })}
  ${sensor(370, 312, 393, 202)}${B('MA-T', 345, 168, { label: 'Mixed air temp' })}
  ${sensor(415, 300, 498, 202)}${B('FLT-DP', 450, 168, { label: 'Filter ΔP' })}
  ${sensor(650, 312, 608, 202)}${B('CC-LAT', 560, 168, { label: 'Coil leaving air' })}
  ${sensor(740, 296, 718, 202)}${B('SF-STS', 670, 168, { label: 'Fan status' })}
  ${sensor(850, 312, 848, 202)}${B('SA-T', 800, 168, { label: 'Supply air temp' })}
  ${B('SA-T-SP', 905, 168, { label: 'SAT set point' })}
  ${sensor(930, 348, 1058, 202)}${B('SA-RH', 1010, 168, { label: 'Supply air RH' })}
  ${B('OAD-CMD', 40, 405, { label: 'OA damper cmd' })}${B('OAD-POS', 140, 405, { label: 'OA damper pos' })}
  ${sensor(213, 352, 288, 405)}${B('OA-F', 240, 405, { label: 'OA flow' })}
  ${B('HCV-POS', 380, 405, { label: 'Preheat valve' })}
  ${B('CCV-POS', 500, 455, { label: 'CHW valve' })}
  ${B('SF-SPD', 650, 405, { label: 'Fan speed' })}${B('SF-KW', 650, 460, { label: 'Fan power' })}
  ${sensor(993, 352, 838, 405)}${B('SA-F', 790, 405, { label: 'Supply air flow' })}
  ${sensor(1070, 348, 943, 405)}${B('DSP', 895, 405, { label: 'Duct static' })}${B('DSP-SP', 1000, 405, { label: 'Static set point' })}
  ${B('CC-Q', 560, 230, { label: 'Coil load (truth)' })}
  ${has(m['OA-T']) ? `${sensor(92, 306, 54, 214)}${B('OA-T', 6, 180, { label: 'OA temp (intake)' })}` : ''}
  ${has(m['OA-RH']) ? B('OA-RH', 106, 180, { label: 'OA RH (intake)' }) : ''}
  ${has(m['RA-CO2']) ? `${sensor(704, 110, 704, 42)}${B('RA-CO2', 656, 8, { label: 'Return air CO₂' })}` : ''}
  ${has(m['SA-DP']) ? B('SA-DP', 1000, 460, { label: 'Supply dew point' }) : ''}
  ${safety(m['FRZ-STAT'], 545, 318, 'FRZ')}${safety(m['SMK-DET'], 1035, 302, 'SMOKE')}
  </svg>`;
}

// ---------------------------------------------------------------- details panel
function details(a) {
  const m = pmap(a.id);
  const col = (title, body) => (body.trim() ? `<div class="dcol"><h5>${title}</h5>${body}</div>` : '');
  const kv = (rows) => { const h = kvRows(rows); return h ? `<dl class="kvlist">${h}</dl>` : ''; };
  const frac = (label, pid) => (has(pid) ? `<div class="frac${S.pointById[pid].kind === 'truth' ? ' truth-only' : ''}"><span class="k">${label}</span>${pv(pid)}${pbar(pid, 100)}</div>` : '');
  const cols = [
    col('Air quality &amp; psychrometrics', kv([['OA temp (intake)', m['OA-T']], ['OA temp (weather stn)', 'WX/OA-T'],
      ['OA RH (intake)', m['OA-RH']], ['Return air RH', m['RA-RH']], ['Return air CO₂', m['RA-CO2']], ['Supply air RH', m['SA-RH']], ['Supply dew point', m['SA-DP']], ['Supply PM2.5', m['SA-PM25']]])),
    col('Outdoor-air fraction', frac('Temperature-based (BAS)', m['OA-FRAC-CALC']) + frac('Airflow-based (AFMS)', m['OA-FRAC-AFMS']) + frac('True OA fraction', m['OA-FRAC'])
      + kv([['OA flow', m['OA-F']], ['Supply flow', m['SA-F']]]) + `<p class="hint">Design minimum OA ${(+a.meta.min_oa_m3s || 0).toFixed(2)} m³/s (${a.meta.design_flow_m3s ? Math.round((100 * a.meta.min_oa_m3s) / a.meta.design_flow_m3s) : '-'} % of design flow).</p>`),
    col('Cooling coil (CHW)', kv([['Entering water', m['CC-EWT']], ['Leaving water', m['CC-LWT']], ['Water ΔT', null, '<span id="cc-dt">-</span>'], ['Water flow', m['CC-WF']],
      ['Load (BTU meter)', m['CC-BTU']], ['Load (truth)', m['CC-Q']], ['Air-side ΔP', m['CC-DP']], ['Leaving air temp', m['CC-LAT']], ['Valve position', m['CCV-POS']]])),
    col('Preheat coil (HW) &amp; safeties', kv([['Leaving air temp', m['HC-LAT']], ['Load (BTU meter)', m['HC-BTU']], ['Valve position', m['HCV-POS']], ['Mixed air temp', m['MA-T']], ['Filter ΔP', m['FLT-DP']]])
      + `<div class="lamps col">${lamp(m['FRZ-STAT'], 'Freeze stat', 'alarm')}${lamp(m['SMK-DET'], 'Smoke detector', 'alarm')}</div>`),
    col('Supply fan &amp; VFD', kv([['Speed', m['SF-SPD']], ['VFD frequency', m['SF-HZ']], ['Motor current', m['SF-AMPS']], ['Power', m['SF-KW']], ['Specific fan power', m['SF-W-PER-CMS']],
      ['Run hours', m['SF-RUNHRS']], ['Starts', m['SF-STARTS']]]) + gaugeRow('vib', m['SF-VIB'], 'Vibration')),
  ].join('');
  return cols ? `<section class="card details-card"><div class="card-h"><b>Unit details</b><small>coil hydronics, fan drive, safeties and outdoor-air verification</small></div><div class="dgrid">${cols}</div></section>` : '';
}

// ---------------------------------------------------------------- page
export function render(main, { arg }) {
  const ahus = S.equip.filter((e) => e.type === 'AHU');
  eid = S.equipById[arg]?.type === 'AHU' ? arg : ahus[0].id;
  const a = S.equipById[eid];
  const m = pmap(eid);
  const vavs = a.meta.vav || [];
  main.innerHTML = `
  <div class="page-head"><h1>Air handling unit</h1>
    <div class="tabs">${ahus.map((x) => `<a href="#ahu/${x.id}" class="${x.id === eid ? 'on' : ''}">${x.id}</a>`).join('')}</div>
    <span class="crumb">${esc(a.description)} · EnergyPlus <code>${esc(a.eplus_name)}</code></span></div>
  <div class="eq-grid">
    <section class="card schem-card">${schematic(a)}</section>
    <aside class="card status-card">
      <div class="card-h"><b>Unit status</b></div>
      <div class="lamps">${lamp(m['FRZ-STAT'], 'Freeze stat', 'alarm')}${lamp(m['SMK-DET'], 'Smoke detector', 'alarm')}</div>
      <dl class="kvlist big">
        <dt>Operating mode</dt><dd>${pv(m['OCC-MODE'], { cls: 'mode' })}</dd>
        <dt>Fan start/stop cmd</dt><dd>${pv(m['SF-CMD'])}</dd>
        <dt>Economizer</dt><dd>${pv(m['ECON-EN'])}</dd>
        <dt>Mixed air set point</dt><dd>${pv(m['MA-T-SP'])}</dd>
        <dt>SAT set point</dt><dd>${pv(m['SA-T-SP'])}</dd>
        <dt>Static set point</dt><dd>${pv(m['DSP-SP'])}</dd>
        <dt>Outdoor air temp</dt><dd>${pv(has(m['OA-T']) ? m['OA-T'] : 'WX/OA-T')}</dd>
        <dt>OA fraction (calc.)</dt><dd>${has(m['OA-FRAC-CALC']) ? pv(m['OA-FRAC-CALC']) : '<span id="oa-frac">-</span>'}</dd>
        <dt class="truth-only">Cooling coil load</dt><dd class="truth-only">${pv(m['CC-Q'])}</dd>
      </dl>
      <div class="card-h"><b>Design data</b></div>
      <dl class="kvlist">
        <dt>Design supply flow</dt><dd>${(+a.meta.design_flow_m3s).toFixed(2)} m³/s</dd>
        <dt>Minimum outdoor air</dt><dd>${(+a.meta.min_oa_m3s).toFixed(2)} m³/s</dd>
        <dt>Fan</dt><dd>${esc(a.meta.fan_type || '-')}</dd>
        <dt>Air loop</dt><dd><code>${esc(a.meta.air_loop)}</code></dd>
      </dl>
      <p class="hint">Click any value to see its trend, Brick class and – for set points and commands – to write a priority override.</p>
    </aside>
  </div>
  ${details(a)}
  <div class="eq-grid2">
    <section class="card">
      <div class="card-h"><b>Served VAV terminals</b><small>${vavs.length}</small></div>
      <table class="tbl"><thead><tr><th>Terminal</th><th>Zone temp</th><th>Htg / clg SP</th><th>Airflow</th><th>Flow SP</th><th>Damper</th><th>Reheat</th><th>CO₂</th></tr></thead>
      <tbody>${vavs.map((v) => {
        const vm = pmap(v), z = S.equipById[v].meta.zone_equip, zm = pmap(z);
        return `<tr><td><a href="#vav/${esc(v)}">${esc(v.replace('VAV-', ''))}</a><small class="sub">${esc(zoneLabel(S.equipById[v].meta.zone))}${S.equipById[z]?.meta?.multiplier > 1 ? ' ×' + S.equipById[z].meta.multiplier : ''}</small></td>
          <td>${pv(zm['ZN-T'])}</td><td>${pv(zm['HTG-SP'], { unit: false })} / ${pv(zm['CLG-SP'])}</td>
          <td>${pv(vm['DA-F'])}</td><td>${pv(vm['DA-F-SP'])}</td><td>${pv(vm['DMPR-POS'])}</td><td>${pv(vm['RHV-POS'])}</td><td>${pv(zm['ZN-CO2'])}</td></tr>`;
      }).join('')}</tbody></table>
    </section>
    <section class="card chart-card"><div class="card-h"><b>Last 24 h</b><small>supply / mixed / return air temperatures, fan speed and valve/damper positions</small></div>
      <div id="ahu-chart" class="chart-box" style="height:280px"></div></section>
  </div>`;
  chart = new TrendChart($('#ahu-chart', main));
  loadChart();
  timer = setInterval(loadChart, 30000);
}

function loadChart() {
  const m = pmap(eid);
  const names = ['SA-T', 'SA-T-SP', 'MA-T', 'RA-T', 'SF-SPD', 'OAD-POS', 'CCV-POS'];
  const n = Math.round(86400 / (S.info.timestep_s || 300));
  loadSeries(names.map((x) => m[x]), n, { truth: S.truth, pointById: S.pointById, labels: names })
    .then(({ times, series }) => chart?.setData(times, series)).catch(() => {});
}
export function onTruth() { loadChart(); }

/** Rotate damper blades: horizontal duct closed = blade vertical (90°). */
function setDamper(id, openPct, vertical) {
  const g = document.getElementById(id);
  if (!g) return;
  const p = Math.max(0, Math.min(100, openPct ?? 0));
  const ang = 90 * (1 - p / 100);
  for (const b of g.querySelectorAll('.blade')) b.setAttribute('transform', `rotate(${vertical ? -ang : ang} ${b.dataset.cx} ${b.dataset.cy})`);
}

export function update() {
  const m = pmap(eid);
  const svg = document.getElementById('ahu-svg');
  if (!svg) return;
  const running = (val(m['SF-STS']) ?? 0) >= 0.5;
  svg.classList.toggle('running', running);
  const oa = val(m['OAD-POS']);
  setDamper('d-oa', oa, false);
  setDamper('d-rel', oa, false);
  setDamper('d-ret', oa === null ? null : 100 - oa, true);
  const hc = val(m['HCV-POS']) ?? 0, cc = val(m['CCV-POS']) ?? 0;
  document.querySelector('#c-hc .coil-fill')?.setAttribute('fill-opacity', (0.12 + 0.8 * hc / 100).toFixed(2));
  document.querySelector('#c-cc .coil-fill')?.setAttribute('fill-opacity', (0.12 + 0.8 * cc / 100).toFixed(2));
  document.getElementById('v-hc')?.classList.toggle('open', hc > 1);
  document.getElementById('v-cc')?.classList.toggle('open', cc > 1);
  // safety lamps in the duct
  for (const n of ['FRZ-STAT', 'SMK-DET']) document.getElementById('sl-' + n)?.classList.toggle('on', (val(m[n]) ?? 0) >= 0.5);
  const ewt = val(m['CC-EWT']), lwt = val(m['CC-LWT']), dt = document.getElementById('cc-dt');
  if (dt) dt.textContent = ewt === null || lwt === null ? '---' : `${(lwt - ewt).toFixed(1)} K`;
  // OA fraction from temperatures (what a commissioning agent would compute) - only if the BAS has no such point
  const oat = val(has(m['OA-T']) ? m['OA-T'] : 'WX/OA-T'), mat = val(m['MA-T']), rat = val(m['RA-T']);
  const el = document.getElementById('oa-frac');
  if (el) {
    const f = oat !== null && mat !== null && rat !== null && Math.abs(rat - oat) > 1.5 ? (rat - mat) / (rat - oat) : null;
    el.textContent = f === null ? 'n/a (ΔT too small)' : `${Math.round(100 * Math.max(0, Math.min(1, f)))} %`;
  }
}

export function destroy() { clearInterval(timer); chart?.destroy(); chart = null; }
