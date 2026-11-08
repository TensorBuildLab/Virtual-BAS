/* =============================================================================
 * Faults & events - the injection console. Humans (here) and AI agents
 * (POST /api/injections) add abnormalities to the outer space: sensor faults,
 * actuator/equipment/control/network faults and operational events.
 * ========================================================================== */
import { S, $, $$, esc, post, del, toast, fmtDT, unitLabel } from '../core.js';

const LAYERS = [
  ['sensor', 'Sensor', 'Measurement layer - corrupts what the BAS sees; physics unaffected'],
  ['actuator', 'Actuator', 'Dampers, valves and fans not doing what they are told'],
  ['equipment', 'Equipment', 'Degradation of chillers, boilers, towers, filters and fans (EnergyPlus fault models)'],
  ['control', 'Control', 'Schedules, sequences and controller software'],
  ['network', 'Network', 'BACnet communication and historian'],
  ['occupancy', 'Occupancy', 'People - surges, meetings, holidays'],
  ['gains', 'Internal gains', 'Plug loads, lighting, open windows'],
  ['weather', 'Weather', 'Heat waves, cold snaps, ambient CO₂'],
];

let selType = null;

export function render(main, { q = {} } = {}) {
  const byLayer = {};
  for (const f of S.catalog) (byLayer[f.layer] ||= []).push(f);
  const host = location.origin;
  main.innerHTML = `
  <div class="page-head"><h1>Faults &amp; events</h1><span class="crumb">injection console - ground-truth labelled abnormalities in the outer space</span></div>
  <div class="api-hint">
    <div><b>Humans and AI agents use the same interface.</b> Pick a fault or event below, or call the REST API directly. Every injection is logged as a
    ground-truth label (type, target, onset, severity) in the historian - ideal for benchmarking FDD and AI operators.</div>
    <pre>curl -X POST ${esc(host)}/api/injections -H "Content-Type: application/json" \\
  -d '{"type":"sensor_drift","target":"ZN-Core_mid/ZN-T","start":"now","duration":"2d","params":{"rate_per_day":1.0},"source":"ai"}'</pre>
    <a href="/docs#/default/inject_api_injections_post" target="_blank">OpenAPI docs →</a>
  </div>
  <section class="card">
    <div class="card-h"><b>Injections</b><small>all faults and events in this session (ground-truth labels)</small><span class="spacer"></span>
      <div class="chaos"><span class="k">Random chaos generator</span><input type="number" id="chaos-rate" min="0" step="0.5" value="2" class="num"> <small>faults / week</small>
      <button class="btn" id="chaos-go">Apply</button><button class="btn btn-ghost" id="chaos-off" title="Rate 0 disables the generator">Off</button></div></div>
    <div class="tbl-wrap inj-wrap"><table class="tbl inj-tbl"><thead><tr><th>ID</th><th>Type</th><th>Target</th><th>Category</th><th>Layer</th><th>Source</th><th>Start</th><th>End</th><th>Status</th><th style="width:120px">Severity</th><th></th></tr></thead>
      <tbody id="inj-rows"></tbody></table></div>
  </section>
  <div class="fault-grid">
    <div class="catalog">${LAYERS.filter(([k]) => byLayer[k]).map(([k, title, sub]) => `
      <section class="layer"><div class="layer-h"><span class="lay-badge lay-${k}">${esc(title)}</span><small>${esc(sub)}</small></div>
        <div class="fcards">${byLayer[k].map((f) => `<button class="fcard" data-type="${esc(f.name)}">
          <div class="fc-h"><b>${esc(f.name)}</b><span class="cat cat-${esc(f.category)}">${esc(f.category)}</span></div>
          <div class="fc-d">${esc(f.description)}</div>
          <code class="eq">${esc(f.equation)}</code>
          <div class="fc-t">target: ${esc(f.target)}</div></button>`).join('')}</div></section>`).join('')}
    </div>
    <aside class="card inj-form" id="inj-form"><div class="muted pad">Select a fault or event from the catalogue to configure an injection.</div></aside>
  </div>`;

  $$('.fcard', main).forEach((b) => { b.onclick = () => selectType(b.dataset.type); });
  $('#chaos-go', main).onclick = () => setChaos(+$('#chaos-rate').value || 0);
  $('#chaos-off', main).onclick = () => setChaos(0);
  $('#inj-rows', main).addEventListener('click', async (e) => {
    const b = e.target.closest('button[data-clear]');
    if (!b) return;
    try { await del(`/api/injections/${encodeURIComponent(b.dataset.clear)}`); toast(`Cleared ${b.dataset.clear}`, 'ok'); } catch (err) { toast(err.message, 'err'); }
  });
  // ?type=<name> preselects a catalogue entry (handy for links and screenshots)
  if (q.type && S.catalog.some((x) => x.name === q.type)) selType = q.type;
  if (selType) selectType(selType);
  if (q.target && $('#if-target')) $('#if-target').value = q.target;
}

