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
#  can attack. including the open files, ranks, diagonals they have.

# Bishops are generally more powerful when they have open diagonals (especially the central diagonals and in endgame).

# Queens become more powerful as the number of sqaures they can atttack increases.

# Rooks are more powerful when they have open files and ranks, and also when they are connected to each other.
# It doesn't matter if they are in the center or not.

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
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
    500,   500,   500,   500,   500,   500,   500,   500,
]

BISHOP_PST = [

]

PST = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
}