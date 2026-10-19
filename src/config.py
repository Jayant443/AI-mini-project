import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900
}

# Piece-square tables (psts) for each piece type
# A king needs two psts, one for the opening/midgame (stay safe) and one for the endgame (get active).
# A king is considered weak when it is (or can be) attacked.

# Pawns require two psts, for white and black (inverted). Plus a position evaluation whrere doubled pawns,
# isolated pawns, connected pawns and passed pawns are evaluated. Passed pawns must be evaluated based on the
# opposite colored pawns that can stop them (must check square infront of them). 

# Knight psts stay constant throughout the game, as knights are more powerful in the center than in the edges.

# Rooks, bishop, queens are sliding pieces that are evaluated based on their mobility and the number of square they
# can attack. including the open files, ranks, diagonals they have.

# Bishops are generally more powerful when they have open diagonals (especially the central diagonals and in endgame).

# Queens become more powerful as the number of sqaures they can atttack increases.

# Rooks are more powerful when they have open files and ranks, and also when they are connected to each other.
# It doesn't matter if they are in the center or not.

# Board to array in python chess:

# {63: Piece.from_symbol('r'), 62: Piece.from_symbol('n'), 61: Piece.from_symbol('b'), 
# 60: Piece.from_symbol('k'), 59: Piece.from_symbol('q'), 58: Piece.from_symbol('b'), 
# 57: Piece.from_symbol('n'), 56: Piece.from_symbol('r'), 55: Piece.from_symbol('p'), 
# 54: Piece.from_symbol('p'), 53: Piece.from_symbol('p'), 52: Piece.from_symbol('p'), 
# 51: Piece.from_symbol('p'), 50: Piece.from_symbol('p'), 49: Piece.from_symbol('p'), 
# 48: Piece.from_symbol('p'), 15: Piece.from_symbol('P'), 14: Piece.from_symbol('P'), 
# 13: Piece.from_symbol('P'), 12: Piece.from_symbol('P'), 11: Piece.from_symbol('P'), 
# 10: Piece.from_symbol('P'), 9: Piece.from_symbol('P'), 8: Piece.from_symbol('P'), 
# 7: Piece.from_symbol('R'), 6: Piece.from_symbol('N'), 5: Piece.from_symbol('B'), 
# 4: Piece.from_symbol('K'), 3: Piece.from_symbol('Q'), 2: Piece.from_symbol('B'), 
# 1: Piece.from_symbol('N'), 0: Piece.from_symbol('R')}


# b = [
#     chess.A1 (white rook), chess.B1, chess.C1, chess.D1, chess.E1, chess.F1, chess.G1, chess.H1,
#     chess.A2             , chess.B2, chess.C2, chess.D2, chess.E2, chess.F2, chess.G2, chess.H2,
#     chess.A3             , chess.B3, chess.C3, chess.D3, chess.E3, chess.F3, chess.G3, chess.H3,
#     chess.A4             , chess.B4, chess.C4, chess.D4, chess.E4, chess.F4, chess.G4, chess.H4,
#     chess.A5             , chess.B5, chess.C5, chess.D5, chess.E5, chess.F5, chess.G5, chess.H5,
#     chess.A6             , chess.B6, chess.C6, chess.D6, chess.E6, chess.F6, chess.G6, chess.H6,
#     chess.A7             , chess.B7, chess.C7, chess.D7, chess.E7, chess.F7, chess.G7, chess.H7,
#     chess.A8 (black rook), chess.B8, chess.C8, chess.D8, chess.E8, chess.F8, chess.G8, chess.H8
# ]

PAWN_PST = [
      0,   0,   0,   0,   0,   0,   0,   0,
     10,  10,  10, -10, -10,  10,  10,  10,
     10,  10,  20,  30,  30,  20,  10,  10,
     15,  15,  25,  40,  40,  25,  15,  15,
     20,  20,  30,  50,  50,  30,  20,  20,
     30,  30,  40,  60,  60,  40,  30,  30,
     80,  80,  80,  80,  80,  80,  80,  80,
      0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_PST = [
    -50, -30, -20, -20, -20, -20, -30, -50,
    -30, -10,   0,   5,   5,   0, -10, -30,
    -20,   5,  10,  15,  15,  10,   5, -20,
    -20,   0,  15,  20,  20,  15,   0, -20,
    -20,   5,  15,  20,  20,  15,   5, -20,
    -20,   0,  10,  15,  15,  10,   0, -20,
    -30, -10,   0,   0,   0,   0, -10, -30,
    -50, -30, -20, -20, -20, -20, -30, -50,
]

ROOK_PST = [
    500,   500,   500,   500,   500,   500,   500,   500,
    510,   510,   510,   510,   510,   510,   510,   510,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    510,   510,   510,   510,   510,   510,   510,   510,
    500,   500,   500,   500,   500,   500,   500,   500,
]

BISHOP_PST = [

]

PST = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
}