import { Chessground } from 'https://cdn.jsdelivr.net/npm/chessground@9.2.1/dist/chessground.min.js';

const { Chess } = window;

const ENGINE_NAME = 'Nuwanda';
const ENGINE_MOVE_URL = '/api/engine-move';
const PIECE_GLYPHS = {
  w: { q: '♕', r: '♖', b: '♗', n: '♘' },
  b: { q: '♛', r: '♜', b: '♝', n: '♞' },
};
const CAPTURE_ORDER = ['q', 'r', 'b', 'n', 'p'];
const CAPTURE_PIECE_URLS = {
  w: {
    q: 'https://chessboardjs.com/img/chesspieces/wikipedia/wQ.png',
    r: 'https://chessboardjs.com/img/chesspieces/wikipedia/wR.png',
    b: 'https://chessboardjs.com/img/chesspieces/wikipedia/wB.png',
    n: 'https://chessboardjs.com/img/chesspieces/wikipedia/wN.png',
    p: 'https://chessboardjs.com/img/chesspieces/wikipedia/wP.png',
  },
  b: {
    q: 'https://chessboardjs.com/img/chesspieces/wikipedia/bQ.png',
    r: 'https://chessboardjs.com/img/chesspieces/wikipedia/bR.png',
    b: 'https://chessboardjs.com/img/chesspieces/wikipedia/bB.png',
    n: 'https://chessboardjs.com/img/chesspieces/wikipedia/bN.png',
    p: 'https://chessboardjs.com/img/chesspieces/wikipedia/bP.png',
  },
};

const toCgColor = (color) => (color === 'w' ? 'white' : 'black');

const boardEl = document.getElementById('board');
const labelTop = document.getElementById('label-top');
const labelBottom = document.getElementById('label-bottom');
const statusEl = document.getElementById('status');
const moveListEl = document.getElementById('move-list');
const thinkingOverlay = document.getElementById('thinking-overlay');
const thinkingText = document.getElementById('thinking-text');
const promotionOverlay = document.getElementById('promotion-overlay');
const errorBox = document.getElementById('error-box');
const errorText = document.getElementById('error-text');
const nameModal = document.getElementById('name-modal');
const nameForm = document.getElementById('name-form');
const nameInput = document.getElementById('player-name');
const optionsToggle = document.getElementById('btn-options');
const optionsPanel = document.getElementById('options-panel');
const themeToggle = document.getElementById('btn-theme');
const fenForm = document.getElementById('fen-form');
const fenInput = document.getElementById('fen-input');
const timeSelect = document.getElementById('engine-time');
const selfPlayBtn = document.getElementById('btn-self-play') || (() => {
  const button = document.createElement('button');
  button.id = 'btn-self-play';
  button.type = 'button';
  button.textContent = 'Self-play';
  document.querySelector('.controls').appendChild(button);
  return button;
})();
const hintBtn = document.getElementById('btn-hint') || (() => {
  const button = document.createElement('button');
  button.id = 'btn-hint';
  button.type = 'button';
  button.textContent = 'HINT';
  document.querySelector('.board-column').appendChild(button);
  return button;
})();
const pgnBtn = document.getElementById('btn-copy-pgn');
const capturedTopEl = document.getElementById('captured-top');
const capturedBottomEl = document.getElementById('captured-bottom');
const evalBarEl = document.getElementById('eval-bar');
const evalBarWhiteEl = document.getElementById('eval-bar-white');
const evalBarScoreEl = document.getElementById('eval-bar-score');

function currentTheme() {
  return document.documentElement.dataset.theme
    || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}

function updateThemeToggle() {
  const isDark = currentTheme() === 'dark';
  themeToggle.textContent = 'Light mode';
  themeToggle.setAttribute('aria-pressed', String(!isDark));
}

themeToggle.addEventListener('click', () => {
  const nextTheme = currentTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = nextTheme;
  try { localStorage.setItem('nuwanda-theme', nextTheme); } catch (_) {}
  updateThemeToggle();
});
updateThemeToggle();

// Keep the controls in their intended sections even if cached markup is served.
document.getElementById('error-box').insertAdjacentElement('afterend', hintBtn);
moveListEl.insertAdjacentElement('afterend', pgnBtn);

