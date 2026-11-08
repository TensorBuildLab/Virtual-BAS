/* =============================================================================
 * VAV page - single-duct VAV terminal with hot-water reheat and the zone it
 * serves; controller loop outputs and a 24 h trend.
 * ========================================================================== */
import { S, $, esc, pv, pmap, svgBox, val, has, zoneLabel } from '../core.js';
import { TrendChart, loadSeries } from '../chart.js';
import { lamp, pbar, kvRows } from '../widgets.js';

let eid = null, chart = null, timer = null;

function schematic(v) {
  const vm = pmap(v.id), zid = v.meta.zone_equip, zm = pmap(zid);
  const V = (n, x, y, o) => svgBox(vm[n], x, y, o);
  const Z = (n, x, y, o) => svgBox(zm[n], x, y, o);
  return `<svg class="schem vav-svg" id="vav-svg" viewBox="0 0 1000 470" role="img" aria-label="VAV terminal schematic">
  <defs><marker id="arr2" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="arrowhead"/></marker></defs>
  <!-- ducts -->
  <g class="duct-edge"><rect x="30" y="92" width="180" height="56"/><rect x="200" y="70" width="220" height="100"/><rect x="420" y="92" width="340" height="56"/><rect x="700" y="92" width="60" height="150"/></g>
  <g class="duct-fill"><rect x="30" y="92" width="180" height="56"/><rect x="200" y="70" width="220" height="100"/><rect x="420" y="92" width="340" height="56"/><rect x="700" y="92" width="60" height="150"/></g>
  <path class="flow flow-oa" d="M34 120H730V236"/>
  <a href="#ahu/${esc(v.parent)}"><text class="io-lbl link" x="30" y="${has(vm['DA-VP']) ? 166 : 178}">PRIMARY AIR ← ${esc(v.parent)}</text></a>
  <!-- flow cross (velocity pressure pickup) -->
  <g class="afms"><path d="M150 94V146M162 94V146"/><path d="M140 120H172"/></g><text class="comp-lbl" x="156" y="86" text-anchor="middle">FLOW SENSOR</text>
  <!-- damper + actuator -->
  <rect class="box-body" x="200" y="70" width="220" height="100" rx="2"/>
  <text class="comp-lbl" x="310" y="164" text-anchor="middle">TERMINAL UNIT</text>
  <g id="vav-dmp" class="damper"><g class="blade" data-cx="300" data-cy="120"><path d="M300 86V154"/><circle cx="300" cy="120" r="3"/></g></g>
  <rect class="actuator" x="284" y="40" width="32" height="20" rx="3"/><text class="act-lbl" x="300" y="54" text-anchor="middle">M</text><path class="leader" d="M300 60V86"/>
  <!-- reheat coil -->
  <g class="coil hw" id="vav-coil"><rect class="coil-fill" x="440" y="92" width="26" height="56"/><rect class="coil-frame" x="440" y="92" width="26" height="56"/>
    <path class="coil-tubes" d="M443 100H463M443 110H463M443 120H463M443 130H463M443 140H463"/></g>
  <text class="comp-lbl" x="453" y="86" text-anchor="middle">REHEAT</text>
  <path class="pipe pipe-hws" d="M446 148V250"/><path class="pipe pipe-hwr" d="M460 148V250"/>
  <g class="valve" id="vav-valve"><path class="valve-body" d="M451 183L469 197V183L451 197Z"/><path class="valve-stem" d="M460 190H474M474 184V196"/></g>
  <text class="pipe-lbl" x="453" y="264" text-anchor="middle">HWS HWR</text>
  <!-- diffuser + room -->
  <path class="diffuser" d="M690 242H770L760 252H700Z"/>
  <path class="io-arrow" d="M712 256L700 276M748 256L760 276M730 256V280" marker-end="url(#arr2)"/>
  <rect class="room" x="520" y="242" width="460" height="218" rx="4"/>
  <text class="room-lbl" x="532" y="262">ZONE ${esc(v.meta.zone)}</text>
  <text class="room-sub" x="532" y="278">${esc(zoneLabel(v.meta.zone))}${S.equipById[zid]?.meta?.multiplier > 1 ? ` · represents ${S.equipById[zid].meta.multiplier} floors (×${S.equipById[zid].meta.multiplier})` : ''}</text>
  <!-- controller -->
  <rect class="ctrl-box" x="30" y="222" width="400" height="238" rx="4"/>
  <text class="room-lbl" x="44" y="242">VAV CONTROLLER (DDC)</text>
  <path class="signal" d="M430 330H520"/><path class="signal" d="M300 222V170"/><path class="signal" d="M156 222V148"/>
  <!-- loop bars -->
  <g id="bar-clg" class="loopbar clg"><text class="lbl" x="44" y="352">Cooling loop</text><rect class="bar-bg" x="140" y="342" width="160" height="12" rx="2"/><rect class="bar" x="140" y="342" width="0" height="12" rx="2"/></g>
  <g id="bar-htg" class="loopbar htg"><text class="lbl" x="44" y="376">Heating loop</text><rect class="bar-bg" x="140" y="366" width="160" height="12" rx="2"/><rect class="bar" x="140" y="366" width="0" height="12" rx="2"/></g>
  <!-- value boxes: terminal -->
  ${V('DA-F', 40, 6, { label: 'Airflow' })}${V('DA-F-SP', 140, 6, { label: 'Airflow set point' })}
  ${V('DMPR-CMD', 330, 6, { label: 'Damper command' })}${V('DMPR-POS', 432, 6, { label: 'Damper position' })}
  ${V('RHV-POS', 478, 172, { label: 'Reheat valve' })}
  ${V('DA-T', 560, 6, { label: 'Discharge air temp' })}${sensor(608, 120, 608, 40)}
  ${V('RH-Q', 664, 6, { label: 'Reheat (truth)' })}
  ${V('CLG-LOOP', 44, 262, { label: 'Cooling loop', w: 92 })}${V('HTG-LOOP', 140, 262, { label: 'Heating loop', w: 92 })}
  ${Z('OCC-MODE', 236, 262, { label: 'Occupancy mode', w: 92 })}
  ${has(vm['ZN-MODE']) ? V('ZN-MODE', 332, 262, { label: 'Terminal mode', w: 94 }) : ''}
  ${has(vm['CLG-REQ']) ? `${V('CLG-REQ', 44, 300, { label: 'Cooling requests', w: 92 })}${V('PRS-REQ', 140, 300, { label: 'Pressure requests', w: 92 })}${V('HW-REQ', 236, 300, { label: 'HW requests', w: 92 })}` : ''}
  ${has(vm['LOW-FLOW-ALM']) ? V('LOW-FLOW-ALM', 332, 300, { label: 'Low-flow alarm', w: 94 }) : ''}
  ${has(vm['DA-VP']) ? V('DA-VP', 40, 176, { label: 'Velocity pressure' }) : ''}
  ${has(vm['RH-BTU']) ? V('RH-BTU', 582, 172, { label: 'Reheat BTU meter' }) : ''}
  <text class="comp-lbl" x="44" y="426">sequence: ${esc(S.info.control_profile)} · served by ${esc(v.parent)}</text>
  <text class="comp-lbl" x="44" y="410">min flow ${(v.meta.vmin_frac * 100).toFixed(0)} % of ${(+v.meta.vmax_m3s).toFixed(2)} m³/s · reheat ${(v.meta.reheat_max_water_m3s * 1000).toFixed(2)} L/s max</text>
  <!-- value boxes: zone -->
  ${Z('ZN-T', 540, 292, { label: 'Zone temp', w: 100 })}${Z('HTG-SP', 648, 292, { label: 'Heating SP' })}${Z('CLG-SP', 752, 292, { label: 'Cooling SP' })}${Z('ZN-RH', 856, 292, { label: 'Zone RH', w: 110 })}
  ${Z('ZN-CO2', 540, 348, { label: 'Zone CO₂', w: 100 })}${Z('OCC-HTG-SP', 648, 348, { label: 'Occ. heating SP' })}${Z('OCC-CLG-SP', 752, 348, { label: 'Occ. cooling SP' })}${Z('ZN-OCC', 856, 348, { label: 'Occupancy sensor', w: 110 })}
  ${Z('LIGHT-KW', 540, 404, { label: 'Lighting', w: 100 })}${Z('PLUG-KW', 648, 404, { label: 'Plug loads' })}${Z('OCCUPANTS', 752, 404, { label: 'People (truth)' })}${Z('PMV', 856, 404, { label: 'PMV (truth)', w: 110 })}
  </svg>`;
}
const sensor = (x, y, x2, y2) => `<path class="leader" d="M${x} ${y}L${x2} ${y2}"/><circle class="sensor" cx="${x}" cy="${y}" r="5"/>`;

