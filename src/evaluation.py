import chess
from chess import (BB_FILES, BB_RANKS, BB_ALL, BB_FILE_A, BB_FILE_H,BB_KING_ATTACKS, BB_PAWN_ATTACKS, scan_forward)
from config import (
            ATTACK_W,
            BACKWARD,
            BISHOP_PAIR,
            BISHOP_PST,
            CONNECTED,
            DOUBLED,
            ISOLATED,
            KING_EG,
            KING_MG,
            KNIGHT_OUTPOST,
            KNIGHT_PST,
            LONG_DIAG,
            MAT_EG,
            MAT_MG,
            MAX_PHASE,
            MOB,
            PASSED,
            PAWN_EG,
            PAWN_MG,
            PHASE_W,
            QUEEN_PST,
            ROOK_7TH,
            ROOK_CONN,
            ROOK_OPEN,
            ROOK_PST,
            ROOK_SEMI,
            SAFETY,
            SHIELD_FAR,
            SHIELD_NEAR,
            SHIELD_OPEN_FILE,
            TEMPO,
            P, N, B, R, Q, K,
            pc,
        )

_PST_MG = {P: PAWN_MG, N: KNIGHT_PST, B: BISHOP_PST, R: ROOK_PST, Q: QUEEN_PST, K: KING_MG}
_PST_EG = {P: PAWN_EG, N: KNIGHT_PST, B: BISHOP_PST, R: ROOK_PST, Q: QUEEN_PST, K: KING_EG}

TAB_MG = {True: {}, False: {}}
TAB_EG = {True: {}, False: {}}
for _t in (P, N, B, R, Q, K):
    TAB_MG[True][_t] = [MAT_MG[_t] + _PST_MG[_t][s ^ 56] for s in range(64)]
    TAB_EG[True][_t] = [MAT_EG[_t] + _PST_EG[_t][s ^ 56] for s in range(64)]
    TAB_MG[False][_t] = [-(MAT_MG[_t] + _PST_MG[_t][s]) for s in range(64)]
    TAB_EG[False][_t] = [-(MAT_EG[_t] + _PST_EG[_t][s]) for s in range(64)]

CENTER = chess.BB_D4 | chess.BB_E4 | chess.BB_D5 | chess.BB_E5

ADJ = [(BB_FILES[f - 1] if f else 0) | (BB_FILES[f + 1] if f < 7 else 0) for f in range(8)]
FRONT = {True: [0] * 64, False: [0] * 64}
for _sq in range(64):
    _f, _r = chess.square_file(_sq), chess.square_rank(_sq)
    _cols = BB_FILES[_f] | ADJ[_f]
    FRONT[True][_sq] = _cols & ~((1 << (8 * (_r + 1))) - 1)
    FRONT[False][_sq] = _cols & ((1 << (8 * _r)) - 1)

def _pawn_attacks(pawns, color):
    if color:
        return (((pawns << 7) & ~BB_FILE_H) | ((pawns << 9) & ~BB_FILE_A)) & BB_ALL
    return ((pawns >> 7) & ~BB_FILE_A) | ((pawns >> 9) & ~BB_FILE_H)

_pawn_cache = {}

def _pawns_one(mine, theirs, color):
    mg = eg = 0
    passed = 0
    for f in range(8):
        n = pc(mine & BB_FILES[f])
        if n > 1:
            mg += DOUBLED[0] * (n - 1)
            eg += DOUBLED[1] * (n - 1)
    their_att = _pawn_attacks(theirs, not color)
    for sq in scan_forward(mine):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        rel = r if color else 7 - r
        isolated = not (mine & ADJ[f])
        if isolated:
            mg += ISOLATED[0]
            eg += ISOLATED[1]
        if not (theirs & FRONT[color][sq]):
            passed |= 1 << sq
            pm, pe = PASSED[rel]
            mg += pm
            eg += pe
        supported = mine & BB_PAWN_ATTACKS[not color][sq]
        phalanx = mine & ADJ[f] & BB_RANKS[r]
        if supported or phalanx:
            c = CONNECTED[rel] * (2 if (supported and phalanx) else 1)
            mg += c
            eg += c // 2
        if not isolated and not supported and not phalanx:
            stop = sq + 8 if color else sq - 8
            if 0 <= stop < 64 and (their_att >> stop) & 1:
                behind = mine & ADJ[f] & (
                    ((1 << (8 * r)) - 1) if color else ~((1 << (8 * (r + 1))) - 1))
                if not behind:
                    mg += BACKWARD[0]
                    eg += BACKWARD[1]
    return mg, eg, passed

