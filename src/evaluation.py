import chess
from config import PIECE_VALUES, PST

def evaluate_board(board: chess.Board):
    pawn_structure_score = pawn_structure(board) + material(board) + pst_score(board) + rook_activity(board) + bishop_activity(board)
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
    score = 0
    for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
        friendly_pawns = board.pieces(chess.PAWN, color)
        enemy_pawns = board.pieces(chess.PAWN, not color)
        rooks = board.pieces(chess.ROOK, color)

        for square in rooks:
            file_index = chess.square_file(square)
            file_mask = chess.BB_FILES[file_index]
            has_friendly_pawn = bool(friendly_pawns & file_mask)
            has_enemy_pawn = bool(enemy_pawns & file_mask)
            if not has_friendly_pawn and not has_enemy_pawn:
                score += sign * 25
            elif not has_friendly_pawn:
                score += sign * 15

            rank_index = chess.square_rank(square)
            seventh_rank = (rank_index == 6 if color == chess.WHITE else rank_index == 1)

            if seventh_rank:
                score += sign * 20
        rook_squares = list(rooks)
        for index, first in enumerate(rook_squares):
            for second in rook_squares[index + 1:]:
                same_rank = chess.square_rank(first) == chess.square_rank(second)
                same_file = chess.square_file(first) == chess.square_file(second)
                if same_rank or same_file:
                    score += sign * 20
    return score

def bishop_activity(board: chess.Board):
    score = 0
    for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
        bishops = board.pieces(chess.BISHOP, color)

        for square in bishops:
            attacks = board.attacks(square)
            friendly_pieces = board.occupied_co[color]
            mobility = len(attacks - friendly_pieces)
            score += sign * mobility * 2
            for target in attacks:
                distance = max(
                    abs(chess.square_file(target) - chess.square_file(square)),
                    abs(chess.square_rank(target) - chess.square_rank(square)),
                )
                if distance >= 4:
                    score += sign * 5
                    break
    return score

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
