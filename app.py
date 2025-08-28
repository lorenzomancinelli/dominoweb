from flask import Flask, render_template_string, jsonify, request, session, url_for
from fractions import Fraction
import random
import uuid

app = Flask(__name__)
app.secret_key = "b9f8d2a7c4e1g6h3j0k9l8m2n5p7q1r4"

# ---------------- CONFIG ----------------
TILES = [
    ("1/2","3/6"), ("12/24","4/10"), ("6/21","4/2"), ("10/5","6/9"),
    ("1/2","6/12"), ("2/3","7/7"), ("5/5","11/33"), ("4/12","1/4"),
    ("5/20","1/3"), ("5/15","2/5"), ("8/20","4/11"), ("8/22","3/3"),
    ("12/12","9/12"), ("30/40","3/5"), ("15/25","1/7"), ("2/14","50/100"),
    ("9/18","3/21"), ("2/14","6/3"), ("20/10","4/6"), ("10/15","12/12"),
    ("9/9","3/9"), ("10/30","2/10"), ("5/25","1/7"), ("11/77","4/6"),
    ("22/33","2/8"), ("7/28","4/8"), ("7/14","14/14"), ("21/21","7/21"),
    ("6/18","6/8"), ("3/4","2/4"), ("15/30","20/30"), ("14/21","1/5"),
    ("20/100","40/100"), ("4/10","3/9"), ("9/27","14/7"), ("18/9","15/30"),
    ("35/70","2/4")
]

# ---------------- FUNZIONI ----------------
def create_new_game():
    shuffled_tiles = TILES.copy()
    random.shuffle(shuffled_tiles)
    train_tile = dict(left=shuffled_tiles[0][0], right=shuffled_tiles[0][1])
    shelf1 = [dict(left=t[0], right=t[1]) for t in shuffled_tiles]
    shelf2 = shelf1.copy()
    random.shuffle(shelf2)
    return {
        "train": [train_tile],   # prima riga
        "train2": [],            # seconda riga vuota
        "p1_shelf": shelf1,
        "p2_shelf": shelf2,
        "current_player": 1,
        "scores": {"1":0, "2":0},
        "timer": 20,
        "last_message": "",
        "winner": None
    }

# ---------------- MULTI-SESSION ----------------
games = {}

@app.before_request
def assign_game_id():
    if "game_id" not in session:
        session["game_id"] = str(uuid.uuid4())
    if session["game_id"] not in games:
        games[session["game_id"]] = create_new_game()

