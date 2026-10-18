import chess
import random

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
    
    def get_human_move(self):
        while True:
            print([move.uci() for move in self.board.legal_moves])
            move_input = input("Your move (e.g. e2e4, or 'quit'): ").strip()
            if move_input.lower() == "quit":
                return None
            try:
                move = chess.Move.from_uci(move_input)
                if move in self.board.legal_moves:
                    return move
                print("Illegal move. Try again.")
            except ValueError:
                print("Invalid format. Enter moves like e2e4 or g1f3.")

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
        print("Game over!")
        print("Result:", self.board.result())
        print("Termination:", self.board.outcome().termination.name)
