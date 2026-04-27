// ─── Config ───────────────────────────────────────────────────────────────────
const CONFIG = {
  cardWidth: 220,
  rowHeight: 22,
  headerHeight: 32,
  gridCols: 7,
  gridGapX: 60,
  gridGapY: 50,
};

// ─── State ────────────────────────────────────────────────────────────────────
let tables    = {};
let relations = [];
let pan       = { x: 0, y: 0 };
let zoom      = 1;
let dragging  = null;
let connStyle = 'elbow';
let showLabels = true;
let fkOnly    = false;

const viewport = document.getElementById('viewport');
const canvas   = document.getElementById('canvas');
const svgLayer = document.getElementById('connector-layer');
const tooltip  = document.getElementById('tooltip');
const minimap  = document.getElementById('minimap');
const mmCtx    = minimap.getContext('2d');

// ─── MMD Parser ───────────────────────────────────────────────────────────────
function parseMmd(text) {
  const tbls = {}, rels = [];
  let current = null;
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('erDiagram') || line.startsWith('%%')) continue;
    const relMatch = line.match(/^(\w+)\s+[}|o]{1,3}--[|o{]{1,3}\s+(\w+)\s*:\s*"([^"]*)"/);
    if (relMatch) { rels.push({ from: relMatch[1], to: relMatch[2], label: relMatch[3] }); continue; }
    const openMatch = line.match(/^(\w+)\s*\{/);
    if (openMatch) { current = openMatch[1]; if (!tbls[current]) tbls[current] = { columns: [] }; continue; }
    if (line === '}') { current = null; continue; }
    if (current) {
      const parts = line.split(/\s+/);
      if (parts.length >= 2) {
        const flags = parts.slice(2).join(' ');
        tbls[current].columns.push({
          type: parts[0], name: parts[1],
          isPK: /\bPK\b/.test(flags), isFK: /\bFK\b/.test(flags), isUQ: /\bUQ\b/.test(flags),
        });
      }
    }
  }
  return { tbls, rels };
}

// ─── Layout ───────────────────────────────────────────────────────────────────
function tableW(name) {
  const t = tables[name];
  return (t.el ? t.el.offsetWidth : null) || CONFIG.cardWidth;
}

function tableH(name) {
  const t = tables[name];
  return (t.el ? t.el.offsetHeight : null) || (CONFIG.headerHeight + t.columns.length * CONFIG.rowHeight + 8);
}

