/* =============================================================================
 * app.js - boot, live data connection, header, sidebar tree and hash router.
 *
 * Pages are modules exporting { render(main, ctx), update?(), destroy?() }.
 * Hash routes: #overview  #ahu/AHU-1  #vav/VAV-Core_mid  #plant  #trends?p=a,b
 *              #alarms  #faults  #points     (append ?truth=1 to enable truth)
 * ========================================================================== */
import { S, $, $$, api, post, toast, esc, refreshBindings, parseHash, parseT, fmtHM, fmtDate, equipOfType } from './core.js';
import { openPoint, closePoint, updatePointDialog, openSession } from './dialogs.js';
import * as overview from './pages/overview.js';
import * as ahu from './pages/ahu.js';
import * as vav from './pages/vav.js';
import * as plant from './pages/plant.js';
import * as trends from './pages/trends.js';
import * as alarms from './pages/alarms.js';
import * as faults from './pages/faults.js';
import * as points from './pages/points.js';

const PAGES = { overview, ahu, vav, plant, trends, alarms, faults, points };
let current = null;      // active page module
let currentKey = '';     // route key used to avoid needless rebuilds

// ------------------------------------------------------------------ boot
async function boot() {
  try {
    const [info, equip, pts, cat, snap] = await Promise.all([
      api('/api/info'), api('/api/equipment'), api('/api/points'), api('/api/faults/catalog'), api('/api/snapshot?truth=1'),
    ]);
    S.info = info; S.equip = equip; S.points = pts; S.catalog = cat; S.snap = snap;
    for (const e of equip) S.equipById[e.id] = e;
    for (const p of pts) {
      S.pointById[p.id] = p;
      (S.pointsByEquip[p.equip] ||= []).push(p);
    }
  } catch (e) {
    $('#main').innerHTML = `<div class="loading err">Cannot reach the Virtual BAS server: ${esc(e.message)}</div>`;
    setTimeout(boot, 3000);
    return;
  }
  // truth toggle: hash ?truth=1/0 wins, else remembered preference
  const q = parseHash().q;
  let tr = false;
  try { tr = localStorage.getItem('vbas.truth') === '1'; } catch { /* storage unavailable */ }
  if (q.truth !== undefined) tr = q.truth === '1';
  setTruth(tr, false);

  $('#h-bldg').textContent = S.info.building;
  $('#f-info').textContent = `EnergyPlus ${S.info.energyplus} · ${S.info.n_points} points · ${S.info.n_equipment} devices · control: ${S.info.control_profile} · realism ${S.info.realism} · seed ${S.info.seed} · Δt ${S.info.timestep_s / 60} min`;
  buildTree();
  wireHeader();
  window.addEventListener('hashchange', route);
  route();
  onSnapshot(S.snap);
  connect();
}

