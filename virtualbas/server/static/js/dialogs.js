/* =============================================================================
 * dialogs.js - point detail / priority-override dialog and session dialog.
 * ========================================================================== */
import { S, $, esc, post, toast, evalPoint, fmtFull, unitLabel, devText, SOFT_KINDS, refreshBindings, pv, tierBadge, TIERS, SOURCES } from './core.js';
import { TrendChart, loadSeries } from './chart.js';

let ptChart = null;
let ptPid = null;

/** Open the point dialog: details, live value vs truth, priority array, 24 h trend. */
export function openPoint(pid) {
  const p = S.pointById[pid];
  if (!p) return;
  ptPid = pid;
  const dlg = $('#dlg-point');
  const soft = SOFT_KINDS.has(p.kind);
  const tags = (p.tags || []).map((t) => `<span class="tag">${esc(t)}</span>`).join('');
  dlg.innerHTML = `
    <form method="dialog" class="dlg-head"><div><div class="dlg-title">${esc(pid)}</div><div class="dlg-sub">${esc(p.description)}</div></div><button class="x" aria-label="Close">✕</button></form>
    <div class="dlg-body">
      <div class="pt-grid">
        <div class="pt-live">
          <div class="pt-big">${pv(pid, { cls: 'pv-big' })}</div>
          <dl class="kvlist">
            <dt>Kind</dt><dd><span class="kind kind-${esc(p.kind)}">${esc(p.kind)}</span>${p.kind === 'truth' ? ' <small class="truth-ink">ground truth only, not visible to the BAS</small>' : ''}</dd>
            <dt>Tier</dt><dd>${tierBadge(p, true)} <small>${esc(TIERS[p.tier]?.[2] || '')}</small></dd>
            <dt>Source</dt><dd>${esc(SOURCES[p.source] || p.source || '-')}</dd>
            <dt>Unit</dt><dd>${esc(unitLabel(p.unit) || '-')}</dd>
            <dt>Equipment</dt><dd>${esc(p.equip)} <small>(${esc(p.equip_type)})</small></dd>
            <dt>Brick class</dt><dd>${p.brick ? `<code>brick:${esc(p.brick)}</code>` : '-'}</dd>
            <dt>Sensor class</dt><dd>${esc(p.sensor_class || '-')}</dd>
            <dt>Haystack tags</dt><dd>${tags || '-'}</dd>
            <dt>Truth</dt><dd id="pt-truth">-</dd>
          </dl>
        </div>
        ${soft ? `
        <div class="pt-write">
          <h4>Priority array <small>(BACnet-style, 1 = highest)</small></h4>
          <div class="prio" id="pt-prio"></div>
          <div class="form-row">
            <label>Value<input type="number" step="any" id="pt-val" placeholder="${esc(unitLabel(p.unit))}"></label>
            <label>Priority<select id="pt-pri">${Array.from({ length: 16 }, (_, i) => `<option ${i + 1 === 8 ? 'selected' : ''}>${i + 1}</option>`).join('')}</select></label>
            <label>Duration (min)<input type="number" min="0" id="pt-dur" placeholder="∞"></label>
          </div>
          <div class="form-row">
            <button class="btn btn-primary" id="pt-write">Write override</button>
            <button class="btn" id="pt-release">Release priority</button>
          </div>
          <p class="hint">Operator writes go to <code>POST /api/write</code>. ${p.writable ? 'This point is an operator-adjustable set point.' : 'This is a controller-internal value; an override replaces the control-sequence output.'}</p>
        </div>` : `<div class="pt-write"><h4>Measured point</h4><p class="hint">Field sensors and meters are read-only. To corrupt this measurement, use the <a href="#faults">fault injection console</a> (e.g. <code>sensor_bias</code>, <code>sensor_drift</code>).</p></div>`}
      </div>
      <div class="pt-trend"><div id="pt-chart" class="chart-box" style="height:220px"></div></div>
    </div>`;
  dlg.querySelector('.x').onclick = () => closePoint();
  dlg.addEventListener('close', () => { ptPid = null; ptChart?.destroy(); ptChart = null; }, { once: true });
  if (soft) {
    $('#pt-write', dlg).onclick = async () => {
      const v = parseFloat($('#pt-val', dlg).value);
      if (Number.isNaN(v)) { toast('Enter a numeric value', 'warn'); return; }
      const dur = parseFloat($('#pt-dur', dlg).value);
      try {
        await post('/api/write', { point: pid, value: v, priority: +$('#pt-pri', dlg).value, duration_s: dur > 0 ? dur * 60 : null, source: 'operator' });
        toast(`Wrote ${v} to ${pid} @ priority ${$('#pt-pri', dlg).value}`, 'ok');
      } catch (e) { toast(e.message, 'err'); }
    };
    $('#pt-release', dlg).onclick = async () => {
      try {
        await post('/api/write', { point: pid, value: null, priority: +$('#pt-pri', dlg).value, source: 'operator' });
        toast(`Released ${pid} @ priority ${$('#pt-pri', dlg).value}`, 'ok');
      } catch (e) { toast(e.message, 'err'); }
    };
  }
  if (!dlg.open) dlg.showModal();
  updatePointDialog();
  ptChart = new TrendChart($('#pt-chart', dlg));
  const n = Math.round(86400 / (S.info?.timestep_s || 300));
  loadSeries([pid], n, { truth: S.truth, pointById: S.pointById, labels: [p.name] })
    .then(({ times, series }) => ptChart?.setData(times, series)).catch(() => {});
}

