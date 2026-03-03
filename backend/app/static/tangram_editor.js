/**
 * Tangram Puzzle Editor — admin tool for creating / editing puzzles.
 * Pieces are dragged on an SVG canvas; their final positions become the
 * targetPose values saved in the puzzle JSON.
 */

/* ── State ─────────────────────────────────────────────────────── */
let _puzzle = null;       // full puzzle JSON currently being edited
let _pieces = [];         // runtime piece state
let _selectedIdx = -1;
let _dragging = false;
let _dragOffset = { x: 0, y: 0 };
let _svg = null;
const _svgNS = 'http://www.w3.org/2000/svg';

/* ── Constants ─────────────────────────────────────────────────── */
const BOARD = { width: 400, height: 420 };
const TRAY  = { x: 0, y: 300, w: 400, h: 120 };
const PLAY  = { x: 50, y: 10, w: 300, h: 280 };
const ROT_STEP = 15;

const PIECE_LABELS = {
  big_tri_1:     '🔴 Big Triangle 1',
  big_tri_2:     '🟠 Big Triangle 2',
  med_tri:       '🟢 Medium Triangle',
  small_tri_1:   '🔵 Small Triangle 1',
  small_tri_2:   '🟣 Small Triangle 2',
  square:        '🩷 Square',
  parallelogram: '🩵 Parallelogram',
};

/* ── Helpers ───────────────────────────────────────────────────── */
function polyToPoints(verts) {
  return verts.map(v => v[0] + ',' + v[1]).join(' ');
}

function polyCentroid(verts) {
  let cx = 0, cy = 0;
  verts.forEach(v => { cx += v[0]; cy += v[1]; });
  return { x: cx / verts.length, y: cy / verts.length };
}

function svgTf(x, y, rot, flipped) {
  let tf = 'translate(' + x + ',' + y + ') rotate(' + rot + ')';
  if (flipped) {
    // Mirror horizontally around the polygon origin (we flip the <g> contents)
    // We apply scaleX(-1) with the centroid offset handled in the polygon points
    tf += ' scale(-1,1)';
  }
  return tf;
}

function setStatus(msg, isError) {
  const el = document.getElementById('te-status');
  if (!el) return;
  el.textContent = msg;
  el.style.color = isError ? '#ef4444' : '#10b981';
  setTimeout(() => { if (el.textContent === msg) el.textContent = ''; }, 4000);
}

/* ── Draw / init SVG ──────────────────────────────────────────── */
function teRender() {
  const wrap = document.getElementById('te-canvas');
  wrap.innerHTML = '';

  const svg = document.createElementNS(_svgNS, 'svg');
  svg.setAttribute('viewBox', '0 0 ' + BOARD.width + ' ' + BOARD.height);
  svg.setAttribute('width', '100%');
  svg.style.display = 'block';
  svg.style.borderRadius = '0.75rem';
  svg.style.background = 'rgba(88,28,135,0.3)';
  svg.style.border = '2px solid rgba(139,92,246,0.3)';
  svg.style.touchAction = 'none';
  svg.style.userSelect = 'none';
  wrap.appendChild(svg);
  _svg = svg;

  // Play area
  const pr = document.createElementNS(_svgNS, 'rect');
  pr.setAttribute('x', PLAY.x); pr.setAttribute('y', PLAY.y);
  pr.setAttribute('width', PLAY.w); pr.setAttribute('height', PLAY.h);
  pr.setAttribute('fill', 'rgba(139,92,246,0.08)');
  pr.setAttribute('stroke', 'rgba(139,92,246,0.2)');
  pr.setAttribute('stroke-width', '1');
  pr.setAttribute('stroke-dasharray', '4,4');
  pr.setAttribute('rx', '8');
  svg.appendChild(pr);

  // Tray area
  const tr = document.createElementNS(_svgNS, 'rect');
  tr.setAttribute('x', TRAY.x); tr.setAttribute('y', TRAY.y);
  tr.setAttribute('width', TRAY.w); tr.setAttribute('height', TRAY.h);
  tr.setAttribute('fill', 'rgba(88,28,135,0.25)');
  tr.setAttribute('stroke', 'rgba(139,92,246,0.15)');
  tr.setAttribute('stroke-width', '1');
  tr.setAttribute('rx', '8');
  svg.appendChild(tr);

  // Pieces
  _pieces.forEach((p, idx) => {
    const g = document.createElementNS(_svgNS, 'g');
    g.style.cursor = 'grab';
    g.dataset.idx = idx;

    const poly = document.createElementNS(_svgNS, 'polygon');
    poly.setAttribute('points', polyToPoints(p.polygon));
    poly.setAttribute('fill', p.color);
    poly.setAttribute('stroke', '#fff');
    poly.setAttribute('stroke-width', '1.5');
    poly.setAttribute('stroke-linejoin', 'round');
    g.appendChild(poly);

    g.setAttribute('transform', svgTf(p.x, p.y, p.rotation, p.flipped));
    svg.appendChild(g);
    p.el = g;
  });

  // Pointer events
  svg.addEventListener('mousedown', onDown);
  svg.addEventListener('mousemove', onMove);
  svg.addEventListener('mouseup', onUp);
  svg.addEventListener('mouseleave', onUp);
  svg.addEventListener('touchstart', onDown, { passive: false });
  svg.addEventListener('touchmove', onMove, { passive: false });
  svg.addEventListener('touchend', onUp);

  // Piece list sidebar
  renderPieceList();
  selectPiece(-1);
}

