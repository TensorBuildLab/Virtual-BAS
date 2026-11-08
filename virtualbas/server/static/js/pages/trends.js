/* =============================================================================
 * Trends - searchable point picker grouped by equipment, up to 8 series,
 * time window, auto refresh, truth overlay and CSV export.
 * URL: #trends?p=ZN-Core_mid/ZN-T,VAV-Core_mid/DA-F&w=24h
 * ========================================================================== */
import { S, $, $$, esc, toast, unitLabel } from '../core.js';
import { TrendChart, loadSeries, SERIES_COLORS } from '../chart.js';

const WINDOWS = { '6h': 6, '24h': 24, '3d': 72, '7d': 168, '14d': 336 };
const MAX = 8;
let sel = [];            // selected point ids (order = colour slot)
let slot = {};           // pid -> colour slot, stable while selected
let win = '24h';
let auto = true, timer = null, chart = null, last = null;

function assignSlots() {
  const used = new Set(Object.values(slot));
  for (const k of Object.keys(slot)) if (!sel.includes(k)) { used.delete(slot[k]); delete slot[k]; }
  for (const p of sel) {
    if (slot[p] !== undefined) continue;
    let i = 0;
    while (used.has(i)) i++;
    slot[p] = i; used.add(i);
  }
}

function syncHash() {
  const q = [];
  if (sel.length) q.push('p=' + sel.join(','));
  if (win !== '24h') q.push('w=' + win);
  if (S.truth) q.push('truth=1');
  history.replaceState(null, '', '#trends' + (q.length ? '?' + q.join('&') : ''));
}

function readQuery(q) {
  sel = (q.p || '').split(',').map((s) => s.trim()).filter((p) => S.pointById[p]).slice(0, MAX);
  if (q.w && WINDOWS[q.w]) win = q.w;
}

export function render(main, { q }) {
  readQuery(q);
  if (!sel.length && !q.p) sel = ['ZN-Core_mid/ZN-T', 'VAV-Core_mid/DA-F'].filter((p) => S.pointById[p]);
  slot = {};
  assignSlots();
  // picker grouped by equipment
  const groups = S.equip.map((e) => ({ e, pts: S.pointsByEquip[e.id] || [] })).filter((g) => g.pts.length);
  main.innerHTML = `
  <div class="page-head"><h1>Trends</h1><span class="crumb">historian ring buffer · ${Math.round((S.info.timestep_s || 300) / 60)}-min samples · up to 14 days</span></div>
  <div class="trend-grid">
    <aside class="card picker">
      <input type="search" id="tr-q" class="search" placeholder="Search points (id, description, Brick class)…">
      <div class="picker-list" id="tr-list">${groups.map((g) => `
        <details data-eq="${esc(g.e.id)}"><summary>${esc(g.e.id)} <small>${esc(g.e.type)}</small></summary>
        ${g.pts.map((p) => `<label class="pk${p.kind === 'truth' ? ' truth-only' : ''}" data-s="${esc((p.id + ' ' + p.description + ' ' + (p.brick || '')).toLowerCase())}">
          <input type="checkbox" value="${esc(p.id)}"><span class="pk-n">${esc(p.name)}</span><small>${esc(p.description)}</small><span class="pk-u">${esc(unitLabel(p.unit))}</span></label>`).join('')}
        </details>`).join('')}</div>
    </aside>
    <section class="card trend-main">
      <div class="toolbar">
        <div class="seg" id="tr-win">${Object.keys(WINDOWS).map((w) => `<button data-w="${w}">${w}</button>`).join('')}</div>
        <label class="chk"><input type="checkbox" id="tr-auto" ${auto ? 'checked' : ''}> Auto refresh</label>
        <span class="truth-only small">Truth overlay on: dashed lines = EnergyPlus</span>
        <span class="spacer"></span>
        <button class="btn" id="tr-clear">Clear</button>
        <button class="btn" id="tr-csv">⭳ CSV</button>
      </div>
      <div class="chips" id="tr-chips"></div>
      <div id="tr-chart" class="chart-box trend-chart"></div>
    </section>
  </div>`;

  chart = new TrendChart($('#tr-chart', main), { emptyText: 'Select up to 8 points on the left' });
  $('#tr-q', main).oninput = (e) => filter(e.target.value);
  $('#tr-list', main).addEventListener('change', (e) => {
    const cb = e.target;
    if (cb.type !== 'checkbox') return;
    if (cb.checked) {
      if (sel.length >= MAX) { cb.checked = false; toast(`At most ${MAX} series`, 'warn'); return; }
      sel.push(cb.value);
    } else sel = sel.filter((p) => p !== cb.value);
    changed();
  });
  $$('#tr-win button', main).forEach((b) => { b.onclick = () => { win = b.dataset.w; changed(); }; });
  $('#tr-auto', main).onchange = (e) => { auto = e.target.checked; };
  $('#tr-clear', main).onclick = () => { sel = []; changed(); };
  $('#tr-csv', main).onclick = downloadCsv;
  changed();
  timer = setInterval(() => { if (auto) load(); }, 10000);
}