let game = new Chess();
let startingFen = game.fen();
let playerColor = 'w';
let selfPlay = false;
let playerName = 'Player';
let orientation = 'w';
let thinking = false;
let hinting = false;
let lastMove = null;
let bestMoveHint = null;
let pendingPromotion = null;
let gameGen = 0;
let copyFlashTimer = null;

const engineInfoByPly = new Map();
const hintInfoByPly = new Map();

const board = Chessground(boardEl, {
  movable: {
    free: false,
    color: 'white',
    dests: new Map(),
    events: { after: onBoardMove },
  },
  events: {},
});

function destsFromGame() {
  const dests = new Map();
  for (const square of game.SQUARES) {
    const moves = game.moves({ square, verbose: true });
    if (moves.length) {
      dests.set(square, [...new Set(moves.map((m) => m.to))]);
    }
  }
  return dests;
}

function playerCanMove() {
  if (selfPlay || thinking || pendingPromotion || game.game_over()) return false;
  return game.turn() === playerColor;
}

function syncBoard() {
  board.set({
    fen: game.fen(),
    orientation: toCgColor(orientation),
    turnColor: toCgColor(game.turn()),
    movable: {
      color: playerCanMove() ? toCgColor(playerColor) : undefined,
      dests: destsFromGame(),
    },
    check: game.in_check(),
    lastMove: lastMove || undefined,
  });
  board.setShapes(bestMoveHint ? [{
    orig: bestMoveHint.slice(0, 2),
    dest: bestMoveHint.slice(2, 4),
    brush: 'green',
  }] : []);
  renderCaptured();
}

function onBoardMove(from, to) {
  if (!playerCanMove()) { syncBoard(); return; }
  const candidates = game.moves({ square: from, verbose: true })
    .filter((m) => m.to === to);
  if (!candidates.length) { syncBoard(); return; }
  if (candidates.some((m) => m.promotion)) {
    pendingPromotion = { from, to };
    syncBoard();
    openPromotionPicker();
    return;
  }
  commitPlayerMove({ from, to });
}

function commitPlayerMove(spec) {
  const move = game.move(spec);
  if (!move) { syncBoard(); return; }
  bestMoveHint = null;
  lastMove = [move.from, move.to];
  syncBoard();
  renderMoveList();
  updateStatus();
  if (game.game_over()) { showGameOver(); return; }
  requestEngineMove();
}

function openPromotionPicker() {
  const glyphs = PIECE_GLYPHS[game.turn()];
  promotionOverlay.querySelectorAll('button[data-piece]').forEach((btn) => {
    btn.textContent = glyphs[btn.dataset.piece];
  });
  promotionOverlay.hidden = false;
}

function closePromotionPicker() {
  promotionOverlay.hidden = true;
  pendingPromotion = null;
}

promotionOverlay.querySelectorAll('button[data-piece]').forEach((btn) => {
  btn.addEventListener('click', () => {
    if (!pendingPromotion) return;
    const spec = { ...pendingPromotion, promotion: btn.dataset.piece };
    closePromotionPicker();
    commitPlayerMove(spec);
  });
});

promotionOverlay.addEventListener('click', (event) => {
  if (event.target !== promotionOverlay) return;
  closePromotionPicker();
  syncBoard();
});


function uciMoves() {
  return game.history({ verbose: true })
    .map((m) => m.from + m.to + (m.promotion || ''));
}