function renderPieceList() {
  const list = document.getElementById('te-piece-list');
  if (!list) return;
  list.innerHTML = '';
  _pieces.forEach((p, idx) => {
    const div = document.createElement('div');
    div.className = 'flex items-center gap-2 px-2 py-1 rounded cursor-pointer hover:bg-realm-purple-700/40';
    div.id = 'te-pl-' + idx;

    const swatch = document.createElement('span');
    swatch.style.display = 'inline-block';
    swatch.style.width = '14px';
    swatch.style.height = '14px';
    swatch.style.borderRadius = '3px';
    swatch.style.background = p.color;
    div.appendChild(swatch);

    const label = document.createElement('span');
    label.className = 'text-sm text-realm-purple-200';
    label.textContent = PIECE_LABELS[p.id] || p.id;
    div.appendChild(label);

    const pos = document.createElement('span');
    pos.className = 'text-xs text-realm-purple-400 ml-auto';
    pos.textContent = Math.round(p.x) + ',' + Math.round(p.y) + ' ' + p.rotation + '°';
    pos.id = 'te-pos-' + idx;
    div.appendChild(pos);

    div.addEventListener('click', () => selectPiece(idx));
    list.appendChild(div);
  });
}

function updatePiecePos(idx) {
  const pos = document.getElementById('te-pos-' + idx);
  const p = _pieces[idx];
  let txt = Math.round(p.x) + ',' + Math.round(p.y) + ' ' + p.rotation + '°';
  if (p.flipped) txt += ' ↔';
  if (pos) pos.textContent = txt;
}

/* ── Selection ─────────────────────────────────────────────────── */
function selectPiece(idx) {
  // Deselect old
  if (_selectedIdx >= 0 && _pieces[_selectedIdx] && _pieces[_selectedIdx].el) {
    _pieces[_selectedIdx].el.querySelector('polygon').setAttribute('stroke', '#fff');
    const old = document.getElementById('te-pl-' + _selectedIdx);
    if (old) old.classList.remove('bg-realm-purple-700/60');
  }
  _selectedIdx = idx;
  const info = document.getElementById('te-piece-info');
  if (idx >= 0) {
    _svg.appendChild(_pieces[idx].el);  // bring to front
    _pieces[idx].el.querySelector('polygon').setAttribute('stroke', '#fbbf24');
    if (info) info.textContent = (PIECE_LABELS[_pieces[idx].id] || _pieces[idx].id) + '  (' + Math.round(_pieces[idx].x) + ',' + Math.round(_pieces[idx].y) + ' ' + _pieces[idx].rotation + '°)';
    const plEl = document.getElementById('te-pl-' + idx);
    if (plEl) plEl.classList.add('bg-realm-purple-700/60');
  } else {
    if (info) info.textContent = 'Select a piece';
  }
}

/* ── Pointer events ────────────────────────────────────────────── */
function svgPt(e) {
  const pt = _svg.createSVGPoint();
  const t = e.touches ? e.touches[0] : e;
  pt.x = t.clientX;
  pt.y = t.clientY;
  return pt.matrixTransform(_svg.getScreenCTM().inverse());
}

