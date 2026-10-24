import os
import sys
import threading

import chess
from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from evaluation import evaluate_stm
from search import Search

MIN_TIME = 0.1
MAX_TIME = 10.0
DEFAULT_TIME = 2.0

app = Flask(__name__, template_folder="templates", static_folder="static")

searcher = Search()
search_lock = threading.Lock()


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/engine-move")
def engine_move():
    payload = request.get_json(silent=True) or {}

    moves = payload.get("moves")
    if not isinstance(moves, list) or not all(isinstance(m, str) for m in moves):
        return jsonify(error="'moves' must be a list of UCI strings"), 400

    fen = payload.get("fen")
    if fen is not None and not isinstance(fen, str):
        return jsonify(error="'fen' must be a FEN string"), 400

    try:
        time_limit = float(payload.get("time", DEFAULT_TIME))
    except (TypeError, ValueError):
        return jsonify(error="'time' must be a number"), 400
    time_limit = max(MIN_TIME, min(MAX_TIME, time_limit))

    try:
        board = chess.Board(fen) if fen is not None else chess.Board()
    except ValueError as exc:
        return jsonify(error=f"invalid FEN: {exc}"), 400

    if not board.is_valid():
        return jsonify(error="FEN describes an invalid chess position"), 400

    try:
        for uci in moves:
            board.push_uci(uci)
    except (chess.InvalidMoveError, chess.IllegalMoveError):
        return jsonify(error=f"illegal move list: {uci!r} is not legal here"), 400

    if board.is_game_over():
        return jsonify(error="the game is already over"), 400

    with search_lock:
        searcher.last_depth = 0
        searcher.last_score = evaluate_stm(board)
        move = searcher.search(board, time_limit=time_limit)
        depth, score, nodes = searcher.last_depth, searcher.last_score, searcher.nodes

    if move is None:
        return jsonify(error="the game is already over"), 400

    return jsonify(move=move.uci(), san=board.san(move),
                   depth=depth, eval=score, nodes=nodes)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, threaded=True)
