/* =============================================================================
 * chart.js - small dependency-free canvas trend chart.
 *
 *  - multi-series, shared time axis
 *  - one pane per engineering unit (small multiples instead of dual y-axes)
 *  - gaps for null values, observed solid / truth dashed
 *  - crosshair + tooltip hover readout, HTML legend with click-to-hide
 *
 * Usage:
 *   const c = new TrendChart(containerEl, {legend: true});
 *   c.setData(timesMs, [{id, label, color, unit, values, dashed}]);
 * ========================================================================== */

const CSSV = (name, fb) => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fb;
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const p2 = (n) => String(n).padStart(2, '0');

/** Fixed categorical order (validated dark-mode steps); colour follows the series, never its rank. */
export const SERIES_COLORS = ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#2fae2f', '#9085e9', '#e66767'];

const UNIT_LABEL = { degC: '°C', 'm3/s': 'm³/s', 'W/m2': 'W/m²', '-': '' };

/** "Nice" tick step for a numeric range. */
function niceStep(range, target) {
  const raw = range / Math.max(1, target);
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const f = raw / mag;
  return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * mag;
}
const TIME_STEPS = [5, 10, 15, 30, 60, 120, 180, 360, 720, 1440, 2880, 4320, 10080].map((m) => m * 60000);

export class TrendChart {
  constructor(container, opts = {}) {
    this.opts = Object.assign({ legend: true, minPaneH: 70, emptyText: 'No data' }, opts);
    this.root = container;
    this.root.classList.add('tchart');
    this.root.innerHTML = '';
    if (this.opts.legend) {
      this.legendEl = document.createElement('div');
      this.legendEl.className = 'tchart-legend';
      this.root.appendChild(this.legendEl);
    }
    this.wrap = document.createElement('div');
    this.wrap.className = 'tchart-canvas';
    this.root.appendChild(this.wrap);
    this.canvas = document.createElement('canvas');
    this.wrap.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    this.base = document.createElement('canvas'); // cached plot without hover overlay
    this.times = [];
    this.series = [];
    this.hidden = new Set();
    this.hoverX = null;
    this.canvas.addEventListener('mousemove', (e) => {
      const r = this.canvas.getBoundingClientRect();
      this.hoverX = e.clientX - r.left;
      this.overlay();
    });
    this.canvas.addEventListener('mouseleave', () => { this.hoverX = null; this.overlay(); });
    this.ro = new ResizeObserver(() => this.draw());
    this.ro.observe(this.wrap);
  }

  destroy() { this.ro.disconnect(); }

  /** times: array of epoch ms; series: [{id,label,color,unit,values,dashed}] */
  setData(times, series) {
    this.times = times;
    this.series = series;
    this.renderLegend();
    this.draw();
  }

  renderLegend() {
    if (!this.legendEl) return;
    this.legendEl.innerHTML = '';
    for (const s of this.series) {
      const it = document.createElement('button');
      it.className = 'lg-item' + (this.hidden.has(s.id) ? ' off' : '');
      it.title = 'Click to show/hide';
      it.innerHTML = `<span class="lg-swatch${s.dashed ? ' dashed' : ''}" style="--c:${s.color}"></span>${s.label}`;
      it.onclick = () => {
        if (this.hidden.has(s.id)) this.hidden.delete(s.id); else this.hidden.add(s.id);
        this.renderLegend();
        this.draw();
      };
      this.legendEl.appendChild(it);
    }
  }

  /** Visible series grouped into panes by unit (insertion order). */
  panes() {
    const groups = new Map();
    for (const s of this.series) {
      if (this.hidden.has(s.id)) continue;
      const key = s.unit ?? '';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(s);
    }
    return Array.from(groups, ([unit, list]) => ({ unit, list }));
  }