function onDown(e) {
  const target = e.target.closest('g[data-idx]');
  if (!target) { selectPiece(-1); return; }
  const idx = parseInt(target.dataset.idx);
  e.preventDefault();
  selectPiece(idx);
  _dragging = true;
  const pt = svgPt(e);
  _dragOffset.x = pt.x - _pieces[idx].x;
  _dragOffset.y = pt.y - _pieces[idx].y;
  target.style.cursor = 'grabbing';
}

function onMove(e) {
  if (!_dragging || _selectedIdx < 0) return;
  e.preventDefault();
  const p = _pieces[_selectedIdx];
  const pt = svgPt(e);
  p.x = pt.x - _dragOffset.x;
  p.y = pt.y - _dragOffset.y;
  p.el.setAttribute('transform', svgTf(p.x, p.y, p.rotation, p.flipped));
  updatePiecePos(_selectedIdx);
  selectPiece(_selectedIdx);  // refresh info text
}

function onUp() {
  if (!_dragging || _selectedIdx < 0) return;
  _dragging = false;
  _pieces[_selectedIdx].el.style.cursor = 'grab';
}

/* ── Rotation ──────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('te-rot-ccw').addEventListener('click', () => {
    if (_selectedIdx < 0) return;
    const p = _pieces[_selectedIdx];
    p.rotation = (p.rotation - ROT_STEP + 360) % 360;
    p.el.setAttribute('transform', svgTf(p.x, p.y, p.rotation, p.flipped));
    updatePiecePos(_selectedIdx);
    selectPiece(_selectedIdx);
  });
  document.getElementById('te-rot-cw').addEventListener('click', () => {
    if (_selectedIdx < 0) return;
    const p = _pieces[_selectedIdx];
    p.rotation = (p.rotation + ROT_STEP) % 360;
    p.el.setAttribute('transform', svgTf(p.x, p.y, p.rotation, p.flipped));
    updatePiecePos(_selectedIdx);
    selectPiece(_selectedIdx);
  });
  document.getElementById('te-flip').addEventListener('click', () => {
    if (_selectedIdx < 0) return;
    const p = _pieces[_selectedIdx];
    p.flipped = !p.flipped;
    p.el.setAttribute('transform', svgTf(p.x, p.y, p.rotation, p.flipped));
    updatePiecePos(_selectedIdx);
    selectPiece(_selectedIdx);
  });

  document.getElementById('te-centre').addEventListener('click', () => {
    if (!_pieces.length) return;
    // Compute bounding box of all pieces in world coordinates
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    _pieces.forEach(p => {
      const rad = p.rotation * Math.PI / 180;
      const cosR = Math.cos(rad), sinR = Math.sin(rad);
      p.polygon.forEach(v => {
        let vx = v[0], vy = v[1];
        if (p.flipped) vx = -vx;
        const wx = vx * cosR - vy * sinR + p.x;
        const wy = vx * sinR + vy * cosR + p.y;
        if (wx < minX) minX = wx;
        if (wy < minY) minY = wy;
        if (wx > maxX) maxX = wx;
        if (wy > maxY) maxY = wy;
      });
    });
    // Calculate offset to centre the bounding box within the PLAY area
    const bw = maxX - minX, bh = maxY - minY;
    const cx = PLAY.x + (PLAY.w - bw) / 2;
    const cy = PLAY.y + (PLAY.h - bh) / 2;
    const dx = cx - minX, dy = cy - minY;
    // Shift all pieces
    _pieces.forEach(p => {
      p.x += dx;
      p.y += dy;
    });
    teRender();
    setStatus('Pieces centred in play area ✓');
  });
});

/* ── Load / New / Save / Delete ────────────────────────────────── */

function teLoad() {
  const sel = document.getElementById('te-puzzle-select');
  const pid = sel.value;
  if (!pid) return;

  fetch('/api/tangram/puzzle/' + pid)
    .then(r => { if (!r.ok) throw new Error('not found'); return r.json(); })
    .then(puzzle => {
      _puzzle = puzzle;
      document.getElementById('te-title').value = puzzle.title;
      document.getElementById('te-id').textContent = 'ID: ' + puzzle.id;

      // Use targetPose as the editing position (what we're positioning)
      _pieces = puzzle.pieces.map(p => ({
        id: p.id,
        polygon: p.polygon,
        color: p.color,
        x: p.targetPose.position.x,
        y: p.targetPose.position.y,
        rotation: p.targetPose.rotationDeg,
        flipped: !!(p.targetPose.flipped),
        snap: p.snap,
        lockOnSnap: p.lockOnSnap,
        startPose: p.startPose,
        el: null,
      }));
      teRender();
      setStatus('Loaded "' + puzzle.title + '"');
    })
    .catch(() => setStatus('Failed to load puzzle', true));
}