export function render(main, { arg }) {
  const vavs = S.equip.filter((e) => e.type === 'VAV');
  eid = S.equipById[arg]?.type === 'VAV' ? arg : (S.equipById['VAV-Core_mid'] ? 'VAV-Core_mid' : vavs[0].id);
  const v = S.equipById[eid];
  const vm = pmap(eid), zm = pmap(v.meta.zone_equip);
  const ahus = S.equip.filter((e) => e.type === 'AHU');
  main.innerHTML = `
  <div class="page-head"><h1>VAV terminal</h1>
    <select id="vav-sel" class="sel">${ahus.map((a) => `<optgroup label="${esc(a.id)}">${(a.meta.vav || []).map((x) => `<option value="${esc(x)}" ${x === eid ? 'selected' : ''}>${esc(x)}</option>`).join('')}</optgroup>`).join('')}</select>
    <span class="crumb"><a href="#ahu/${esc(v.parent)}">${esc(v.parent)}</a> › ${esc(eid)} › ${esc(v.meta.zone_equip)} · EnergyPlus <code>${esc(v.eplus_name)}</code></span></div>
  <div class="eq-grid">
    <section class="card schem-card">${schematic(v)}</section>
    <aside class="card status-card">
      <div class="card-h"><b>Terminal status</b></div>
      <dl class="kvlist big">
        <dt>Zone temperature</dt><dd>${pv(zm['ZN-T'])}</dd>
        <dt>Active heating SP</dt><dd>${pv(zm['HTG-SP'])}</dd>
        <dt>Active cooling SP</dt><dd>${pv(zm['CLG-SP'])}</dd>
        <dt>Airflow</dt><dd>${pv(vm['DA-F'])}</dd>
        <dt>Flow set point</dt><dd>${pv(vm['DA-F-SP'])}</dd>
        <dt>Damper cmd → pos</dt><dd>${pv(vm['DMPR-CMD'])} → ${pv(vm['DMPR-POS'])}</dd>
        <dt>Reheat valve</dt><dd>${pv(vm['RHV-POS'])}</dd>
        <dt>Zone mode</dt><dd>${pv(zm['OCC-MODE'])}</dd>
        ${kvRows([['Terminal mode', vm['ZN-MODE']]])}
        <dt class="truth-only">True occupants</dt><dd class="truth-only">${pv(zm['OCCUPANTS'])}</dd>
        <dt class="truth-only">PMV</dt><dd class="truth-only">${pv(zm['PMV'])}</dd>
      </dl>
      ${has(vm['LOW-FLOW-ALM']) ? `<div class="lamps">${lamp(vm['LOW-FLOW-ALM'], 'Low-flow alarm', 'alarm')}</div>` : ''}
      ${['DA-VP', 'RH-WF', 'RH-BTU'].some((n) => has(vm[n])) ? `<div class="card-h"><b>Measurement &amp; reheat</b></div><dl class="kvlist">${kvRows([['Velocity pressure', vm['DA-VP']], ['Discharge air temp', vm['DA-T']], ['Reheat water flow', vm['RH-WF']], ['Reheat BTU meter', vm['RH-BTU']], ['Reheat (truth)', vm['RH-Q']]])}</dl>` : ''}
      ${has(vm['CLG-REQ']) ? `<div class="card-h"><b>G36 requests</b><small>to AHU / plant reset logic</small></div>
        <div class="reqs">${[['Cooling (SAT)', 'CLG-REQ'], ['Pressure (static)', 'PRS-REQ'], ['Hot water', 'HW-REQ']].filter(([, n]) => has(vm[n])).map(([l, n]) => `<div class="req"><span class="k">${l}</span>${pbar(vm[n], 3, 'pb-req')}${pv(vm[n])}</div>`).join('')}</div>` : ''}
      <div class="form-row"><a class="btn" href="#zone/${esc(v.meta.zone_equip)}">Zone IEQ dashboard →</a></div>
      <div class="card-h"><b>Design data</b></div>
      <dl class="kvlist">
        <dt>Max airflow</dt><dd>${(+v.meta.vmax_m3s).toFixed(2)} m³/s</dd>
        <dt>Min airflow</dt><dd>${(100 * v.meta.vmin_frac).toFixed(0)} %</dd>
        <dt>Reheat water max</dt><dd>${(1000 * v.meta.reheat_max_water_m3s).toFixed(2)} L/s</dd>
        <dt>Air loop</dt><dd><code>${esc(v.meta.air_loop)}</code></dd>
      </dl>
      <p class="hint">Writable: OCC-HTG-SP / OCC-CLG-SP (operator set points) and every controller output via priority override - click a value.</p>
    </aside>
  </div>
  <section class="card chart-card"><div class="card-h"><b>Last 24 h</b><small>zone temperature with set points, discharge airflow vs. set point</small><span class="spacer"></span><span class="truth-only small">dashed = EnergyPlus truth</span></div>
    <div id="vav-chart" class="chart-box" style="height:250px"></div></section>`;
  $('#vav-sel', main).onchange = (e) => { location.hash = `#vav/${e.target.value}`; };
  chart = new TrendChart($('#vav-chart', main));
  loadChart();
  timer = setInterval(loadChart, 30000);
}