  draw() {
    const W = this.wrap.clientWidth, H = this.wrap.clientHeight;
    if (!W || !H) return;
    const dpr = window.devicePixelRatio || 1;
    for (const c of [this.canvas, this.base]) {
      c.width = Math.round(W * dpr);
      c.height = Math.round(H * dpr);
    }
    this.canvas.style.width = W + 'px';
    this.canvas.style.height = H + 'px';
    const g = this.base.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    this.W = W; this.H = H; this.dpr = dpr;

    const ink = CSSV('--text-2', '#9fb0c8'), grid = CSSV('--grid', '#26364d'), axis = CSSV('--line', '#33465f');
    const font = '11px system-ui, -apple-system, "Segoe UI", sans-serif';
    g.font = font;
    const L = 58, R = 14, T = 8, B = 24;
    this.plot = { L, R, T, B };
    const panes = this.panes();
    const t = this.times;
    if (!t.length || !panes.length) {
      g.fillStyle = ink; g.textAlign = 'center';
      g.fillText(this.opts.emptyText, W / 2, H / 2);
      this.layout = null;
      this.overlay();
      return;
    }
    const t0 = t[0], t1 = t[t.length - 1] === t0 ? t0 + 60000 : t[t.length - 1];
    const pw = W - L - R;
    const xOf = (ms) => L + ((ms - t0) / (t1 - t0)) * pw;
    const gap = 14;
    const ph = (H - T - B - gap * (panes.length - 1)) / panes.length;

    // ---- time grid (shared)
    const stepMs = TIME_STEPS.find((s) => (s / (t1 - t0)) * pw >= 90) ?? TIME_STEPS[TIME_STEPS.length - 1];
    // align ticks to local midnight (timezone offset) so day labels fall on 00:00
    const tzOff = new Date(t0).getTimezoneOffset() * 60000;
    const ticks = [];
    for (let k = Math.ceil((t0 - tzOff) / stepMs) * stepMs + tzOff; k <= t1; k += stepMs) ticks.push(k);
    g.strokeStyle = grid; g.lineWidth = 1;
    g.fillStyle = ink; g.textAlign = 'center'; g.textBaseline = 'top';
    for (const k of ticks) {
      const x = Math.round(xOf(k)) + 0.5;
      g.beginPath(); g.moveTo(x, T); g.lineTo(x, H - B); g.stroke();
      const d = new Date(k);
      const midnight = d.getHours() === 0 && d.getMinutes() === 0;
      const lbl = stepMs >= 86400000 || midnight ? `${d.getDate()} ${MON[d.getMonth()]}` : `${p2(d.getHours())}:${p2(d.getMinutes())}`;
      g.font = midnight ? 'bold ' + font : font;
      g.fillText(lbl, x, H - B + 6);
    }
    g.font = font;

    // ---- panes
    this.layout = [];
    panes.forEach((pane, i) => {
      const y0 = T + i * (ph + gap), y1 = y0 + ph;
      let lo = Infinity, hi = -Infinity;
      for (const s of pane.list) for (const v of s.values) if (v !== null && v !== undefined) { if (v < lo) lo = v; if (v > hi) hi = v; }
      if (!isFinite(lo)) { lo = 0; hi = 1; }
      if (hi - lo < 1e-9) { lo -= 0.5; hi += 0.5; }
      const pad = (hi - lo) * 0.08;
      const nonNeg = lo >= 0;
      lo -= pad; hi += pad;
      if (nonNeg && lo < 0) lo = 0;  // don't invent negative axis room for non-negative data
      const step = niceStep(hi - lo, Math.max(2, Math.floor(ph / 32)));
      lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
      if (nonNeg && lo < 0) lo = 0;
      const yOf = (v) => y1 - ((v - lo) / (hi - lo)) * (y1 - y0);
      // y grid + labels
      g.textAlign = 'right'; g.textBaseline = 'middle';
      const dec = Math.max(0, -Math.floor(Math.log10(step) + 1e-9));
      for (let v = lo; v <= hi + step / 2; v += step) {
        const y = Math.round(yOf(v)) + 0.5;
        g.strokeStyle = grid; g.beginPath(); g.moveTo(L, y); g.lineTo(W - R, y); g.stroke();
        g.fillStyle = ink; g.fillText(v.toFixed(dec), L - 6, y);
      }
      g.strokeStyle = axis;
      g.strokeRect(L + 0.5, y0 + 0.5, pw, y1 - y0);
      // unit label
      g.save();
      g.fillStyle = ink; g.textAlign = 'left'; g.textBaseline = 'top';
      g.font = 'bold ' + font;
      g.fillText(UNIT_LABEL[pane.unit] ?? pane.unit, L + 6, y0 + 4);
      g.restore();
      // series (truth first so observed draws on top)
      const ordered = [...pane.list].sort((a, b) => (b.dashed ? 1 : 0) - (a.dashed ? 1 : 0));
      g.save();
      g.beginPath(); g.rect(L, y0, pw, y1 - y0); g.clip();
      for (const s of ordered) {
        g.strokeStyle = s.color;
        g.lineWidth = s.dashed ? 1.6 : 2;
        g.globalAlpha = s.dashed ? 0.95 : 1;
        g.setLineDash(s.dashed ? [6, 4] : []);
        g.lineJoin = 'round';
        g.beginPath();
        let pen = false, nPts = 0, lastX = 0, lastY = 0;
        for (let k = 0; k < t.length; k++) {
          const v = s.values[k];
          if (v === null || v === undefined) {
            if (pen && nPts === 1) { g.moveTo(lastX - 1, lastY); g.lineTo(lastX + 1, lastY); }
            pen = false; nPts = 0; continue;
          }
          const x = xOf(t[k]), y = yOf(v);
          if (!pen) { g.moveTo(x, y); pen = true; } else g.lineTo(x, y);
          nPts++; lastX = x; lastY = y;
        }
        g.stroke();
      }
      g.restore();
      g.setLineDash([]); g.globalAlpha = 1;
      this.layout.push({ pane, y0, y1, yOf });
    });
    this.xOf = xOf; this.t0 = t0; this.t1 = t1; this.pw = pw;
    this.overlay();
  }

