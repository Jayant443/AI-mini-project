import chess
from config import PIECE_VALUES, PST

def evaluate_board(board: chess.Board):
    pawn_structure_score = pawn_structure(board) + material(board) + pst_score(board)
    return pawn_structure_score

def material(board: chess.Board):
    score = 0
    for piece in board.piece_map().values():
        value = PIECE_VALUES.get(piece.piece_type, 0)
        score += value if piece.color == chess.WHITE else -value
    return score

def pst_score(board: chess.Board):
    score = 0
    for square, piece in board.piece_map().items():
        table = PST.get(piece.piece_type)
        if table is None:
            continue
        pst_square = square if piece.color == chess.WHITE else square ^ 56
        value = table[pst_square]
        score += value if piece.color == chess.WHITE else -value
    return score

def rook_activity(board: chess.Board):
    pass

def bishop_activity(board: chess.Board):
    pass

def queen_activity(board: chess.Board):
    pass

def king_safety(board: chess.Board):
    pass

def doubled_pawn_count(board, color):
    pawns = board.pieces(chess.PAWN, color)
    file_counts = [0] * 8
    for square in pawns:
        file_index = chess.square_file(square)
        file_counts[file_index] += 1
    return sum(max(0, count - 1) for count in file_counts)

def isolated_pawn_count(board, color):
    pawns = board.pieces(chess.PAWN, color)
    pawn_files = {chess.square_file(square) for square in pawns}
    count = 0

    for square in pawns:
        file_index = chess.square_file(square)
        has_left_neighbor = (file_index > 0 and file_index - 1 in pawn_files)
        has_right_neighbor = (file_index < 7 and file_index + 1 in pawn_files)
        if not has_left_neighbor and not has_right_neighbor:
            count += 1

    return count

def connected_pawn_count(board, color):
    pawns = board.pieces(chess.PAWN, color)
    direction = 1 if color == chess.WHITE else -1
    count = 0

    for square in pawns:
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)
        for file_offset in (-1, 1):
            neighbor_file = file_index + file_offset
            neighbor_rank = rank_index + direction
            if not (0 <= neighbor_file < 8):
                continue
            if not (0 <= neighbor_rank < 8):
                continue
            neighbor = chess.square(neighbor_file, neighbor_rank)
            if neighbor in pawns:
                count += 1
                break
    return count

def is_passed_pawn(board, square, color):
    enemy_pawns = board.pieces(chess.PAWN, not color)
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)
    direction = 1 if color == chess.WHITE else -1
    for enemy_square in enemy_pawns:
        enemy_file = chess.square_file(enemy_square)
        enemy_rank = chess.square_rank(enemy_square)
        same_or_adjacent_file = abs(enemy_file - file_index) <= 1
        ahead = (enemy_rank - rank_index) * direction > 0
        if same_or_adjacent_file and ahead:
            return False
    return True

def passed_pawns(board, color):
    return [square for square in board.pieces(chess.PAWN, color) if is_passed_pawn(board, square, color)]

def pawn_structure(board: chess.Board):
    score = 0
    
    for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
        score += sign * (-20 * doubled_pawn_count(board, color) -15 * isolated_pawn_count(board, color) +10 * connected_pawn_count(board, color))
        for square in passed_pawns(board, color):
            rank = chess.square_rank(square)
            advancement = (rank if color == chess.WHITE else 7 - rank)
            score += sign * (10 + 10 * advancement)

    return score
