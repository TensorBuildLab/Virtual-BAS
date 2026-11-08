/* =============================================================================
 * Overview - building section (floor groups x zones), AHU and plant summary,
 * KPIs, building demand trend and the list of active injections.
 * ========================================================================== */
import { S, $, $$, esc, pv, pmap, val, has, zoneLabel, fmtDT } from '../core.js';
import { TrendChart, loadSeries } from '../chart.js';
import { lamp, classify } from '../widgets.js';

/** Floor groups of the DOE large office (top to bottom). */
const FLOORS = [
  { key: 'top', title: 'Floor 12', sub: 'top floor', suffix: 'top', core: 'Core_top' },
  { key: 'mid', title: 'Floors 2–11', sub: 'mid floors, modelled once ×10', suffix: 'mid', core: 'Core_mid', mult: true },
  { key: 'bot', title: 'Floor 1', sub: 'ground floor', suffix: 'bot', core: 'Core_bottom' },
  { key: 'base', title: 'Basement', sub: 'below grade', zones: ['Basement'] },
];

let chart = null, chartTimer = null;

/** Compact site strip: outdoor conditions, outdoor AQ, grid price / carbon, DR status, occupancy, demand. */
function siteStrip() {
  const it = (href, label, body, cls = '') => `<a class="ovs ${cls}" href="${href}"><span class="k">${label}</span><span class="ovs-v">${body}</span></a>`;
  const items = [
    has('WX/OA-T') ? it('#weather', 'Outdoor', `${pv('WX/OA-T')} ${has('WX/OA-RH') ? pv('WX/OA-RH') : ''}`) : '',
    has('WX/OA-PM25') ? it('#weather', 'Outdoor PM2.5', `${pv('WX/OA-PM25')} <span class="lvchip lv-na" id="ovs-aqi">-</span>`) : '',
    has('GRID/PRICE') ? it('#weather', 'Grid price', `${pv('GRID/PRICE')} <span class="tou" id="ovs-tou">${pv('GRID/TOU-PERIOD')}</span>`) : '',
    has('GRID/CO2-INT') ? it('#weather', 'Grid carbon', pv('GRID/CO2-INT')) : '',
    has('GRID/DR-EVENT') ? it('#weather', 'Demand response', `${lamp('GRID/DR-EVENT', '', 'alarm')} <span id="ovs-shed"></span>`, 'ovs-dr') : '',
    has('BLDG/OCC-COUNT') ? it('#zone', 'Occupancy', `${pv('BLDG/OCC-COUNT')}`) : '',
    has('MTR/BLDG-DMD-15') ? it('#weather', '15-min demand', pv('MTR/BLDG-DMD-15')) : '',
  ].filter(Boolean);
  return items.length ? `<div class="ov-strip">${items.join('')}</div>` : '';
}

function zonesOf(f) {
  if (f.zones) return f.zones;
  return [1, 2, 3, 4].map((i) => `Perimeter_${f.suffix}_ZN_${i}`).concat([f.core]);
}

function zoneTile(zone) {
  const zid = `ZN-${zone}`, vid = `VAV-${zone}`;
  const z = pmap(zid), v = pmap(vid);
  const mult = S.equipById[zid]?.meta?.multiplier ?? 1;
  return `<a class="ztile" href="#vav/${esc(vid)}" data-zone="${esc(zid)}">
    <div class="zt-head"><span class="zt-name">${esc(zoneLabel(zone))}</span>${mult > 1 ? `<span class="mult">×${mult}</span>` : ''}<span class="zt-flag"></span></div>
    <div class="zt-temp">${pv(z['ZN-T'])}</div>
    <div class="zt-sp">SP ${pv(z['HTG-SP'], { unit: false })} – ${pv(z['CLG-SP'])}</div>
    <div class="zt-grid">
      <span class="k">CO₂</span>${pv(z['ZN-CO2'])}
      <span class="k">Flow</span>${pv(v['DA-F'])}
    </div>
    <div class="zt-foot">${pv(z['ZN-OCC'], { cls: 'occ' })}<span class="truth-only ppl">${pv(z['OCCUPANTS'], { unit: false })} ppl</span></div>
  </a>`;
}