// ------------------------------------------------------------------ live data
let ws = null, pollTimer = null, wsRetry = null;
function connect() {
  clearTimeout(wsRetry);
  try {
    ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws?truth=1`);
  } catch { startPolling(); return; }
  let opened = false;
  ws.onopen = () => { opened = true; stopPolling(); setConn('ws'); };
  ws.onmessage = (ev) => { try { onSnapshot(JSON.parse(ev.data)); } catch { /* ignore malformed */ } };
  ws.onclose = ws.onerror = () => {
    ws = null;
    startPolling();
    wsRetry = setTimeout(connect, opened ? 3000 : 15000);
  };
}
function startPolling() {
  if (pollTimer) return;
  setConn('poll');
  const tick = async () => {
    try { onSnapshot(await api('/api/snapshot?truth=1')); setConn(ws ? 'ws' : 'poll'); } catch { setConn('offline'); }
  };
  tick();
  pollTimer = setInterval(tick, 1500);
}
function stopPolling() { clearInterval(pollTimer); pollTimer = null; }
function setConn(c) {
  S.conn = c;
  const el = $('#f-conn');
  el.className = 'conn conn-' + c;
  el.textContent = { ws: '● live (WebSocket)', poll: '● live (polling)', offline: '● offline', connecting: '● connecting' }[c];
}

/** Central snapshot handler: header, bindings, page and dialog updates. */
function onSnapshot(s) {
  if (!s || !s.points) return;
  S.snap = s;
  updateHeader();
  refreshBindings(document);
  try { current?.update?.(); } catch (e) { console.error(e); }
  updatePointDialog();
}

// ------------------------------------------------------------------ header
function wireHeader() {
  $$('#h-speed button').forEach((b) => {
    b.onclick = () => control('speed', b.dataset.speed).then(() => {
      if (S.snap?.paused) control('resume');
    });
  });
  $('#h-pause').onclick = () => control(S.snap?.paused ? 'resume' : 'pause');
  $('#h-step').onclick = () => control('step', 1);
  $('#h-truth').onchange = (e) => setTruth(e.target.checked, true);
  $('#h-session').onclick = openSession;
  // any element with data-pid opens the point dialog (except inside dialogs/forms)
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-pid]');
    if (!el || el.closest('dialog') || el.closest('.no-pick') || e.target.closest('a,button,input,select')) return;
    openPoint(el.dataset.pid);
  });
}

async function control(action, value) {
  try {
    const r = await post('/api/control', { action, value });
    if (S.snap) { S.snap.paused = r.paused; S.snap.speed = r.speed; updateHeader(); }
  } catch (e) { toast(e.message, 'err'); }
}

function setTruth(on, remember) {
  S.truth = !!on;
  $('#h-truth').checked = S.truth;
  document.body.classList.toggle('truth-on', S.truth);
  if (remember) { try { localStorage.setItem('vbas.truth', S.truth ? '1' : '0'); } catch { /* ignore */ } }
  refreshBindings(document);
  try { current?.onTruth?.(); current?.update?.(); } catch (e) { console.error(e); }
  updatePointDialog();
}

function speedKey(sp) {
  if (sp === 'max' || sp === null) return 'max';
  return `${Math.round(+sp)}x`;
}

function updateHeader() {
  const s = S.snap;
  const t = parseT(s.time);
  $('#h-clock').textContent = t ? fmtHM(t) : '--:--';
  $('#h-date').textContent = t ? fmtDate(t) : (s.warmup ? 'EnergyPlus warm-up' : '-');
  const state = s.finished ? 'FINISHED' : s.paused ? 'PAUSED' : 'RUNNING';
  const st = $('#h-state');
  st.textContent = state;
  st.className = 'pill pill-' + state.toLowerCase();
  $('#h-warm').hidden = !s.warmup;
  $('#h-pause').textContent = s.paused ? '▶ Resume' : '⏸ Pause';
  const k = speedKey(s.speed);
  $$('#h-speed button').forEach((b) => b.classList.toggle('on', b.dataset.speed === k));
  const t0 = parseT(s.start), t1 = parseT(s.end);
  if (t && t0 && t1) $('#h-prog').style.width = `${Math.max(0, Math.min(100, (100 * (t - t0)) / (t1 - t0))).toFixed(1)}%`;

  const al = s.alarms || [];
  $('#h-nalarm').textContent = al.length;
  $('#h-nalarm').classList.toggle('hot', al.length > 0);
  const nInj = (s.injections || []).filter((i) => i.severity > 0).length;
  $('#h-ninj').textContent = nInj;
  $('#h-ninj').classList.toggle('hot', nInj > 0);
  const banner = $('#h-banner');
  if (al.length) {
    const sevRank = { critical: 0, high: 1, major: 1, medium: 2, minor: 3, low: 3 };
    const top = [...al].sort((a, b) => (sevRank[a.severity] ?? 2) - (sevRank[b.severity] ?? 2))[0];
    banner.className = 'alarm-banner on sev-' + esc(top.severity || 'medium');
    $('#h-banner-text').textContent = `${al.length} active alarm${al.length > 1 ? 's' : ''} - ${top.equip}: ${top.message}${al.length > 1 ? `  (+${al.length - 1} more)` : ''}`;
  } else {
    banner.className = 'alarm-banner';
    $('#h-banner-text').textContent = 'No active alarms';
  }
}

// ------------------------------------------------------------------ sidebar equipment tree
function buildTree() {
  const ahus = equipOfType('AHU');
  let html = '';
  for (const a of ahus) {
    html += `<details data-eq="${esc(a.id)}"><summary><a href="#ahu/${esc(a.id)}">${esc(a.id)}</a><small>${esc(a.eplus_name)}</small></summary>`;
    for (const v of a.meta.vav || []) html += `<a class="leaf" href="#vav/${esc(v)}">${esc(v.replace('VAV-', ''))}</a>`;
    html += '</details>';
  }
  html += `<details><summary><a href="#plant">Central plant</a></summary>`;
  for (const t of ['Chiller', 'CoolingTower', 'Boiler', 'Pump']) {
    for (const e of equipOfType(t)) html += `<a class="leaf" href="#plant">${esc(e.id)}<small>${esc(t)}</small></a>`;
  }
  html += '</details>';
  $('#side-tree').innerHTML = html;
}

// ------------------------------------------------------------------ router
function route() {
  const h = parseHash();
  if (h.q.truth !== undefined && (h.q.truth === '1') !== S.truth) setTruth(h.q.truth === '1', false);
  const mod = PAGES[h.page] || overview;
  const page = PAGES[h.page] ? h.page : 'overview';
  const key = `${page}/${h.arg}`;
  $$('#side [data-nav]').forEach((a) => a.classList.toggle('on', a.dataset.nav === page));
  $$('#side-tree a').forEach((a) => a.classList.toggle('on', a.getAttribute('href') === `#${page}/${h.arg}`));
  closePoint();
  if (key === currentKey && current === mod) { current?.onQuery?.(h.q); return; }
  try { current?.destroy?.(); } catch (e) { console.error(e); }
  current = mod;
  currentKey = key;
  const main = $('#main');
  main.innerHTML = '';
  main.scrollTop = 0;
  try {
    mod.render(main, { arg: h.arg, q: h.q });
  } catch (e) {
    console.error(e);
    main.innerHTML = `<div class="loading err">Page error: ${esc(e.message)}</div>`;
  }
  refreshBindings(main);
  try { mod.update?.(); } catch (e) { console.error(e); }
}

boot();