async function requestEngineMove() {
  const gen = gameGen;
  thinking = true;
  hideError();
  thinkingText.textContent = `${ENGINE_NAME} is thinking…`;
  updateStatus();
  syncBoard();

  try {
    const response = await fetch(ENGINE_MOVE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fen: startingFen,
        moves: uciMoves(),
        time: Number(timeSelect.value),
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (gen !== gameGen) return;
    if (!response.ok || data.error) {
      throw new Error(data.error || `engine request failed (HTTP ${response.status})`);
    }

    updateEvalBar(data.eval, game.turn());
    bestMoveHint = data.move;
    thinking = false;
    syncBoard();
    statusEl.textContent = `Best move: ${data.san}`;
    await new Promise((resolve) => setTimeout(resolve, 450));
    if (gen !== gameGen) return;

    const spec = { from: data.move.slice(0, 2), to: data.move.slice(2, 4) };
    if (data.move.length > 4) spec.promotion = data.move.slice(4);
    const move = game.move(spec);
    if (!move) throw new Error(`engine returned an illegal move: ${data.move}`);

    lastMove = [move.from, move.to];
    bestMoveHint = null;
    engineInfoByPly.set(game.history().length, {
      depth: data.depth, eval: data.eval, nodes: data.nodes,
    });
    syncBoard();
    renderMoveList();
    updateStatus();
    if (game.game_over()) showGameOver();
    else if (selfPlay) requestEngineMove();
  } catch (err) {
    if (gen !== gameGen) return;
    thinking = false;
    syncBoard();
    updateStatus();
    showError(err.message);
  }
}

async function requestBestMoveHint() {
  if (thinking || game.game_over() || game.turn() !== playerColor) return;
  const gen = gameGen;
  hinting = true;
  thinking = true;
  updateStatus();
  syncBoard();
  try {
    const response = await fetch(ENGINE_MOVE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fen: startingFen, moves: uciMoves(), time: Number(timeSelect.value) }),
    });
    const data = await response.json().catch(() => ({}));
    if (gen !== gameGen) return;
    if (!response.ok || data.error) {
      throw new Error(data.error || `engine request failed (HTTP ${response.status})`);
    }
    updateEvalBar(data.eval, game.turn());
    bestMoveHint = data.move;
    hintInfoByPly.set(game.history().length, {
      move: data.san,
      depth: data.depth,
      eval: data.eval,
      nodes: data.nodes,
    });
    thinking = false;
    hinting = false;
    syncBoard();
    renderMoveList();
    updateStatus();
    statusEl.textContent = `Best move: ${data.san}`;
  } catch (err) {
    if (gen !== gameGen) return;
    thinking = false;
    hinting = false;
    syncBoard();
    updateStatus();
    showError(err.message);
  }
}

function newGame(color) {
  gameGen += 1;
  selfPlay = color === 'self';
  playerColor = selfPlay ? 'w' : color;
  orientation = selfPlay ? 'w' : color;
  game = new Chess();
  startingFen = game.fen();
  updateEvalBar(0, 'w');
  hinting = false;
  lastMove = null;
  bestMoveHint = null;
  engineInfoByPly.clear();
  hintInfoByPly.clear();
  thinking = false;
  closePromotionPicker();
  hideError();
  syncBoard();
  renderMoveList();
  updateLabels();
  updateStatus();
  if (selfPlay || playerColor === 'b') requestEngineMove();
}

function loadFenPosition(fen) {
  const candidate = new Chess();
  try {
    if (candidate.load(fen) === false) throw new Error('Invalid FEN string.');
  } catch {
    showError('Invalid FEN string. Check the position and try again.');
    return;
  }

  gameGen += 1;
  game = candidate;
  startingFen = game.fen();
  selfPlay = false;
  playerColor = game.turn();
  orientation = playerColor;
  thinking = false;
  hinting = false;
  lastMove = null;
  bestMoveHint = null;
  engineInfoByPly.clear();
  hintInfoByPly.clear();
  updateEvalBar(0, 'w');
  closePromotionPicker();
  hideError();
  fenInput.value = game.fen();
  optionsPanel.hidden = true;
  optionsToggle.setAttribute('aria-expanded', 'false');
  syncBoard();
  renderMoveList();
  updateLabels();
  updateStatus();
}

function gameOverMessage() {
  if (game.in_checkmate()) {
    if (selfPlay) return `Checkmate — ${game.turn() === 'w' ? 'Black' : 'White'} wins!`;
    const winner = game.turn() === playerColor ? ENGINE_NAME : playerName;
    return `Checkmate — ${winner} wins!`;
  }
  if (game.in_stalemate()) return 'Draw — stalemate.';
  if (game.in_threefold_repetition()) return 'Draw — threefold repetition.';
  if (game.insufficient_material()) return 'Draw — insufficient material.';
  if (parseInt(game.fen().split(' ')[4], 10) >= 100) return 'Draw — fifty-move rule.';
  return 'Game over.';
}

function showGameOver() {
  statusEl.textContent = gameOverMessage();
  hideError();
}