  /** Blit cached plot and draw crosshair / tooltip. */
  overlay() {
    const c = this.ctx, dpr = this.dpr || 1;
    if (!this.W) return;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.clearRect(0, 0, this.canvas.width, this.canvas.height);
    c.drawImage(this.base, 0, 0);
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (this.hoverX === null || !this.layout || !this.times.length) return;
    const { L, R, T, B } = this.plot;
    const x = Math.min(Math.max(this.hoverX, L), this.W - R);
    const ms = this.t0 + ((x - L) / this.pw) * (this.t1 - this.t0);
    // nearest sample (binary search)
    const t = this.times;
    let lo = 0, hi = t.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (t[m] < ms) lo = m; else hi = m; }
    const k = Math.abs(t[lo] - ms) < Math.abs(t[hi] - ms) ? lo : hi;
    const xs = this.xOf(t[k]);
    c.strokeStyle = CSSV('--text-2', '#9fb0c8');
    c.lineWidth = 1;
    c.setLineDash([3, 3]);
    c.beginPath(); c.moveTo(Math.round(xs) + 0.5, T); c.lineTo(Math.round(xs) + 0.5, this.H - B); c.stroke();
    c.setLineDash([]);
    const rows = [];
    for (const lay of this.layout) {
      for (const s of lay.pane.list) {
        const v = s.values[k];
        if (v !== null && v !== undefined) {
          c.fillStyle = s.color;
          c.strokeStyle = CSSV('--bg-1', '#101a29');
          c.lineWidth = 2;
          c.beginPath(); c.arc(xs, lay.yOf(v), 4, 0, Math.PI * 2); c.fill(); c.stroke();
        }
        const u = UNIT_LABEL[s.unit] ?? s.unit ?? '';
        rows.push({ color: s.color, dashed: s.dashed, text: `${s.label}`, val: v === null || v === undefined ? '---' : `${(+v).toFixed(Math.abs(v) >= 100 ? 1 : 2)} ${u}` });
      }
    }
    // tooltip box
    const d = new Date(t[k]);
    const head = `${d.getDate()} ${MON[d.getMonth()]} ${p2(d.getHours())}:${p2(d.getMinutes())}`;
    c.font = '12px system-ui, -apple-system, "Segoe UI", sans-serif';
    let wText = 0, wVal = 0;
    for (const r of rows) { wText = Math.max(wText, c.measureText(r.text).width); wVal = Math.max(wVal, c.measureText(r.val).width); }
    const bw = Math.max(130, 26 + wText + 14 + wVal + 10), bh = 24 + rows.length * 18;
    let bx = xs + 14;
    if (bx + bw > this.W - 4) bx = xs - 14 - bw;
    const by = T + 6;
    c.fillStyle = 'rgba(8,14,24,0.94)';
    c.strokeStyle = CSSV('--line', '#33465f');
    c.lineWidth = 1;
    c.beginPath(); c.roundRect ? c.roundRect(bx, by, bw, bh, 5) : c.rect(bx, by, bw, bh); c.fill(); c.stroke();
    c.fillStyle = '#e8eef7'; c.textAlign = 'left'; c.textBaseline = 'middle';
    c.font = 'bold 12px system-ui, -apple-system, "Segoe UI", sans-serif';
    c.fillText(head, bx + 10, by + 12);
    c.font = '12px system-ui, -apple-system, "Segoe UI", sans-serif';
    rows.forEach((r, i) => {
      const yy = by + 30 + i * 18;
      c.strokeStyle = r.color; c.lineWidth = 2.5;
      c.setLineDash(r.dashed ? [4, 3] : []);
      c.beginPath(); c.moveTo(bx + 10, yy); c.lineTo(bx + 24, yy); c.stroke();
      c.setLineDash([]);
      c.fillStyle = '#c9d4e3'; c.textAlign = 'left';
      c.fillText(r.text, bx + 30, yy);
      c.fillStyle = '#ffffff'; c.textAlign = 'right';
      c.fillText(r.val, bx + bw - 10, yy);
    });
  }
}