function changed() {
  assignSlots();
  syncHash();
  $$('#tr-list input[type=checkbox]').forEach((cb) => { cb.checked = sel.includes(cb.value); });
  // open groups that contain a selected point
  $$('#tr-list details').forEach((d) => { if (sel.some((p) => S.pointById[p]?.equip === d.dataset.eq)) d.open = true; });
  $$('#tr-win button').forEach((b) => b.classList.toggle('on', b.dataset.w === win));
  $('#tr-chips').innerHTML = sel.map((p) => `<span class="chip"><span class="lg-swatch" style="--c:${SERIES_COLORS[slot[p]]}"></span>${esc(p)}<button data-x="${esc(p)}" title="Remove">✕</button></span>`).join('')
    || '<span class="muted">No points selected.</span>';
  $$('#tr-chips button').forEach((b) => { b.onclick = () => { sel = sel.filter((p) => p !== b.dataset.x); changed(); }; });
  load();
}

function filter(text) {
  const t = text.trim().toLowerCase();
  $$('#tr-list details').forEach((d) => {
    let any = false;
    d.querySelectorAll('.pk').forEach((l) => {
      const hit = !t || l.dataset.s.includes(t) || d.dataset.eq.toLowerCase().includes(t);
      l.hidden = !hit;
      any ||= hit && (!l.classList.contains('truth-only') || S.truth);
    });
    d.hidden = !any;
    if (t) d.open = any;
  });
}

async function load() {
  const n = Math.round((WINDOWS[win] * 3600) / (S.info.timestep_s || 300));
  try {
    const r = await loadSeries(sel, n, { truth: S.truth, pointById: S.pointById, colors: sel.map((p) => SERIES_COLORS[slot[p]]) });
    last = r;
    chart?.setData(r.times, r.series);
  } catch (e) { console.error(e); }
}

function downloadCsv() {
  if (!last || !last.times.length) { toast('Nothing to export', 'warn'); return; }
  const cols = last.series.filter((s) => !chart.hidden.has(s.id));
  const head = ['time', ...cols.map((s) => (s.dashed ? s.id.replace('#truth', '') + ' [truth]' : s.id) + (s.unit ? ` (${s.unit})` : ''))];
  const rows = [head.map((h) => `"${h.replace(/"/g, '""')}"`).join(',')];
  const iso = (ms) => { const d = new Date(ms); const p = (x) => String(x).padStart(2, '0'); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`; };
  last.times.forEach((t, i) => rows.push([iso(t), ...cols.map((s) => (s.values[i] ?? ''))].join(',')));
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `vbas_trend_${win}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

export function onTruth() { syncHash(); filter($('#tr-q')?.value || ''); load(); }
export function onQuery(q) { readQuery(q); changed(); }
export function destroy() { clearInterval(timer); chart?.destroy(); chart = null; }