# ---------------- HTML ----------------
HTML_PAGE = """ 
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Domino Frazioni</title>
<style>
@keyframes flash {
  0% { color: gold; text-shadow: 0 0 5px gold; }
  50% { color: red; text-shadow: 0 0 20px red; }
  100% { color: gold; text-shadow: 0 0 5px gold; }
}
body { font-family: Arial; text-align:center; margin:0; padding:0; }
#game-container { display:flex; flex-direction:column; height:100vh; }
#train-container { flex: 0 0 auto; margin: 10px auto; width: 95%; overflow-x: auto; }
#train, #train2 { display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; margin-bottom: 10px; }
.row { display:flex; flex-wrap: wrap; justify-content:center; margin:5px 0; }
.tile { display:flex; flex-direction:row; margin:5px; cursor:pointer; border:2px solid black; border-radius:5px; }
.side.selected { background-color: rgba(42,127,255,0.3); border:2px solid green !important; }
.side { padding:10px; width:50px; text-align:center; border-right:1px solid black; }
.side:last-child { border-right:none; }
.selected { border:2px solid blue !important; }
#p2_shelf .side.selected { background-color: rgba(255,106,42,0.3); }
#train .tile, #train2 .tile { border:2px solid black; }
#train2 { margin-top: 15px; border-top: 2px dashed gray; padding-top: 10px; }
#p1_shelf .tile { border:2px solid #2A7FFF; }
#p2_shelf .tile { border:2px solid #FF6A2A; }
.active { border-color: gold !important; box-shadow: 0 0 10px gold; }
#message { color:red; font-weight:bold; height:25px; }
#success { color:green; font-weight:bold; height:25px; }
#timer { font-size:20px; color:red; font-weight:bold; }
</style>
</head>
<body>
<div id="game-container">
  <div id="top-bar" style="display:flex; justify-content:space-between; align-items:center; padding:10px; border-bottom:2px solid black;">
    <div id="player1-info" style="flex:1; text-align:left;">
      <strong id="label1">Giocatore 1:</strong>
      <input id="name1" type="text" /> <button onclick="updateName(1)">Aggiorna</button><br><br>
      <select id="avatar1" onchange="updateAvatar(1)">
        <option value="avatar1.png">Avatar 1</option>
        <option value="avatar2.png">Avatar 2</option>
        <option value="avatar3.png">Avatar 3</option>
        <option value="avatar4.png">Avatar 4</option>
        <option value="avatar5.png">Avatar 5</option>
        <option value="avatar6.png">Avatar 6</option>
      </select><br>
      <img id="avatar_img1" src="{{ url_for('static', filename='avatar1.png') }}" width="100" height="150">
      <div>Punteggio: <span id="score1">0</span></div>
    </div>
    <div id="center-info" style="flex:1; text-align:center;">
      <h1>Domino Frazioni</h1>
       <button onclick="resetGame()" 
            style="padding:15px 30px; font-size:14px; background-color:#2A7FFF; color:white; border:none; border-radius:8px; cursor:pointer;">
          <strong>RIAVVIA PARTITA</strong>
       </button>
      <p style="font-size:16px; color:gray;">
        Abbina le frazioni equivalenti tra le tessere della tua collezione e quelle del treno.<br>
        Vince chi arriva prima a 10 punti.
      </p>
      <div id="turn" style="font-size:24px; color:blue; text-align:center; margin:10px;">Tocca a: Giocatore 1</div>
      <div id="message"></div>
      <div id="timer">Timer: 20s</div>
      <div id="success"></div>
    </div>
    <div id="player2-info" style="flex:1; text-align:right;">
      <strong id="label2">Giocatore 2:</strong>
      <input id="name2" type="text" /> <button onclick="updateName(2)">Aggiorna</button><br><br>
      <select id="avatar2" onchange="updateAvatar(2)">
        <option value="avatar1.png">Avatar 1</option>
        <option value="avatar2.png">Avatar 2</option>
        <option value="avatar3.png">Avatar 3</option>
        <option value="avatar4.png">Avatar 4</option>
        <option value="avatar5.png">Avatar 5</option>
        <option value="avatar6.png">Avatar 6</option>
      </select><br>
      <img id="avatar_img2" src="{{ url_for('static', filename='avatar1.png') }}" width="100" height="150">
      <div>Punteggio: <span id="score2">0</span></div>
    </div>
  </div>
  <!-- TRENO -->
  <div id="train-container">
    <h3>Treno</h3>
    <div id="train" class="row"></div>
    <div id="train2" class="row"></div>
  </div>
  <!-- CASSETTI -->
  <div id="shelves-container" style="display:flex; justify-content:space-between; padding:10px;">
    <div class="shelf-col" style="width:48%; border:2px solid black; border-radius:10px; padding:10px;">
      <h3 id="shelf_title1">Giocatore 1</h3>
      <div id="p1_shelf" class="row"></div>
    </div>
    <div class="shelf-col" style="width:48%; border:2px solid black; border-radius:10px; padding:10px;">
      <h3 id="shelf_title2">Giocatore 2</h3>
      <div id="p2_shelf" class="row"></div>
    </div>
  </div>
</div>
<script>
let selectedShelf=null, selectedTrain=null, lastPlayer=1, timer=20;
function updateName(playerNum){
  const input=document.getElementById("name"+playerNum);
  const name=(input.value||"Giocatore "+playerNum).trim();
  document.getElementById("label"+playerNum).innerText=name+":";
  document.getElementById("shelf_title"+playerNum).innerText=name;
  render();
}
function resetGame(){
  fetch("/reset", {method:"POST"}).then(()=> {
    // ricarica lo stato e aggiorna la UI
    render();
  });
}

function updateAvatar(playerNum){
  const select=document.getElementById("avatar"+playerNum);
  document.getElementById("avatar_img"+playerNum).src="/static/"+select.value;
}
function render() {
  fetch("/state").then(r => r.json()).then(data => {
    if (data.current_player !== lastPlayer) {
      selectedShelf = null;
      selectedTrain = null;
      lastPlayer = data.current_player;
      timer = data.timer;
    }
    function renderTrainRow(trainId, train) {
      const container = document.getElementById(trainId);
      container.innerHTML = "";
      train.forEach((tile, idx) => {
        const tileDiv = document.createElement("div");
        tileDiv.className = "tile";
        ["left", "right"].forEach(side => {
          const sideDiv = document.createElement("div");
          sideDiv.className = "side";
          sideDiv.innerText = tile[side];
          if ((idx === 0 && side === "left") || (idx === train.length - 1 && side === "right")) {
            sideDiv.onclick = () => { selectedTrain = { trainId, trainIdx: idx, side }; render(); tryPlace(); };
          }
          if (selectedTrain && selectedTrain.trainId === trainId && selectedTrain.trainIdx === idx && selectedTrain.side === side) {
            sideDiv.classList.add("selected");
          }
          tileDiv.appendChild(sideDiv);
        });
        container.appendChild(tileDiv);
      });
    }
    renderTrainRow("train", data.train);
    renderTrainRow("train2", data.train2);
    function renderShelf(shelfId, shelf) {
      const shelfDiv = document.getElementById(shelfId);
      shelfDiv.innerHTML = "";
      if ((shelfId === "p1_shelf" && data.current_player === 1) || (shelfId === "p2_shelf" && data.current_player === 2)) shelfDiv.classList.add("active");
      else shelfDiv.classList.remove("active");
      shelf.forEach((t, i) => {
        if (!t) return;
        const tileDiv = document.createElement("div");
        tileDiv.className = "tile";
        ["left", "right"].forEach(side => {
          const sideDiv = document.createElement("div");
          sideDiv.className = "side";
          sideDiv.innerText = t[side];
          if (shelfDiv.classList.contains("active")) sideDiv.onclick = () => { selectedShelf = { shelfId, idx: i, side }; render(); tryPlace(); };
          if (selectedShelf && selectedShelf.shelfId === shelfId && selectedShelf.idx === i && selectedShelf.side === side) sideDiv.classList.add("selected");
          tileDiv.appendChild(sideDiv);
        });
        shelfDiv.appendChild(tileDiv);
      });
    }
    renderShelf("p1_shelf", data.p1_shelf);
    renderShelf("p2_shelf", data.p2_shelf);
    document.getElementById("score1").innerText = data.scores["1"];
    document.getElementById("score2").innerText = data.scores["2"];
    const p1Name = document.getElementById("name1").value || "Giocatore 1";
    const p2Name = document.getElementById("name2").value || "Giocatore 2";
    document.getElementById("turn").innerText = "Tocca a: " + (data.current_player === 1 ? p1Name : p2Name);
    document.getElementById("timer").innerText = "Timer: " + timer + "s";
    const winnerDiv = document.getElementById("success");
    if (data.winner) {
      const playerName = data.winner === 1 ? document.getElementById("name1").value : document.getElementById("name2").value;
      winnerDiv.innerHTML = playerName + " ha vinto la partita! 🎉";
      winnerDiv.style.fontSize = "30px";
      winnerDiv.style.animation = "flash 1s infinite";
    } else {
      winnerDiv.innerHTML = "";
      winnerDiv.style.animation = "";
    }
    const msgDiv = document.getElementById("message");
    if (data.last_message && !msgDiv.dataset.shown) {
      msgDiv.innerText = data.last_message === "success" ? "Accoppiamento corretto!" : "Le frazioni non sono equivalenti!";
      msgDiv.dataset.shown = "true";
      setTimeout(() => { msgDiv.innerText = ""; msgDiv.dataset.shown = ""; }, 2000);
    }
  });
}
function tryPlace() {
  if (!selectedShelf || !selectedTrain) return;
  const payload = { shelfId: selectedShelf.shelfId, idx: selectedShelf.idx, shelfSide: selectedShelf.side, trainId: selectedTrain.trainId, trainIdx: selectedTrain.trainIdx, trainSide: selectedTrain.side };
  fetch("/place", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) })
    .then(r => r.json()).then(data => {
      if (data.result === "success") { selectedShelf = null; selectedTrain = null; timer = 20; }
      render();
    });
}
let timeoutSent = false;
function startTimer(){
  setInterval(()=>{
    if(timer>0){
      timer--;
    } else if(!timeoutSent){
      timeoutSent = true;
      fetch("/timeout",{method:"POST"}).then(()=>{ timer=20; timeoutSent=false; });
    }
    render();
  },1000);
}
render();
startTimer();
</script>
</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/state")
def state():
    game_state = games[session["game_id"]]
    snapshot = dict(game_state)
    snapshot["last_message"] = game_state.get("last_message", "")
    game_state["last_message"] = ""
    return jsonify(snapshot)

@app.route("/reset", methods=["POST"])
def reset():
    games[session["game_id"]] = create_new_game()
    return jsonify({"message": "Partita resettata"})

@app.route("/timeout", methods=["POST"])
def timeout():
    game_state = games[session["game_id"]]
    if game_state["winner"]:
        return jsonify({"message": "La partita è già finita"})

    # non controlliamo più il timer del server, ci fidiamo del client
    game_state["current_player"] = 3 - game_state["current_player"]
    game_state["timer"] = 20
    return jsonify({"message": f"Turno cambiato al giocatore {game_state['current_player']}"})


@app.route("/place", methods=["POST"])
def place():
    game_state = games[session["game_id"]]
    data = request.json

    shelfId = data["shelfId"]
    idx = data["idx"]
    shelfSide = data["shelfSide"]
    trainId = data["trainId"]
    trainIdx = data["trainIdx"]
    trainSide = data["trainSide"]

    player_num = 1 if shelfId=="p1_shelf" else 2
    if game_state["current_player"] != player_num:
        return jsonify({"message":"Non è il tuo turno!","result":"fail"})

    shelf = game_state["p1_shelf"] if player_num==1 else game_state["p2_shelf"]
    tile = shelf[idx]
    if not tile:
        return jsonify({"message":"Tessera già usata!","result":"fail"})

    train = game_state[trainId]
    train_tile = train[trainIdx]

    left_tile = Fraction(tile["left"])
    right_tile = Fraction(tile["right"])
    left_train = Fraction(train_tile["left"])
    right_train = Fraction(train_tile["right"])

    placed = False
    new_tile = tile.copy()

    # aggancio logica identica
    if trainSide == "left":
        if right_tile == left_train:
            train.insert(0, new_tile)
            placed = True
        elif left_tile == left_train:
            new_tile = {"left": tile["right"], "right": tile["left"]}
            train.insert(0, new_tile)
            placed = True
    else:
        if left_tile == right_train:
            train.append(new_tile)
            placed = True
        elif right_tile == right_train:
            new_tile = {"left": tile["right"], "right": tile["left"]}
            train.append(new_tile)
            placed = True

    if not placed:
        return jsonify({"message":"Le frazioni non sono equivalenti!","result":"fail"})

    shelf[idx] = None
    game_state["scores"][str(player_num)] += 1

    # creazione seconda riga indipendente
    if trainId=="train" and len(game_state["train"])==10 and not game_state["train2"]:
        remaining_tiles = [t for t in TILES if {"left": t[0], "right": t[1]} not in game_state["train"]]
        if remaining_tiles:
            t = random.choice(remaining_tiles)
            game_state["train2"].append({"left": t[0], "right": t[1]})

    if game_state["scores"][str(player_num)] >= 10:
        game_state["winner"] = player_num
    else:
        game_state["current_player"] = 3 - player_num
        game_state["timer"] = 20

    game_state["last_message"] = "success"
    return jsonify({"message":"Accoppiamento corretto!","result":"success"})

if __name__ == "__main__":
    app.run(debug=True)