function ahuCard(a) {
  const m = pmap(a.id);
  const zones = a.meta.zones || [];
  return `<a class="card ahu-card" href="#ahu/${esc(a.id)}">
    <div class="card-h"><b>${esc(a.id)}</b><small>${zones.length} zone${zones.length > 1 ? 's' : ''}</small><span class="spacer"></span>${pv(m['OCC-MODE'], { cls: 'mode' })}</div>
    <div class="mini-grid">
      <span class="k">Supply air</span><span>${pv(m['SA-T'])}</span>
      <span class="k">SAT set point</span><span>${pv(m['SA-T-SP'])}</span>
      <span class="k">Supply fan</span><span>${pv(m['SF-SPD'])} ${pv(m['SF-STS'], { cls: 'sts' })}</span>
      <span class="k">OA damper</span><span>${pv(m['OAD-POS'])}</span>
      <span class="k">Duct static</span><span>${pv(m['DSP'])}</span>
    </div>
  </a>`;
}

const KPIS = [
  ['elec_kwh', 'Electricity', 'kWh', 0],
  ['hvac_elec_kwh', 'HVAC electricity', 'kWh', 0],
  ['gas_kwh', 'Natural gas', 'kWh', 0],
  ['unmet_occ_hours', 'Unmet occupied hours', 'h', 1],
  ['comfort_kh', 'Thermal discomfort', 'K·h', 1],
  ['co2_over_1000_h', 'CO₂ > 1000 ppm', 'zone·h', 1],
];

export function render(main) {
  const ahus = S.equip.filter((e) => e.type === 'AHU');
  const ahuOfZone = {};
  for (const a of ahus) for (const z of a.meta.zones || []) ahuOfZone[z] = a.id;
  const pl = (eid) => pmap(eid);
  const chw = pl('CHW-SYS'), hw = pl('HW-SYS'), ch1 = pl('CH-1'), ch2 = pl('CH-2'), blr = pl('BLR-1'), ct = pl('CT-1'), cw = pl('CW-SYS');

  main.innerHTML = `
  <div class="page-head"><h1>Building overview</h1><span class="crumb">${esc(S.info.building)}</span></div>
  ${siteStrip()}
  <div class="ov-grid">
    <section class="card section-card">
      <div class="card-h"><b>Building section</b><small>zone air temperature vs. heating / cooling set points</small><span class="spacer"></span>
        <span class="legend-chips"><span class="lc lc-cold">below heating SP</span><span class="lc lc-ok">in band</span><span class="lc lc-hot">above cooling SP</span></span></div>
      <div class="bldg">
        <div class="roof"></div>
        ${FLOORS.map((f) => {
          const zs = zonesOf(f);
          const ahu = ahuOfZone[zs[0]];
          return `${f.key === 'base' ? '<div class="ground" title="grade"></div>' : ''}<div class="floor floor-${f.key}">
            <div class="floor-lbl"><b>${f.title}</b><small>${f.sub}</small>${ahu ? `<a href="#ahu/${ahu}" class="ahu-link">${ahu}</a>` : ''}</div>
            <div class="floor-zones">${zs.map(zoneTile).join('')}${f.key === 'base' ? `<a class="ztile ztile-plant" href="#plant"><div class="zt-head"><span class="zt-name">Mechanical room</span></div><div class="plant-ico">⛁</div><div class="zt-sp">Chillers · boiler · pumps →</div></a>
              <div class="ov-mini"><div class="card-h"><b>Electric demand</b><small>last 24 h, meters</small></div><div id="ov-chart" class="chart-box" style="height:118px"></div></div>` : ''}</div>
          </div>`;
        }).join('')}
      </div>
    </section>

    <div class="ov-side">
      <section class="ahu-cards">${ahus.map(ahuCard).join('')}</section>

      <a class="card plant-card" href="#plant">
        <div class="card-h"><b>Central plant</b><span class="spacer"></span><small>open plant graphic →</small></div>
        <div class="plant-sum">
          <div><span class="k">CHW supply</span>${pv(chw['CHW-ST'])}<small>SP ${pv(chw['CHW-ST-SP'])}</small></div>
          <div><span class="k">HW supply</span>${pv(hw['HW-ST'])}<small>SP ${pv(hw['HW-ST-SP'])}</small></div>
          <div><span class="k">CW supply</span>${pv(cw['CW-ST'])}<small>SP ${pv(cw['CW-ST-SP'])}</small></div>
          <div><span class="k">CH-1</span>${pv(ch1['KW'])}<small>${pv(ch1['STS'])}</small></div>
          <div><span class="k">CH-2</span>${pv(ch2['KW'])}<small>${pv(ch2['STS'])}</small></div>
          <div><span class="k">Boiler gas</span>${pv(blr['GAS-KW'])}<small>${pv(blr['STS'])}</small></div>
          <div><span class="k">Tower fan</span>${pv(ct['FAN-KW'])}<small>${pv(ct['FAN-STS'])}</small></div>
          <div class="truth-only"><span class="k">CH-1 COP</span>${pv('CH-1/COP')}<small>PLR ${pv('CH-1/PLR')}</small></div>
        </div>
      </a>

      <section class="card">
        <div class="card-h"><b>Key performance indicators</b><small>since simulation start</small></div>
        <div class="kpis">${KPIS.map(([k, l, u]) => `<div class="kpi"><span class="k">${l}</span><b id="kpi-${k}">-</b><small>${u}</small></div>`).join('')}</div>
      </section>

      <section class="card inj-card">
        <div class="card-h"><b>Active faults &amp; events</b><span class="spacer"></span><a href="#faults" class="small-link">injection console →</a></div>
        <div id="ov-inj" class="inj-list"></div>
      </section>
    </div>

  </div>`;

  chart = new TrendChart($('#ov-chart', main));
  loadChart();
  chartTimer = setInterval(loadChart, 30000);
}