function teNew() {
  const title = prompt('Puzzle name:', 'My Puzzle');
  if (!title) return;

  fetch('/api/tangram/blank?title=' + encodeURIComponent(title))
    .then(r => r.json())
    .then(puzzle => {
      _puzzle = puzzle;
      document.getElementById('te-title').value = puzzle.title;
      document.getElementById('te-id').textContent = 'ID: ' + puzzle.id;

      _pieces = puzzle.pieces.map(p => ({
        id: p.id,
        polygon: p.polygon,
        color: p.color,
        x: p.startPose.position.x,
        y: p.startPose.position.y,
        rotation: p.startPose.rotationDeg,
        flipped: false,
        snap: p.snap,
        lockOnSnap: p.lockOnSnap,
        startPose: p.startPose,
        el: null,
      }));
      teRender();
      setStatus('New puzzle "' + title + '" — drag pieces into position then Save');
    })
    .catch(() => setStatus('Failed to create blank puzzle', true));
}

function teSave() {
  if (!_puzzle) { setStatus('Nothing to save — load or create first', true); return; }

  const title = document.getElementById('te-title').value.trim();
  if (!title) { setStatus('Please enter a title', true); return; }

  // Build the puzzle JSON from current piece positions
  const puzzle = JSON.parse(JSON.stringify(_puzzle));
  puzzle.title = title;
  // Recalculate ID from title if this is new
  if (!puzzle.id || puzzle.id === 'untitled') {
    puzzle.id = title.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
  }

  // Update targetPose from editor positions
  _pieces.forEach((p, i) => {
    puzzle.pieces[i].targetPose = {
      position: { x: Math.round(p.x), y: Math.round(p.y) },
      rotationDeg: p.rotation,
      flipped: !!p.flipped,
    };
  });

  fetch('/api/tangram/puzzle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(puzzle),
  })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'ok') {
        _puzzle = puzzle;
        _puzzle.id = data.id;
        document.getElementById('te-id').textContent = 'ID: ' + data.id;
        setStatus('Saved "' + title + '" ✓');
        // Update the dropdown
        addToDropdown(data.id, title);
      } else {
        setStatus('Save failed: ' + (data.msg || 'unknown'), true);
      }
    })
    .catch(() => setStatus('Save failed — network error', true));
}

function teDelete() {
  if (!_puzzle || !_puzzle.id) { setStatus('Nothing to delete', true); return; }
  if (!confirm('Delete puzzle "' + _puzzle.title + '"?')) return;

  fetch('/api/tangram/puzzle/' + _puzzle.id, { method: 'DELETE' })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'ok') {
        setStatus('Deleted "' + _puzzle.title + '"');
        removeFromDropdown(_puzzle.id);
        _puzzle = null;
        _pieces = [];
        document.getElementById('te-canvas').innerHTML = '';
        document.getElementById('te-piece-list').innerHTML = '';
        document.getElementById('te-title').value = '';
        document.getElementById('te-id').textContent = '';
        document.getElementById('te-piece-info').textContent = 'Select a piece';
      } else {
        setStatus('Delete failed', true);
      }
    })
    .catch(() => setStatus('Delete failed — network error', true));
}

/* ── Dropdown management ───────────────────────────────────────── */
function addToDropdown(id, title) {
  const sel = document.getElementById('te-puzzle-select');
  let opt = sel.querySelector('option[value="' + id + '"]');
  if (!opt) {
    opt = document.createElement('option');
    opt.value = id;
    sel.appendChild(opt);
  }
  opt.textContent = title;
  sel.value = id;
}

function removeFromDropdown(id) {
  const sel = document.getElementById('te-puzzle-select');
  const opt = sel.querySelector('option[value="' + id + '"]');
  if (opt) opt.remove();
  sel.value = '';
}
