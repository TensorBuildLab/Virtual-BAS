/* Shared drawing helpers for the Virtual BAS paper diagrams (inline SVG, no external resources).
 *
 * Every diagram page: <div id="fig"></div><script src="diagram_lib.js"></script><script> D.init(w,h); ... D.finish(); </script>
 * Units are printed CSS px (96 px = 1 in). Colours follow paper/figstyle.py.
 * Rich-text markup in labels:  *italic*   #bold#   _{subscript}   ^{superscript}   \* escapes.
 * D.finish() runs a layout check (text/text, text/connector, text/box and connector/box overlaps, bounds) and stores
 * the findings in window.qc; render_html.py waits for window.figReady.
 */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const FONT = 'Arial, Helvetica, sans-serif';
  const MONO = 'Consolas, "Courier New", monospace';
  const C = {
    inner: '#2a78d6', innerBg: '#eef4fc', outer: '#eb6834', outerBg: '#fdf1ea', ai: '#6250d6', aiBg: '#f1effc',
    env: '#1baf7a', envBg: '#e9f7f1', fault: '#e34948', faultBg: '#fdeeee', ink: '#1b1b1a', ink2: '#52514e',
    muted: '#8a8984', grid: '#e3e2de', white: '#ffffff',
    tierStd: '#1f5fae', tierAdv: '#5b9be6', tierNext: '#b5d3f5', truth: '#bdbcb7',
  };
  window.figReady = false;
  let S = null;

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in (attrs || {})) {
      const v = attrs[k];
      if (v !== undefined && v !== null && v !== false) e.setAttribute(k, v);
    }
    if (parent) parent.appendChild(e);
    return e;
  }

  function init(w, h) {
    const fig = document.getElementById('fig');
    fig.style.width = w + 'px';
    fig.style.height = h + 'px';
    const svg = el('svg', { xmlns: NS, width: w, height: h, viewBox: `0 0 ${w} ${h}`, 'font-family': FONT }, fig);
    svg.style.display = 'block';
    S = { svg, w, h, defs: el('defs', {}, svg), markers: {}, boxes: [], texts: [], conns: [], icons: [] };
    S.panelsL = el('g', { id: 'panels' }, svg);
    S.boxesL = el('g', { id: 'boxes' }, svg);
    S.connsL = el('g', { id: 'conns' }, svg);
    S.labelsL = el('g', { id: 'labels' }, svg);
    S.topL = el('g', { id: 'top' }, svg);
    return S;
  }

  // ------------------------------------------------------------------ text
  function rich(parent, x, y, str, o) {
    o = o || {};
    const size = o.size || 10;
    const baseItalic = !!o.italic, baseBold = o.weight === 'bold';
    const t = el('text', {
      x, y, 'font-size': size, fill: o.fill || C.ink, 'text-anchor': o.anchor || 'start',
      'font-weight': baseBold ? 'bold' : null, 'font-style': baseItalic ? 'italic' : null,
      'font-family': o.family || null, 'letter-spacing': o.ls || null,
    }, parent);
    if (o.mono) { t.style.whiteSpace = 'pre'; t.setAttribute('font-family', MONO); }
    let it = baseItalic, bd = baseBold, mode = null, cur = 0, buf = '';
    const flush = () => {
      if (!buf) return;
      const ts = el('tspan', {}, t);
      ts.textContent = buf;
      if (it !== baseItalic) ts.setAttribute('font-style', it ? 'italic' : 'normal');
      if (bd !== baseBold) ts.setAttribute('font-weight', bd ? 'bold' : 'normal');
      const target = mode === 'sub' ? size * 0.26 : mode === 'sup' ? -size * 0.36 : 0;
      if (Math.abs(target - cur) > 1e-6) { ts.setAttribute('dy', (target - cur).toFixed(2)); cur = target; }
      if (mode) ts.setAttribute('font-size', (size * 0.72).toFixed(2));
      buf = '';
    };
    if (o.raw) { buf = str; flush(); }
    else {
      for (let i = 0; i < str.length; i++) {
        const ch = str[i];
        if (ch === '\\' && i + 1 < str.length) { buf += str[++i]; continue; }
        if (ch === '*') { flush(); it = !it; continue; }
        if (ch === '#') { flush(); bd = !bd; continue; }
        if ((ch === '_' || ch === '^') && str[i + 1] === '{') { flush(); mode = ch === '_' ? 'sub' : 'sup'; i++; continue; }
        if (ch === '}' && mode) { flush(); mode = null; continue; }
        buf += ch;
      }
      flush();
    }
    if (o.fillSpans) { /* [[substring, colour], ...] colours whole tspans containing the substring */
      for (const ts of t.querySelectorAll('tspan')) for (const [s, c] of o.fillSpans) if (ts.textContent.includes(s)) ts.setAttribute('fill', c);
    }
    if (!o.noqc) S.texts.push(t); else t.dataset.noqc = '1';
    return t;
  }
  function text(x, y, str, o) { return rich((o && o.parent) || S.labelsL, x, y, str, o || {}); }
  function width(str, o) {
    const t = rich(S.topL, -1000, -1000, str, Object.assign({}, o, { noqc: true }));
    const w = t.getComputedTextLength(); t.remove(); return w;
  }

  // ------------------------------------------------------------------ markers / connectors
  function marker(color, size) {
    size = size || 1;
    const id = 'ah' + color.replace('#', '') + String(size).replace('.', '_');
    if (!S.markers[id]) {
      const L = 6.6 * size, W = 5.2 * size;
      const m = el('marker', { id, markerUnits: 'userSpaceOnUse', markerWidth: L + 1, markerHeight: W + 1, refX: L - 3.5, refY: W / 2, orient: 'auto-start-reverse', viewBox: `0 0 ${L + 1} ${W + 1}` }, S.defs);
      el('path', { d: `M0,0 L${L},${W / 2} L0,${W} L${L * 0.18},${W / 2} Z`, fill: color }, m);
      S.markers[id] = true;
    }
    return `url(#${id})`;
  }
  function roundedPath(pts, r) {
    let d = `M${pts[0][0]},${pts[0][1]}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const p0 = pts[i - 1], p1 = pts[i], p2 = pts[i + 1];
      const d1 = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]), d2 = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
      const rr = Math.min(r, d1 / 2, d2 / 2);
      const a = [p1[0] + (p0[0] - p1[0]) * rr / d1, p1[1] + (p0[1] - p1[1]) * rr / d1];
      const b = [p1[0] + (p2[0] - p1[0]) * rr / d2, p1[1] + (p2[1] - p1[1]) * rr / d2];
      d += ` L${a[0].toFixed(2)},${a[1].toFixed(2)} Q${p1[0]},${p1[1]} ${b[0].toFixed(2)},${b[1].toFixed(2)}`;
    }
    const q = pts[pts.length - 1];
    return d + ` L${q[0]},${q[1]}`;
  }
  function shorten(pts, atStart, atEnd) {
    pts = pts.map(p => p.slice());
    const cut = (a, b, L) => { const d = Math.hypot(b[0] - a[0], b[1] - a[1]); return [b[0] + (a[0] - b[0]) * L / d, b[1] + (a[1] - b[1]) * L / d]; };
    if (atEnd) pts[pts.length - 1] = cut(pts[pts.length - 2], pts[pts.length - 1], atEnd);
    if (atStart) pts[0] = cut(pts[1], pts[0], atStart);
    return pts;
  }
  /* conn(points, {color, w, dash, head: 'end'|'start'|'both'|'none', r, halo, curve}) */
  function conn(pts, o) {
    o = o || {};
    const color = o.color || C.ink2, w = o.w || 1.2, head = o.head || 'end', hs = o.hs || 1;
    const sEnd = (head === 'end' || head === 'both') ? 3.5 * hs : 0, sStart = (head === 'start' || head === 'both') ? 3.5 * hs : 0;
    const p2 = shorten(pts, sStart, sEnd);
    const d = o.curve ? o.curve : roundedPath(p2, o.r === undefined ? 5 : o.r);
    const g = el('g', {}, o.layer || S.connsL);
    if (o.halo) el('path', { d, fill: 'none', stroke: '#fff', 'stroke-width': w + (o.halo === true ? 4 : o.halo), 'stroke-linecap': 'butt' }, g);
    const p = el('path', {
      d, fill: 'none', stroke: color, 'stroke-width': w, 'stroke-dasharray': o.dash ? (o.dash === true ? '3.2 2.4' : o.dash) : null,
      'stroke-linejoin': 'round', 'marker-end': sEnd ? marker(color, hs) : null, 'marker-start': sStart ? marker(color, hs) : null,
    }, g);
    S.conns.push({ el: p, pts, ignore: o.ignore || [] });
    return p;
  }

  // ------------------------------------------------------------------ labels, boxes
  /* pill: text centred at (x, y) on a white rounded background */
  function pill(x, y, str, o) {
    o = o || {};
    const size = o.size || 9.5;
    const t = rich(o.parent || S.labelsL, x, y + size * 0.34, str, { size, anchor: o.anchor || 'middle', fill: o.fill || C.ink, italic: o.italic, weight: o.weight });
    const bb = t.getBBox(), pad = o.pad === undefined ? 2 : o.pad;
    const r = el('rect', { x: bb.x - pad, y: bb.y - 0.3, width: bb.width + 2 * pad, height: bb.height + 0.6, rx: o.rx === undefined ? 2.5 : o.rx, fill: o.bg || '#fff', stroke: o.border || 'none', 'stroke-width': 0.8 });
    t.parentNode.insertBefore(r, t);
    return t;
  }
  function rect(x, y, w, h, o) {
    o = o || {};
    return el('rect', { x, y, width: w, height: h, rx: o.rx === undefined ? 4 : o.rx, fill: o.fill || 'none', stroke: o.stroke || 'none', 'stroke-width': o.sw || 1, 'stroke-dasharray': o.dash || null }, o.parent || S.boxesL);
  }
  /* panel: large background container with a header (title + subtitle) */
  function panel(o) {
    const g = el('g', {}, S.panelsL);
    el('rect', { x: o.x, y: o.y, width: o.w, height: o.h, rx: o.rx || 7, fill: o.fill || '#fff', stroke: o.color, 'stroke-width': o.sw || 1.2 }, g);
    const pad = o.pad || 8;
    if (o.title) {
      const ts = o.ts || 11.5;
      if (o.bar !== false) el('rect', { x: o.x + pad, y: o.y + pad + 1, width: 3, height: o.sub ? ts + 12 : ts, rx: 1.5, fill: o.color }, g);
      const tx = o.x + pad + (o.bar !== false ? 8 : 0);
      rich(g, tx, o.y + pad + ts * 0.85, o.title, { size: ts, weight: 'bold', ls: o.ls || '0.3' });
      if (o.sub) rich(g, tx, o.y + pad + ts + 11, o.sub, { size: o.ss || 9.5, fill: C.ink2 });
    }
    return g;
  }
  /* card({x,y,w,h,color,fill,title,lines,ts,ls,lh,pad,valign,align,icon,iconColor,accent}) */
  function card(o) {
    const g = el('g', {}, o.layer || S.boxesL);
    const id = 'b' + S.boxes.length;
    const rr = el('rect', { x: o.x, y: o.y, width: o.w, height: o.h, rx: o.rx === undefined ? 4 : o.rx, fill: o.fill || '#fff', stroke: o.color || C.ink2, 'stroke-width': o.sw || 1.1, 'stroke-dasharray': o.dash || null }, g);
    S.boxes.push({ id, x: o.x, y: o.y, w: o.w, h: o.h, el: rr, container: !!o.container });
    if (o.accent) {
      const r = o.rx === undefined ? 4 : o.rx;
      el('path', { d: `M${o.x},${o.y + 3.2} V${o.y + r} Q${o.x},${o.y} ${o.x + r},${o.y} H${o.x + o.w - r} Q${o.x + o.w},${o.y} ${o.x + o.w},${o.y + r} V${o.y + 3.2} Z`, fill: o.color }, g);
    }
    const pad = o.pad === undefined ? 7 : o.pad, ts = o.ts || 10.5, ls = o.ls || 9.5, lh = o.lh || 1.28;
    const lines = o.lines || [];
    const tgap = o.tgap === undefined ? 3.5 : o.tgap;
    // block height from first ascender to last descender
    let blockH = 0;
    if (o.title) blockH += ts * 0.74;
    if (lines.length) blockH += (o.title ? ts * 0.26 + tgap : 0) + ls * 0.74 + (lines.length - 1) * ls * lh + ls * 0.22;
    else blockH += ts * 0.22;
    let top;
    if (o.valign === 'top') top = o.y + pad + (o.accent ? 2 : 0);
    else top = o.y + (o.h - blockH) / 2 + (o.accent ? 1.4 : 0);
    const ax = o.align === 'center' ? o.x + o.w / 2 : o.x + pad + (o.indent || 0);
    const anchor = o.align === 'center' ? 'middle' : 'start';
    let y = top;
    const out = { g, id, x: o.x, y: o.y, w: o.w, h: o.h, texts: [] };
    if (o.title) {
      y += ts * 0.74;
      const t = rich(g, ax + (o.tindent || 0), y, o.title, { size: ts, weight: 'bold', anchor, fill: o.titleFill || C.ink });
      t.dataset.c = id; out.texts.push(t);
      y += ts * 0.26 + tgap;
    }
    lines.forEach((ln, i) => {
      const L = typeof ln === 'string' ? { t: ln } : ln;
      y += (i === 0 ? ls * 0.74 : ls * lh);
      const t = rich(g, ax, y, L.t, { size: L.size || ls, fill: L.fill || o.lineFill || C.ink2, anchor, italic: L.italic, weight: L.weight, mono: L.mono });
      t.dataset.c = id; out.texts.push(t);
    });
    if (o.icon) icon(o.icon, o.x + o.w - (o.iconSize || 13) - (o.iconPad || 5), o.y + (o.iconPad || 5) + (o.accent ? 1.5 : 0), o.iconSize || 13, o.iconColor || o.color, g);
    out.l = o.x; out.r = o.x + o.w; out.t = o.y; out.b = o.y + o.h; out.cx = o.x + o.w / 2; out.cy = o.y + o.h / 2;
    return out;
  }
  function chip(x, y, str, o) { /* small rounded tag, (x,y) = top-left; returns {w,h} */
    o = o || {};
    const size = o.size || 9, padx = o.padx === undefined ? 4 : o.padx, h = o.h || size + 5;
    const g = el('g', { 'data-inbox': '1', 'data-tab': o.tab ? '1' : null }, o.parent || S.labelsL);
    const t = rich(g, x + padx + (o.dot ? 7 : 0), y + h / 2 + size * 0.34, str, { size, fill: o.fill || C.ink, weight: o.weight, italic: o.italic });
    const w = t.getComputedTextLength() + 2 * padx + (o.dot ? 7 : 0);
    const r = el('rect', { x, y, width: w, height: h, rx: o.rx === undefined ? h / 2 : o.rx, fill: o.bg || '#fff', stroke: o.color || C.ink2, 'stroke-width': o.sw || 0.8, 'stroke-dasharray': o.dash || null });
    g.insertBefore(r, t);
    if (o.dot) {
      const cx = x + padx + 2.6, cy = y + h / 2;
      el('circle', { cx, cy, r: 2.6, fill: o.dot === 'hollow' ? '#fff' : (o.dotColor || o.color), stroke: o.dotColor || o.color, 'stroke-width': 1 }, g);
    }
    S.boxes.push({ id: 'chip' + S.boxes.length, x, y, w, h, el: r, chip: true });
    t.dataset.c = S.boxes[S.boxes.length - 1].id;
    return { w, h, g, t };
  }

  /* tier badge: [S|ZN-PM25] ; tier in S, A, N, T ; (x, y) = top-left; returns width */
  function badge(x, y, tier, id, o) {
    o = o || {};
    const TC = { S: [C.tierStd, '#fff'], A: [C.tierAdv, '#fff'], N: [C.tierNext, C.ink], T: [C.truth, C.ink] }[tier];
    const h = 13, size = o.size || 9;
    const g = el('g', { 'data-inbox': '1' }, o.parent || S.labelsL);
    const t = rich(g, x + 13 + 3.5, y + h / 2 + size * 0.34, id, { size, fill: C.ink, raw: true, family: o.sans ? null : MONO });
    const w = 13 + 7 + t.getComputedTextLength();
    el('rect', { x, y, width: w, height: h, rx: 2.5, fill: '#fff', stroke: TC[0], 'stroke-width': 0.9 }, g);
    el('path', { d: `M${x + 2.5},${y} H${x + 13} V${y + h} H${x + 2.5} Q${x},${y + h} ${x},${y + h - 2.5} V${y + 2.5} Q${x},${y} ${x + 2.5},${y} Z`, fill: TC[0] }, g);
    const lt = rich(g, x + 6.5, y + h / 2 + 3.2, tier, { size: 9, weight: 'bold', fill: TC[1], anchor: 'middle', noqc: true });
    g.appendChild(t); g.appendChild(lt);
    S.boxes.push({ id: 'badge' + S.boxes.length, x, y, w, h, chip: true });
    t.dataset.c = S.boxes[S.boxes.length - 1].id;
    return w;
  }
  // ------------------------------------------------------------------ icons (16x16 design grid)
  function icon(name, x, y, s, color, parent) {
    const g = el('g', { transform: `translate(${x},${y}) scale(${s / 16})`, fill: 'none', stroke: color, 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, parent || S.topL);
    const P = (d, a) => el('path', Object.assign({ d }, a || {}), g);
    S.icons.push({ x, y, w: s, h: s, name });
    switch (name) {
      case 'thermo': P('M6.4 9.6 V3 a1.6 1.6 0 0 1 3.2 0 V9.6 a3.1 3.1 0 1 1 -3.2 0 Z'); el('circle', { cx: 8, cy: 12.3, r: 1.3, fill: color, stroke: 'none' }, g); P('M8 11 V6'); break;
      case 'gear': {
        let d = ''; const n = 8;
        for (let i = 0; i < n * 2; i++) {
          const a0 = (i / (n * 2)) * 2 * Math.PI, a1 = ((i + 1) / (n * 2)) * 2 * Math.PI, R = i % 2 ? 5.2 : 7;
          d += (i ? 'L' : 'M') + (8 + R * Math.cos(a0)).toFixed(2) + ',' + (8 + R * Math.sin(a0)).toFixed(2) + ' L' + (8 + R * Math.cos(a1)).toFixed(2) + ',' + (8 + R * Math.sin(a1)).toFixed(2) + ' ';
        }
        P(d + 'Z', { 'stroke-width': 1.3 }); el('circle', { cx: 8, cy: 8, r: 2.1 }, g); break;
      }
      case 'valve': P('M1.5 8 L8 11.2 L1.5 14.4 Z M14.5 8 L8 11.2 L14.5 14.4 Z'); P('M8 11.2 V5.5'); P('M4.6 2 H11.4 V5.5 H4.6 Z'); break;
      case 'bolt': P('M9.3 1 L3.2 9.2 H7.6 L6.6 15 L12.8 6.6 H8.4 Z', { fill: color, stroke: 'none' }); break;
      case 'db': P('M2.5 3.8 a5.5 2.2 0 0 0 11 0 a5.5 2.2 0 0 0 -11 0 V12.2 a5.5 2.2 0 0 0 11 0 V3.8'); P('M2.5 8 a5.5 2.2 0 0 0 11 0'); break;
      case 'person': el('circle', { cx: 8, cy: 4.6, r: 2.7 }, g); P('M2.8 15 a5.2 5.2 0 0 1 10.4 0'); break;
      case 'robot': P('M3 6 H13 V13.5 H3 Z'); el('circle', { cx: 6, cy: 9.5, r: 1, fill: color, stroke: 'none' }, g); el('circle', { cx: 10, cy: 9.5, r: 1, fill: color, stroke: 'none' }, g); P('M8 6 V3'); el('circle', { cx: 8, cy: 2.2, r: 1, fill: color, stroke: 'none' }, g); P('M1 9 V11 M15 9 V11'); break;
      case 'clock': el('circle', { cx: 8, cy: 8, r: 6.5 }, g); P('M8 4.3 V8 L10.8 9.6'); break;
      case 'monitor': P('M1.5 2.5 H14.5 V11 H1.5 Z'); P('M6 14.2 H10 M8 11 V14.2'); break;
      case 'doc': P('M3.5 1.5 H9.8 L12.5 4.2 V14.5 H3.5 Z'); P('M9.8 1.5 V4.2 H12.5'); P('M5.8 7.5 H10.2 M5.8 10 H10.2 M5.8 12.4 H8.6', { 'stroke-width': 1.1 }); break;
      case 'api': P('M5.5 3 Q3 3 3 5.5 V6.6 Q3 8 1.6 8 Q3 8 3 9.4 V10.5 Q3 13 5.5 13'); P('M10.5 3 Q13 3 13 5.5 V6.6 Q13 8 14.4 8 Q13 8 13 9.4 V10.5 Q13 13 10.5 13'); break;
      case 'loop': P('M13 8 a5 5 0 1 1 -1.6 -3.7'); P('M11.8 1.6 L11.6 4.6 L8.6 4.2'); break;
      case 'cloud': P('M4.5 12.5 H12 a3 3 0 0 0 0.3 -6 a4.2 4.2 0 0 0 -8 0.8 a2.6 2.6 0 0 0 0.2 5.2 Z'); break;
      case 'dice': P('M2.5 2.5 H13.5 V13.5 H2.5 Z'); [[5.3, 5.3], [10.7, 10.7], [8, 8], [10.7, 5.3], [5.3, 10.7]].forEach(([a, b]) => el('circle', { cx: a, cy: b, r: 1, fill: color, stroke: 'none' }, g)); break;
      case 'building': P('M3 14.5 V2.5 H10 V14.5 M10 6 H13.5 V14.5 M1.5 14.5 H14.8'); P('M5.2 5 H7.8 M5.2 8 H7.8 M5.2 11 H7.8', { 'stroke-width': 1.1 }); break;
      case 'leaf': P('M3 13 C3 6 7 2.5 13.5 2.5 C13.5 9 10 13 3 13 Z'); P('M3 13 L9 7'); break;
      case 'shield': P('M8 1.5 L13.5 3.5 V8 C13.5 11.5 11 13.8 8 14.8 C5 13.8 2.5 11.5 2.5 8 V3.5 Z'); break;
      case 'cap': P('M1 6.5 L8 3 L15 6.5 L8 10 Z'); P('M4 8 V11.5 C6 13 10 13 12 11.5 V8'); P('M15 6.5 V10.5'); break;
      case 'factory': P('M1.5 14.5 V8 L5.5 5.5 V8 L9.5 5.5 V8 L13.5 5.5 V14.5 Z'); P('M11 5.5 V1.8 H13 V5.5'); break;
      case 'people': el('circle', { cx: 5.5, cy: 5, r: 2.2 }, g); el('circle', { cx: 11, cy: 5.6, r: 1.9 }, g); P('M1.2 14 a4.3 4.3 0 0 1 8.6 0'); P('M9.4 10.2 a3.8 3.8 0 0 1 5.6 3.8'); break;
      case 'chart': P('M2 14 H14.5'); P('M2 14 V2'); P('M4 11 L7 7.5 L9.5 9.5 L14 4'); break;
      case 'sun': el('circle', { cx: 8, cy: 8, r: 3 }, g); P('M8 1.2 V2.8 M8 13.2 V14.8 M1.2 8 H2.8 M13.2 8 H14.8 M3.2 3.2 L4.3 4.3 M11.7 11.7 L12.8 12.8 M3.2 12.8 L4.3 11.7 M11.7 4.3 L12.8 3.2', { 'stroke-width': 1.3 }); break;
      case 'speaker': P('M2 6 H5 L9 2.8 V13.2 L5 10 H2 Z'); P('M11.3 5.5 a3.6 3.6 0 0 1 0 5 M13.2 3.6 a6.2 6.2 0 0 1 0 8.8', { 'stroke-width': 1.2 }); break;
      case 'bulb': P('M5.4 10.5 C3.4 9 2.9 7.6 2.9 6.2 a5.1 5.1 0 0 1 10.2 0 c0 1.4 -0.5 2.8 -2.5 4.3 V12 H5.4 Z'); P('M6 14.5 H10'); break;
      case 'chat': P('M2 3 H14 V10.5 H7 L4 13.5 V10.5 H2 Z'); break;
      case 'filter': P('M2 2.5 H14 V13.5 H2 Z'); P('M4.5 2.5 L6 13.5 M8 2.5 L9.5 13.5 M11.5 2.5 L13 13.5', { 'stroke-width': 1 }); break;
      case 'fan': el('circle', { cx: 8, cy: 8, r: 6.5 }, g); P('M8 8 C8 4 10.5 3 11.5 4.5 C12.5 6 10 8 8 8 Z M8 8 C4.5 9.8 3.2 7.6 4 6.2 C4.8 4.8 7.6 6 8 8 Z M8 8 C8.4 12 6 13.2 5 11.8 C4 10.4 6.4 8.6 8 8 Z', { 'stroke-width': 1 }); break;
      default: break;
    }
    return g;
  }

  // ------------------------------------------------------------------ layout check
  function bb(e) { const b = e.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height }; }
  function inter(a, b, m) { m = m || 0; return a.x < b.x + b.w - m && b.x < a.x + a.w - m && a.y < b.y + b.h - m && b.y < a.y + a.h - m; }
  function inside(p, r, m) { m = m || 0; return p[0] > r.x + m && p[0] < r.x + r.w - m && p[1] > r.y + m && p[1] < r.y + r.h - m; }
  function check() {
    const issues = [];
    const texts = S.texts.filter(t => t.isConnected && t.textContent.trim()).map(t => ({ t, b: bb(t), s: t.textContent.slice(0, 28) }));
    for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++)
      if (inter(texts[i].b, texts[j].b, 0.6)) issues.push(`text/text: "${texts[i].s}" x "${texts[j].s}"`);
    const boxes = S.boxes.filter(b => !b.container);
    for (const T of texts) {
      if (T.b.x < 0.5 || T.b.y < 0.3 || T.b.x + T.b.w > S.w - 0.5 || T.b.y + T.b.h > S.h - 0.3) issues.push(`bounds: "${T.s}"`);
      for (const I of S.icons) if (inter(T.b, I, 0.2)) issues.push(`text/icon: "${T.s}" x ${I.name}`);
      const own = T.t.dataset.c;
      for (const B of boxes) {
        if (B.id === own) {
          if (T.b.x < B.x + 1.5 || T.b.x + T.b.w > B.x + B.w - 1.5 || T.b.y < B.y + 0.5 || T.b.y + T.b.h > B.y + B.h - 0.5)
            issues.push(`overflow: "${T.s}" in ${B.id} by ${Math.max(B.x + 1.5 - T.b.x, T.b.x + T.b.w - B.x - B.w + 1.5).toFixed(1)}px`);
        } else if (inter(T.b, B, 0.4)) {
          const fullyIn = T.b.x >= B.x && T.b.x + T.b.w <= B.x + B.w && T.b.y >= B.y && T.b.y + T.b.h <= B.y + B.h;
          if (!(fullyIn && B.allowInner) && !(fullyIn && T.t.closest('[data-inbox]')) && !T.t.closest('[data-tab]')) issues.push(`text/box: "${T.s}" x ${B.id}${B.chip ? '(chip)' : ''}`);
        }
      }
    }
    for (const Cn of S.conns) {
      const p = Cn.el, L = p.getTotalLength();
      const hitT = new Set(), hitB = new Set();
      for (let s = 2.5; s < L - 2.5; s += 0.8) {
        const q = p.getPointAtLength(s), pt = [q.x, q.y];
        for (const T of texts) if (!hitT.has(T) && inside(pt, T.b, 0.4)) { hitT.add(T); issues.push(`conn/text: "${T.s}"`); }
        for (const B of boxes) if (!hitB.has(B) && !Cn.ignore.includes(B.id) && inside(pt, B, 1.2)) { hitB.add(B); issues.push(`conn/box: ${B.id} at ${pt.map(v => v.toFixed(0))}`); }
        if (pt[0] < 0 || pt[1] < 0 || pt[0] > S.w || pt[1] > S.h) { issues.push('conn out of bounds'); break; }
      }
    }
    return issues;
  }
  function finish() {
    const issues = check();
    window.qc = issues;
    if (issues.length) console.warn('QC issues:\n' + issues.join('\n')); else console.log('QC ok');
    window.figReady = true;
  }

  window.D = { C, el, init, rich, text, width, conn, pill, rect, panel, card, chip, badge, icon, marker, finish, check, get S() { return S; }, FONT, MONO };
})();