function autoLayout(names) {
  const PAD = 80;

  const cols = Math.ceil(Math.sqrt(names.length * 1.6));
  names.forEach((name, i) => {
    const w = tableW(name), h = tableH(name);
    tables[name].x = (i % cols) * (w + 300) + 60 + (Math.random() - 0.5) * 80;
    tables[name].y = Math.floor(i / cols) * (h + 240) + 60 + (Math.random() - 0.5) * 80;
  });

  const adj = {};
  names.forEach(n => { adj[n] = new Set(); });
  relations.forEach(r => {
    if (adj[r.from] && adj[r.to]) { adj[r.from].add(r.to); adj[r.to].add(r.from); }
  });

  const siblingPairs = [];
  names.forEach(hub => {
    const nb = [...(adj[hub] || [])];
    for (let i = 0; i < nb.length; i++)
      for (let j = i + 1; j < nb.length; j++)
        siblingPairs.push([nb[i], nb[j]]);
  });

  const IDEAL = 600, REPEL = 350, ITER = 400, COOL = 0.975;
  let temp = 250;

  for (let iter = 0; iter < ITER; iter++) {
    const force = {};
    names.forEach(n => { force[n] = { x: 0, y: 0 }; });

    for (let i = 0; i < names.length; i++) {
      for (let j = i + 1; j < names.length; j++) {
        const na = names[i], nb = names[j];
        const ta = tables[na], tb = tables[nb];
        const wa = tableW(na), ha = tableH(na);
        const wb = tableW(nb), hb = tableH(nb);
        const ax = ta.x+wa/2, ay = ta.y+ha/2;
        const bx = tb.x+wb/2, by = tb.y+hb/2;
        const dx = ax-bx, dy = ay-by;
        const dist = Math.hypot(dx, dy) || 1;
        const degA = (adj[na]?.size||0)+1, degB = (adj[nb]?.size||0)+1;
        const rs = REPEL * Math.sqrt(degA * degB);
        const overlapX = (wa+wb)/2+PAD - Math.abs(dx);
        const overlapY = (ha+hb)/2+PAD - Math.abs(dy);
        const f = (overlapX>0&&overlapY>0) ? rs*4/dist : rs*rs/(dist*dist);
        force[na].x+=(dx/dist)*f; force[na].y+=(dy/dist)*f;
        force[nb].x-=(dx/dist)*f; force[nb].y-=(dy/dist)*f;
      }
    }

    relations.forEach(r => {
      if (!tables[r.from]||!tables[r.to]) return;
      const ta=tables[r.from], tb=tables[r.to];
      const wa=tableW(r.from), ha=tableH(r.from);
      const wb=tableW(r.to),   hb=tableH(r.to);
      const dx=(tb.x+wb/2)-(ta.x+wa/2), dy=(tb.y+hb/2)-(ta.y+ha/2);
      const dist=Math.hypot(dx,dy)||1;
      const ideal=IDEAL+((adj[r.from]?.size||1)+(adj[r.to]?.size||1))*40;
      const f=(dist-ideal)*0.1;
      force[r.from].x+=(dx/dist)*f; force[r.from].y+=(dy/dist)*f;
      force[r.to].x  -=(dx/dist)*f; force[r.to].y  -=(dy/dist)*f;
    });

    siblingPairs.forEach(([na,nb]) => {
      if (!tables[na]||!tables[nb]) return;
      const ta=tables[na], tb=tables[nb];
      const wa=tableW(na), ha=tableH(na), wb=tableW(nb), hb=tableH(nb);
      const acx=ta.x+wa/2, acy=ta.y+ha/2, bcx=tb.x+wb/2, bcy=tb.y+hb/2;
      const TOL=100;
      if (Math.abs(acy-bcy)<TOL) { const s=(TOL-Math.abs(acy-bcy))*0.8, sg=acy>=bcy?1:-1; force[na].y+=sg*s; force[nb].y-=sg*s; }
      if (Math.abs(acx-bcx)<TOL) { const s=(TOL-Math.abs(acx-bcx))*0.8, sg=acx>=bcx?1:-1; force[na].x+=sg*s; force[nb].x-=sg*s; }
    });

    if (iter%5===0) {
      relations.forEach(rel => {
        if (!tables[rel.from]||!tables[rel.to]) return;
        const ta=tables[rel.from], tb=tables[rel.to];
        const wa=tableW(rel.from), ha=tableH(rel.from), wb=tableW(rel.to), hb=tableH(rel.to);
        const ra={x:ta.x,y:ta.y,w:wa,h:ha,cx:ta.x+wa/2,cy:ta.y+ha/2};
        const rb={x:tb.x,y:tb.y,w:wb,h:hb,cx:tb.x+wb/2,cy:tb.y+hb/2};
        const {p1,p2}=bestPorts(ra,rb);
        const samples=wireSamples(p1,p2,16);
        const M=30;
        names.forEach(name => {
          if (name===rel.from||name===rel.to) return;
          const t=tables[name], w=tableW(name), h=tableH(name);
          if (!samples.some(pt=>pt.x>=t.x-M&&pt.x<=t.x+w+M&&pt.y>=t.y-M&&pt.y<=t.y+h+M)) return;
          const cx=t.x+w/2, cy=t.y+h/2, mx=(p1.x+p2.x)/2, my=(p1.y+p2.y)/2;
          const fx=cx-mx, fy=cy-my, mag=Math.hypot(fx,fy)||1;
          force[name].x+=(fx/mag)*200+15; force[name].y+=(fy/mag)*200+15;
        });
      });
    }

    names.forEach(name => {
      const f=force[name], mag=Math.hypot(f.x,f.y)||1, c=Math.min(mag,temp);
      tables[name].x=Math.max(0,tables[name].x+(f.x/mag)*c);
      tables[name].y=Math.max(0,tables[name].y+(f.y/mag)*c);
    });
    temp*=COOL;
  }

  resolveOverlaps(names, PAD);
}

