"""
sudoku_backend.py  ─  Sudoku REST API (all game logic lives here)
══════════════════════════════════════════════════════════════════
Install : pip install flask flask-cors
Run     : python sudoku_backend.py
API     : http://localhost:5000

Endpoints
─────────
POST /api/new-game   { difficulty }            → { game_id, board, original, difficulty }
POST /api/validate   { board }                 → { errors, complete }
POST /api/hint       { game_id, board }        → { row, col, value }
POST /api/solve      { game_id }               → { solution }
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random, copy, uuid

app = Flask(__name__)
CORS(app)                          # Allow requests from the browser frontend

# ── In-memory session store ───────────────────────────────────────────────────
# { game_id: { 'solution': [[int]*9]*9, 'difficulty': str } }
sessions: dict = {}


# ══════════════════════════════════════════════════════════════════════════════
#  Core Sudoku Logic
# ══════════════════════════════════════════════════════════════════════════════

def empty_board() -> list:
    return [[0] * 9 for _ in range(9)]


def is_valid(board: list, row: int, col: int, num: int) -> bool:
    """Return True if placing `num` at (row, col) obeys Sudoku rules."""
    if num in board[row]:
        return False
    if any(board[r][col] == num for r in range(9)):
        return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    return not any(
        board[r][c] == num
        for r in range(br, br + 3)
        for c in range(bc, bc + 3)
    )


def find_empty(board: list):
    """Return (row, col) of the first empty cell, or None if board is full."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None


def solve(board: list, randomize: bool = True) -> bool:
    """
    Backtracking solver.  Modifies `board` in-place.
    `randomize=True` shuffles candidate digits → produces varied puzzles.
    """
    pos = find_empty(board)
    if pos is None:
        return True                # Board is complete
    row, col = pos
    digits = random.sample(range(1, 10), 9) if randomize else range(1, 10)
    for num in digits:
        if is_valid(board, row, col, num):
            board[row][col] = num
            if solve(board, randomize):
                return True
            board[row][col] = 0   # Backtrack
    return False


def count_solutions(board: list, limit: int = 2) -> int:
    """
    Count distinct solutions, stopping at `limit`.
    Used to ensure the generated puzzle has a unique solution.
    """
    pos = find_empty(board)
    if pos is None:
        return 1
    row, col = pos
    count = 0
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num
            count += count_solutions(board, limit)
            board[row][col] = 0
            if count >= limit:
                break
    return count


# Target clue counts per difficulty
CLUE_COUNTS = {"easy": 36, "medium": 30, "hard": 25}


def generate_puzzle(difficulty: str = "medium") -> tuple:
    """
    Generate a puzzle + its unique solution.

    Algorithm:
      1. Fill a blank board with a valid random solution.
      2. Remove cells one-by-one (random order).
      3. After each removal verify the puzzle still has exactly one solution.
      4. Stop when the target clue count is reached.

    Returns (puzzle_board, solution_board).
    """
    board = empty_board()
    solve(board, randomize=True)
    solution = copy.deepcopy(board)

    target = CLUE_COUNTS.get(difficulty, 30)
    cells  = list(range(81))
    random.shuffle(cells)

    for idx in cells:
        r, c = divmod(idx, 9)
        if board[r][c] == 0:
            continue
        backup = board[r][c]
        board[r][c] = 0
        # Uniqueness check on a scratch copy (preserves board state)
        if count_solutions(copy.deepcopy(board)) != 1:
            board[r][c] = backup      # Restore: removal breaks uniqueness
        clues = sum(v != 0 for row in board for v in row)
        if clues <= target:
            break

    return board, solution


def find_errors(board: list) -> list:
    """
    Return [[row, col], ...] of cells that conflict with Sudoku rules.
    Temporarily removes each value to test validity.
    """
    errors = []
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == 0:
                continue
            board[r][c] = 0
            if not is_valid(board, r, c, v):
                errors.append([r, c])
            board[r][c] = v
    return errors


# ══════════════════════════════════════════════════════════════════════════════
#  REST Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/new-game", methods=["POST"])
def new_game():
    """
    Generate a new puzzle.

    Request  : { "difficulty": "easy" | "medium" | "hard" }
    Response : { "game_id", "board", "original", "difficulty" }
    """
    data       = request.get_json(force=True) or {}
    difficulty = data.get("difficulty", "medium")
    if difficulty not in CLUE_COUNTS:
        difficulty = "medium"

    board, solution = generate_puzzle(difficulty)
    game_id = str(uuid.uuid4())
    sessions[game_id] = {"solution": solution, "difficulty": difficulty}

    return jsonify({
        "game_id":    game_id,
        "board":      board,
        "original":   copy.deepcopy(board),   # Frozen snapshot of starting clues
        "difficulty": difficulty,
    })


@app.route("/api/validate", methods=["POST"])
def validate():
    """
    Validate the current board state.

    Request  : { "board": [[int]*9]*9 }
    Response : { "errors": [[row, col], ...], "complete": bool }
    """
    data   = request.get_json(force=True) or {}
    board  = data.get("board", [])
    errors = find_errors(board)
    filled = all(board[r][c] != 0 for r in range(9) for c in range(9))
    return jsonify({"errors": errors, "complete": filled and not errors})


@app.route("/api/hint", methods=["POST"])
def hint():
    """
    Reveal one random empty cell from the solution.

    Request  : { "game_id": str, "board": [[int]*9]*9 }
    Response : { "row": int, "col": int, "value": int }
               | { "message": "No empty cells remaining" }
    """
    data    = request.get_json(force=True) or {}
    game_id = data.get("game_id")
    board   = data.get("board", [])

    if game_id not in sessions:
        return jsonify({"error": "Invalid or expired game ID"}), 404

    solution = sessions[game_id]["solution"]
    empties  = [(r, c) for r in range(9) for c in range(9) if board[r][c] == 0]

    if not empties:
        return jsonify({"message": "No empty cells remaining"})

    r, c = random.choice(empties)
    return jsonify({"row": r, "col": c, "value": solution[r][c]})


@app.route("/api/solve", methods=["POST"])
def solve_endpoint():
    """
    Return the complete solution for the current game.

    Request  : { "game_id": str }
    Response : { "solution": [[int]*9]*9 }
    """
    data    = request.get_json(force=True) or {}
    game_id = data.get("game_id")

    if game_id not in sessions:
        return jsonify({"error": "Invalid or expired game ID"}), 404

    return jsonify({"solution": sessions[game_id]["solution"]})


# ══════════════════════════════════════════════════════════════════════════════
#  Entry Point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("  ┌─────────────────────────────────────────┐")
    print("  │   Sudoku Backend  →  localhost:5000     │")
    print("  │   Open sudoku_frontend.html in browser  │")
    print("  └─────────────────────────────────────────┘")
    print()
    app.run(debug=True, port=5000)
