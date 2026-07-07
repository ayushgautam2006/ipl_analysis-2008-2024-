"""
IPL Match Winner Predictor — Flask Backend
Works with the current 10-feature RandomForest encoder.
"""
import os, json, pickle
import numpy as np
from flask import Flask, request, jsonify, render_template

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PKL   = os.path.join(BASE_DIR, "model.pkl")
ENCODER_PKL = os.path.join(BASE_DIR, "encoder.pkl")
STATS_JSON  = os.path.join(BASE_DIR, "team_stats.json")

app = Flask(__name__)

# ── Load artefacts ────────────────────────────────────────────────────────────
print("Loading model artefacts...")
with open(MODEL_PKL,   "rb") as f: model      = pickle.load(f)
with open(ENCODER_PKL, "rb") as f: enc        = pickle.load(f)
with open(STATS_JSON,  "r")  as f: stats_data = json.load(f)

le_team   = enc["le_team"]
le_venue  = enc["le_venue"]
global_wr = enc["global_wr"]
h2h_data  = enc["h2h"]          # {tuple: {team: wins, total: n}}
all_teams = enc["all_teams"]
all_venues= enc["all_venues"]
model_acc = enc.get("accuracy", 0)
team_stats= stats_data["teams"]
h2h_stats = stats_data["h2h"]

TEAM_NORM = {
    "Delhi Daredevils":       "Delhi Capitals",
    "Kings XI Punjab":        "Punjab Kings",
    "Rising Pune Supergiant": "Rising Pune Supergiants",
}
def normalise(name):
    return TEAM_NORM.get(str(name).strip(), str(name).strip())

def h2h_win_rate(t1, t2):
    key = tuple(sorted([t1, t2]))
    data = h2h_data.get(key, {})
    total = data.get("total", 0)
    if total == 0:
        return 0.5
    return data.get(t1, 0) / total

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/meta")
def meta():
    return jsonify({
        "teams":    all_teams,
        "venues":   all_venues,
        "accuracy": model_acc,
    })

@app.route("/api/predict", methods=["POST"])
def predict():
    data  = request.get_json(force=True)
    t1    = normalise(data.get("team1", ""))
    t2    = normalise(data.get("team2", ""))
    venue = data.get("venue", "") or ""
    toss_w= normalise(data.get("toss_winner", t1) or t1)
    toss_d= data.get("toss_decision", "bat")

    if t1 not in all_teams or t2 not in all_teams:
        return jsonify({"error": "Unknown team"}), 400
    if t1 == t2:
        return jsonify({"error": "Teams must be different"}), 400

    # Encode teams
    t1_enc = int(le_team.transform([t1])[0])
    t2_enc = int(le_team.transform([t2])[0])

    # Encode venue (fallback to median if unknown)
    if venue and venue in le_venue.classes_:
        venue_enc = int(le_venue.transform([venue])[0])
    else:
        venue_enc = int(np.median(np.arange(len(le_venue.classes_))))

    toss_is_t1 = 1 if toss_w == t1 else 0
    toss_bat   = 1 if toss_d == "bat" else 0
    t1_wr      = global_wr.get(t1, 0.5)
    t2_wr      = global_wr.get(t2, 0.5)
    h2h_wr     = h2h_win_rate(t1, t2)

    X = np.array([[
        t1_enc, t2_enc, toss_is_t1, toss_bat,
        venue_enc, 2024, t1_wr, t2_wr, h2h_wr, t1_wr - t2_wr
    ]])

    proba   = model.predict_proba(X)[0]
    t1_prob = float(proba[1])   # class=1 → t1 wins
    t2_prob = float(proba[0])

    predicted_winner = t1 if t1_prob >= 0.5 else t2

    key     = str(tuple(sorted([t1, t2])))
    h2h_row = h2h_stats.get(key, {})

    return jsonify({
        "winner":      predicted_winner,
        "team1":       t1,
        "team2":       t2,
        "team1_prob":  round(t1_prob * 100, 1),
        "team2_prob":  round(t2_prob * 100, 1),
        "h2h": {
            "total":      h2h_row.get("total", 0),
            "team1_wins": h2h_row.get(t1, 0),
            "team2_wins": h2h_row.get(t2, 0),
        },
        "team1_stats": team_stats.get(t1, {}),
        "team2_stats": team_stats.get(t2, {}),
    })

@app.route("/api/team-stats/<path:team>")
def team_stats_endpoint(team):
    team = normalise(team)
    if team not in team_stats:
        return jsonify({"error": "Team not found"}), 404
    data = team_stats[team]
    h2h_all = {}
    for k, v in h2h_stats.items():
        teams_in_key = eval(k)
        if team in teams_in_key:
            opp = [t for t in teams_in_key if t != team][0]
            h2h_all[opp] = {"played": v.get("total", 0), "won": v.get(team, 0)}
    return jsonify({**data, "h2h_vs_all": h2h_all})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