// Sample points along all three wire styles between two ports
function wireSamples(p1, p2, steps) {
  const pts = [];
  const mx = (p1.x + p2.x) / 2;
  // straight
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    pts.push({ x: p1.x + (p2.x-p1.x)*t, y: p1.y + (p2.y-p1.y)*t });
  }
  // curve (cubic bezier)
  for (let i = 0; i <= steps; i++) {
    const t = i / steps, mt = 1 - t;
    pts.push({
      x: mt*mt*mt*p1.x + 3*mt*mt*t*mx + 3*mt*t*t*mx + t*t*t*p2.x,
      y: mt*mt*mt*p1.y + 3*mt*mt*t*p1.y + 3*mt*t*t*p2.y + t*t*t*p2.y,
    });
  }
  // elbow
  [[p1, {x:mx,y:p1.y}], [{x:mx,y:p1.y},{x:mx,y:p2.y}], [{x:mx,y:p2.y},p2]].forEach(([a,b]) => {
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      pts.push({ x: a.x+(b.x-a.x)*t, y: a.y+(b.y-a.y)*t });
    }
  });
  return pts;
}

function resolveOverlaps(names, pad) {
  let changed = true, passes = 0;
  while (changed && passes++ < 60) {
    changed = false;
    for (let i = 0; i < names.length; i++) {
      for (let j = i + 1; j < names.length; j++) {
        const a = tables[names[i]], b = tables[names[j]];
        const wa = tableW(names[i]), ha = tableH(names[i]);
        const wb = tableW(names[j]), hb = tableH(names[j]);
        const acx = a.x+wa/2, acy = a.y+ha/2;
        const bcx = b.x+wb/2, bcy = b.y+hb/2;
        const overlapX = (wa+wb)/2 + pad - Math.abs(acx-bcx);
        const overlapY = (ha+hb)/2 + pad - Math.abs(acy-bcy);
        if (overlapX > 0 && overlapY > 0) {
          const pushX = (overlapX/2+1) * (acx>=bcx?1:-1);
          const pushY = (overlapY/2+1) * (acy>=bcy?1:-1);
          a.x=Math.max(0,a.x+pushX*0.5); a.y=Math.max(0,a.y+pushY*0.5);
          b.x=Math.max(0,b.x-pushX*0.5); b.y=Math.max(0,b.y-pushY*0.5);
          changed = true;
        }
      }
    }
  }
}

// ─── Card Builder ─────────────────────────────────────────────────────────────
function buildCard(name, data) {
  const card = document.createElement('div');
  card.className = 'erd-table';
  card.dataset.table = name;
  const hdr = document.createElement('div');
  hdr.className = 'erd-table-header';
  hdr.textContent = name;
  card.appendChild(hdr);
  const body = document.createElement('div');
  body.className = 'erd-table-body';
  data.columns.forEach(col => {
    const row = document.createElement('div');
    row.className = 'erd-col';
    const badge = document.createElement('span');
    badge.className = 'erd-badge' + (col.isPK ? ' pk' : col.isFK ? ' fk' : col.isUQ ? ' uq' : '');
    badge.textContent = col.isPK ? 'PK' : col.isFK ? 'FK' : col.isUQ ? 'UQ' : '';
    row.appendChild(badge);
    const nm = document.createElement('span');
    nm.className = 'erd-col-name';
    nm.textContent = col.name;
    row.appendChild(nm);
    const tp = document.createElement('span');
    tp.className = 'erd-col-type';
    tp.textContent = col.type;
    row.appendChild(tp);
    body.appendChild(row);
  });
  card.appendChild(body);
  return card;
}

// ─── Render Tables ────────────────────────────────────────────────────────────
function renderTables() {
  canvas.innerHTML = '';
  Object.entries(tables).forEach(([name, data]) => {
    const card = buildCard(name, data);
    card.style.left = data.x + 'px';
    card.style.top  = data.y + 'px';
    canvas.appendChild(card);
    data.el = card;
    makeDraggable(card, name);
  });
}

