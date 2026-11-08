/* =============================================================================
 * Points - full BAS point list with filters, live present value, stale flag,
 * ground truth and semantic metadata (Haystack tags, Brick class).
 * Click a row to open the point dialog (trend + priority override).
 * Availability tier filter: standard (typical BAS today) / advanced /
 * next-gen (AI & IEQ instrumentation) / truth (EnergyPlus only).
 * URL: #points?equip=AHU-1&kind=sensor&tier=next_gen&q=temp
 * ========================================================================== */
import { S, $, $$, esc, unitLabel, SOFT_KINDS, TIERS, SOURCES, tierBadge } from '../core.js';

const KINDS = ['sensor', 'meter', 'setpoint', 'command', 'virtual', 'status', 'truth'];
let f = { equip: '', kind: '', tier: '', q: '' };
const readQ = (q) => ({ equip: q.equip || '', kind: q.kind || '', tier: q.tier || '', q: q.q || '' });

export function render(main, { q }) {
  f = readQ(q);
  const nTier = {};
  for (const p of S.points) nTier[p.tier] = (nTier[p.tier] || 0) + 1;
  const exposed = new Set(S.info.point_tiers || Object.keys(TIERS));
  main.innerHTML = `
  <div class="page-head"><h1>Points</h1><span class="crumb">${S.points.length} points · BACnet-style object list with Project Haystack tags and Brick classes</span></div>
  <div class="tier-sum">${Object.entries(TIERS).map(([k, t]) => `<button class="tier-card${k === 'truth' ? ' truth-only' : ''}${f.tier === k ? ' on' : ''}${k !== 'truth' && !exposed.has(k) ? ' off' : ''}" data-tier="${k}">
      ${tierBadge({ tier: k })}<b>${nTier[k] || 0}</b><span>${esc(t[1])}</span><small>${esc(t[2])}${k !== 'truth' && !exposed.has(k) ? ' · not exposed in this session' : ''}</small></button>`).join('')}</div>
  <section class="card">
    <div class="toolbar">
      <select id="pt-eq" class="sel"><option value="">All equipment</option>${S.equip.map((e) => `<option value="${esc(e.id)}">${esc(e.id)} (${esc(e.type)})</option>`).join('')}</select>
      <select id="pt-kind" class="sel"><option value="">All kinds</option>${KINDS.map((k) => `<option value="${k}" class="${k === 'truth' ? 'truth-only' : ''}">${k}</option>`).join('')}</select>
      <div class="seg" id="pt-tier"><button data-t="">All</button>${Object.entries(TIERS).map(([k, t]) => `<button data-t="${k}" class="${k === 'truth' ? 'truth-only' : ''}">${esc(t[1])}</button>`).join('')}</div>
      <input type="search" id="pt-q" class="search" placeholder="Search id, description, tag, Brick class…" value="${esc(f.q)}">
      <span class="spacer"></span><span id="pt-n" class="muted"></span>
    </div>
    <div class="tbl-wrap"><table class="tbl pt-tbl"><thead><tr>
      <th>Point</th><th>Description</th><th>Kind</th><th>Source</th><th class="num">Present value</th><th>Status</th><th class="num truth-col">Truth (E+)</th><th>Brick class</th><th>Tags</th></tr></thead>
      <tbody>${S.points.map((p) => `<tr class="pt-row${p.kind === 'truth' ? ' truth-only-row' : ''}${SOFT_KINDS.has(p.kind) ? ' soft' : ''}" data-pid="${esc(p.id)}"
          data-eq="${esc(p.equip)}" data-kind="${esc(p.kind)}" data-tier="${esc(p.tier || '')}" data-s="${esc((p.id + ' ' + p.description + ' ' + (p.tags || []).join(' ') + ' ' + (p.brick || '') + ' ' + p.sensor_class + ' ' + (p.tier || '') + ' ' + (p.source || '')).toLowerCase())}">
        <td>${tierBadge(p)}<code>${esc(p.id)}</code>${SOFT_KINDS.has(p.kind) ? ' <span class="wr" title="Software point - priority write possible">✎</span>' : ''}</td>
        <td>${esc(p.description)}</td>
        <td><span class="kind kind-${esc(p.kind)}">${esc(p.kind)}</span></td>
        <td><span class="srcl srcl-${esc(p.source || '')}">${esc(SOURCES[p.source] || p.source || '-')}</span></td>
        <td class="num"><span class="v">---</span> <span class="u">${esc(unitLabel(p.unit))}</span></td>
        <td class="stcell"><span class="dbadge"></span><span class="ovr-flag">OVR</span></td>
        <td class="num truth-col"><span class="tv"></span></td>
        <td><small>${esc(p.brick || '')}</small></td>
        <td><small class="tags">${esc((p.tags || []).join(' '))}</small></td></tr>`).join('')}</tbody></table></div>
  </section>`;
  $('#pt-eq', main).value = f.equip;
  $('#pt-kind', main).value = f.kind;
  $('#pt-eq', main).onchange = (e) => { f.equip = e.target.value; apply(); };
  $('#pt-kind', main).onchange = (e) => { f.kind = e.target.value; apply(); };
  $('#pt-q', main).oninput = (e) => { f.q = e.target.value; apply(); };
  for (const b of $$('#pt-tier button', main)) b.onclick = () => { f.tier = b.dataset.t; apply(); };
  for (const b of $$('.tier-card', main)) b.onclick = () => { f.tier = f.tier === b.dataset.tier ? '' : b.dataset.tier; apply(); };
  apply();
}

function apply() {
  const t = f.q.trim().toLowerCase();
  let n = 0;
  for (const r of $$('.pt-row')) {
    const show = (!f.equip || r.dataset.eq === f.equip) && (!f.kind || r.dataset.kind === f.kind) && (!f.tier || r.dataset.tier === f.tier) && (!t || r.dataset.s.includes(t))
      && (r.dataset.kind !== 'truth' || S.truth);
    r.hidden = !show;
    if (show) n++;
  }
  $('#pt-n').textContent = `${n} shown`;
  $$('#pt-tier button').forEach((b) => b.classList.toggle('on', b.dataset.t === f.tier));
  $$('.tier-card').forEach((b) => b.classList.toggle('on', b.dataset.tier === f.tier));
}

export function onTruth() { apply(); }
export function onQuery(q) { f = readQ(q); $('#pt-eq').value = f.equip; $('#pt-kind').value = f.kind; $('#pt-q').value = f.q; apply(); }