def _pawn_structure(board):
    wp = board.pawns & board.occupied_co[True]
    bp = board.pawns & board.occupied_co[False]
    key = (wp, bp)
    res = _pawn_cache.get(key)
    if res is None:
        wm, we, wpass = _pawns_one(wp, bp, True)
        bm, be, bpass = _pawns_one(bp, wp, False)
        res = (wm - bm, we - be, wpass, bpass)
        if len(_pawn_cache) > 200_000:
            _pawn_cache.clear()
        _pawn_cache[key] = res
    return res

def _piece_terms(board, color):
    mg = eg = 0
    own = board.occupied_co[color]
    enemy = board.occupied_co[not color]
    mine_p = board.pawns & own
    their_p = board.pawns & enemy
    safe = ~own & ~_pawn_attacks(their_p, not color) & BB_ALL

    eksq = board.king(not color)
    zone = (BB_KING_ATTACKS[eksq] | (1 << eksq)) if eksq is not None else 0
    attackers = units = 0
    rel_7th = 6 if color else 1

    for t in (N, B, R, Q):
        pieces = board.pieces_mask(t, color)
        if not pieces:
            continue
        wm, we, base = MOB[t]
        if t == B and pc(pieces) >= 2:
            mg += BISHOP_PAIR[0]
            eg += BISHOP_PAIR[1]
        for sq in scan_forward(pieces):
            att = board.attacks_mask(sq)
            m = pc(att & safe) - base
            mg += wm * m
            eg += we * m
            if att & zone:
                attackers += 1
                units += ATTACK_W[t]
            f = chess.square_file(sq)
            if t == B:
                c = pc(att & CENTER)
                if c >= 2:
                    mg += LONG_DIAG * (c - 1)
            elif t == N:
                r = chess.square_rank(sq)
                rel = r if color else 7 - r
                if 3 <= rel <= 5 and (mine_p & BB_PAWN_ATTACKS[not color][sq]) \
                        and not (their_p & ADJ[f] & FRONT[color][sq]):
                    mg += KNIGHT_OUTPOST[0]
                    eg += KNIGHT_OUTPOST[1]
            elif t == R:
                if not (mine_p & BB_FILES[f]):
                    b = ROOK_OPEN if not (their_p & BB_FILES[f]) else ROOK_SEMI
                    mg += b
                    eg += b
                if chess.square_rank(sq) == rel_7th:
                    mg += ROOK_7TH
                    eg += ROOK_7TH
                if att & pieces:
                    mg += ROOK_CONN
                    eg += ROOK_CONN
    return mg, eg, attackers, units

def _king_safety(board, color, attackers, units):
    ksq = board.king(color)
    if ksq is None:
        return 0
    f, r = chess.square_file(ksq), chess.square_rank(ksq)
    rel = r if color else 7 - r
    score = 0
    if rel <= 1:
        mine_p = board.pawns & board.occupied_co[color]
        step = 8 if color else -8
        for ff in (f - 1, f, f + 1):
            if not 0 <= ff < 8:
                continue
            s1 = chess.square(ff, r) + step
            if 0 <= s1 < 64 and (mine_p >> s1) & 1:
                score += SHIELD_NEAR
            elif 0 <= s1 + step < 64 and (mine_p >> (s1 + step)) & 1:
                score += SHIELD_FAR
            if not (mine_p & BB_FILES[ff]):
                score += SHIELD_OPEN_FILE
    if attackers >= 2:
        score -= SAFETY[min(units, 29)]
    return score

def evaluate(board):
    mg = eg = phase = 0
    for sq, p in board.piece_map().items():
        t, c = p.piece_type, p.color
        mg += TAB_MG[c][t][sq]
        eg += TAB_EG[c][t][sq]
        phase += PHASE_W.get(t, 0)
    if phase > MAX_PHASE:
        phase = MAX_PHASE
    pm, pe, wpass, bpass = _pawn_structure(board)
    mg += pm
    eg += pe
    occ = board.occupied
    for sq in scan_forward(wpass):
        if (occ >> (sq + 8)) & 1:
            rel = chess.square_rank(sq)
            mg -= PASSED[rel][0] // 2
            eg -= PASSED[rel][1] // 2
    for sq in scan_forward(bpass):
        if (occ >> (sq - 8)) & 1:
            rel = 7 - chess.square_rank(sq)
            mg += PASSED[rel][0] // 2
            eg += PASSED[rel][1] // 2
    wm, we, w_att, w_units = _piece_terms(board, True)
    bm, be, b_att, b_units = _piece_terms(board, False)
    mg += wm - bm
    eg += we - be
    mg += _king_safety(board, True, b_att, b_units)
    mg -= _king_safety(board, False, w_att, w_units)
    v = mg * phase + eg * (MAX_PHASE - phase)
    return v // MAX_PHASE if v >= 0 else -((-v) // MAX_PHASE)

def evaluate_stm(board):
    s = evaluate(board)
    return (s + TEMPO) if board.turn else (-s + TEMPO)