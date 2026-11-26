
let playerName = "";
let activeGame = false;

const startScreen = document.getElementById("start-screen");
const gameScreen = document.getElementById("game-screen");
const nameInput = document.getElementById("playerName");
const difficultyInput = document.getElementById("difficulty");
const guessInput = document.getElementById("guessInput");
const message = document.getElementById("message");

document.getElementById("startBtn").addEventListener("click", startGame);
document.getElementById("guessBtn").addEventListener("click", makeGuess);
document.getElementById("restartBtn").addEventListener("click", resetGame);

guessInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") makeGuess();
});

nameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") startGame();
});

async function startGame() {
    playerName = nameInput.value.trim();

    const difficulty = difficultyInput.value;

    if (!playerName) {
        alert("Please enter your name.");
        return;
    }

    try {
        const response = await fetch("/api/start", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                name: playerName,
                difficulty: difficulty
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error);
            return;
        }

        activeGame = true;

        startScreen.hidden = true;
        gameScreen.hidden = false;

        document.getElementById("displayName").textContent = playerName;
        document.getElementById("displayLevel").textContent = difficulty;
        document.getElementById("attempts").textContent = data.attempts;

        message.textContent = "Game started! Good luck.";
        message.style.background = "#123b34";

        guessInput.value = "";
        guessInput.focus();

    } catch (error) {
        alert("Unable to connect to the game server.");
    }
}


async function makeGuess() {
    if (!activeGame) return;

    const value = guessInput.value.trim();

    if (value === "") {
        message.textContent = "Enter a number first.";
        return;
    }

    const guess = Number(value);

    if (!Number.isInteger(guess) || guess < 1 || guess > 100) {
        message.textContent = "Enter a whole number from 1 to 100.";
        return;
    }

    try {
        const response = await fetch("/api/guess", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                name: playerName,
                guess: guess
            })
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.error;
            return;
        }

        document.getElementById("attempts").textContent =
            data.attempts_left;

        message.textContent = data.message;

        if (data.finished && data.won) {
            message.textContent =
                `${data.message} Your score is ${data.score}!`;

            message.style.background = "#123b34";
            activeGame = false;
            loadLeaderboard();

        } else if (data.finished) {
            message.textContent =
                `${data.message} The secret number was ${data.target}.`;

            message.style.background = "#7f1d1d";
            activeGame = false;
            loadLeaderboard();

        } else {
            message.style.background = "#1e293b";
        }

        guessInput.value = "";

        if (activeGame) {
            guessInput.focus();
        }

    } catch (error) {
        message.textContent = "Unable to connect to the server.";
    }
}


function resetGame() {
    activeGame = false;
    playerName = "";

    gameScreen.hidden = true;
    startScreen.hidden = false;

    guessInput.value = "";
    message.textContent = "";

    nameInput.value = "";
    nameInput.focus();

    loadLeaderboard();
}


async function loadLeaderboard() {
    const board = document.getElementById("leaderboard");

    try {
        const response = await fetch("/api/leaderboard");
        const scores = await response.json();

        if (scores.length === 0) {
            board.textContent = "No winners yet. Be the first!";
            return;
        }

        board.replaceChildren();

        scores.forEach((player, index) => {
            const row = document.createElement("div");
            row.className = "score-row";

            const rank = document.createElement("span");
            rank.textContent = `${index + 1}. ${player.player_name}`;

            const level = document.createElement("span");
            level.textContent = player.difficulty;

            const score = document.createElement("strong");
            score.textContent = `${player.score} pts`;

            row.append(rank, level, score);
            board.appendChild(row);
        });

    } catch (error) {
        board.textContent = "Leaderboard unavailable.";
    }
}

loadLeaderboard();
