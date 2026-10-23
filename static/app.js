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

// Keep the controls in their intended sections even if cached markup is served.
document.getElementById('error-box').insertAdjacentElement('afterend', hintBtn);
moveListEl.insertAdjacentElement('afterend', pgnBtn);

let game = new Chess();
let playerColor = 'w';
let selfPlay = false;
let playerName = 'Player';
let orientation = 'w';
let thinking = false;
let lastMove = null;
let bestMoveHint = null;
let pendingPromotion = null;
let gameGen = 0;
let copyFlashTimer = null;

const engineInfoByPly = new Map();

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
        moves: uciMoves(),
        time: Number(timeSelect.value),
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (gen !== gameGen) return;
    if (!response.ok || data.error) {
      throw new Error(data.error || `engine request failed (HTTP ${response.status})`);
    }

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
  thinking = true;
  updateStatus();
  syncBoard();
  try {
    const response = await fetch(ENGINE_MOVE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ moves: uciMoves(), time: Number(timeSelect.value) }),
    });
    const data = await response.json().catch(() => ({}));
    if (gen !== gameGen) return;
    if (!response.ok || data.error) {
      throw new Error(data.error || `engine request failed (HTTP ${response.status})`);
    }
    bestMoveHint = data.move;
    thinking = false;
    syncBoard();
    updateStatus();
    statusEl.textContent = `Best move: ${data.san}`;
  } catch (err) {
    if (gen !== gameGen) return;
    thinking = false;
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
  lastMove = null;
  bestMoveHint = null;
  engineInfoByPly.clear();
  thinking = false;
  closePromotionPicker();
  hideError();
  syncBoard();
  renderMoveList();
  updateLabels();
  updateStatus();
  if (selfPlay || playerColor === 'b') requestEngineMove();
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
  if (thinking) {
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
  for (let i = 0; i < history.length; i += 1) {
    const li = document.createElement('li');
    const moveNumber = Math.floor(i / 2) + 1;
    const movePrefix = i % 2 === 0 ? `${moveNumber}. ` : `${moveNumber}. `;
    li.append(`${movePrefix}${history[i]}`);
    appendEngineInfo(li, i + 1);
    moveListEl.appendChild(li);
  }
  moveListEl.scrollTop = moveListEl.scrollHeight;
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
hintBtn.addEventListener('click', requestBestMoveHint);
pgnBtn.addEventListener('click', copyPgn);

nameForm.addEventListener('submit', (event) => {
  event.preventDefault();
  playerName = nameInput.value.trim() || 'Player';
  nameModal.hidden = true;
  newGame(playerColor);
});

updateLabels();
updateStatus();
syncBoard();
nameInput.focus();