async function setChaos(rate) {
  try {
    await post('/api/random', { rate_per_week: rate });
    toast(rate > 0 ? `Random fault generator: ${rate} / week` : 'Random fault generator off', 'ok');
  } catch (e) { toast(e.message, 'err'); }
}

/** Candidate targets for a catalogue target specification. */
function targets(spec) {
  if (spec === 'point:sensor') {
    const out = [];
    for (const e of S.equip) {
      const pts = (S.pointsByEquip[e.id] || []).filter((p) => p.kind === 'sensor' || p.kind === 'meter');
      if (pts.length) out.push({ group: e.id, items: pts.map((p) => ({ v: p.id, t: `${p.id} - ${p.description}` })) });
    }
    return out;
  }
  if (spec.startsWith('equip:')) {
    const types = spec.slice(6).split('|');
    const list = S.equip.filter((e) => types.includes('*') || types.includes(e.type));
    const groups = {};
    for (const e of list) (groups[e.type] ||= []).push({ v: e.id, t: `${e.id} - ${e.description}` });
    return Object.entries(groups).map(([group, items]) => ({ group, items }));
  }
  const zones = S.equip.filter((e) => e.type === 'Zone').map((e) => ({ v: e.id, t: `${e.id}${e.meta.multiplier > 1 ? ' (×' + e.meta.multiplier + ')' : ''}` }));
  if (spec === 'zone') return [{ group: 'Zones', items: zones }];
  if (spec === 'zone|building') return [{ group: 'Whole building', items: [{ v: 'building', t: 'building (all zones)' }] }, { group: 'Zones', items: zones }];
  return [{ group: 'Whole building', items: [{ v: 'building', t: 'building' }] }];
}

function selectType(name) {
  const f = S.catalog.find((x) => x.name === name);
  if (!f) return;
  selType = name;
  $$('.fcard').forEach((b) => b.classList.toggle('on', b.dataset.type === name));
  const tg = targets(f.target);
  const params = Object.entries(f.params || {});
  const box = $('#inj-form');
  box.innerHTML = `
    <div class="card-h"><b>${esc(f.name)}</b><span class="cat cat-${esc(f.category)}">${esc(f.category)}</span><span class="lay-badge lay-${esc(f.layer)}">${esc(f.layer)}</span></div>
    <p class="fc-d">${esc(f.description)}</p>
    <code class="eq block">${esc(f.equation)}</code>
    <div class="form-grid one">
      <label>Target <small>${esc(f.target)}</small>
        ${tg.reduce((n, g) => n + g.items.length, 0) > 12 ? '<input type="search" id="if-tq" class="search sm" placeholder="filter targets…">' : ''}
        <select id="if-target" size="${Math.min(8, Math.max(1, tg.reduce((n, g) => n + g.items.length, 0) > 12 ? 8 : 1))}">${tg.map((g) => `<optgroup label="${esc(g.group)}">${g.items.map((i) => `<option value="${esc(i.v)}">${esc(i.t)}</option>`).join('')}</optgroup>`).join('')}</select></label>
      <div class="form-row">
        <label>Start<input id="if-start" value="now" title="now, +2h, or ISO time 2023-07-12T08:00"></label>
        <label>Duration<input id="if-dur" value="1d" title="e.g. 6h, 2d - empty = until cleared"></label>
      </div>
      <div class="form-row">
        <label>Profile<select id="if-prof"><option value="step">step</option><option value="ramp">ramp</option><option value="intermittent">intermittent</option></select></label>
        <label class="prof-ramp" hidden>Ramp time (h)<input type="number" id="if-ramp" value="1" min="0" step="0.25"></label>
        <label class="prof-int" hidden>Period (h)<input type="number" id="if-per" value="1" min="0.1" step="0.25"></label>
        <label class="prof-int" hidden>Duty (0–1)<input type="number" id="if-duty" value="0.5" min="0" max="1" step="0.05"></label>
      </div>
      ${params.length ? `<fieldset><legend>Parameters</legend>${params.map(([k, p]) => `
        <label>${esc(k)} <small>${esc(p.description)}${p.unit ? ` [${esc(unitLabel(p.unit))}]` : ''}</small>
          <input type="number" step="any" data-param="${esc(k)}" value="${p.default ?? ''}" ${p.minimum !== null && p.minimum !== undefined ? `min="${p.minimum}"` : ''} ${p.maximum !== null && p.maximum !== undefined ? `max="${p.maximum}"` : ''} placeholder="${p.default === null ? 'auto' : ''}"></label>`).join('')}</fieldset>` : '<p class="muted">No parameters.</p>'}
      <label>Note<input id="if-note" placeholder="optional free text"></label>
    </div>
    <div class="form-row right"><button class="btn btn-danger" id="if-go">⚡ Inject</button></div>
    <p class="hint">Severity profile s(t): step = 1 while active, ramp = linear 0→1, intermittent = on/off with the given period and duty cycle.</p>`;
  const sel = $('#if-target', box);
  if (sel.options.length) sel.selectedIndex = 0;
  $('#if-tq', box)?.addEventListener('input', (e) => {
    const t = e.target.value.toLowerCase();
    let first = null;
    for (const o of sel.options) { o.hidden = t && !o.textContent.toLowerCase().includes(t); if (!o.hidden && !first) first = o; }
    if (first && sel.selectedOptions[0]?.hidden) first.selected = true;
  });
  $('#if-prof', box).onchange = (e) => {
    $$('.prof-ramp', box).forEach((l) => { l.hidden = e.target.value !== 'ramp'; });
    $$('.prof-int', box).forEach((l) => { l.hidden = e.target.value !== 'intermittent'; });
  };
  $('#if-go', box).onclick = () => inject(f, box);
}