/**
 * Load trend data for point ids from the historian and turn it into chart
 * series. If `truth` is true, a dashed truth series is added for every
 * measured point (sensor/meter) that has an EnergyPlus counterpart.
 */
export async function loadSeries(pids, n, { truth = false, pointById = {}, colors = null, labels = null } = {}) {
  if (!pids.length) return { times: [], series: [], raw: null };
  const q = encodeURIComponent(pids.join(','));
  const obsP = fetch(`/api/trend?points=${q}&n=${n}&source=observed`).then((r) => r.json());
  const tPids = truth ? pids.filter((p) => ['sensor', 'meter'].includes(pointById[p]?.kind)) : [];
  const truP = tPids.length
    ? fetch(`/api/trend?points=${encodeURIComponent(tPids.join(','))}&n=${n}&source=truth`).then((r) => r.json())
    : Promise.resolve(null);
  const [o, tr] = await Promise.all([obsP, truP]);
  const times = (o.time || []).map((s) => new Date(String(s).replace(' ', 'T')).getTime());
  const series = [];
  pids.forEach((pid, i) => {
    const p = pointById[pid];
    const color = colors?.[i] ?? SERIES_COLORS[i % SERIES_COLORS.length];
    const label = labels?.[i] ?? pid;
    if (o[pid]) series.push({ id: pid, label, color, unit: p?.unit ?? '', values: o[pid], dashed: false });
    if (tr && tr[pid]) series.push({ id: pid + '#truth', label: `${label} (truth)`, color, unit: p?.unit ?? '', values: tr[pid], dashed: true });
  });
  return { times, series, raw: { obs: o, truth: tr } };
}
