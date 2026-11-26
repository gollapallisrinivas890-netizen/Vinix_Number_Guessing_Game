import random
import sqlite3
import os

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

os.makedirs("instance", exist_ok=True)
DB_PATH = os.path.join("instance", "game.db")

LEVELS = {
    "easy": {"attempts": 10, "points": 100},
    "medium": {"attempts": 7, "points": 200},
    "hard": {"attempts": 5, "points": 300}
}

games = {}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            attempts_used INTEGER NOT NULL,
            score INTEGER NOT NULL,
            result TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_result(game, result, score):
    conn = get_db()
    conn.execute("""
        INSERT INTO game_history
        (player_name, difficulty, attempts_used, score, result)
        VALUES (?, ?, ?, ?, ?)
    """, (
        game["name"],
        game["difficulty"],
        game["attempts_used"],
        score,
        result
    ))
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_game():
    data = request.get_json() or {}

    name = str(data.get("name", "")).strip()
    difficulty = str(data.get("difficulty", "easy")).lower()

    if not name or len(name) > 30:
        return jsonify({"error": "Enter a name between 1 and 30 characters."}), 400

    if not name.replace(" ", "").isalpha():
        return jsonify({"error": "Name must contain letters only."}), 400

    if difficulty not in LEVELS:
        return jsonify({"error": "Invalid difficulty."}), 400

    game = {
        "name": name,
        "difficulty": difficulty,
        "target": random.randint(1, 100),
        "attempts_left": LEVELS[difficulty]["attempts"],
        "attempts_used": 0,
        "points": LEVELS[difficulty]["points"],
        "finished": False
    }

    games[name.lower()] = game

    return jsonify({
        "message": "Game started!",
        "attempts": game["attempts_left"],
        "difficulty": difficulty
    })


@app.route("/api/guess", methods=["POST"])
def guess():
    data = request.get_json() or {}

    name = str(data.get("name", "")).strip().lower()
    game = games.get(name)

    if not game:
        return jsonify({"error": "Start a game first."}), 400

    if game["finished"]:
        return jsonify({"error": "Game has ended. Start a new game."}), 400

    guess_value = data.get("guess")

    if isinstance(guess_value, bool) or not isinstance(guess_value, int):
        return jsonify({"error": "Enter a valid whole number."}), 400

    if not 1 <= guess_value <= 100:
        return jsonify({"error": "Enter a number from 1 to 100."}), 400

    game["attempts_used"] += 1
    game["attempts_left"] -= 1

    if guess_value == game["target"]:
        game["finished"] = True

        score = max(
            10,
            game["points"] - (game["attempts_used"] - 1) * 10
        )

        save_result(game, "Won", score)

        return jsonify({
            "message": "Correct! You won!",
            "won": True,
            "finished": True,
            "score": score,
            "attempts_left": game["attempts_left"]
        })

    if game["attempts_left"] == 0:
        game["finished"] = True
        save_result(game, "Lost", 0)

        return jsonify({
            "message": "Game over!",
            "won": False,
            "finished": True,
            "target": game["target"],
            "attempts_left": 0
        })

    hint = "Too low! Try a higher number." if guess_value < game["target"] else "Too high! Try a lower number."

    return jsonify({
        "message": hint,
        "won": False,
        "finished": False,
        "attempts_left": game["attempts_left"]
    })


@app.route("/api/leaderboard")
def leaderboard():
    conn = get_db()

    rows = conn.execute("""
        SELECT player_name, difficulty, score, attempts_used, result, created_at
        FROM game_history
        WHERE result = 'Won'
        ORDER BY score DESC, attempts_used ASC
        LIMIT 10
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
