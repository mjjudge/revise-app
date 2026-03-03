/**
 * Reward Games Framework — "Brain Reset Rewards"
 * Each game is a self-contained module registered in GAMES.
 * On milestone, a random enabled game is selected and shown in a modal overlay.
 */

/* ═══════════════════════════════════════════════════════════════════
   GAME REGISTRY
   ═══════════════════════════════════════════════════════════════════ */
const GAMES = {};
let _enabledGames = null;    // populated by loadEnabledGames()

function registerGame(id, name, icon, initFn, cleanupFn) {
  GAMES[id] = { id, name, icon, init: initFn, cleanup: cleanupFn || (() => {}) };
}

function loadEnabledGames(enabledList) {
  _enabledGames = new Set(enabledList);
}

function pickRandomGame() {
  const pool = Object.keys(GAMES).filter(id => !_enabledGames || _enabledGames.has(id));
  if (pool.length === 0) return null;
  return GAMES[pool[Math.floor(Math.random() * pool.length)]];
}

/* ═══════════════════════════════════════════════════════════════════
   MODAL SYSTEM
   ═══════════════════════════════════════════════════════════════════ */
let _activeGame = null;

function openRewardGame(specificGameId) {
  const game = specificGameId ? GAMES[specificGameId] : pickRandomGame();
  if (!game) return;
  _activeGame = game;

  const modal = document.getElementById('reward-game-modal');
  const title = document.getElementById('reward-game-title');
  const container = document.getElementById('reward-game-container');

  title.textContent = game.icon + ' ' + game.name;
  container.innerHTML = '';
  modal.classList.remove('hidden');

  game.init(container, () => closeRewardGame());
}

function closeRewardGame() {
  if (_activeGame && _activeGame.cleanup) _activeGame.cleanup();
  _activeGame = null;
  const modal = document.getElementById('reward-game-modal');
  if (modal) modal.classList.add('hidden');
  const container = document.getElementById('reward-game-container');
  if (container) container.innerHTML = '';
}