export function closePoint() { const d = $('#dlg-point'); if (d.open) d.close(); }

/** Called on every snapshot while the dialog is open. */
export function updatePointDialog() {
  if (!ptPid) return;
  const dlg = $('#dlg-point');
  refreshBindings(dlg);
  const r = evalPoint(ptPid);
  const tEl = $('#pt-truth', dlg);
  if (tEl) {
    if (!r.hasTruth) tEl.textContent = 'software point - no physical counterpart';
    else if (!S.truth) tEl.innerHTML = '<small>enable “Ground truth” in the header</small>';
    else tEl.innerHTML = `<span class="truth-ink">${esc(fmtFull(ptPid, r.truth))}</span> ${r.dev !== null ? `<span class="dbadge lvl-${r.level}">${esc(devText(r))}</span>` : ''}`;
  }
  const prio = $('#pt-prio', dlg);
  if (prio) {
    const slots = S.snap?.overrides?.[ptPid] || {};
    let html = '';
    for (let i = 1; i <= 16; i++) {
      const v = slots[i] ?? slots[String(i)];
      const lbl = i === 16 ? '16' : String(i);
      html += `<div class="prio-slot${v !== undefined ? ' on' : ''}" title="Priority ${i}${i === 8 ? ' (manual operator)' : ''}${i === 16 ? ' (default)' : ''}"><span>${lbl}</span><b>${v !== undefined ? esc(String(+(+v).toFixed(3))) : '-'}</b></div>`;
    }
    html += `<div class="prio-slot prio-def"><span>Ctrl</span><b>${esc(fmtFull(ptPid, r.v))}</b></div>`;
    prio.innerHTML = html;
  }
}

// ---------------------------------------------------------------- session dialog
/** Dialog to restart the simulation with a new scenario (POST /api/session). */
export function openSession() {
  const dlg = $('#dlg-session');
  const i = S.info || {};
  const d0 = (i.start || '2023-07-10').slice(0, 10);
  const d1 = (i.end || '2023-07-24').slice(0, 10);
  dlg.innerHTML = `
    <form method="dialog" class="dlg-head"><div><div class="dlg-title">New simulation session</div><div class="dlg-sub">Restart EnergyPlus with a new scenario. The current run, trends and injections are discarded.</div></div><button class="x">✕</button></form>
    <div class="dlg-body">
      <div class="form-grid">
        <label>Start date<input type="date" id="ss-start" value="${d0}"></label>
        <label>End date<input type="date" id="ss-end" value="${d1}"></label>
        <label>Control profile<select id="ss-prof"><option value="baseline">baseline (typical existing building)</option><option value="g36">g36 (ASHRAE Guideline 36)</option></select></label>
        <label>Speed<select id="ss-speed">${['1x', '10x', '60x', '360x', 'max'].map((s) => `<option ${s === '60x' ? 'selected' : ''}>${s}</option>`).join('')}</select></label>
        <label>Realism <span id="ss-real-v">${i.realism ?? 1}</span><input type="range" min="0" max="1" step="0.05" id="ss-real" value="${i.realism ?? 1}"></label>
        <label>Random faults / week<input type="number" min="0" step="0.5" id="ss-rate" value="0"></label>
        <label class="chk"><input type="checkbox" id="ss-occ" checked> Stochastic occupancy</label>
      </div>
      <p class="hint">Realism 0 = ideal sensors (outer space equals inner space); 1 = field-typical noise, drift, quantisation, delays and data loss.</p>
      <div class="form-row right"><button class="btn" id="ss-cancel">Cancel</button><button class="btn btn-primary" id="ss-go">Restart simulation</button></div>
    </div>`;
  $('#ss-prof', dlg).value = i.control_profile || 'baseline';
  $('#ss-real', dlg).oninput = (e) => { $('#ss-real-v', dlg).textContent = e.target.value; };
  dlg.querySelector('.x').onclick = () => dlg.close();
  $('#ss-cancel', dlg).onclick = () => dlg.close();
  $('#ss-go', dlg).onclick = async () => {
    const body = {
      scenario: {
        start: $('#ss-start', dlg).value, end: $('#ss-end', dlg).value,
        realism: +$('#ss-real', dlg).value,
        control: { profile: $('#ss-prof', dlg).value },
        occupancy: { stochastic: $('#ss-occ', dlg).checked },
        random_faults: { rate_per_week: +$('#ss-rate', dlg).value || 0 },
      },
      speed: $('#ss-speed', dlg).value,
    };
    $('#ss-go', dlg).disabled = true;
    $('#ss-go', dlg).textContent = 'Starting EnergyPlus…';
    try {
      await post('/api/session', body);
      toast('New session started', 'ok');
      dlg.close();
      setTimeout(() => location.reload(), 600);
    } catch (e) {
      toast(e.message, 'err');
      $('#ss-go', dlg).disabled = false;
      $('#ss-go', dlg).textContent = 'Restart simulation';
    }
  };
  dlg.showModal();
}
