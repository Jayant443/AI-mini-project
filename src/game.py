import chess
import random
from evaluation import evaluate_board

class Game:
    def __init__(self):
        self.board = chess.Board()
        self.human_color = chess.WHITE

    def choose_color(self):
        while True:
            choice = input("Choose your color (white/black): ").strip().lower()
            if choice in ("white", "w"):
                self.human_color = chess.WHITE
                return
            if choice in ("black", "b"):
                self.human_color = chess.BLACK
                return
            print("Invalid choice. Enter 'white' or 'black'.")
    
    def ask_promotion(self, from_square, to_square):
        piece_map = {
            "q": chess.QUEEN,
            "r": chess.ROOK,
            "b": chess.BISHOP,
            "n": chess.KNIGHT,
        }
        while True:
            choice = input("Promote to (q=queen, r=rook, b=bishop, n=knight): ").strip().lower()
            if choice in piece_map:
                return chess.Move(from_square, to_square, promotion=piece_map[choice])
            print("Invalid choice. Enter q, r, b or n.")

    def get_human_move(self):
        while True:
            print([move.uci() for move in self.board.legal_moves])
            move_input = input("Your move (e.g. e2e4, or 'quit'): ").strip()
            if move_input.lower() == "quit":
                return None
            try:
                move = chess.Move.from_uci(move_input)
            except ValueError:
                print("Invalid format. Enter moves like e2e4 or g1f3.")
                continue
            matching = [legal for legal in self.board.legal_moves if legal.from_square == move.from_square and legal.to_square == move.to_square]
            if not matching:
                print("Illegal move. Try again.")
                continue
            promotions = [legal for legal in matching if legal.promotion]
            if promotions:
                return self.ask_promotion(move.from_square, move.to_square)
            return matching[0]

    def engine_move(self):
        legal_moves = list(self.board.legal_moves)
        move = random.choice(legal_moves)
        print(f"Engine plays: {self.board.san(move)} ({move.uci()})")
        self.board.push(move)

    def play_game(self):
        self.choose_color()
        if self.human_color == chess.WHITE:
            print("You are White. The engine is Black.")
        else:
            print("You are Black. The engine is White.")
        print("Enter moves in UCI format, e.g. e2e4.")
        print("Type 'quit' to exit.")
        print(self.board.unicode(orientation=self.human_color, invert_color=True))
        print(f"Evaluation (pawn structure only): {evaluate_board(self.board)}")

        while not self.board.is_game_over():
            if self.board.turn == self.human_color:
                human_move = self.get_human_move()
                if human_move is None:
                    print("Game ended by resignation/exit.")
                    return
                print(f"You play: {self.board.san(human_move)}")
                self.board.push(human_move)
            else:
                self.engine_move()
            print(self.board.unicode(orientation=self.human_color, invert_color=True))
            print(f"Evaluation (pawn structure only): {evaluate_board(self.board)}")
        print("Game over!")
        print("Result:", self.board.result())
        print("Termination:", self.board.outcome().termination.name)