// ─── Connector Math ───────────────────────────────────────────────────────────
function cardRect(name) {
  const t = tables[name];
  if (!t || !t.el) return null;
  const w = t.el.offsetWidth  || CONFIG.cardWidth;
  const h = t.el.offsetHeight || (CONFIG.headerHeight + t.columns.length * CONFIG.rowHeight + 8);
  return { x: t.x, y: t.y, w, h, cx: t.x + w/2, cy: t.y + h/2 };
}

function bestPorts(a, b) {
  const dx = b.cx - a.cx, dy = b.cy - a.cy;
  let p1, p2;
  if (Math.abs(dx) >= Math.abs(dy)) {
    p1 = dx > 0 ? { x: a.x+a.w, y: a.cy } : { x: a.x, y: a.cy };
    p2 = dx > 0 ? { x: b.x,     y: b.cy } : { x: b.x+b.w, y: b.cy };
  } else {
    p1 = dy > 0 ? { x: a.cx, y: a.y+a.h } : { x: a.cx, y: a.y };
    p2 = dy > 0 ? { x: b.cx, y: b.y }     : { x: b.cx, y: b.y+b.h };
  }
  return { p1, p2 };
}

function pathData(p1, p2) {
  if (connStyle === 'straight') return `M${p1.x},${p1.y} L${p2.x},${p2.y}`;
  if (connStyle === 'curve') {
    const mx = (p1.x + p2.x) / 2;
    return `M${p1.x},${p1.y} C${mx},${p1.y} ${mx},${p2.y} ${p2.x},${p2.y}`;
  }
  const mx = (p1.x + p2.x) / 2;
  return `M${p1.x},${p1.y} L${mx},${p1.y} L${mx},${p2.y} L${p2.x},${p2.y}`;
}

// ─── Draw Connectors ──────────────────────────────────────────────────────────
function drawConnectors() {
  svgLayer.innerHTML = '';
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = `
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="var(--conn)"/>
    </marker>
    <marker id="dot-start" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
      <circle cx="3" cy="3" r="2.2" fill="none" stroke="var(--conn)" stroke-width="1.2"/>
    </marker>`;
  svgLayer.appendChild(defs);
  const visible = fkOnly
    ? relations.filter(r => tables[r.from] && tables[r.from].columns.some(c => c.isFK && c.name === r.label))
    : relations;
  visible.forEach(rel => {
    const a = cardRect(rel.from), b = cardRect(rel.to);
    if (!a || !b) return;
    const { p1, p2 } = bestPorts(a, b);
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.classList.add('conn-group');
    const hit = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    hit.setAttribute('d', pathData(p1, p2));
    hit.classList.add('conn-hit');
    hit.addEventListener('mouseenter', e => showTooltip(e, rel.label));
    hit.addEventListener('mouseleave', hideTooltip);
    g.appendChild(hit);
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData(p1, p2));
    path.classList.add('conn-line');
    path.setAttribute('marker-end', 'url(#arrow)');
    path.setAttribute('marker-start', 'url(#dot-start)');
    g.appendChild(path);
    if (showLabels && rel.label) {
      const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      txt.setAttribute('x', (p1.x + p2.x) / 2);
      txt.setAttribute('y', (p1.y + p2.y) / 2 - 4);
      txt.classList.add('conn-label');
      txt.textContent = rel.label;
      g.appendChild(txt);
    }
    svgLayer.appendChild(g);
  });
}

// ─── Tooltip ──────────────────────────────────────────────────────────────────
function showTooltip(e, text) { tooltip.textContent = text; tooltip.style.display = 'block'; moveTooltip(e); }
function moveTooltip(e) { tooltip.style.left = (e.clientX+12)+'px'; tooltip.style.top = (e.clientY+12)+'px'; }
function hideTooltip() { tooltip.style.display = 'none'; }
document.addEventListener('mousemove', e => { if (tooltip.style.display !== 'none') moveTooltip(e); });

