/* =============================================================================
 * Alarms - active alarms (from the live snapshot) and alarm history
 * (GET /api/alarms, refreshed every 5 s).
 * ========================================================================== */
import { S, $, esc, api, fmtDT } from '../core.js';

let timer = null, history = [];

const sevCls = (s) => `sev sev-${esc(s || 'medium')}`;

export function render(main) {
  main.innerHTML = `
  <div class="page-head"><h1>Alarms</h1><span class="crumb">BAS alarm server - rules evaluate <b>observed</b> values only (outer space)</span></div>
  <section class="card"><div class="card-h"><b>Active alarms</b><small id="al-n"></small></div>
    <table class="tbl"><thead><tr><th style="width:110px">Severity</th><th>Alarm</th><th>Equipment</th><th>Message</th><th>Since</th></tr></thead><tbody id="al-active"></tbody></table></section>
  <section class="card"><div class="card-h"><b>Alarm history</b><small>last 500 transitions, newest first</small><span class="spacer"></span>
    <input type="search" id="al-q" class="search sm" placeholder="Filter…"></div>
    <table class="tbl"><thead><tr><th style="width:130px">Time</th><th style="width:90px">State</th><th style="width:110px">Severity</th><th>Alarm</th><th>Equipment</th><th>Message</th></tr></thead><tbody id="al-hist"></tbody></table></section>`;
  $('#al-q', main).oninput = drawHistory;
  loadHistory();
  timer = setInterval(loadHistory, 5000);
}

async function loadHistory() {
  try { history = (await api('/api/alarms')).history || []; drawHistory(); } catch { /* keep last */ }
}

function drawHistory() {
  const t = ($('#al-q')?.value || '').toLowerCase();
  const rows = [...history].reverse().filter((h) => !t || JSON.stringify(h).toLowerCase().includes(t));
  const el = $('#al-hist');
  if (!el) return;
  el.innerHTML = rows.length ? rows.map((h) => `<tr class="${h.state === 'ALARM' ? 'row-alarm' : 'row-normal'}">
    <td>${esc(fmtDT(h.time))}</td><td><span class="state state-${esc(h.state)}">${esc(h.state)}</span></td><td><span class="${sevCls(h.severity)}">${esc(h.severity)}</span></td>
    <td><code>${esc(h.id)}</code></td><td>${equipLink(h.equip)}</td><td>${esc(h.message)}</td></tr>`).join('')
    : '<tr><td colspan="6" class="muted">No alarm transitions yet.</td></tr>';
}

function equipLink(eq) {
  const e = S.equipById[eq];
  if (!e) return esc(eq);
  const href = e.type === 'AHU' ? `#ahu/${eq}` : e.type === 'VAV' ? `#vav/${eq}` : e.type === 'Zone' ? `#zone/${eq}` : ['Chiller', 'Boiler', 'CoolingTower', 'Pump', 'PlantLoop', 'WaterHeater'].includes(e.type) ? '#plant'
    : ['WeatherStation', 'Grid', 'Meter', 'Building'].includes(e.type) ? '#weather' : `#points?equip=${eq}`;
  return `<a href="${href}">${esc(eq)}</a>`;
}

export function update() {
  const al = S.snap.alarms || [];
  const el = $('#al-active');
  if (!el) return;
  $('#al-n').textContent = `${al.length} active`;
  el.innerHTML = al.length ? al.map((a) => `<tr class="row-alarm"><td><span class="${sevCls(a.severity)}">${esc(a.severity)}</span></td>
    <td><code>${esc(a.id)}</code></td><td>${equipLink(a.equip)}</td><td>${esc(a.message)}</td><td>${esc(fmtDT(a.since))}</td></tr>`).join('')
    : '<tr><td colspan="5" class="muted">No active alarms.</td></tr>';
}

export function destroy() { clearInterval(timer); }