function updateStatus() {
  hintBtn.disabled = selfPlay || thinking || game.game_over() || game.turn() !== playerColor;
  hintBtn.textContent = hinting ? 'Finding hint…' : 'HINT';
  if (thinking) {
    if (hinting) {
      statusEl.textContent = 'Finding the best move…';
      return;
    }
    const side = game.turn() === 'w' ? 'White' : 'Black';
    statusEl.textContent = selfPlay
      ? `${ENGINE_NAME} (${side}) is thinking…`
      : `${ENGINE_NAME} is thinking…`;
    return;
  }
  if (game.game_over()) { showGameOver(); return; }
  if (selfPlay) {
    const side = game.turn() === 'w' ? 'White' : 'Black';
    statusEl.textContent = `Self-play: ${ENGINE_NAME} (${side}) to move${game.in_check() ? ' (check)' : ''}`;
    return;
  }
  const side = game.turn() === playerColor ? playerName : ENGINE_NAME;
  statusEl.textContent = `${side} to move${game.in_check() ? ' (check)' : ''}`;
}

function updateLabels() {
  if (selfPlay) {
    labelTop.textContent = orientation === 'w' ? `${ENGINE_NAME} (Black)` : `${ENGINE_NAME} (White)`;
    labelBottom.textContent = orientation === 'w' ? `${ENGINE_NAME} (White)` : `${ENGINE_NAME} (Black)`;
    return;
  }
  const playerBottom = orientation === playerColor;
  labelBottom.textContent = playerBottom ? `${playerName} (you)` : ENGINE_NAME;
  labelTop.textContent = playerBottom ? ENGINE_NAME : `${playerName} (you)`;
}

function formatEval(cp) {
  return `${cp >= 0 ? '+' : ''}${(cp / 100).toFixed(2)}`;
}

function updateEvalBar(scoreCp, sideToMove) {
  const score = Number.isFinite(Number(scoreCp)) ? Number(scoreCp) : 0;
  const whiteScore = sideToMove === 'w' ? score : -score;
  const isMate = Math.abs(whiteScore) >= 99000;
  const whiteShare = isMate
    ? (whiteScore > 0 ? 99 : 1)
    : 50 + 50 * Math.tanh(Math.max(-10000, Math.min(10000, whiteScore)) / 1000);

  evalBarWhiteEl.style.height = `${whiteShare}%`;
  evalBarScoreEl.textContent = isMate
    ? (whiteScore > 0 ? 'M' : '−M')
    : formatEval(whiteScore);
  if (whiteShare >= 50) {
    evalBarScoreEl.style.top = 'auto';
    evalBarScoreEl.style.bottom = '4px';
    evalBarScoreEl.style.color = '#111';
  } else {
    evalBarScoreEl.style.top = '4px';
    evalBarScoreEl.style.bottom = 'auto';
    evalBarScoreEl.style.color = '#fff';
  }
  evalBarEl.setAttribute(
    'aria-label',
    isMate
      ? `Evaluation: ${whiteScore > 0 ? 'White' : 'Black'} has mate`
      : `Evaluation: ${formatEval(whiteScore)} pawns for White`,
  );
}

function capturedByColor() {
  const counts = {
    w: { p: 0, n: 0, b: 0, r: 0, q: 0 },
    b: { p: 0, n: 0, b: 0, r: 0, q: 0 },
  };
  for (const m of game.history({ verbose: true })) {
    if (m.captured) counts[m.color][m.captured] += 1;
  }
  return counts;
}

function fillCaptured(el, counts, pieceColor) {
  el.textContent = '';
  for (const type of CAPTURE_ORDER) {
    for (let i = 0; i < counts[type]; i += 1) {
      const img = document.createElement('img');
      img.src = CAPTURE_PIECE_URLS[pieceColor][type];
      img.alt = '';
      el.appendChild(img);
    }
  }
}

function renderCaptured() {
  const counts = capturedByColor();
  const bottomSide = orientation;
  const topSide = orientation === 'w' ? 'b' : 'w';
  fillCaptured(capturedTopEl, counts[topSide], topSide === 'w' ? 'b' : 'w');
  fillCaptured(capturedBottomEl, counts[bottomSide], bottomSide === 'w' ? 'b' : 'w');
}