// ─── Drag tables (mouse only, header) ────────────────────────────────────────
function makeDraggable(el, name) {
  const hdr = el.querySelector('.erd-table-header');
  hdr.addEventListener('mousedown', e => {
    e.preventDefault();
    e.stopPropagation();
    dragging = { el, name, ox: e.clientX - tables[name].x * zoom, oy: e.clientY - tables[name].y * zoom };
    el.classList.add('dragging');
  });
}

document.addEventListener('mousemove', e => {
  if (!dragging) return;
  tables[dragging.name].x = (e.clientX - dragging.ox) / zoom;
  tables[dragging.name].y = (e.clientY - dragging.oy) / zoom;
  dragging.el.style.left = tables[dragging.name].x + 'px';
  dragging.el.style.top  = tables[dragging.name].y + 'px';
  drawConnectors(); drawMinimap();
});

document.addEventListener('mouseup', () => {
  if (dragging) { dragging.el.classList.remove('dragging'); dragging = null; }
});

// ─── Pan canvas (mouse drag on background) ───────────────────────────────────
let isPanning = false, panStart = { x: 0, y: 0 };

viewport.addEventListener('mousedown', e => {
  if (dragging) return;
  if (e.target.closest('.erd-table')) return;
  isPanning = true;
  panStart = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  viewport.style.cursor = 'grabbing';
});

document.addEventListener('mousemove', e => {
  if (!isPanning) return;
  pan.x = e.clientX - panStart.x;
  pan.y = e.clientY - panStart.y;
  applyTransform();
});

document.addEventListener('mouseup', () => {
  isPanning = false;
  viewport.style.cursor = '';
});

// ─── Wheel: trackpad two-finger scroll = pan, pinch (ctrlKey) = zoom ─────────
viewport.addEventListener('wheel', e => {
  if (e.target.closest('.erd-table')) return; // let table body scroll natively
  e.preventDefault();
  if (e.ctrlKey) {
    // pinch-to-zoom — anchor to viewport center
    const factor = e.deltaY > 0 ? 0.95 : 1.05;
    const newZoom = Math.min(2, Math.max(0.2, zoom * factor));
    const cx = viewport.clientWidth  / 2;
    const cy = viewport.clientHeight / 2;
    pan.x = cx - (cx - pan.x) * (newZoom / zoom);
    pan.y = cy - (cy - pan.y) * (newZoom / zoom);
    zoom = newZoom;
    document.getElementById('zoom-slider').value = Math.round(zoom * 100);
    document.getElementById('zoom-label').textContent = Math.round(zoom * 100) + '%';
  } else {
    // two-finger scroll — pan both axes
    pan.x -= e.deltaX;
    pan.y -= e.deltaY;
  }
  applyTransform();
}, { passive: false });

document.getElementById('zoom-slider').addEventListener('input', e => {
  const newZoom = e.target.value / 100;
  const rect = viewport.getBoundingClientRect();
  const mx = rect.width / 2, my = rect.height / 2;
  pan.x = mx - (mx - pan.x) * (newZoom / zoom);
  pan.y = my - (my - pan.y) * (newZoom / zoom);
  zoom = newZoom;
  document.getElementById('zoom-label').textContent = e.target.value + '%';
  applyTransform();
});

// ─── Transform ────────────────────────────────────────────────────────────────
function applyTransform() {
  const t = `translate(${pan.x}px,${pan.y}px) scale(${zoom})`;
  canvas.style.transform = t;
  svgLayer.style.transform = t;
  drawMinimap();
}

// ─── Fit to Screen ────────────────────────────────────────────────────────────
function fitToScreen() {
  if (!Object.keys(tables).length) return;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  Object.entries(tables).forEach(([name, t]) => {
    const w = t.el ? t.el.offsetWidth  : CONFIG.cardWidth;
    const h = t.el ? t.el.offsetHeight : (CONFIG.headerHeight + t.columns.length * CONFIG.rowHeight + 8);
    minX = Math.min(minX, t.x); minY = Math.min(minY, t.y);
    maxX = Math.max(maxX, t.x + w);    maxY = Math.max(maxY, t.y + h);
  });
  const vw = viewport.clientWidth, vh = viewport.clientHeight;
  zoom = Math.min(vw / (maxX - minX + 80), vh / (maxY - minY + 80), 1);
  pan.x = (vw - (maxX - minX) * zoom) / 2 - minX * zoom;
  pan.y = (vh - (maxY - minY) * zoom) / 2 - minY * zoom;
  document.getElementById('zoom-slider').value = Math.round(zoom * 100);
  document.getElementById('zoom-label').textContent = Math.round(zoom * 100) + '%';
  applyTransform();
}

