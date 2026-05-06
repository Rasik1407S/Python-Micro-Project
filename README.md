<div align="center">
  <h1>🧩 Sudoku</h1>
  <p><em>Python does the thinking. The browser draws the board. No build step.</em></p>
</div>

<div align="center">

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.x-lightgrey?style=flat-square)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/react-18-61dafb?style=flat-square)](https://react.dev/)
[![No Build Step](https://img.shields.io/badge/build-none-success?style=flat-square)]()
[![Last Commit](https://img.shields.io/github/last-commit/Rasik1407S/Python-Micro-Project?style=flat-square)](https://github.com/Rasik1407S/Python-Micro-Project/commits)
[![Issues](https://img.shields.io/github/issues/Rasik1407S/Python-Micro-Project?style=flat-square)](https://github.com/Rasik1407S/Python-Micro-Project/issues)

</div>

<!-- Add a screenshot or GIF here: assets/demo.png -->

---

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Running the Game](#running-the-game)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

---

## 🧠 About

Two files. No `npm install`. No build pipeline.

`sudoku_backend.py` handles all game logic - generating valid, uniquely-solvable puzzles, checking moves, handing out hints, returning solutions - through four Flask endpoints. `sudoku_frontend.html` loads React 18 and Babel from a CDN, renders the board, and talks to the API. Open the HTML file in a browser after starting the Python server and you're playing.

The split is deliberate. The frontend holds no game state beyond what the user has typed. The solution never leaves the server. React's only job is to display what Python decides.

---

## ✨ Features

- 🎲 **Puzzle generation** - backtracking solver with randomised digit order produces a different layout every game; a uniqueness check guarantees exactly one solution
- 🎚️ **Three difficulty levels** - Easy (36 clues), Medium (30), Hard (25); switch mid-session and a new puzzle starts immediately
- ✅ **Live move validation** - every placed digit is checked against Sudoku rules on the server; conflicts highlight in red instantly
- 💡 **Hints** - reveals one random empty cell from the solution; the hint counter tracks how many you've used
- 🔍 **Auto-solve** - sends the game ID to `/api/solve` and fills the board with the server's stored solution
- ⏱️ **Live timer** - counts up from the first cell placement; stops on completion or solve
- ⌨️ **Keyboard navigation** - arrow keys move the selection, digit keys place numbers, `Del` / `Backspace` / `0` erase
- 🎨 **Oxidised-bronze / forest-shadow palette** - dark theme with per-cell state colouring (selected, same-number highlight, error, original clue)
- 📦 **Zero frontend dependencies** - React, ReactDOM, and Babel load from CDN; no `node_modules`, no bundler

---

## 🏗️ Architecture

```
sudoku_frontend.html                    sudoku_backend.py
──────────────────────                  ─────────────────────────────
React 18 (CDN + Babel)                  Flask  ·  port 5000
                                        In-memory session store
  renders board                         { game_id → solution, difficulty }
  handles input
  manages timer          HTTP/JSON
  calls API  ─────────────────────────► POST /api/new-game
                                        POST /api/validate
             ◄───────────────────────── POST /api/hint
                                        POST /api/solve
```

Sessions are stored in a plain Python dict. Restarting the server clears all active games — by design for a micro-project.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.8+, Flask, flask-cors |
| Frontend | React 18, Babel Standalone (both via CDN) |
| Fonts | Cinzel · Courier Prime · Jost (Google Fonts) |
| Communication | REST / JSON |
| Session storage | In-memory Python dict (no database) |

---

## 📋 Prerequisites

- Python >= 3.8
- pip

That's it. The frontend has no local dependencies.

---

## ▶️ Running the Game

### 1. Clone the repository

```bash
git clone https://github.com/Rasik1407S/Python-Micro-Project.git
cd Python-Micro-Project
```

### 2. Install Python dependencies

```bash
pip install flask flask-cors
```

### 3. Start the backend

```bash
python sudoku_backend.py
```

You'll see:

```
  ┌─────────────────────────────────────────┐
  │   Sudoku Backend  →  localhost:5000     │
  │   Open sudoku_frontend.html in browser  │
  └─────────────────────────────────────────┘
```

### 4. Open the frontend

Open `sudoku_frontend.html` directly in your browser. The page fetches a Medium puzzle from `http://localhost:5000/api` on load.

No dev server. No proxy config. No port 3000.

---

## 📡 API Reference

All four endpoints accept and return JSON. The backend runs at `http://localhost:5000`.

---

### `POST /api/new-game`

Generates a new puzzle and stores the solution server-side.

**Request:**
```json
{ "difficulty": "easy" | "medium" | "hard" }
```

**Response:**
```json
{
  "game_id":    "550e8400-e29b-41d4-a716-446655440000",
  "board":      [[5, 3, 0, 0, 7, 0, 0, 0, 0], ...],
  "original":   [[5, 3, 0, 0, 7, 0, 0, 0, 0], ...],
  "difficulty": "medium"
}
```

`board` and `original` are identical at the start. `original` is a frozen snapshot — the frontend uses it to prevent overwriting starting clues. `0` is an empty cell. The solution is retained in the session and never returned here.

---

### `POST /api/validate`

Checks the current board state for rule violations.

**Request:**
```json
{ "board": [[5, 3, 4, 0, 7, 0, 0, 0, 0], ...] }
```

**Response:**
```json
{
  "errors":   [[0, 3], [2, 7]],
  "complete": false
}
```

`errors` is a list of `[row, col]` pairs where a placed digit conflicts with another in the same row, column, or 3×3 box. `complete` is `true` only when the board is fully filled with no errors.

---

### `POST /api/hint`

Reveals one randomly chosen empty cell from the solution.

**Request:**
```json
{ "game_id": "550e8400-...", "board": [[...], ...] }
```

**Response:**
```json
{ "row": 4, "col": 7, "value": 3 }
```

If no empty cells remain:
```json
{ "message": "No empty cells remaining" }
```

---

### `POST /api/solve`

Returns the complete solution stored for this game.

**Request:**
```json
{ "game_id": "550e8400-..." }
```

**Response:**
```json
{ "solution": [[5, 3, 4, 6, 7, 8, 9, 1, 2], ...] }
```

A `404` with `{ "error": "Invalid or expired game ID" }` is returned if the session has been cleared (i.e., server was restarted).

---

## 📁 Project Structure

```
Python-Micro-Project/
├── sudoku_backend.py     # Flask API — all game logic (puzzle gen, validation, hints, solve)
├── sudoku_frontend.html  # Single-file React UI — board, numpad, timer, controls
└── README.md
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: describe what you added'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Ideas worth exploring: difficulty scoring beyond clue count, pencil marks, persistent sessions via SQLite, a mobile-friendly layout.

---

## 👤 Author

**Rasik** — [@Rasik1407S](https://github.com/Rasik1407S)

Project Link: [https://github.com/Rasik1407S/Python-Micro-Project](https://github.com/Rasik1407S/Python-Micro-Project)
