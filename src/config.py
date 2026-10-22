"""
Piece-square tables (psts) for each piece type
A king needs two psts, one for the opening/midgame (stay safe) and one for the endgame (get active).
A king is considered weak when it is (or can be) attacked.

Pawns require two psts, for white and black (inverted). Plus a position evaluation whrere doubled pawns,
isolated pawns, connected pawns and passed pawns are evaluated. Passed pawns must be evaluated based on the
opposite colored pawns that can stop them (must check square infront of them). 

Knight psts stay constant throughout the game, as knights are more powerful in the center than in the edges.

Rooks, bishop, queens are sliding pieces that are evaluated based on their mobility and the number of square they
can attack. including the open files, ranks, diagonals they have.

Bishops are generally more powerful when they have open diagonals (especially the central diagonals and in endgame).

Queens become more powerful as the number of sqaures they can atttack increases.

Rooks are more powerful when they have open files and ranks, and also when they are connected to each other.
It doesn't matter if they are in the center or not.
"""

import chess

pc = chess.popcount
P, N, B, R, Q, K = chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING

MAT_MG = {P: 100, N: 320, B: 330, R: 500, Q: 950, K: 0}
MAT_EG = {P: 120, N: 310, B: 330, R: 540, Q: 950, K: 0}

PAWN_MG = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0]

PAWN_EG = [
     0,  0,  0,  0,  0,  0,  0,  0,
    70, 70, 70, 70, 70, 70, 70, 70,
    40, 40, 40, 40, 40, 40, 40, 40,
    22, 22, 22, 22, 22, 22, 22, 22,
    10, 10, 10, 10, 10, 10, 10, 10,
     4,  4,  4,  4,  4,  4,  4,  4,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0]

KNIGHT_PST = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50]

BISHOP_PST = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -20,-10,-10,-10,-10,-10,-10,-20]

ROOK_PST = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0]

QUEEN_PST = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20]

KING_MG = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20]

KING_EG = [
   -50,-40,-30,-20,-20,-30,-40,-50,
   -30,-20,-10,  0,  0,-10,-20,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-30,  0,  0,  0,  0,-30,-30,
   -50,-30,-30,-30,-30,-30,-30,-50]

PHASE_W = {N: 1, B: 1, R: 2, Q: 4}
MAX_PHASE = 24

DOUBLED = (-10, -20)
ISOLATED = (-10, -15)
BACKWARD = (-8, -10)
PASSED = [(0, 0), (5, 10), (10, 20), (20, 40), (35, 70), (60, 120), (100, 200), (0, 0)]
CONNECTED = [0, 0, 5, 8, 12, 20, 30, 0]

BISHOP_PAIR = (30, 50)
LONG_DIAG = 8
KNIGHT_OUTPOST = (20, 10)
ROOK_OPEN, ROOK_SEMI, ROOK_7TH, ROOK_CONN = 25, 12, 20, 5
TEMPO = 10

MOB = {N: (4, 4, 4), B: (4, 5, 6), R: (2, 4, 7), Q: (1, 2, 14)}
ATTACK_W = {N: 2, B: 2, R: 3, Q: 5}
SAFETY = [0, 0, 5, 15, 35, 70, 110, 160, 220, 280] + [320] * 20
SHIELD_NEAR, SHIELD_FAR, SHIELD_OPEN_FILE = 10, 5, -15