async function inject(f, box) {
  const target = $('#if-target', box).value;
  if (!target) { toast('Choose a target', 'warn'); return; }
  const params = {};
  $$('[data-param]', box).forEach((i) => { if (i.value !== '') params[i.dataset.param] = +i.value; });
  const prof = $('#if-prof', box).value;
  const body = {
    type: f.name, target, start: $('#if-start', box).value.trim() || 'now', profile: prof, params, source: 'human',
    note: $('#if-note', box).value,
  };
  const dur = $('#if-dur', box).value.trim();
  if (dur) body.duration = dur;
  if (prof === 'ramp') body.ramp_s = (+$('#if-ramp', box).value || 1) * 3600;
  if (prof === 'intermittent') { body.period_s = (+$('#if-per', box).value || 1) * 3600; body.duty = +$('#if-duty', box).value; }
  try {
    const r = await post('/api/injections', body);
    toast(`Injected ${r.id}: ${f.name} → ${target}`, 'ok');
  } catch (e) { toast(e.message, 'err'); }
}

function status(i, now) {
  if (i.cleared) return ['cleared', 'st-cleared'];
  if (i.start > now) return ['scheduled', 'st-sched'];
  if (i.end && i.end <= now) return ['ended', 'st-ended'];
  return ['active', 'st-active'];
}

export function update() {
  const el = $('#inj-rows');
  if (!el) return;
  const now = S.snap.time || '';
  const list = [...(S.snap.injections || [])].reverse();
  const html = list.length ? list.map((i) => {
    const [st, cls] = status(i, now);
    return `<tr class="${cls}"><td><code>${esc(i.id)}</code></td><td><b>${esc(i.type)}</b>${i.note ? `<small class="sub">${esc(i.note)}</small>` : ''}</td><td>${esc(i.target)}</td>
      <td><span class="cat cat-${esc(i.category)}">${esc(i.category)}</span></td><td><span class="lay-badge lay-${esc(i.layer)}">${esc(i.layer)}</span></td>
      <td><span class="src src-${esc(i.source)}">${esc(i.source)}</span></td><td>${esc(fmtDT(i.start))}</td><td>${i.end ? esc(fmtDT(i.end)) : '∞'}</td>
      <td><span class="ist">${st}</span></td>
      <td><span class="sevbar" title="current severity ${i.severity}"><span style="width:${Math.round(100 * (i.severity || 0))}%"></span></span></td>
      <td>${st === 'active' || st === 'scheduled' ? `<button class="btn sm" data-clear="${esc(i.id)}">Clear</button>` : ''}</td></tr>`;
  }).join('') : '<tr><td colspan="11" class="muted">No injections yet. Choose a fault above, call the REST API, or enable the random chaos generator.</td></tr>';
  // only touch the DOM when something changed, so Clear clicks are never lost
  if (el._html !== html) { el.innerHTML = html; el._html = html; }
}

/** Same page, new query (e.g. #faults?type=meeting): preselect that catalogue entry. */
export function onQuery(q) {
  if (q.type && S.catalog.some((x) => x.name === q.type)) selectType(q.type);
  if (q.target && $('#if-target')) $('#if-target').value = q.target;
}