document.getElementById('btn-fit').addEventListener('click', fitToScreen);
document.getElementById('btn-reset').addEventListener('click', () => {
  zoom = 1; pan = { x: 0, y: 0 };
  document.getElementById('zoom-slider').value = 100;
  document.getElementById('zoom-label').textContent = '100%';
  applyTransform();
});

// ─── Controls ─────────────────────────────────────────────────────────────────
document.getElementById('conn-style').addEventListener('change', e => { connStyle = e.target.value; drawConnectors(); });
document.getElementById('show-labels').addEventListener('change', e => { showLabels = e.target.checked; drawConnectors(); });
document.getElementById('show-fk-only').addEventListener('change', e => { fkOnly = e.target.checked; drawConnectors(); });
document.getElementById('theme-select').addEventListener('change', e => { document.body.dataset.theme = e.target.value; });

// ─── Minimap ──────────────────────────────────────────────────────────────────
function drawMinimap() {
  const W = minimap.width = 160, H = minimap.height = 100;
  mmCtx.clearRect(0, 0, W, H);
  if (!Object.keys(tables).length) return;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  Object.values(tables).forEach(t => {
    const h = t.el ? t.el.offsetHeight : 100;
    minX = Math.min(minX, t.x); minY = Math.min(minY, t.y);
    maxX = Math.max(maxX, t.x + (t.el?t.el.offsetWidth:CONFIG.cardWidth));
    maxY = Math.max(maxY, t.y + h);
  });
  const s = Math.min((W-8)/(maxX-minX+1), (H-8)/(maxY-minY+1));
  mmCtx.fillStyle = 'rgba(100,140,200,0.25)';
  Object.values(tables).forEach(t => {
    const w = t.el ? t.el.offsetWidth  : CONFIG.cardWidth;
    const h = t.el ? t.el.offsetHeight : 100;
    mmCtx.fillRect((t.x-minX)*s+4, (t.y-minY)*s+4, w*s, h*s);
  });
  const vw = viewport.clientWidth, vh = viewport.clientHeight;
  mmCtx.strokeStyle = 'rgba(0,120,255,0.8)';
  mmCtx.lineWidth = 1.5;
  mmCtx.strokeRect((-pan.x/zoom-minX)*s+4, (-pan.y/zoom-minY)*s+4, (vw/zoom)*s, (vh/zoom)*s);
}

// ─── Init ─────────────────────────────────────────────────────────────────────
function loadMmd(text) {
  const { tbls, rels } = parseMmd(text);
  tables = {};
  Object.entries(tbls).forEach(([name, data]) => { tables[name] = { ...data, x: 0, y: 0, el: null }; });
  relations = rels;

  // Infer FK flags from relations — label matches a column name in the source table
  relations.forEach(rel => {
    const t = tables[rel.from];
    if (!t) return;
    const col = t.columns.find(c => c.name === rel.label);
    if (col) col.isFK = true;
  });

  renderTables();
  requestAnimationFrame(() => requestAnimationFrame(() => {
    autoLayout(Object.keys(tables));
    Object.entries(tables).forEach(([, t]) => {
      t.el.style.left = t.x + 'px';
      t.el.style.top  = t.y + 'px';
    });
    drawConnectors();
    fitToScreen();
    drawMinimap();
  }));
}

fetch('./db_schema.mmd')
  .then(r => r.text())
  .then(loadMmd)
  .catch(err => {
    canvas.innerHTML = '<p style="padding:20px;color:#c00">Could not load db_schema.mmd. Run serve.cmd to open with a local server.</p>';
    console.error(err);
  });