/* ═══════════════════════════════════════════════════════════════════
   GAME 1: MINI SUDOKU (4×4)
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  const PUZZLES = [
    {solution:[1,2,3,4, 3,4,1,2, 2,1,4,3, 4,3,2,1], blanks:[1,3,5,6,9,10,14,15]},
    {solution:[2,4,1,3, 3,1,4,2, 4,2,3,1, 1,3,2,4], blanks:[0,2,5,7,8,11,13,14]},
    {solution:[3,1,4,2, 4,2,3,1, 1,4,2,3, 2,3,1,4], blanks:[1,2,4,7,8,10,13,15]},
    {solution:[4,3,2,1, 1,2,4,3, 3,4,1,2, 2,1,3,4], blanks:[0,3,4,6,9,11,12,14]},
    {solution:[1,3,4,2, 4,2,1,3, 2,4,3,1, 3,1,2,4], blanks:[0,2,5,7,9,10,12,15]},
    {solution:[2,1,4,3, 4,3,2,1, 1,2,3,4, 3,4,1,2], blanks:[1,3,4,6,10,11,13,14]},
  ];

  let currentPuzzle = null;

  function init(container, onComplete) {
    currentPuzzle = PUZZLES[Math.floor(Math.random() * PUZZLES.length)];

    container.innerHTML = `
      <p class="text-realm-purple-300 text-sm text-center mb-3">Fill blanks so every row, column & 2×2 box has 1-2-3-4</p>
      <div id="sdk-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;max-width:220px;margin:0 auto 12px auto;"></div>
      <div id="sdk-msg" class="text-center text-lg font-bold h-8 mb-3"></div>
      <div class="flex gap-3">
        <button id="sdk-check" class="flex-1 py-2 bg-realm-gold-500 hover:bg-realm-gold-400 text-realm-purple-900 font-bold rounded-xl transition-colors">✅ Check</button>
      </div>
    `;

    const grid = document.getElementById('sdk-grid');
    for (let i = 0; i < 16; i++) {
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.inputMode = 'numeric';
      inp.maxLength = 1;
      inp.dataset.idx = i;
      Object.assign(inp.style, {
        width: '50px', height: '50px', textAlign: 'center',
        fontSize: '1.25rem', fontWeight: 'bold', borderRadius: '0.5rem',
        border: '2px solid rgba(139,92,246,0.5)',
        background: 'rgba(88,28,135,0.6)', color: '#e9d5ff', outline: 'none',
      });
      // 2×2 box borders
      if (i % 4 === 1) { inp.style.borderRightWidth = '3px'; inp.style.borderRightColor = 'rgba(251,191,36,0.5)'; }
      if (Math.floor(i / 4) === 1) { inp.style.borderBottomWidth = '3px'; inp.style.borderBottomColor = 'rgba(251,191,36,0.5)'; }

      if (!currentPuzzle.blanks.includes(i)) {
        inp.value = currentPuzzle.solution[i];
        inp.readOnly = true;
        inp.style.background = 'rgba(139,92,246,0.3)';
        inp.style.color = '#fbbf24';
        inp.style.cursor = 'default';
      } else {
        inp.addEventListener('input', function() {
          this.value = this.value.replace(/[^1-4]/g, '');
          this.style.borderColor = 'rgba(139,92,246,0.5)';
          this.style.background = 'rgba(88,28,135,0.6)';
        });
        inp.addEventListener('focus', function() {
          this.style.borderColor = '#fbbf24';
          this.style.boxShadow = '0 0 8px rgba(251,191,36,0.4)';
        });
        inp.addEventListener('blur', function() {
          this.style.boxShadow = 'none';
          if (!this.value) this.style.borderColor = 'rgba(139,92,246,0.5)';
        });
      }
      grid.appendChild(inp);
    }

    document.getElementById('sdk-check').addEventListener('click', function() {
      const inputs = grid.querySelectorAll('input');
      let allCorrect = true, allFilled = true;
      inputs.forEach((inp, i) => {
        if (inp.readOnly) return;
        const val = parseInt(inp.value);
        if (!val) { allFilled = false; allCorrect = false; return; }
        if (val === currentPuzzle.solution[i]) {
          inp.style.borderColor = '#10b981';
          inp.style.background = 'rgba(16,185,129,0.2)';
        } else {
          inp.style.borderColor = '#ef4444';
          inp.style.background = 'rgba(239,68,68,0.2)';
          allCorrect = false;
        }
      });
      const msg = document.getElementById('sdk-msg');
      if (!allFilled) {
        msg.textContent = '⚠️ Fill in all blanks first!';
        msg.style.color = '#fbbf24';
      } else if (allCorrect) {
        msg.textContent = '🎉 Perfect! You solved it!';
        msg.style.color = '#10b981';
        setTimeout(() => onComplete(), 1500);
      } else {
        msg.textContent = '🤔 Not quite — try again!';
        msg.style.color = '#ef4444';
      }
    });
  }

  registerGame('sudoku', 'Mini Sudoku', '🧩', init);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 2: TIC-TAC-TOE vs Computer
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  const WIN_LINES = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];

  function init(container, onComplete) {
    let board = Array(9).fill(null);
    let gameOver = false;

    container.innerHTML = `
      <p class="text-realm-purple-300 text-sm text-center mb-3">You are ✕ — beat the computer!</p>
      <div id="ttt-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;max-width:210px;margin:0 auto 12px auto;"></div>
      <div id="ttt-msg" class="text-center text-lg font-bold h-8 mb-2"></div>
    `;

    const grid = document.getElementById('ttt-grid');
    for (let i = 0; i < 9; i++) {
      const cell = document.createElement('button');
      cell.dataset.idx = i;
      Object.assign(cell.style, {
        width: '64px', height: '64px', fontSize: '1.75rem', fontWeight: 'bold',
        borderRadius: '0.5rem', border: '2px solid rgba(139,92,246,0.5)',
        background: 'rgba(88,28,135,0.6)', color: '#e9d5ff', cursor: 'pointer',
      });
      cell.addEventListener('click', () => playerMove(i));
      grid.appendChild(cell);
    }

    function render() {
      const cells = grid.querySelectorAll('button');
      cells.forEach((c, i) => {
        c.textContent = board[i] === 'X' ? '✕' : board[i] === 'O' ? '○' : '';
        c.style.color = board[i] === 'X' ? '#fbbf24' : board[i] === 'O' ? '#a78bfa' : '#e9d5ff';
        c.style.cursor = (!board[i] && !gameOver) ? 'pointer' : 'default';
      });
    }

    function checkWin(player) {
      return WIN_LINES.some(line => line.every(i => board[i] === player));
    }

    function isFull() { return board.every(c => c !== null); }

    function aiMove() {
      // Check if AI can win
      for (let i = 0; i < 9; i++) {
        if (!board[i]) { board[i] = 'O'; if (checkWin('O')) return; board[i] = null; }
      }
      // Block player win
      for (let i = 0; i < 9; i++) {
        if (!board[i]) { board[i] = 'X'; if (checkWin('X')) { board[i] = 'O'; return; } board[i] = null; }
      }
      // Take centre, then corners, then edges
      const pref = [4, 0, 2, 6, 8, 1, 3, 5, 7];
      for (const p of pref) {
        if (!board[p]) { board[p] = 'O'; return; }
      }
    }

    function endGame(msg, color) {
      gameOver = true;
      const el = document.getElementById('ttt-msg');
      el.textContent = msg;
      el.style.color = color;
      setTimeout(() => onComplete(), 2000);
    }

    function playerMove(i) {
      if (gameOver || board[i]) return;
      board[i] = 'X';
      render();
      if (checkWin('X')) { endGame('🎉 You win!', '#10b981'); return; }
      if (isFull()) { endGame("🤝 It's a draw!", '#fbbf24'); return; }
      setTimeout(() => {
        aiMove();
        render();
        if (checkWin('O')) { endGame('🤖 Computer wins! Good game!', '#a78bfa'); return; }
        if (isFull()) { endGame("🤝 It's a draw!", '#fbbf24'); }
      }, 400);
    }

    render();
  }

  registerGame('tictactoe', 'Tic-Tac-Toe', '⭕', init);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 3: SPACE INVADERS MINI
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  let _raf = null;
  let _siKeyDown = null;
  let _siKeyUp = null;
  let _siTimer = null;

  function init(container, onComplete) {
    container.innerHTML = `
      <p class="text-realm-purple-300 text-sm text-center mb-2">Arrow keys to move · Space to fire · 45 seconds!</p>
      <canvas id="si-canvas" width="300" height="360" style="display:block;margin:0 auto;border-radius:0.75rem;background:#0d001a;"></canvas>
      <div class="flex justify-between items-center mt-2" style="max-width:300px;margin:0 auto;">
        <span id="si-score" class="text-realm-gold-400 font-bold">Score: 0</span>
        <span id="si-timer" class="text-realm-purple-300 font-bold">45s</span>
      </div>
      <div id="si-mobile" class="flex justify-center gap-4 mt-2">
        <button id="si-left" class="px-4 py-2 bg-realm-purple-700 rounded-lg text-lg">⬅️</button>
        <button id="si-fire" class="px-4 py-2 bg-realm-gold-500 text-realm-purple-900 rounded-lg text-lg font-bold">🔫</button>
        <button id="si-right" class="px-4 py-2 bg-realm-purple-700 rounded-lg text-lg">➡️</button>
      </div>
    `;

    const canvas = document.getElementById('si-canvas');
    const ctx = canvas.getContext('2d');
    const W = 300, H = 360;
    let score = 0, timeLeft = 45, gameActive = true;
    let shipX = W / 2 - 15;
    const shipW = 30, shipH = 20;
    let bullets = [];
    let aliens = [];
    let alienDir = 1, alienSpeed = 0.5;
    const keys = {};

    // Create aliens (4 rows × 6 cols)
    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 6; c++) {
        aliens.push({ x: 20 + c * 44, y: 20 + r * 32, w: 28, h: 20, alive: true });
      }
    }

    _siTimer = setInterval(() => {
      if (!gameActive) return;
      timeLeft--;
      const el = document.getElementById('si-timer');
      if (el) el.textContent = timeLeft + 's';
      if (timeLeft <= 0) {
        gameActive = false;
        clearInterval(_siTimer);
        _siTimer = null;
        showEnd();
      }
    }, 1000);

    function removeKeyListeners() {
      if (_siKeyDown) { document.removeEventListener('keydown', _siKeyDown); _siKeyDown = null; }
      if (_siKeyUp)   { document.removeEventListener('keyup',   _siKeyUp);   _siKeyUp = null;   }
    }

    function showEnd() {
      gameActive = false;
      removeKeyListeners();
      ctx.fillStyle = 'rgba(0,0,0,0.7)';
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#fbbf24';
      ctx.font = 'bold 24px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Time\'s up!', W/2, H/2 - 15);
      ctx.fillStyle = '#e9d5ff';
      ctx.font = '18px sans-serif';
      ctx.fillText('Score: ' + score, W/2, H/2 + 15);
      setTimeout(() => onComplete(), 2000);
    }

    function update() {
      if (!gameActive) return;
      // Ship movement
      if (keys['ArrowLeft'] || keys['a']) shipX = Math.max(0, shipX - 4);
      if (keys['ArrowRight'] || keys['d']) shipX = Math.min(W - shipW, shipX + 4);

      // Bullets
      bullets = bullets.filter(b => b.y > 0);
      bullets.forEach(b => b.y -= 6);

      // Aliens movement
      let hitEdge = false;
      aliens.forEach(a => {
        if (!a.alive) return;
        a.x += alienDir * alienSpeed;
        if (a.x <= 0 || a.x + a.w >= W) hitEdge = true;
      });
      if (hitEdge) {
        alienDir *= -1;
        aliens.forEach(a => { if (a.alive) a.y += 12; });
      }

      // Collision detection
      bullets.forEach((b, bi) => {
        aliens.forEach(a => {
          if (!a.alive) return;
          if (b.x >= a.x && b.x <= a.x + a.w && b.y >= a.y && b.y <= a.y + a.h) {
            a.alive = false;
            bullets.splice(bi, 1);
            score++;
            const el = document.getElementById('si-score');
            if (el) el.textContent = 'Score: ' + score;
          }
        });
      });

      // All aliens dead? Respawn!
      if (aliens.every(a => !a.alive)) {
        alienSpeed += 0.3;
        for (let r = 0; r < 4; r++) {
          for (let c = 0; c < 6; c++) {
            const idx = r * 6 + c;
            aliens[idx].x = 20 + c * 44;
            aliens[idx].y = 20 + r * 32;
            aliens[idx].alive = true;
          }
        }
      }
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);
      // Ship
      ctx.fillStyle = '#fbbf24';
      ctx.fillRect(shipX, H - 40, shipW, shipH);
      ctx.fillRect(shipX + shipW/2 - 3, H - 48, 6, 10);
      // Bullets
      ctx.fillStyle = '#10b981';
      bullets.forEach(b => ctx.fillRect(b.x - 2, b.y, 4, 10));
      // Aliens
      const alienColors = ['#ef4444', '#f59e0b', '#8b5cf6', '#3b82f6'];
      aliens.forEach((a, i) => {
        if (!a.alive) return;
        ctx.fillStyle = alienColors[Math.floor(i / 6) % alienColors.length];
        ctx.fillRect(a.x, a.y, a.w, a.h);
        // eyes
        ctx.fillStyle = '#fff';
        ctx.fillRect(a.x + 6, a.y + 6, 4, 4);
        ctx.fillRect(a.x + a.w - 10, a.y + 6, 4, 4);
      });
    }

    function loop() {
      update();
      draw();
      if (gameActive) _raf = requestAnimationFrame(loop);
    }

    function fire() {
      if (!gameActive) return;
      if (bullets.length < 3) {
        bullets.push({ x: shipX + shipW/2, y: H - 50 });
      }
    }

    _siKeyDown = function(e) {
      if (!gameActive) return;
      keys[e.key] = true;
      if (e.key === ' ') { e.preventDefault(); e.stopPropagation(); fire(); }
    };
    _siKeyUp = function(e) {
      keys[e.key] = false;
    };
    document.addEventListener('keydown', _siKeyDown);
    document.addEventListener('keyup', _siKeyUp);

    // Mobile controls
    const leftBtn = document.getElementById('si-left');
    const rightBtn = document.getElementById('si-right');
    const fireBtn = document.getElementById('si-fire');
    let leftInt = null, rightInt = null;
    leftBtn.addEventListener('touchstart', e => { e.preventDefault(); leftInt = setInterval(() => { keys['ArrowLeft'] = true; }, 30); });
    leftBtn.addEventListener('touchend', () => { clearInterval(leftInt); keys['ArrowLeft'] = false; });
    rightBtn.addEventListener('touchstart', e => { e.preventDefault(); rightInt = setInterval(() => { keys['ArrowRight'] = true; }, 30); });
    rightBtn.addEventListener('touchend', () => { clearInterval(rightInt); keys['ArrowRight'] = false; });
    fireBtn.addEventListener('click', fire);
    fireBtn.addEventListener('touchstart', e => { e.preventDefault(); fire(); });

    _raf = requestAnimationFrame(loop);
  }

  function cleanup() {
    if (_raf) cancelAnimationFrame(_raf);
    _raf = null;
    if (_siKeyDown) { document.removeEventListener('keydown', _siKeyDown); _siKeyDown = null; }
    if (_siKeyUp)   { document.removeEventListener('keyup',   _siKeyUp);   _siKeyUp = null;   }
    if (_siTimer) { clearInterval(_siTimer); _siTimer = null; }
  }

  registerGame('space_invaders', 'Space Invaders', '🚀', init, cleanup);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 4: PATTERN MEMORY
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  let _timeouts = [];

  function init(container, onComplete) {
    _timeouts = [];
    const gridSize = 16;  // 4×4
    const seqLen = 3;     // start easy — 3 squares
    const sequence = [];
    while (sequence.length < seqLen) {
      const n = Math.floor(Math.random() * gridSize);
      if (!sequence.includes(n)) sequence.push(n);
    }

    let phase = 'showing';  // showing → input → done
    let inputIdx = 0;

    container.innerHTML = `
      <p id="pm-instruction" class="text-realm-purple-300 text-sm text-center mb-3">Watch the pattern…</p>
      <div id="pm-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;max-width:240px;margin:0 auto 12px auto;"></div>
      <div id="pm-msg" class="text-center text-lg font-bold h-8 mb-2"></div>
      <div id="pm-progress" class="text-center text-realm-purple-300 text-sm"></div>
      <div id="pm-actions" class="text-center mt-2"></div>
    `;

    const grid = document.getElementById('pm-grid');
    const cells = [];
    for (let i = 0; i < gridSize; i++) {
      const cell = document.createElement('button');
      Object.assign(cell.style, {
        width: '54px', height: '54px', borderRadius: '0.5rem',
        border: '2px solid rgba(139,92,246,0.4)',
        background: 'rgba(88,28,135,0.5)', cursor: 'pointer', transition: 'all 0.2s',
      });
      cell.addEventListener('click', () => onCellClick(i));
      grid.appendChild(cell);
      cells.push(cell);
    }

    function highlight(idx, on) {
      cells[idx].style.background = on ? '#fbbf24' : 'rgba(88,28,135,0.5)';
      cells[idx].style.borderColor = on ? '#fbbf24' : 'rgba(139,92,246,0.4)';
      cells[idx].style.boxShadow = on ? '0 0 12px rgba(251,191,36,0.6)' : 'none';
    }

    function playSequence() {
      // Clear any existing timeouts
      _timeouts.forEach(t => clearTimeout(t));
      _timeouts = [];
      phase = 'showing';
      inputIdx = 0;
      document.getElementById('pm-instruction').textContent = 'Watch the pattern…';
      document.getElementById('pm-progress').textContent = '';
      document.getElementById('pm-msg').textContent = '';
      document.getElementById('pm-actions').innerHTML = '';

      // Reset all cells
      cells.forEach((c, i) => highlight(i, false));

      // Show sequence
      sequence.forEach((sq, i) => {
        const tOn = setTimeout(() => highlight(sq, true), i * 700);
        const tOff = setTimeout(() => highlight(sq, false), i * 700 + 500);
        _timeouts.push(tOn, tOff);
      });

      const tReady = setTimeout(() => {
        phase = 'input';
        document.getElementById('pm-instruction').textContent = 'Now tap them in the same order!';
        document.getElementById('pm-progress').textContent = '0 / ' + seqLen;
      }, seqLen * 700 + 300);
      _timeouts.push(tReady);
    }

    function onCellClick(i) {
      if (phase !== 'input') return;
      if (i === sequence[inputIdx]) {
        highlight(i, true);
        setTimeout(() => highlight(i, false), 300);
        inputIdx++;
        document.getElementById('pm-progress').textContent = inputIdx + ' / ' + seqLen;
        if (inputIdx >= seqLen) {
          phase = 'done';
          document.getElementById('pm-msg').textContent = '🎉 Perfect memory!';
          document.getElementById('pm-msg').style.color = '#10b981';
          setTimeout(() => onComplete(), 1500);
        }
      } else {
        cells[i].style.background = 'rgba(239,68,68,0.3)';
        cells[i].style.borderColor = '#ef4444';
        setTimeout(() => {
          cells[i].style.background = 'rgba(88,28,135,0.5)';
          cells[i].style.borderColor = 'rgba(139,92,246,0.4)';
        }, 300);
        phase = 'wrong';
        document.getElementById('pm-msg').textContent = '🤔 Oops! Wrong square…';
        document.getElementById('pm-msg').style.color = '#ef4444';
        document.getElementById('pm-progress').textContent = '';
        // Show Watch Again button
        const actions = document.getElementById('pm-actions');
        actions.innerHTML = `<button id="pm-replay" class="px-4 py-2 bg-realm-purple-700 hover:bg-realm-purple-600 text-white rounded-lg text-sm font-bold transition">🔄 Watch Again</button>`;
        document.getElementById('pm-replay').addEventListener('click', () => {
          playSequence();
        });
      }
    }

    // Initial play
    playSequence();
  }

  function cleanup() {
    _timeouts.forEach(t => clearTimeout(t));
    _timeouts = [];
  }

  registerGame('pattern_memory', 'Pattern Memory', '🧠', init, cleanup);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 5: REFLEX TAP
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  let _timeout = null;

  function init(container, onComplete) {
    let round = 0, maxRounds = 10;
    let times = [];
    let waiting = false, startTime = 0;

    container.innerHTML = `
      <p class="text-realm-purple-300 text-sm text-center mb-2">Tap the circle as fast as you can! 10 rounds</p>
      <div id="rt-area" style="position:relative;width:280px;height:250px;margin:0 auto;border-radius:0.75rem;background:rgba(88,28,135,0.4);border:2px solid rgba(139,92,246,0.3);overflow:hidden;cursor:crosshair;"></div>
      <div class="flex justify-between mt-2" style="max-width:280px;margin:4px auto;">
        <span id="rt-round" class="text-realm-purple-300 text-sm">Round: 0/10</span>
        <span id="rt-avg" class="text-realm-gold-400 font-bold text-sm">Avg: –</span>
      </div>
      <div id="rt-msg" class="text-center text-lg font-bold h-8 mt-2"></div>
    `;

    const area = document.getElementById('rt-area');

    function showTarget() {
      if (round >= maxRounds) {
        const avg = Math.round(times.reduce((a, b) => a + b, 0) / times.length);
        const msg = document.getElementById('rt-msg');
        msg.textContent = '⚡ Average: ' + avg + 'ms' + (avg < 350 ? ' — Lightning fast!' : avg < 500 ? ' — Quick reflexes!' : ' — Keep practising!');
        msg.style.color = '#10b981';
        setTimeout(() => onComplete(), 2500);
        return;
      }

      // Wait random delay before showing
      const delay = 800 + Math.random() * 1500;
      _timeout = setTimeout(() => {
        const x = 20 + Math.random() * 210;
        const y = 20 + Math.random() * 190;
        const target = document.createElement('div');
        target.id = 'rt-target';
        Object.assign(target.style, {
          position: 'absolute', left: x + 'px', top: y + 'px',
          width: '50px', height: '50px', borderRadius: '50%',
          background: 'radial-gradient(circle, #fbbf24, #f59e0b)',
          boxShadow: '0 0 15px rgba(251,191,36,0.6)',
          cursor: 'pointer', transition: 'transform 0.1s',
        });
        target.addEventListener('click', e => {
          e.stopPropagation();
          const elapsed = Date.now() - startTime;
          times.push(elapsed);
          target.remove();
          round++;
          document.getElementById('rt-round').textContent = 'Round: ' + round + '/10';
          const avg = Math.round(times.reduce((a, b) => a + b, 0) / times.length);
          document.getElementById('rt-avg').textContent = 'Avg: ' + avg + 'ms';
          showTarget();
        });
        area.appendChild(target);
        startTime = Date.now();
        waiting = true;
      }, delay);
    }

    showTarget();
  }

  function cleanup() {
    if (_timeout) clearTimeout(_timeout);
    _timeout = null;
  }

  registerGame('reflex_tap', 'Reflex Tap', '⚡', init, cleanup);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 6: WORD SCRAMBLE
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  const WORD_BANKS = {
    maths: ['FRACTION', 'DECIMAL', 'PERCENT', 'ALGEBRA', 'INTEGER', 'EQUATION', 'POLYGON', 'TRIANGLE', 'PARALLEL', 'SYMMETRY', 'PRODUCT', 'QUOTIENT', 'RADIUS', 'DIAMETER', 'FACTOR', 'MEDIAN', 'VOLUME', 'PRISM'],
    geography: ['EROSION', 'GLACIER', 'CLIMATE', 'PLATEAU', 'CONTOUR', 'MEANDER', 'ESTUARY', 'TUNDRA', 'BIOME', 'RELIEF', 'TRIBUTARY', 'ALTITUDE', 'TERRAIN', 'VOLCANO', 'DELTA', 'COMPASS', 'LATITUDE', 'LONGITUDE'],
    general: ['SCIENCE', 'HISTORY', 'COMPASS', 'PYRAMID', 'CULTURE', 'EXTREME', 'ANCIENT', 'WEATHER', 'DENSITY', 'GRAVITY', 'CRYSTAL', 'ELEMENT', 'PLANET', 'MAGNET', 'FOREST', 'ISLAND'],
  };

  let _timer = null;

  function scramble(word) {
    const arr = word.split('');
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    const s = arr.join('');
    return s === word ? scramble(word) : s;  // ensure it's different
  }

  function init(container, onComplete) {
    // Pick 5 random words from mixed banks
    const allWords = [...WORD_BANKS.maths, ...WORD_BANKS.geography, ...WORD_BANKS.general];
    const shuffled = allWords.sort(() => Math.random() - 0.5);
    const words = shuffled.slice(0, 5);

    let currentIdx = 0;
    let solved = 0;
    let timeLeft = 60;

    container.innerHTML = `
      <div class="flex justify-between items-center mb-3" style="max-width:280px;margin:0 auto;">
        <span id="ws-progress" class="text-realm-purple-300 text-sm">Word 1 of 5</span>
        <span id="ws-timer" class="text-realm-gold-400 font-bold">60s</span>
      </div>
      <div id="ws-scrambled" class="text-center text-2xl font-bold tracking-wider text-realm-gold-400 mb-4" style="letter-spacing:0.2em;"></div>
      <div class="flex gap-2 justify-center mb-3" style="max-width:280px;margin:0 auto;">
        <input id="ws-input" type="text" placeholder="Type the word…" autocomplete="off"
               style="flex:1;padding:8px 12px;border-radius:0.5rem;border:2px solid rgba(139,92,246,0.5);background:rgba(88,28,135,0.6);color:#e9d5ff;font-size:1rem;outline:none;"
        />
        <button id="ws-submit" class="px-4 py-2 bg-realm-gold-500 hover:bg-realm-gold-400 text-realm-purple-900 font-bold rounded-lg">Go</button>
      </div>
      <div id="ws-msg" class="text-center text-lg font-bold h-8"></div>
    `;

    function showWord() {
      if (currentIdx >= words.length || timeLeft <= 0) {
        const msg = document.getElementById('ws-msg');
        msg.textContent = '🎉 ' + solved + '/5 unscrambled!';
        msg.style.color = '#10b981';
        clearInterval(_timer);
        setTimeout(() => onComplete(), 2000);
        return;
      }
      document.getElementById('ws-scrambled').textContent = scramble(words[currentIdx]);
      document.getElementById('ws-input').value = '';
      document.getElementById('ws-input').focus();
      document.getElementById('ws-progress').textContent = 'Word ' + (currentIdx + 1) + ' of 5';
      document.getElementById('ws-msg').textContent = '';
    }

    function checkWord() {
      const answer = document.getElementById('ws-input').value.trim().toUpperCase();
      if (answer === words[currentIdx]) {
        solved++;
        document.getElementById('ws-msg').textContent = '✅ Correct!';
        document.getElementById('ws-msg').style.color = '#10b981';
        currentIdx++;
        setTimeout(showWord, 600);
      } else {
        document.getElementById('ws-msg').textContent = '❌ Try again!';
        document.getElementById('ws-msg').style.color = '#ef4444';
        document.getElementById('ws-input').value = '';
        document.getElementById('ws-input').focus();
      }
    }

    document.getElementById('ws-submit').addEventListener('click', checkWord);
    document.getElementById('ws-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') checkWord();
    });

    _timer = setInterval(() => {
      timeLeft--;
      const el = document.getElementById('ws-timer');
      if (el) el.textContent = timeLeft + 's';
      if (timeLeft <= 0) {
        clearInterval(_timer);
        const msg = document.getElementById('ws-msg');
        if (msg) {
          msg.textContent = '⏰ Time\'s up! ' + solved + '/5 solved!';
          msg.style.color = '#fbbf24';
        }
        setTimeout(() => onComplete(), 2000);
      }
    }, 1000);

    showWord();
  }

  function cleanup() {
    if (_timer) clearInterval(_timer);
    _timer = null;
  }

  registerGame('word_scramble', 'Word Scramble', '🔤', init, cleanup);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 7: MINI 2048
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  function init(container, onComplete) {
    let grid = Array(16).fill(0);
    let highest = 0;
    let gameActive = true;

    container.innerHTML = `
      <p class="text-realm-purple-300 text-sm text-center mb-2">Arrow keys to slide · Merge to reach 256!</p>
      <div id="g2048-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;max-width:240px;margin:0 auto 8px auto;"></div>
      <div class="flex justify-between" style="max-width:240px;margin:0 auto;">
        <span id="g2048-high" class="text-realm-gold-400 font-bold text-sm">Highest: 0</span>
        <span id="g2048-msg" class="text-lg font-bold"></span>
      </div>
      <div id="g2048-mobile" class="flex justify-center gap-2 mt-3">
        <button data-dir="left" class="px-3 py-2 bg-realm-purple-700 rounded-lg">⬅️</button>
        <div class="flex flex-col gap-2">
          <button data-dir="up" class="px-3 py-2 bg-realm-purple-700 rounded-lg">⬆️</button>
          <button data-dir="down" class="px-3 py-2 bg-realm-purple-700 rounded-lg">⬇️</button>
        </div>
        <button data-dir="right" class="px-3 py-2 bg-realm-purple-700 rounded-lg">➡️</button>
      </div>
    `;

    const TILE_COLORS = {
      0: 'rgba(88,28,135,0.3)', 2: '#6d28d9', 4: '#7c3aed', 8: '#8b5cf6',
      16: '#a78bfa', 32: '#f59e0b', 64: '#ef4444', 128: '#10b981', 256: '#fbbf24',
    };

    const gridEl = document.getElementById('g2048-grid');
    for (let i = 0; i < 16; i++) {
      const cell = document.createElement('div');
      Object.assign(cell.style, {
        width: '54px', height: '54px', borderRadius: '0.5rem',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.1rem', fontWeight: 'bold', color: '#fff',
        transition: 'all 0.15s',
      });
      gridEl.appendChild(cell);
    }

    function addRandom() {
      const empties = [];
      grid.forEach((v, i) => { if (!v) empties.push(i); });
      if (empties.length === 0) return;
      const idx = empties[Math.floor(Math.random() * empties.length)];
      grid[idx] = Math.random() < 0.9 ? 2 : 4;
    }

    function render() {
      const cells = gridEl.querySelectorAll('div');
      grid.forEach((v, i) => {
        cells[i].textContent = v || '';
        cells[i].style.background = TILE_COLORS[v] || '#fbbf24';
        cells[i].style.fontSize = v >= 100 ? '0.9rem' : '1.1rem';
      });
      highest = Math.max(...grid);
      document.getElementById('g2048-high').textContent = 'Highest: ' + highest;
    }

    function slide(row) {
      let arr = row.filter(v => v);
      let merged = [];
      for (let i = 0; i < arr.length; i++) {
        if (i + 1 < arr.length && arr[i] === arr[i + 1]) {
          merged.push(arr[i] * 2);
          i++;
        } else {
          merged.push(arr[i]);
        }
      }
      while (merged.length < 4) merged.push(0);
      return merged;
    }

    function move(dir) {
      if (!gameActive) return;
      const old = grid.slice();

      if (dir === 'left') {
        for (let r = 0; r < 4; r++) {
          const row = grid.slice(r * 4, r * 4 + 4);
          const res = slide(row);
          for (let c = 0; c < 4; c++) grid[r * 4 + c] = res[c];
        }
      } else if (dir === 'right') {
        for (let r = 0; r < 4; r++) {
          const row = grid.slice(r * 4, r * 4 + 4).reverse();
          const res = slide(row).reverse();
          for (let c = 0; c < 4; c++) grid[r * 4 + c] = res[c];
        }
      } else if (dir === 'up') {
        for (let c = 0; c < 4; c++) {
          const col = [grid[c], grid[c + 4], grid[c + 8], grid[c + 12]];
          const res = slide(col);
          for (let r = 0; r < 4; r++) grid[r * 4 + c] = res[r];
        }
      } else if (dir === 'down') {
        for (let c = 0; c < 4; c++) {
          const col = [grid[c], grid[c + 4], grid[c + 8], grid[c + 12]].reverse();
          const res = slide(col).reverse();
          for (let r = 0; r < 4; r++) grid[r * 4 + c] = res[r];
        }
      }

      // Check if anything changed
      if (grid.some((v, i) => v !== old[i])) {
        addRandom();
        render();
        if (Math.max(...grid) >= 256) {
          gameActive = false;
          const msg = document.getElementById('g2048-msg');
          msg.textContent = '🎉 256!';
          msg.style.color = '#fbbf24';
          setTimeout(() => onComplete(), 2000);
        } else if (grid.every(v => v) && !canMove()) {
          gameActive = false;
          const msg = document.getElementById('g2048-msg');
          msg.textContent = 'Highest: ' + Math.max(...grid);
          msg.style.color = '#a78bfa';
          setTimeout(() => onComplete(), 2000);
        }
      }
    }

    function canMove() {
      for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) {
        const v = grid[r * 4 + c];
        if (!v) return true;
        if (c < 3 && grid[r * 4 + c + 1] === v) return true;
        if (r < 3 && grid[(r + 1) * 4 + c] === v) return true;
      }
      return false;
    }

    const keyHandler = (e) => {
      const dirMap = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down' };
      if (dirMap[e.key]) { e.preventDefault(); move(dirMap[e.key]); }
    };
    document.addEventListener('keydown', keyHandler);

    // Mobile buttons
    document.querySelectorAll('#g2048-mobile button').forEach(btn => {
      btn.addEventListener('click', () => move(btn.dataset.dir));
    });

    // Touch swipe
    let touchStart = null;
    const cont = document.getElementById('g2048-grid');
    cont.addEventListener('touchstart', e => { touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY }; });
    cont.addEventListener('touchend', e => {
      if (!touchStart) return;
      const dx = e.changedTouches[0].clientX - touchStart.x;
      const dy = e.changedTouches[0].clientY - touchStart.y;
      if (Math.abs(dx) + Math.abs(dy) < 30) return;
      if (Math.abs(dx) > Math.abs(dy)) move(dx > 0 ? 'right' : 'left');
      else move(dy > 0 ? 'down' : 'up');
      touchStart = null;
    });

    addRandom();
    addRandom();
    render();

    // Store cleanup for keydown listener
    container._g2048cleanup = () => document.removeEventListener('keydown', keyHandler);
  }

  function cleanup() {
    const container = document.getElementById('reward-game-container');
    if (container && container._g2048cleanup) container._g2048cleanup();
  }

  registerGame('mini_2048', 'Mini 2048', '🔢', init, cleanup);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 8: GRAVITY COLLECTOR
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  let _raf = null, _timer = null;

  function init(container, onComplete) {
    container.innerHTML = `
      <p class="text-realm-purple-300 text-sm text-center mb-2">Arrow keys to move · Collect stars! 45 seconds</p>
      <canvas id="gc-canvas" width="280" height="280" style="display:block;margin:0 auto;border-radius:0.75rem;background:radial-gradient(ellipse at center, #1a0533, #0d001a);"></canvas>
      <div class="flex justify-between mt-2" style="max-width:280px;margin:0 auto;">
        <span id="gc-score" class="text-realm-gold-400 font-bold">⭐ 0</span>
        <span id="gc-timer" class="text-realm-purple-300 font-bold">45s</span>
      </div>
      <div id="gc-mobile" class="flex justify-center gap-2 mt-2">
        <button data-k="ArrowLeft" class="px-3 py-2 bg-realm-purple-700 rounded-lg">⬅️</button>
        <div class="flex flex-col gap-2">
          <button data-k="ArrowUp" class="px-3 py-2 bg-realm-purple-700 rounded-lg">⬆️</button>
          <button data-k="ArrowDown" class="px-3 py-2 bg-realm-purple-700 rounded-lg">⬇️</button>
        </div>
        <button data-k="ArrowRight" class="px-3 py-2 bg-realm-purple-700 rounded-lg">➡️</button>
      </div>
    `;

    const canvas = document.getElementById('gc-canvas');
    const ctx = canvas.getContext('2d');
    const W = 280, H = 280;
    const CX = W / 2, CY = H / 2;
    let ship = { x: CX, y: CY - 60, vx: 0, vy: 0 };
    let stars = [];
    let score = 0, timeLeft = 45, active = true;
    const keys = {};

    function spawnStar() {
      const angle = Math.random() * Math.PI * 2;
      const dist = 50 + Math.random() * 80;
      stars.push({
        x: CX + Math.cos(angle) * dist,
        y: CY + Math.sin(angle) * dist,
        angle, dist, speed: 0.005 + Math.random() * 0.01,
        size: 3 + Math.random() * 3,
      });
    }
    for (let i = 0; i < 6; i++) spawnStar();

    _timer = setInterval(() => {
      if (!active) return;
      timeLeft--;
      const el = document.getElementById('gc-timer');
      if (el) el.textContent = timeLeft + 's';
      if (timeLeft <= 0) {
        active = false;
        clearInterval(_timer);
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = '#fbbf24';
        ctx.font = 'bold 22px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('⭐ ' + score + ' stars collected!', W/2, H/2);
        setTimeout(() => onComplete(), 2000);
      }
    }, 1000);

    function update() {
      if (!active) return;
      // Ship movement with mild gravity toward center
      const gx = (CX - ship.x) * 0.0008;
      const gy = (CY - ship.y) * 0.0008;
      if (keys['ArrowLeft'] || keys['a']) ship.vx -= 0.3;
      if (keys['ArrowRight'] || keys['d']) ship.vx += 0.3;
      if (keys['ArrowUp'] || keys['w']) ship.vy -= 0.3;
      if (keys['ArrowDown'] || keys['s']) ship.vy += 0.3;
      ship.vx = (ship.vx + gx) * 0.97;
      ship.vy = (ship.vy + gy) * 0.97;
      ship.x += ship.vx;
      ship.y += ship.vy;
      // Boundary wrap
      if (ship.x < 0) ship.x = W;
      if (ship.x > W) ship.x = 0;
      if (ship.y < 0) ship.y = H;
      if (ship.y > H) ship.y = 0;

      // Orbit stars
      stars.forEach(s => {
        s.angle += s.speed;
        s.x = CX + Math.cos(s.angle) * s.dist;
        s.y = CY + Math.sin(s.angle) * s.dist;
      });

      // Collect stars
      stars = stars.filter(s => {
        const dx = s.x - ship.x, dy = s.y - ship.y;
        if (Math.sqrt(dx * dx + dy * dy) < 14) {
          score++;
          const el = document.getElementById('gc-score');
          if (el) el.textContent = '⭐ ' + score;
          spawnStar();
          return false;
        }
        return true;
      });
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);
      // Centre gravitational object
      ctx.beginPath();
      ctx.arc(CX, CY, 12, 0, Math.PI * 2);
      ctx.fillStyle = '#7c3aed';
      ctx.fill();
      ctx.strokeStyle = '#a78bfa';
      ctx.lineWidth = 2;
      ctx.stroke();
      // Stars
      stars.forEach(s => {
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
        ctx.fillStyle = '#fbbf24';
        ctx.shadowBlur = 8;
        ctx.shadowColor = '#fbbf24';
        ctx.fill();
        ctx.shadowBlur = 0;
      });
      // Ship
      ctx.beginPath();
      ctx.arc(ship.x, ship.y, 8, 0, Math.PI * 2);
      ctx.fillStyle = '#10b981';
      ctx.fill();
      ctx.strokeStyle = '#34d399';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    function loop() {
      update();
      draw();
      if (active) _raf = requestAnimationFrame(loop);
    }

    const keyDown = e => { keys[e.key] = true; };
    const keyUp = e => { keys[e.key] = false; };
    document.addEventListener('keydown', keyDown);
    document.addEventListener('keyup', keyUp);

    // Mobile controls
    let _mobileInts = [];
    document.querySelectorAll('#gc-mobile button').forEach(btn => {
      btn.addEventListener('touchstart', e => {
        e.preventDefault();
        const k = btn.dataset.k;
        const int = setInterval(() => { keys[k] = true; }, 30);
        _mobileInts.push(int);
        btn._int = int;
      });
      btn.addEventListener('touchend', () => {
        keys[btn.dataset.k] = false;
        clearInterval(btn._int);
      });
    });

    _raf = requestAnimationFrame(loop);

    container._gcCleanup = () => {
      document.removeEventListener('keydown', keyDown);
      document.removeEventListener('keyup', keyUp);
      _mobileInts.forEach(i => clearInterval(i));
    };
  }

  function cleanup() {
    if (_raf) cancelAnimationFrame(_raf);
    if (_timer) clearInterval(_timer);
    _raf = null;
    _timer = null;
    const c = document.getElementById('reward-game-container');
    if (c && c._gcCleanup) c._gcCleanup();
  }

  registerGame('gravity_collector', 'Gravity Collector', '🌌', init, cleanup);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 9: TANGRAM BUILDER (SVG drag-and-drop)
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  let _pointerHandlers = null;

  function init(container, onComplete) {
    container.innerHTML = `
      <p id="tg-instruction" class="text-realm-purple-300 text-sm text-center mb-2">Loading puzzle…</p>
      <div id="tg-area" style="position:relative;max-width:400px;margin:0 auto;"></div>
      <div id="tg-controls" class="flex justify-center gap-3 mt-2">
        <button id="tg-rot-ccw" class="px-3 py-1 bg-realm-purple-700 hover:bg-realm-purple-600 text-white rounded-lg text-sm font-bold">↺ Rotate</button>
        <button id="tg-flip" class="px-3 py-1 bg-realm-purple-700 hover:bg-realm-purple-600 text-white rounded-lg text-sm font-bold">↔ Flip</button>
        <button id="tg-rot-cw" class="px-3 py-1 bg-realm-purple-700 hover:bg-realm-purple-600 text-white rounded-lg text-sm font-bold">Rotate ↻</button>
      </div>
      <div class="flex justify-between mt-2" style="max-width:400px;margin:4px auto;">
        <span id="tg-count" class="text-realm-purple-300 text-sm">0 / 7 placed</span>
        <span id="tg-msg" class="text-lg font-bold"></span>
      </div>
    `;

    // Load puzzle list from API, then pick random
    fetch('/api/tangram/puzzles')
      .then(r => r.json())
      .then(list => {
        if (!list.length) throw new Error('no puzzles');
        const pick = list[Math.floor(Math.random() * list.length)];
        return fetch('/api/tangram/puzzle/' + pick.id).then(r => r.json());
      })
      .then(puzzle => initPuzzle(container, puzzle, onComplete))
      .catch(() => {
        const el = document.getElementById('tg-instruction');
        if (el) el.textContent = 'Could not load puzzle.';
      });
  }

  function initPuzzle(container, puzzle, onComplete) {
    const board = puzzle.board;
    const rotStep = puzzle.rules.rotationStepDeg || 15;
    document.getElementById('tg-instruction').textContent =
      'Drag pieces to build the "' + puzzle.title + '" · tap piece then rotate buttons';

    const area = document.getElementById('tg-area');
    const svgNS = 'http://www.w3.org/2000/svg';

    // Create SVG
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + board.width + ' ' + board.height);
    svg.setAttribute('width', '100%');
    svg.style.display = 'block';
    svg.style.borderRadius = '0.75rem';
    svg.style.background = 'rgba(88,28,135,0.3)';
    svg.style.border = '2px solid rgba(139,92,246,0.3)';
    svg.style.touchAction = 'none';
    svg.style.userSelect = 'none';
    area.appendChild(svg);

    // Draw play area boundary (subtle)
    const pa = board.playArea;
    const playRect = document.createElementNS(svgNS, 'rect');
    playRect.setAttribute('x', pa.x);
    playRect.setAttribute('y', pa.y);
    playRect.setAttribute('width', pa.w);
    playRect.setAttribute('height', pa.h);
    playRect.setAttribute('fill', 'rgba(139,92,246,0.08)');
    playRect.setAttribute('stroke', 'rgba(139,92,246,0.2)');
    playRect.setAttribute('stroke-width', '1');
    playRect.setAttribute('stroke-dasharray', '4,4');
    playRect.setAttribute('rx', '8');
    svg.appendChild(playRect);

    // Draw tray area boundary
    const ta = board.trayArea;
    const trayRect = document.createElementNS(svgNS, 'rect');
    trayRect.setAttribute('x', ta.x);
    trayRect.setAttribute('y', ta.y);
    trayRect.setAttribute('width', ta.w);
    trayRect.setAttribute('height', ta.h);
    trayRect.setAttribute('fill', 'rgba(88,28,135,0.25)');
    trayRect.setAttribute('stroke', 'rgba(139,92,246,0.15)');
    trayRect.setAttribute('stroke-width', '1');
    trayRect.setAttribute('rx', '8');
    svg.appendChild(trayRect);

    function polyToPoints(verts) {
      return verts.map(v => v[0] + ',' + v[1]).join(' ');
    }
    function svgTransform(x, y, rot, flipped) {
      let tf = 'translate(' + x + ',' + y + ') rotate(' + rot + ')';
      if (flipped) tf += ' scale(-1,1)';
      return tf;
    }
    function polyKey(polygon) {
      return polygon.map(v => v.join(',')).join(';');
    }

    // Build target slots grouped by polygon shape (for interchangeable pieces)
    //   { polyKey → [{ x, y, rot, flipped, snapDist, snapRot, claimed: false }] }
    const targetSlots = {};
    puzzle.pieces.forEach(p => {
      const key = polyKey(p.polygon);
      if (!targetSlots[key]) targetSlots[key] = [];
      targetSlots[key].push({
        x: p.targetPose.position.x,
        y: p.targetPose.position.y,
        rot: p.targetPose.rotationDeg,
        flipped: !!(p.targetPose.flipped),
        snapDist: p.snap.distPx,
        snapRot: p.snap.rotDeg,
        claimed: false,
      });
    });

    // Draw a single merged silhouette of all target pieces.
    // We transform each piece's polygon to world coordinates, then build
    // a single <path> from their outlines so no internal lines are visible.
    function transformPoly(polygon, x, y, rotDeg, flipped) {
      const rad = rotDeg * Math.PI / 180;
      const cosR = Math.cos(rad), sinR = Math.sin(rad);
      return polygon.map(function(v) {
        let vx = v[0], vy = v[1];
        if (flipped) vx = -vx;
        const rx = vx * cosR - vy * sinR;
        const ry = vx * sinR + vy * cosR;
        return [rx + x, ry + y];
      });
    }

    // Build a single compound SVG path from all target piece polygons
    let silhouettePath = '';
    puzzle.pieces.forEach(function(p) {
      const tp = p.targetPose;
      const worldPts = transformPoly(p.polygon, tp.position.x, tp.position.y,
                                      tp.rotationDeg, !!(tp.flipped));
      silhouettePath += 'M' + worldPts.map(function(pt) {
        return pt[0].toFixed(2) + ',' + pt[1].toFixed(2);
      }).join('L') + 'Z ';
    });

    // SVG filter: dilate slightly to close sub-pixel gaps, then soften edges
    const defs = document.createElementNS(svgNS, 'defs');
    const filter = document.createElementNS(svgNS, 'filter');
    filter.setAttribute('id', 'tg-shadow-filter');
    filter.setAttribute('x', '-5%');
    filter.setAttribute('y', '-5%');
    filter.setAttribute('width', '110%');
    filter.setAttribute('height', '110%');
    // Dilate to close tiny gaps between adjacent pieces
    const morph = document.createElementNS(svgNS, 'feMorphology');
    morph.setAttribute('operator', 'dilate');
    morph.setAttribute('radius', '1');
    morph.setAttribute('in', 'SourceAlpha');
    morph.setAttribute('result', 'dilated');
    filter.appendChild(morph);
    // Slight blur on the dilated shape
    const blur = document.createElementNS(svgNS, 'feGaussianBlur');
    blur.setAttribute('in', 'dilated');
    blur.setAttribute('stdDeviation', '0.5');
    blur.setAttribute('result', 'blurred');
    filter.appendChild(blur);
    // Flood with the silhouette colour
    const flood = document.createElementNS(svgNS, 'feFlood');
    flood.setAttribute('flood-color', 'rgba(139,92,246,0.18)');
    flood.setAttribute('result', 'color');
    filter.appendChild(flood);
    // Composite: use blurred alpha as mask for the colour
    const comp = document.createElementNS(svgNS, 'feComposite');
    comp.setAttribute('in', 'color');
    comp.setAttribute('in2', 'blurred');
    comp.setAttribute('operator', 'in');
    filter.appendChild(comp);
    defs.appendChild(filter);
    svg.appendChild(defs);

    const ghostPath = document.createElementNS(svgNS, 'path');
    ghostPath.setAttribute('d', silhouettePath);
    ghostPath.setAttribute('fill', 'rgba(139,92,246,0.15)');
    ghostPath.setAttribute('stroke', 'none');
    ghostPath.setAttribute('fill-rule', 'nonzero');
    ghostPath.setAttribute('filter', 'url(#tg-shadow-filter)');
    svg.appendChild(ghostPath);

    // Piece state
    const pieces = puzzle.pieces.map(p => ({
      id: p.id,
      polygon: p.polygon,
      polyKey: polyKey(p.polygon),
      color: p.color,
      x: p.startPose.position.x,
      y: p.startPose.position.y,
      rotation: p.startPose.rotationDeg,
      flipped: !!(p.startPose && p.startPose.flipped),
      locked: false,
      el: null,
    }));

    let selectedIdx = -1;
    let dragging = false;
    let dragOffset = { x: 0, y: 0 };
    let lockedCount = 0;

    // Create piece SVG elements
    pieces.forEach((p, idx) => {
      const g = document.createElementNS(svgNS, 'g');
      g.style.cursor = 'grab';

      const poly = document.createElementNS(svgNS, 'polygon');
      poly.setAttribute('points', polyToPoints(p.polygon));
      poly.setAttribute('fill', p.color);
      poly.setAttribute('stroke', '#fff');
      poly.setAttribute('stroke-width', '1.5');
      poly.setAttribute('stroke-linejoin', 'round');
      g.appendChild(poly);

      g.setAttribute('transform', svgTransform(p.x, p.y, p.rotation, p.flipped));
      g.dataset.idx = idx;
      svg.appendChild(g);
      p.el = g;
    });

    function selectPiece(idx) {
      if (selectedIdx >= 0 && pieces[selectedIdx] && pieces[selectedIdx].el) {
        const oldPoly = pieces[selectedIdx].el.querySelector('polygon');
        if (oldPoly && !pieces[selectedIdx].locked) oldPoly.setAttribute('stroke', '#fff');
      }
      selectedIdx = idx;
      if (idx >= 0 && !pieces[idx].locked) {
        svg.appendChild(pieces[idx].el);
        const poly = pieces[idx].el.querySelector('polygon');
        if (poly) poly.setAttribute('stroke', '#fbbf24');
      }
    }

    function checkSnap(p) {
      // Try all unclaimed target slots that share this piece's polygon shape
      const slots = targetSlots[p.polyKey];
      if (!slots) return false;

      for (const slot of slots) {
        if (slot.claimed) continue;

        const dx = p.x - slot.x;
        const dy = p.y - slot.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        let rotDiff = ((p.rotation - slot.rot) % 360 + 540) % 360 - 180;

        if (dist <= slot.snapDist && Math.abs(rotDiff) <= slot.snapRot && p.flipped === slot.flipped) {
          // Snap to this slot!
          p.x = slot.x;
          p.y = slot.y;
          p.rotation = slot.rot;
          p.flipped = slot.flipped;
          p.locked = true;
          slot.claimed = true;
          p.el.setAttribute('transform', svgTransform(p.x, p.y, p.rotation, p.flipped));
          p.el.style.cursor = 'default';
          p.el.style.opacity = '0.85';
          const poly = p.el.querySelector('polygon');
          if (poly) { poly.setAttribute('stroke', '#10b981'); poly.setAttribute('stroke-width', '2'); }
          lockedCount++;

          const countEl = document.getElementById('tg-count');
          if (countEl) countEl.textContent = lockedCount + ' / ' + pieces.length + ' placed';

          if (lockedCount >= pieces.length) {
            const msgEl = document.getElementById('tg-msg');
            if (msgEl) { msgEl.textContent = '🎉 Beautiful!'; msgEl.style.color = '#10b981'; }
            const instrEl = document.getElementById('tg-instruction');
            if (instrEl) instrEl.textContent = 'Puzzle complete!';
            setTimeout(() => onComplete(), 1800);
          }
          return true;
        }
      }
      return false;
    }

    // Get SVG coordinates from mouse/touch event
    function svgPoint(e) {
      const pt = svg.createSVGPoint();
      const touch = e.touches ? e.touches[0] : e;
      pt.x = touch.clientX;
      pt.y = touch.clientY;
      const ctm = svg.getScreenCTM().inverse();
      return pt.matrixTransform(ctm);
    }

    function onPointerDown(e) {
      const target = e.target.closest('g[data-idx]');
      if (!target) { selectPiece(-1); return; }
      const idx = parseInt(target.dataset.idx);
      if (pieces[idx].locked) return;

      e.preventDefault();
      selectPiece(idx);
      dragging = true;

      const pt = svgPoint(e);
      dragOffset.x = pt.x - pieces[idx].x;
      dragOffset.y = pt.y - pieces[idx].y;
      target.style.cursor = 'grabbing';
    }

    function onPointerMove(e) {
      if (!dragging || selectedIdx < 0) return;
      e.preventDefault();
      const p = pieces[selectedIdx];
      if (p.locked) return;

      const pt = svgPoint(e);
      p.x = pt.x - dragOffset.x;
      p.y = pt.y - dragOffset.y;
      p.el.setAttribute('transform', svgTransform(p.x, p.y, p.rotation, p.flipped));
    }

    function onPointerUp(e) {
      if (!dragging || selectedIdx < 0) return;
      dragging = false;
      const p = pieces[selectedIdx];
      if (!p.locked) {
        p.el.style.cursor = 'grab';
        checkSnap(p);
      }
    }

    svg.addEventListener('mousedown', onPointerDown);
    svg.addEventListener('mousemove', onPointerMove);
    svg.addEventListener('mouseup', onPointerUp);
    svg.addEventListener('mouseleave', onPointerUp);
    svg.addEventListener('touchstart', onPointerDown, { passive: false });
    svg.addEventListener('touchmove', onPointerMove, { passive: false });
    svg.addEventListener('touchend', onPointerUp);

    _pointerHandlers = { svg, onPointerDown, onPointerMove, onPointerUp };

    document.getElementById('tg-rot-ccw').addEventListener('click', () => {
      if (selectedIdx < 0 || pieces[selectedIdx].locked) return;
      const p = pieces[selectedIdx];
      p.rotation = (p.rotation - rotStep + 360) % 360;
      p.el.setAttribute('transform', svgTransform(p.x, p.y, p.rotation, p.flipped));
      checkSnap(p);
    });
    document.getElementById('tg-rot-cw').addEventListener('click', () => {
      if (selectedIdx < 0 || pieces[selectedIdx].locked) return;
      const p = pieces[selectedIdx];
      p.rotation = (p.rotation + rotStep) % 360;
      p.el.setAttribute('transform', svgTransform(p.x, p.y, p.rotation, p.flipped));
      checkSnap(p);
    });
    document.getElementById('tg-flip').addEventListener('click', () => {
      if (selectedIdx < 0 || pieces[selectedIdx].locked) return;
      const p = pieces[selectedIdx];
      p.flipped = !p.flipped;
      p.el.setAttribute('transform', svgTransform(p.x, p.y, p.rotation, p.flipped));
      checkSnap(p);
    });
  }

  function cleanup() {
    if (_pointerHandlers) {
      const { svg, onPointerDown, onPointerMove, onPointerUp } = _pointerHandlers;
      svg.removeEventListener('mousedown', onPointerDown);
      svg.removeEventListener('mousemove', onPointerMove);
      svg.removeEventListener('mouseup', onPointerUp);
      svg.removeEventListener('mouseleave', onPointerUp);
      svg.removeEventListener('touchstart', onPointerDown);
      svg.removeEventListener('touchmove', onPointerMove);
      svg.removeEventListener('touchend', onPointerUp);
      _pointerHandlers = null;
    }
  }

  registerGame('tangram', 'Tangram Builder', '🔷', init, cleanup);
})();


/* ═══════════════════════════════════════════════════════════════════
   GAME 10: PIXEL ART REVEAL
   ═══════════════════════════════════════════════════════════════════ */