function loadChart() {
  const v = S.equipById[eid], vm = pmap(eid), zm = pmap(v.meta.zone_equip);
  const pids = [zm['ZN-T'], zm['HTG-SP'], zm['CLG-SP'], vm['DA-F'], vm['DA-F-SP']];
  const n = Math.round(86400 / (S.info.timestep_s || 300));
  loadSeries(pids, n, { truth: S.truth, pointById: S.pointById, labels: ['ZN-T', 'HTG-SP', 'CLG-SP', 'DA-F', 'DA-F-SP'] })
    .then(({ times, series }) => chart?.setData(times, series)).catch(() => {});
}
export function onTruth() { loadChart(); }

export function update() {
  const vm = pmap(eid);
  const svg = document.getElementById('vav-svg');
  if (!svg) return;
  const flow = val(vm['DA-F']) ?? 0;
  svg.classList.toggle('running', flow > 0.001);
  const pos = Math.max(0, Math.min(100, val(vm['DMPR-POS']) ?? 0));
  const b = svg.querySelector('#vav-dmp .blade');
  b?.setAttribute('transform', `rotate(${(90 * pos) / 100} 300 120)`);
  const rh = val(vm['RHV-POS']) ?? 0;
  svg.querySelector('#vav-coil .coil-fill')?.setAttribute('fill-opacity', (0.12 + 0.8 * rh / 100).toFixed(2));
  svg.querySelector('#vav-valve')?.classList.toggle('open', rh > 1);
  for (const [id, name] of [['bar-clg', 'CLG-LOOP'], ['bar-htg', 'HTG-LOOP']]) {
    const x = Math.max(0, Math.min(100, val(vm[name]) ?? 0));
    svg.querySelector(`#${id} .bar`)?.setAttribute('width', (1.6 * x).toFixed(1));
  }
}

export function destroy() { clearInterval(timer); chart?.destroy(); chart = null; }
