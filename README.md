# Spot On! ⚽

> **Probability-driven football predictions — no guesswork.**

Spot On! is a web-based football match prediction system that uses rigorous statistical modelling to calculate the likelihood of every possible outcome for a given fixture.

---

## How it works

### Poisson Model

Football scoring can be modelled as a Poisson process: each team scores goals at an approximately random rate determined by their historical attack and defence performance. The model computes:

- **λ_home** — expected goals for the home side
- **λ_away** — expected goals for the away side

From these two rates, a **9×9 probability matrix** is built covering all scorelines from 0–0 to 8–8. Cells below the diagonal sum to a home win, on the diagonal to a draw, and above to an away win.

### Dixon-Coles Correction

Plain Poisson underestimates 0–0 and 1–1 draws while overestimating other low-scoring outcomes. The Dixon-Coles correction (1997) applies tau factors to these four critical scorelines using an empirical correlation parameter **ρ = −0.13**:

| Score | Tau factor       |
|-------|------------------|
| 0–0   | 1 − λh·λa·ρ      |
| 1–0   | 1 + λa·ρ         |
| 0–1   | 1 + λh·ρ         |
| 1–1   | 1 − ρ            |

After the correction the matrix is renormalised to sum to 1.

---

## Getting a free API key

1. Go to [football-data.org](https://www.football-data.org/)
2. Click **Register** and create a free account
3. Copy your API key from the user dashboard
4. Paste it into `backend/.env`:
   ```
   FOOTBALL_DATA_API_KEY=your_key_here
   ```

> **No key?** The system works with built-in demo data — great for exploring the interface before setting up the API.

---

## How to run

> **Prerequisite:** Python 3.10 or higher ([python.org](https://python.org)).

### Linux / macOS

```bash
chmod +x run.sh
./run.sh
```

### Windows

Double-click `run.bat` or run it from the Command Prompt:

```bat
run.bat
```

> **Windows tip:** make sure `python` is on your system PATH. When installing Python, check the **"Add Python to PATH"** option.

### 2. Open the frontend

Open `frontend/index.html` directly in your browser — no web server required.

### 3. Use it

1. Select a league (e.g. Premier League)
2. Choose the home and away teams
3. Click **Analyse**
4. Get win/draw/loss probabilities and the 10 most likely scorelines in seconds

---

## Example output

```
Manchester City  vs  Manchester United
Premier League

  Home Win     Draw      Away Win
  Man. City            Man. Utd
   52.3%        24.1%      23.6%

Expected goals: Man. City 1.84 · Man. Utd 0.97

Most likely scorelines:
  2-1  11.2%  |  1-0  9.8%  |  2-0  9.1%  |  1-1  8.7%  |  3-1  6.7%
  2-2   4.8%  |  0-0  4.4%  |  3-0  4.2%  |  0-1  3.8%  |  1-2  3.3%

Based on 38 matches · Confidence: High
```

---

## Supported leagues

| ID    | League                  | Country   |
|-------|-------------------------|-----------|
| `PL`  | Premier League          | England   |
| `BL1` | Bundesliga              | Germany   |
| `SA`  | Serie A                 | Italy     |
| `PD`  | La Liga                 | Spain     |
| `FL1` | Ligue 1                 | France    |
| `BSB` | Brasileirão Série A     | Brazil    |

---

## Known limitations

- **Rate limit:** The free football-data.org plan allows **10 requests per minute**. If you run many analyses in quick succession, wait a moment before retrying.
- **Match history:** The model uses up to **38 recent matches** per team in the selected league. Newly promoted sides or teams with few matches will receive a **low confidence** rating.
- **Leagues:** Only the 6 leagues listed above are supported on the free API tier.
- **No live data:** Results do not account for injuries, line-ups, or weather conditions — only statistical history.
- **Cache:** Team data is cached for 24 h and match data for 6 h to respect the rate limit.

---

## Project structure

```
spot-on/
├── backend/
│   ├── main.py          # FastAPI: /api/leagues, /api/teams, /api/predict endpoints
│   ├── model.py         # Poisson + Dixon-Coles implementation
│   ├── data_service.py  # football-data.org client + SQLite cache
│   ├── requirements.txt
│   └── .env.example     # Configuration template (copy to .env)
├── frontend/
│   ├── index.html       # SPA with 3 states: selection, loading, result
│   ├── style.css        # Dark theme, animations, responsive layout
│   └── app.js           # Full client-side logic
├── run.sh               # Startup script (Linux/macOS)
├── run.bat              # Startup script (Windows)
└── README.md
```

---

*Spot On! — For educational and statistical purposes only. Do not use for gambling.*
