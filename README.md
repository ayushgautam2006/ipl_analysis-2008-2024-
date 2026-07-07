# IPL Analysis & Match Predictor

Comprehensive analysis and AI-powered match winner prediction for IPL (Indian Premier League) cricket data from 2008–2024.

## Project Structure

```
ipl_analysis/
├── Data/                           # Raw data files
│   ├── matches.csv                 # Match metadata & results (1090 matches)
│   ├── deliveries.csv              # Ball-by-ball data (260K+ records)
│   └── deliveries_cleaned.csv      # Cleaned deliveries dataset
│
├── app/                            # Flask web application
│   ├── app.py                      # Backend API (predict, meta, team-stats)
│   ├── templates/
│   │   └── index.html              # Frontend UI
│   └── static/
│       ├── style.css               # Dark glassmorphism theme
│       └── script.js               # Charts, team selection, API calls
│
├── notebooks/
│   └── ipl_insights.ipynb          # EDA notebook (42 cells)
│
├── train_model.ipynb               # Feature engineering + Model training notebook
├── model.pkl                       # Trained Random Forest model (generated)
├── encoder.pkl                     # Label encoders & lookup (generated)
├── team_stats.json                 # Pre-computed team analytics (generated)
├── Output_Files/                   # Analysis outputs & exports
├── Dockerfile                      # Docker deployment config
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Running the Match Predictor Web App

### Prerequisites

- Python 3.10+
- `pip`

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

### 2. Train the model

> Skip this step if `predictor/model.pkl` already exists.

Open and run all cells in the training notebook:

```powershell
jupyter notebook train_model.ipynb
```

This reads `Data/matches.csv` and `Data/deliveries.csv`, trains a Random Forest classifier, and saves `model.pkl`, `encoder.pkl`, and `team_stats.json` directly in the project root directory.

### 3. Start the web app

```powershell
python app/app.py
```

### 4. Open in browser

```
http://127.0.0.1:5000
```

---

## Running with Docker

```powershell
# Build and start
docker-compose up -d

# Open in browser
http://localhost:5000

# Stop
docker-compose down
```

> The Docker image bundles the pre-trained model files. Re-run `docker-compose up -d --build` after retraining the model locally.

---

## How to Use the Predictor

1. Select **Team 1** and **Team 2** from the dropdowns
2. Optionally choose a **Venue**, **Toss Winner**, and **Toss Decision** for a more precise prediction
3. Click **Predict Winner**
4. View the predicted winner, win probability bars, head-to-head record, and full team analysis

---

## Analysis Sections (Notebook)

To run the EDA notebook:

```powershell
jupyter notebook notebooks/ipl_insights.ipynb
```

Sections covered:
1. **Data Cleaning** — Type conversion, missing values, duplicates
2. **Venue Analysis** — Performance by location, pitch characteristics
3. **Player Analysis** — Top batters (runs, SR), Top bowlers (wickets, economy)
4. **Team Performance** — Win rates, head-to-head records
5. **Innings Breakdown** — Phase-wise analysis (Powerplay / Middle / Death)
6. **Dismissal Patterns** — Methods, vulnerable players, fielding stats
7. **Comprehensive Dashboard** — 9-panel visualization summary

---

## Requirements

```
flask>=3.0.0
numpy>=1.26.0
pandas>=2.1.0
scikit-learn>=1.4.0
gunicorn>=21.2.0
```

---

## Key Stats

| Metric | Value |
|---|---|
| Matches analyzed | 1,090 |
| Deliveries | 260,000+ |
| Teams | 16 IPL franchises |
| Venues | 58 unique grounds |
| Model accuracy | ~55.5% |
| Model type | Random Forest Classifier |

---

*Data: IPL 2008–2024*