function loadChart() {
  const pids = ['MTR/BLDG-ELEC-KW', 'MTR/CLG-ELEC-KW'];
  const n = Math.round(86400 / (S.info.timestep_s || 300));
  loadSeries(pids, n, { truth: S.truth, pointById: S.pointById, labels: ['Building', 'Chillers'] })
    .then(({ times, series }) => chart?.setData(times, series)).catch(() => {});
}

export function onTruth() { loadChart(); }

export function update() {
  const s = S.snap;
  // site strip
  const aqi = document.getElementById('ovs-aqi');
  if (aqi) { const c = classify('aqi25', val('WX/OA-PM25')); aqi.textContent = c.label; aqi.className = 'lvchip lv-' + c.level; }
  const tou = document.getElementById('ovs-tou');
  if (tou) tou.dataset.p = String(Math.round(val('GRID/TOU-PERIOD') ?? -1));
  const dr = document.querySelector('.ovs-dr');
  if (dr) {
    const on = (val('GRID/DR-EVENT') ?? 0) >= 0.5;
    dr.classList.toggle('on', on);
    const shed = val('GRID/DR-SHED-KW');
    document.getElementById('ovs-shed').textContent = on && shed !== null ? `shed ${Math.round(shed)} kW` : '';
  }
  // zone tile colour: compare observed zone temperature to active set points
  for (const el of $$('.ztile[data-zone]')) {
    const z = el.dataset.zone;
    const t = val(`${z}/ZN-T`), h = val(`${z}/HTG-SP`), c = val(`${z}/CLG-SP`);
    let st = 'na', flag = 'NO DATA';
    if (t !== null && h !== null && c !== null) {
      if (t < h - 0.5) { st = 'cold'; flag = 'COLD'; } else if (t > c + 0.5) { st = 'hot'; flag = 'HOT'; } else { st = 'ok'; flag = ''; }
    }
    if (el.dataset.st !== st) {
      el.classList.remove('zt-cold', 'zt-ok', 'zt-hot', 'zt-na');
      el.classList.add('zt-' + st);
      el.dataset.st = st;
      el.querySelector('.zt-flag').textContent = flag;
    }
  }
  // KPIs
  for (const [k, , , d] of KPIS) {
    const el = document.getElementById('kpi-' + k);
    const v = s.kpi?.[k];
    if (el) el.textContent = v === undefined || v === null ? '-' : Number(v).toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: d });
  }
  // active injections
  const list = (s.injections || []).filter((i) => i.severity > 0 || (!i.cleared && (!i.end || i.end > s.time) && i.start > s.time));
  const box = $('#ov-inj');
  if (box) {
    box.innerHTML = list.length ? list.slice(0, 8).map((i) => `<div class="inj-row">
        <span class="cat cat-${esc(i.category)}">${esc(i.category)}</span>
        <span class="inj-type">${esc(i.type)}</span>
        <span class="inj-tgt">${esc(i.target)}</span>
        <span class="src src-${esc(i.source)}">${esc(i.source)}</span>
        <span class="sevbar" title="severity ${i.severity}"><span style="width:${Math.round(100 * i.severity)}%"></span></span>
        <small>${i.severity > 0 ? 'since ' + fmtDT(i.start) : 'starts ' + fmtDT(i.start)}</small>
      </div>`).join('') + (list.length > 8 ? `<div class="muted">+${list.length - 8} more…</div>` : '')
      : '<div class="muted">No active injections - the building is operating “as is” (sensor realism only).</div>';
  }
}

export function destroy() {
  clearInterval(chartTimer);
  chart?.destroy();
  chart = null;
}