function renderMoveList() {
  const history = game.history();
  moveListEl.innerHTML = '';
  appendHintRow(0);
  for (let i = 0; i < history.length; i += 1) {
    const li = document.createElement('li');
    const moveNumber = Math.floor(i / 2) + 1;
    li.append(`${moveNumber}. ${history[i]}`);
    appendEngineInfo(li, i + 1);
    moveListEl.appendChild(li);
    appendHintRow(i + 1);
  }
  moveListEl.scrollTop = moveListEl.scrollHeight;
}

function appendHintRow(positionPly) {
  const info = hintInfoByPly.get(positionPly);
  if (!info) return;
  const li = document.createElement('li');
  li.textContent = `Hint: ${info.move}`;
  const span = document.createElement('span');
  span.className = 'engine-info';
  span.textContent = ` [${info.depth} · ${formatEval(info.eval)} · ${info.nodes} nodes]`;
  li.appendChild(span);
  moveListEl.appendChild(li);
}

function appendEngineInfo(li, ply) {
  const info = engineInfoByPly.get(ply);
  if (!info) return;
  const span = document.createElement('span');
  span.className = 'engine-info';
  span.textContent = ` [${info.depth} · ${formatEval(info.eval)} · ${info.nodes} nodes]`;
  li.appendChild(span);
}

function showError(message) {
  errorText.textContent = message;
  errorBox.hidden = false;
}

function hideError() {
  errorBox.hidden = true;
}

function pgnText() {
  let result = '*';
  if (game.game_over()) {
    result = game.in_checkmate()
      ? (game.turn() === 'w' ? '0-1' : '1-0')
      : '1/2-1/2';
  }
  const white = selfPlay ? ENGINE_NAME : (playerColor === 'w' ? playerName : ENGINE_NAME);
  const black = selfPlay ? ENGINE_NAME : (playerColor === 'b' ? playerName : ENGINE_NAME);
  game.header('White', white, 'Black', black, 'Result', result);
  return game.pgn();
}

async function copyPgn() {
  const pgn = pgnText();
  try {
    await navigator.clipboard.writeText(pgn);
  } catch {
    const ta = document.createElement('textarea');
    ta.value = pgn;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
  }
  pgnBtn.textContent = 'Copied!';
  clearTimeout(copyFlashTimer);
  copyFlashTimer = setTimeout(() => { pgnBtn.textContent = 'Copy PGN'; }, 1500);
}

document.getElementById('btn-new').addEventListener('click', () => newGame(playerColor));
document.getElementById('btn-white').addEventListener('click', () => newGame('w'));
document.getElementById('btn-black').addEventListener('click', () => newGame('b'));
selfPlayBtn.addEventListener('click', () => newGame('self'));
document.getElementById('btn-flip').addEventListener('click', () => {
  orientation = orientation === 'w' ? 'b' : 'w';
  syncBoard();
  updateLabels();
});
document.getElementById('btn-retry').addEventListener('click', () => {
  if (!errorBox.hidden) requestEngineMove();
});
optionsToggle.addEventListener('click', () => {
  optionsPanel.hidden = !optionsPanel.hidden;
  optionsToggle.setAttribute('aria-expanded', String(!optionsPanel.hidden));
  if (!optionsPanel.hidden) fenInput.focus();
});
fenForm.addEventListener('submit', (event) => {
  event.preventDefault();
  loadFenPosition(fenInput.value.trim());
});
document.addEventListener('click', (event) => {
  if (optionsPanel.hidden || optionsPanel.contains(event.target) || optionsToggle.contains(event.target)) return;
  optionsPanel.hidden = true;
  optionsToggle.setAttribute('aria-expanded', 'false');
});
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape' || optionsPanel.hidden) return;
  optionsPanel.hidden = true;
  optionsToggle.setAttribute('aria-expanded', 'false');
  optionsToggle.focus();
});
hintBtn.addEventListener('click', requestBestMoveHint);
pgnBtn.addEventListener('click', copyPgn);

nameForm.addEventListener('submit', (event) => {
  event.preventDefault();
  playerName = nameInput.value.trim() || 'Player';
  nameModal.hidden = true;
  newGame(playerColor);
});

updateEvalBar(0, 'w');
updateLabels();
updateStatus();
syncBoard();
nameInput.focus();
