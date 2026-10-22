import time
import chess
from evaluation import evaluate_stm

INF = 10 ** 9
MATE = 100_000
MAX_PLY = 64
EXACT, LOWER, UPPER = 0, 1, 2

ORDER_VAL = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 2000}

class Timeout(Exception):
    pass

class Search:
    def __init__(self):
        self.tt = {}
        self.killers = [[None, None] for _ in range(MAX_PLY + 2)]
        self.history = {}
        self.nodes = 0
        self.deadline = float("inf")
        self.root_best = None
        self.last_depth = 0
        self.last_score = 0

    def _tick(self):
        self.nodes += 1
        if (self.nodes & 2047) == 0 and time.time() > self.deadline:
            raise Timeout

    def _order(self, board, moves, tt_move=None, ply=0):
        killers = self.killers[ply]
        hist = self.history
        turn = board.turn

        def score(m):
            if m == tt_move:
                return 10_000_000
            if board.is_capture(m):
                victim = board.piece_type_at(m.to_square) or chess.PAWN
                attacker = board.piece_type_at(m.from_square)
                return 1_000_000 + 10 * ORDER_VAL[victim] - ORDER_VAL[attacker]
            if m.promotion:
                return 900_000 + m.promotion
            if m == killers[0]:
                return 800_000
            if m == killers[1]:
                return 790_000
            return hist.get((turn, m.from_square, m.to_square), 0)

        return sorted(moves, key=score, reverse=True)

    def quiesce(self, board, alpha, beta, ply):
        self._tick()
        if ply >= MAX_PLY:
            return evaluate_stm(board)
        if board.is_check():
            moves = list(board.legal_moves)
            if not moves:
                return -MATE + ply
            best = -INF
        else:
            best = evaluate_stm(board)
            if best >= beta:
                return best
            if best > alpha:
                alpha = best
            moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
        for m in self._order(board, moves):
            board.push(m)
            sc = -self.quiesce(board, -beta, -alpha, ply + 1)
            board.pop()
            if sc > best:
                best = sc
                if sc > alpha:
                    alpha = sc
                    if alpha >= beta:
                        break
        return best

    def negamax(self, board, depth, alpha, beta, ply):
        self._tick()
        if ply > 0 and (board.is_repetition(2) or board.halfmove_clock >= 100 or board.is_insufficient_material()):
            return 0
        if ply >= MAX_PLY:
            return evaluate_stm(board)
        in_check = board.is_check()
        if in_check:
            depth += 1
        if depth <= 0:
            return self.quiesce(board, alpha, beta, ply)
        alpha0 = alpha
        key = board._transposition_key()
        entry = self.tt.get(key)
        tt_move = None
        if entry is not None:
            e_depth, e_flag, e_score, tt_move = entry
            if ply > 0 and e_depth >= depth:
                if e_flag == EXACT:
                    return e_score
                if e_flag == LOWER and e_score >= beta:
                    return e_score
                if e_flag == UPPER and e_score <= alpha:
                    return e_score
        moves = list(board.legal_moves)
        if not moves:
            return -MATE + ply if in_check else 0
        best, best_move = -INF, None
        for m in self._order(board, moves, tt_move, ply):
            quiet = not board.is_capture(m) and not m.promotion
            board.push(m)
            sc = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()
            if sc > best:
                best, best_move = sc, m
                if sc > alpha:
                    alpha = sc
                    if alpha >= beta:
                        if quiet:
                            k = self.killers[ply]
                            if k[0] != m:
                                k[1], k[0] = k[0], m
                            hk = (board.turn, m.from_square, m.to_square)
                            self.history[hk] = self.history.get(hk, 0) + depth * depth
                        break

        if ply == 0:
            self.root_best = best_move
        if abs(best) < MATE - 1000:
            flag = LOWER if best >= beta else (UPPER if best <= alpha0 else EXACT)
            if len(self.tt) > 2_000_000:
                self.tt.clear()
            self.tt[key] = (depth, flag, best, best_move)
        return best

    def search(self, board, max_depth=64, time_limit=5.0):
        self.deadline = time.time() + time_limit
        self.nodes = 0
        self.history.clear()
        self.killers = [[None, None] for _ in range(MAX_PLY + 2)]
        legal = list(board.legal_moves)
        if not legal:
            return None
        root_len = len(board.move_stack)
        best_move = legal[0]
        if len(legal) == 1:
            return best_move
        for depth in range(1, max_depth + 1):
            try:
                score = self.negamax(board, depth, -INF, INF, 0)
            except Timeout:
                while len(board.move_stack) > root_len:
                    board.pop()
                break
            if self.root_best is not None:
                best_move = self.root_best
            self.last_depth, self.last_score = depth, score
            if abs(score) >= MATE - 1000:
                break
        return best_move
