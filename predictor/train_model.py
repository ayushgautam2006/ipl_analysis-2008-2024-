"""
IPL Match Winner Predictor — Training Script
Trains a Random Forest model on historical IPL data (2008-2024).
Saves model, encoders, and team statistics for the Flask app.
"""
import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "Data")
OUT_DIR   = os.path.dirname(os.path.abspath(__file__))

MATCHES_CSV    = os.path.join(DATA_DIR, "matches.csv")
DELIVERIES_CSV = os.path.join(DATA_DIR, "deliveries.csv")
MODEL_PKL      = os.path.join(OUT_DIR,  "model.pkl")
ENCODER_PKL    = os.path.join(OUT_DIR,  "encoder.pkl")
STATS_JSON     = os.path.join(OUT_DIR,  "team_stats.json")

# ── Team name normalisation (franchise renames) ────────────────────────────────
TEAM_NORM = {
    "Delhi Daredevils":        "Delhi Capitals",
    "Kings XI Punjab":         "Punjab Kings",
    "Rising Pune Supergiant":  "Rising Pune Supergiants",
    "Deccan Chargers":         "Deccan Chargers",
}

def normalise(name):
    return TEAM_NORM.get(str(name).strip(), str(name).strip())


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load & clean data
# ─────────────────────────────────────────────────────────────────────────────
print("Loading data …")
matches    = pd.read_csv(MATCHES_CSV)
deliveries = pd.read_csv(DELIVERIES_CSV)

# Normalise team names
for col in ["team1", "team2", "toss_winner", "winner"]:
    matches[col] = matches[col].apply(lambda x: normalise(x) if pd.notna(x) else x)

for col in ["batting_team", "bowling_team"]:
    deliveries[col] = deliveries[col].apply(lambda x: normalise(x) if pd.notna(x) else x)

# Keep only completed matches (winner known)
matches = matches[
    matches["winner"].notna() &
    (matches["winner"] != "NA") &
    (matches["winner"] != "")
].copy()

# Season → integer year
matches["season_year"] = matches["season"].apply(
    lambda s: int(str(s).split("/")[0])
)

# Venue: fill missing
matches["venue"] = matches["venue"].fillna("Unknown Venue")