(function() {
  // Simple pixel art images (8×8, each cell is a hex color or '' for blank)
  const ARTWORKS = [
    { name: 'Castle', pixels: [
      '','#888','#888','#fbbf24','#fbbf24','#888','#888','',
      '','#888','#888','#888','#888','#888','#888','',
      '#888','#888','#888','#888','#888','#888','#888','#888',
      '#888','','#6d28d9','','','#6d28d9','','#888',
      '#888','','#6d28d9','','','#6d28d9','','#888',
      '#888','#888','#888','#6d28d9','#6d28d9','#888','#888','#888',
      '#888','#888','#888','#6d28d9','#6d28d9','#888','#888','#888',
      '#10b981','#10b981','#888','#888','#888','#888','#10b981','#10b981',
    ]},
    { name: 'Cat', pixels: [
      '','','#f59e0b','','','#f59e0b','','',
      '','#f59e0b','#f59e0b','#f59e0b','#f59e0b','#f59e0b','#f59e0b','',
      '#f59e0b','#f59e0b','#10b981','#f59e0b','#f59e0b','#10b981','#f59e0b','#f59e0b',
      '#f59e0b','#f59e0b','#f59e0b','#ef4444','#ef4444','#f59e0b','#f59e0b','#f59e0b',
      '','#f59e0b','#f59e0b','#f59e0b','#f59e0b','#f59e0b','#f59e0b','',
      '','','#f59e0b','#f59e0b','#f59e0b','#f59e0b','','',
      '','#f59e0b','','#f59e0b','#f59e0b','','#f59e0b','',
      '','#f59e0b','','','','','#f59e0b','',
    ]},
    { name: 'Landscape', pixels: [
      '#3b82f6','#3b82f6','#3b82f6','#3b82f6','#3b82f6','#3b82f6','#fbbf24','#3b82f6',
      '#3b82f6','#3b82f6','#3b82f6','#3b82f6','#3b82f6','#fbbf24','#fbbf24','#fbbf24',
      '#3b82f6','#3b82f6','#888','#3b82f6','#3b82f6','#3b82f6','#3b82f6','#3b82f6',
      '#3b82f6','#888','#888','#888','#3b82f6','#3b82f6','#3b82f6','#3b82f6',
      '#888','#888','#10b981','#888','#888','#3b82f6','#888','#3b82f6',
      '#10b981','#10b981','#10b981','#10b981','#10b981','#888','#888','#888',
      '#10b981','#10b981','#10b981','#10b981','#10b981','#10b981','#10b981','#10b981',
      '#92400e','#92400e','#10b981','#10b981','#10b981','#10b981','#92400e','#92400e',
    ]},
  ];

  function init(container, onComplete) {
    // Pick artwork, reveal tiles progressively on click
    const art = ARTWORKS[Math.floor(Math.random() * ARTWORKS.length)];
    const total = art.pixels.filter(p => p).length;
    let revealed = 0;

    container.innerHTML = `
      <p class="text-realm-purple-300 text-sm text-center mb-2">Tap tiles to reveal the "${art.name}" pixel art!</p>
      <div id="pa-grid" style="display:grid;grid-template-columns:repeat(8,1fr);gap:2px;max-width:280px;margin:0 auto 8px auto;"></div>
      <div class="flex justify-between" style="max-width:280px;margin:0 auto;">
        <span id="pa-count" class="text-realm-purple-300 text-sm">${revealed}/${total}</span>
        <span id="pa-msg" class="text-lg font-bold"></span>
      </div>
    `;

    const grid = document.getElementById('pa-grid');
    for (let i = 0; i < 64; i++) {
      const cell = document.createElement('button');
      const hasColor = !!art.pixels[i];
      Object.assign(cell.style, {
        width: '32px', height: '32px', borderRadius: '4px',
        border: '1px solid rgba(139,92,246,0.3)',
        background: hasColor ? 'rgba(88,28,135,0.6)' : 'transparent',
        cursor: hasColor ? 'pointer' : 'default',
        transition: 'all 0.3s',
      });

      if (hasColor) {
        cell.addEventListener('click', () => {
          if (cell.dataset.revealed) return;
          cell.dataset.revealed = '1';
          cell.style.background = art.pixels[i];
          cell.style.borderColor = art.pixels[i];
          cell.style.cursor = 'default';
          revealed++;
          document.getElementById('pa-count').textContent = revealed + '/' + total;
          if (revealed >= total) {
            const msg = document.getElementById('pa-msg');
            msg.textContent = '🎨 Beautiful!';
            msg.style.color = '#10b981';
            setTimeout(() => onComplete(), 1500);
          }
        });
      }

      grid.appendChild(cell);
    }
  }

  registerGame('pixel_art', 'Pixel Art Reveal', '🎨', init);
})();


/* ═══════════════════════════════════════════════════════════════════
   ADMIN: Game preview / toggle support
   ═══════════════════════════════════════════════════════════════════ */
function previewGame(gameId) {
  openRewardGame(gameId);
}

function toggleGame(gameId, checkbox) {
  fetch('/admin/games/toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId, enabled: checkbox.checked }),
  }).then(r => r.json()).then(data => {
    if (data.status !== 'ok') {
      checkbox.checked = !checkbox.checked;
      alert('Failed to toggle game');
    }
  });
}