print(f"  Matches loaded: {len(matches)}")
print(f"  Deliveries loaded: {len(deliveries)}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Pre-compute team & H2H statistics
# ─────────────────────────────────────────────────────────────────────────────
print("Computing team statistics …")

all_teams = sorted(set(matches["team1"].unique()) | set(matches["team2"].unique()))

# ── Overall win / loss record ──────────────────────────────────────────────
team_records = {}
for team in all_teams:
    tm = matches[(matches["team1"] == team) | (matches["team2"] == team)]
    wins = matches[matches["winner"] == team]
    team_records[team] = {
        "matches": int(len(tm)),
        "wins":    int(len(wins)),
        "losses":  int(len(tm) - len(wins)),
        "win_rate": round(len(wins) / max(len(tm), 1), 4),
        "seasons":  sorted([str(s) for s in tm["season"].unique().tolist()]),
    }

# ── H2H record ────────────────────────────────────────────────────────────
h2h = {}   # key = frozenset{t1, t2}, value = {team: wins}
for _, row in matches.iterrows():
    t1, t2, winner = row["team1"], row["team2"], row["winner"]
    key = tuple(sorted([t1, t2]))
    if key not in h2h:
        h2h[key] = {t1: 0, t2: 0, "total": 0}
    h2h[key]["total"] += 1
    if winner in h2h[key]:
        h2h[key][winner] += 1

# ── Per-venue win rates per team ───────────────────────────────────────────
venue_wins = {}
for team in all_teams:
    tm = matches[(matches["team1"] == team) | (matches["team2"] == team)]
    vw = {}
    for venue, grp in tm.groupby("venue"):
        w = (grp["winner"] == team).sum()
        vw[venue] = {"played": int(len(grp)), "wins": int(w)}
    # top 3 venues by wins
    sorted_venues = sorted(vw.items(), key=lambda x: x[1]["wins"], reverse=True)[:3]
    venue_wins[team] = {v: d for v, d in sorted_venues}

# ── Batting stats from deliveries ─────────────────────────────────────────
print("Computing batting/bowling stats …")
bat_stats = (
    deliveries.groupby("batter")["batsman_runs"].sum().reset_index()
              .rename(columns={"batsman_runs": "total_runs"})
)
bat_team = (
    deliveries.groupby(["batter", "batting_team"])["batsman_runs"].sum()
              .reset_index()
              .sort_values("batsman_runs", ascending=False)
              .drop_duplicates("batter")
              .rename(columns={"batsman_runs": "runs", "batting_team": "team"})
)
bat_full = bat_stats.merge(bat_team[["batter", "team"]], on="batter", how="left")

# ── Bowling stats from deliveries ─────────────────────────────────────────
bowl_stats = (
    deliveries[deliveries["is_wicket"] == 1]
    .groupby("bowler").size().reset_index(name="wickets")
)
bowl_team = (
    deliveries.groupby(["bowler", "bowling_team"])["total_runs"].count()
              .reset_index()
              .sort_values("total_runs", ascending=False)
              .drop_duplicates("bowler")
              .rename(columns={"total_runs": "balls", "bowling_team": "team"})
)
bowl_full = bowl_stats.merge(bowl_team[["bowler", "team"]], on="bowler", how="left")

# ── Top batters & bowlers per team ─────────────────────────────────────────
top_batters = {}
top_bowlers = {}
for team in all_teams:
    tb = bat_full[bat_full["team"] == team].nlargest(5, "total_runs")
    top_batters[team] = [
        {"name": r["batter"], "runs": int(r["total_runs"])}
        for _, r in tb.iterrows()
    ]
    tb2 = bowl_full[bowl_full["team"] == team].nlargest(5, "wickets")
    top_bowlers[team] = [
        {"name": r["bowler"], "wickets": int(r["wickets"])}
        for _, r in tb2.iterrows()
    ]

# ── Average score per match ────────────────────────────────────────────────
avg_scores = {}
match_scores = (
    deliveries.groupby(["match_id", "batting_team"])["total_runs"].sum().reset_index()
)
for team in all_teams:
    ts = match_scores[match_scores["batting_team"] == team]["total_runs"]
    avg_scores[team] = round(float(ts.mean()), 1) if len(ts) > 0 else 0.0

# ── Assemble full stats dict ───────────────────────────────────────────────
team_stats = {}
for team in all_teams:
    team_stats[team] = {
        **team_records.get(team, {}),
        "avg_score":    avg_scores.get(team, 0),
        "top_batters":  top_batters.get(team, []),
        "top_bowlers":  top_bowlers.get(team, []),
        "best_venues":  venue_wins.get(team, {}),
    }

# ── Save stats JSON ───────────────────────────────────────────────────────
with open(STATS_JSON, "w") as f:
    json.dump({"teams": team_stats, "h2h": {str(k): v for k, v in h2h.items()}}, f, indent=2)
print(f"  Saved -> {STATS_JSON}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Build feature matrix
# ─────────────────────────────────────────────────────────────────────────────
print("Building feature matrix …")

le_team  = LabelEncoder()
le_venue = LabelEncoder()

le_team.fit(all_teams)
le_venue.fit(matches["venue"].unique())

# Total win rates (global, for prediction)
global_wr = {t: team_records[t]["win_rate"] for t in all_teams}

def h2h_win_rate(t1, t2):
    """team1's win rate in h2h matches."""
    key = tuple(sorted([t1, t2]))
    data = h2h.get(key, {})
    total = data.get("total", 0)
    if total == 0:
        return 0.5
    return data.get(t1, 0) / total

rows = []
for _, row in matches.iterrows():
    t1, t2, winner = row["team1"], row["team2"], row["winner"]
    if winner not in [t1, t2]:
        continue
    try:
        t1_enc    = le_team.transform([t1])[0]
        t2_enc    = le_team.transform([t2])[0]
        venue_enc = le_venue.transform([row["venue"]])[0]
    except Exception:
        continue

    target        = 1 if winner == t1 else 0
    toss_is_t1    = 1 if row["toss_winner"] == t1 else 0
    toss_bat      = 1 if row["toss_decision"] == "bat" else 0
    t1_wr         = global_wr.get(t1, 0.5)
    t2_wr         = global_wr.get(t2, 0.5)
    h2h_wr        = h2h_win_rate(t1, t2)

    rows.append({
        "t1_enc":     t1_enc,
        "t2_enc":     t2_enc,
        "toss_is_t1": toss_is_t1,
        "toss_bat":   toss_bat,
        "venue_enc":  venue_enc,
        "season_yr":  row["season_year"],
        "t1_wr":      t1_wr,
        "t2_wr":      t2_wr,
        "h2h_wr":     h2h_wr,
        "wr_diff":    t1_wr - t2_wr,
        "target":     target,
    })

df_feat = pd.DataFrame(rows)

FEATURE_COLS = [
    "t1_enc", "t2_enc", "toss_is_t1", "toss_bat",
    "venue_enc", "season_yr", "t1_wr", "t2_wr", "h2h_wr", "wr_diff"
]

X = df_feat[FEATURE_COLS].values
y = df_feat["target"].values

print(f"  Feature matrix: {X.shape}, class balance: {y.mean():.3f}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Train model
# ─────────────────────────────────────────────────────────────────────────────
print("Training Random Forest …")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=5,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"\n  Test Accuracy : {acc*100:.1f}%")
print(classification_report(y_test, y_pred, target_names=["team2 wins", "team1 wins"]))

# Feature importance
fi = sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1])
print("\n  Feature Importances:")
for feat, imp in fi:
    print(f"    {feat:15s}: {imp:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Save model & encoders
# ─────────────────────────────────────────────────────────────────────────────
with open(MODEL_PKL, "wb") as f:
    pickle.dump(model, f)

encoder_bundle = {
    "le_team":       le_team,
    "le_venue":      le_venue,
    "global_wr":     global_wr,
    "h2h":           h2h,
    "all_teams":     all_teams,
    "all_venues":    sorted(matches["venue"].unique().tolist()),
    "feature_cols":  FEATURE_COLS,
    "accuracy":      round(acc * 100, 1),
}
with open(ENCODER_PKL, "wb") as f:
    pickle.dump(encoder_bundle, f)

print(f"\n  Model   -> {MODEL_PKL}")
print(f"  Encoder -> {ENCODER_PKL}")
print("\nTraining complete!")
